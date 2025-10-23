from fastapi import APIRouter, HTTPException, Query, Form, UploadFile, File, Request, Body
from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.bll.envioWhatsapp_bll import (
    guardar_mensajes_bulk_form,
    obtener_pendientes_y_marcar,
    obtener_pendientes_y_marcar_por_campana,
    actualizar_tiene_whatsapp,
    obtener_clientes
)
from starlette.concurrency import run_in_threadpool
import asyncio

router = APIRouter(prefix="", tags=["Envio WhatsApp"])

@router.post("/whatsapp/registrar")
async def registrar_mensajes(
    request: Request,
    numeros: List[str] = Form(...),
    mensaje: str = Form(...),
    campana: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    idUsuarioApp: Optional[int] = Form(None)  # fallback si no viene header
):
    try:
        # 1) Preferir header inyectado por Gateway (p. ej. desde JWT)
        user_from_header = request.headers.get("X-User-Id")
        id_usuario_app: Optional[int] = None
        if user_from_header and str(user_from_header).strip().isdigit():
            id_usuario_app = int(user_from_header)
        elif idUsuarioApp is not None:
            id_usuario_app = idUsuarioApp  # fallback desde form

        # 2) Llamar BLL con el user-id
        return {
            "ok": True,
            **guardar_mensajes_bulk_form(
                numeros=numeros,
                mensaje=mensaje,
                campana=campana,
                files=files,
                id_usuario_app=id_usuario_app
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/whatsapp/pendientes-json")
def get_pendientes_json(
    estado: str = Query("ENVIADO", description="Estado a marcar al entregar al RPA"),
    limit: int = Query(1, ge=1, le=5000)  # si quieres 1 aleatorio como antes
):
    try:
        return obtener_pendientes_y_marcar(limit=limit, estado=estado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whatsapp/pendientes-json-npl")
def get_pendientes_json_npl(
    estado: str = Query("ENVIADO", description="Estado a marcar al entregar al RPA"),
    limit: int = Query(1, ge=1, le=5000)
):
    try:
        return obtener_pendientes_y_marcar_por_campana("NPL", limit=limit, estado=estado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whatsapp/pendientes-json-jcap")
def get_pendientes_json_jcap(
    estado: str = Query("ENVIADO", description="Estado a marcar al entregar al RPA"),
    limit: int = Query(1, ge=1, le=5000)
):
    try:
        return obtener_pendientes_y_marcar_por_campana("JCAP", limit=limit, estado=estado)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ActualizarTieneWhatsAppRequest(BaseModel):
    numero: str
    tiene_whatsapp: str  # Recibimos como string desde UiPath

@router.post("/whatsapp/actualizar-tiene")
async def post_actualizar_tiene_uipath_compatible(request: Request):
    """
    Endpoint compatible con UiPath - maneja el JSON raw para evitar problemas de parsing
    """
    request.client.host if request.client else "unknown"
    dict(request.headers)
    
    try:
        raw_body = await request.body()
        raw_str = raw_body.decode("utf-8", errors="replace")  
        
        len(raw_body)
        raw_body.hex()[:200] + "..." if len(raw_body) > 100 else raw_body.hex()
        repr(raw_str)
        
        # Intentar parsear JSON de múltiples formas
        body = None
        parse_error = None
        
        # Método 1: JSON estándar
        try:
            import json
            body = json.loads(raw_str)
        except json.JSONDecodeError as e1:
            parse_error = f"json.loads failed: {e1}"
            print("✗ json.loads failed:", e1)
            
            # Método 2: Limpiar caracteres problemáticos
            try:
                clean_str = raw_str.strip()
                if clean_str.startswith('\ufeff'):
                    clean_str = clean_str[1:]
                body = json.loads(clean_str)
            except json.JSONDecodeError as e2:
                print("✗ Cleaning failed:", e2)
                # Método 3: Intenta como form-data o query params
                try:
                    from urllib.parse import parse_qs
                    if "=" in raw_str and "&" in raw_str:
                        parsed = parse_qs(raw_str)
                        body = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
                except Exception as e3:
                    print("✗ Form-data parsing failed:", e3)
        
        if body is None:
            raise HTTPException(
                status_code=400, 
                detail=f"No se pudo parsear el JSON. Error: {parse_error}. Raw: {raw_str[:200]}"
            )
        
        
        numero = body.get("numero")
        tiene_whatsapp_in = body.get("tiene_whatsapp")
        
        print(f"Extracted - numero: {numero!r}, tiene_whatsapp: {tiene_whatsapp_in!r}")
        
        if not numero:
            raise ValueError("Falta campo 'numero'")
        
        if tiene_whatsapp_in is None:
            raise ValueError("Falta campo 'tiene_whatsapp'")
        
        numero = str(numero).strip()
        if not numero:
            raise ValueError("Campo 'numero' está vacío")
        
        tiene_bool = _normalize_si_no(tiene_whatsapp_in)
        print("FINAL CONVERSION:", f"numero={numero}, tiene_whatsapp={tiene_bool}")
        
        # Llamar BLL
        try:
            resp = await asyncio.wait_for(
                run_in_threadpool(
                    actualizar_tiene_whatsapp,
                    numero=numero,
                    tiene_whatsapp=tiene_bool
                ),
                timeout=300
            )
            return resp
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="La operación tardó más de 5 segundos y fue cancelada."
            )
                
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

def _normalize_si_no(v) -> str:
    """Normaliza diferentes valores a 'si' o 'no'"""
    if v is None:
        raise ValueError("Valor no puede ser None")
    s = str(v).strip().lower()
    if s in {"1", "true", "si", "sí", "y", "yes", "on"}:
        return "si"
    if s in {"0", "false", "no", "n", "off"}:
        return "no"
    if isinstance(v, bool):
        return "si" if v else "no"
    
    raise ValueError(f"Valor inválido para tiene_whatsapp: {v!r}. Valores válidos: 'si'/'no', 'true'/'false', '1'/'0'")

class ClientesEnvioItem(BaseModel):
    Numero: str
    Mensaje: Optional[str] = None
    fileName: Optional[str] = None
    Adjunto: Optional[str] = None
    FechaHoraEnvio: Optional[datetime] = None
    Estado: Optional[str] = None
    Tiene_Whatsapp: Optional[str] = None 
    Campana: Optional[str] = None

@router.get("/whatsapp/clientes", response_model=List[ClientesEnvioItem])
def api_top():
    return obtener_clientes()