from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from io import BytesIO
from fastapi.responses import Response
from app.bll.acuerdoPago_bll import insertar_excel_acuerdos_bytes, pop_dni_get, obtener_registro
import aiofiles
from pathlib import Path
from typing import Optional

router = APIRouter()

SAVE_DIR = Path(r"\\BITMXL94920DQ\Uipat Datos\Acuerdo Pago")

@router.post("/excel/guardarAcuerdo")
async def guardar_acuerdos_excel(file: UploadFile = File(...)):

    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No se proporcionó un archivo")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="El archivo está vacío")
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo es demasiado grande (máximo 10MB)")

        # 1) Insertar en BD
        result = insertar_excel_acuerdos_bytes(content)

        # 2) Preparar ruta absoluta
        if not SAVE_DIR.is_absolute():
            raise HTTPException(status_code=500, detail="SAVE_DIR no es una ruta absoluta. Edítala en el archivo API.")
        SAVE_DIR.mkdir(parents=True, exist_ok=True)

        # 3) Obtener DNI para el nombre del archivo (usa el primero no vacío si viene de la BLL)
        dni_list = result.get("dni_list") if isinstance(result, dict) else None
        dni = next((d for d in (dni_list or []) if d), "SIN_DNI")

        # 4) Sanitizar y armar nombre final .xlsx
        def _sanitize(name: str) -> str:
            for ch in '<>:"/\\|?*':
                name = name.replace(ch, "_")
            return name.strip() or "SIN_DNI"

        out_name = f"{_sanitize(dni)}.xlsx"
        out_path = SAVE_DIR / out_name

        # 5) Guardar bytes tal cual
        async with aiofiles.open(out_path, "wb") as f:
            await f.write(content)

        resp = {
            "success": True,
            "archivo_subido": file.filename,
            "tamaño_bytes": len(content),
            "dni_usado_para_nombre": dni,
            "ruta_guardado": str(out_path),
            **(result if isinstance(result, dict) else {})
        }
        return resp

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")

@router.get("/excel/dni")
async def obtener_y_marcar_dni(
    estado_from: str | None = Query(default="PENDIENTE"),
    estado_to:   str | None = Query(default="ENVIADO"),
):
    """
    Pop atómico: elige 1 DNI aleatorio en estado_from y lo marca a estado_to.
    200 → ya quedó marcado. 404 → no hay disponible.
    """
    try:
        dni = pop_dni_get(estado_from, estado_to)
        return {"dni": dni}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")
    
@router.post("/acuerdos/marcar-enviada", tags=["Acuerdo Pago"])
async def acuerdos_marcar_enviada_y_devolver(
    solo_activos: bool = Query(default=True),
    exige_estado: Optional[str] = Query(default="ACTIVO"),
):
    """
    Pop atómico: marca enviada=1 en 1 registro pendiente y
    devuelve los **datos del registro** ya marcado.
    404 → no había pendientes.
    """
    try:
        data = obtener_registro(solo_activos=solo_activos, exige_estado=exige_estado)
        if not data:
            raise HTTPException(status_code=404, detail="No hay acuerdos pendientes por enviar")
        return data  # 200 con el JSON del registro actualizado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")