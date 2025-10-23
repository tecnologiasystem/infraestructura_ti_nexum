from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body, BackgroundTasks
from app.bll.contelfinanciera_bll import procesar_resultado_automatizacionColtefinanciera
from app.dal.contelfinanciera_dal import DetalleModel

router = APIRouter()

@router.post("/automatizacion/resultadoColtefinanciera", tags=["Automatizacion Coltefinanciera"])
async def recibir_resultado(request: Request):
    """
    Recibe un JSON con resultado de automatización, valida datos, y llama a BLL para procesarlo.
    Retorna éxito o error 404 si no se encontró registro para actualizar.
    """
    raw = await request.json()
    print("📥 Payload crudo:", raw)
    try:
        resultado = DetalleModel(**raw)
    except ValidationError as ve:
        print("❌ ValidationError:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    updated = procesar_resultado_automatizacionColtefinanciera(resultado)
    if not updated:
        raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    return {"success": True, "mensaje": "Resultado guardado correctamente"}

