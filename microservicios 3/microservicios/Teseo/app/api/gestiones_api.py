from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from io import BytesIO
from fastapi.responses import Response
from app.bll.gestiones_bll import insertar_excel_acuerdos_bytes
import aiofiles
from pathlib import Path
from typing import Optional

router = APIRouter()

SAVE_DIR = Path(r"\\172.18.73.76\Uipat Datos\Gestiones")

@router.post("/excel/guardarGestion")
async def guardar_gestiones_excel(file: UploadFile = File(...)):

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

        out_name = f"{_sanitize(dni)}.xlsx" #GESTION_123456789
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

