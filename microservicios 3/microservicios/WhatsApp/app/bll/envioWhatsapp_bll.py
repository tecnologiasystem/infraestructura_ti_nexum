from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import os, re, uuid, json, mimetypes
from fastapi import UploadFile
from app.dal.envioWhatsapp_dal import (
    insertar_detalle_bulk,
    obtener_y_marcar_pendientes,
    obtener_y_marcar_pendientes_por_campana,
    actualizar_tiene_whatsapp_por_numero,
    clientes_envio
)
import unicodedata
from pathlib import Path

WHATSAPP_ATTACH = os.getenv("WHATSAPP_ATTACH", r"\\BITMXL94920DQ\Uipat Datos\Adjuntos WhatsApp")

# =========================
# Modelos
# =========================

class MensajeWhatsAppForm(BaseModel):
    numeros: List[str] = Field(..., description="Números en formato internacional/local")
    mensaje: str

    @validator('numeros')
    def validar_numeros(cls, v):
        if not v:
            raise ValueError("Debe incluir al menos un número")
        return [s.strip() for s in v if s and s.strip()]

# =========================
# Helpers de archivos
# =========================


def _sanitize(name: str) -> str:
    # usa solo el nombre (ni rutas ni fakepath del navegador)
    name = Path(name).name
    # normaliza acentos
    name = unicodedata.normalize("NFKD", name)
    # reemplaza caracteres inválidos por "_"
    name = re.sub(r'[\\/:*?"<>|\r\n\t]+', '_', name).strip()
    # evita vacío
    return name or "archivo"

def _next_non_conflicting_path(dir_path: Path, filename: str) -> Path:
    """Devuelve una ruta única conservando el nombre original. Si existe,
    crea nombre_(1).ext, nombre_(2).ext, ..."""
    filename = _sanitize(filename or "archivo")
    base = Path(filename).stem
    ext = Path(filename).suffix
    cand = dir_path / f"{base}{ext}"
    if not cand.exists():
        return cand
    i = 1
    while True:
        cand = dir_path / f"{base}_({i}){ext}"
        if not cand.exists():
            return cand
        i += 1

def guardar_archivos_a_disco(files: Optional[List[UploadFile]]) -> List[str]:
    """
    Recibe UploadFile(s) y retorna lista de rutas absolutas guardadas en disco,
    conservando el nombre original del archivo del cliente.
    """
    if not files:
        return []

    Path(WHATSAPP_ATTACH).mkdir(parents=True, exist_ok=True)
    rutas: List[str] = []

    for f in files:
        destino = _next_non_conflicting_path(Path(WHATSAPP_ATTACH), f.filename or "archivo")
        # lectura y escritura en bloques
        with open(destino, "wb") as out:
            while True:
                chunk = f.file.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        rutas.append(str(destino))
    return rutas

# =========================
# Casos de uso
# =========================

def guardar_mensajes_bulk_form(numeros: List[str], mensaje: str, campana: str, files: Optional[List[UploadFile]], id_usuario_app: Optional[int]) -> dict:
    """
    Inserta PENDIENTES (uno por número).
    - Guarda los adjuntos en DISCO
    - En BD guarda JSON con las rutas
    """
    rutas = guardar_archivos_a_disco(files)
    adjunto_json = json.dumps(rutas, ensure_ascii=False) if rutas else None
    nombres = [os.path.basename(p) for p in rutas] if rutas else []
    file_name = json.dumps(nombres, ensure_ascii=False) if nombres else None

    total, err = insertar_detalle_bulk(
        numeros=numeros,
        mensaje=mensaje,
        campana=campana,
        adjunto_json=adjunto_json,
        file_name=file_name,
        id_usuario_app=id_usuario_app
    )
    if err:
        raise Exception(f"Error al insertar en bloque: {err}")

    return {
        "insertados": total,
        "payload_automatizacion": {
            "mensaje": mensaje,
            "adjuntos": rutas,     
            "destinos": numeros
        }
    }

def _parsear_adjuntos_json(adjunto_raw: Optional[str]) -> List[str]:
    """Adjunto viene como JSON (lista de rutas) o vacío."""
    if not adjunto_raw:
        return []
    try:
        data = json.loads(adjunto_raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        return [p for p in (adjunto_raw or '').split('|') if p.strip()]
    return []

def obtener_pendientes_y_marcar(limit: int = 1000, estado: str = "ENVIADO"):
    rows, err = obtener_y_marcar_pendientes(limit=limit, nuevo_estado=estado)
    if err:
        raise Exception(err)
    if not rows:
        return {}

    r = rows[0]
    adjuntos = _parsear_adjuntos_json(r.get("adjunto"))  # lista de rutas
    adjuntos_nombres = [os.path.basename(p) for p in adjuntos]
    return {
        "numero": r["numero"],
        "mensaje": r["mensaje"],
        "adjunto": adjuntos_nombres  
    }

def obtener_pendientes_y_marcar_por_campana(campana: str, limit: int = 1000, estado: str = "ENVIADO"):
    rows, err = obtener_y_marcar_pendientes_por_campana(campana=campana, limit=limit, nuevo_estado=estado)
    if err:
        raise Exception(err)
    if not rows:
        return {}
    r = rows[0]
    adjuntos = _parsear_adjuntos_json(r.get("adjunto"))
    adjuntos_nombres = [os.path.basename(p) for p in adjuntos]
    return {
        "numero": r["numero"],
        "mensaje": r["mensaje"],
        "adjunto": adjuntos_nombres
    }

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

def actualizar_tiene_whatsapp(numero: str, tiene_whatsapp):
    """Actualiza el campo tiene_whatsapp guardando 'si' o 'no' directamente"""
    valor_normalizado = _normalize_si_no(tiene_whatsapp)
    
    filas, err = actualizar_tiene_whatsapp_por_numero(numero.strip(), valor_normalizado)
    if err:
        raise Exception(err)
    return {"numero": numero.strip(), "tiene_whatsapp": valor_normalizado}

def obtener_clientes() -> List[Dict[str, Any]]:
    return clientes_envio()