from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from app.bll.email_click_bll import EmailClickBLL

router = APIRouter()

class EnvioRequest(BaseModel):
    subject: str
    body: str
    senderEmail: str
    userId: int | None = None
    idUsuario: int | None = None
    descripcion: str | None = None 


class ProgramarRequest(BaseModel):
    subject: str
    body: str
    fecha_envio: str 
    senderEmail: str  
    userId: int | None = None
    idUsuario: int | None = None


@router.post("/subir_excel")
async def subir_excel(request: Request, file: UploadFile = File(...)):
    bll = EmailClickBLL()
    ok, msg, variables, excelFileName = await bll.subir_excel(file, request.app.state.UPLOAD_FOLDER)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "variables": variables, "excelFileName": excelFileName}

@router.post("/guardar_imagen")
async def guardar_imagen(
    request: Request,
    file: UploadFile = File(...),
    areas: str = Form(...),
):
    bll = EmailClickBLL()
    ok, msg = await bll.guardar_imagen(file, areas, request.app.state.IMAGES_FOLDER)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}

@router.post("/enviar_correos")
async def enviar_correos(req: EnvioRequest, request: Request):
    bll = EmailClickBLL()

    # 1) obtener clientes para contar destinatarios (solo conteo rápido)
    clientes = bll._obtener_clientes()
    destinatarios = []
    for c in clientes:
        correo = bll._get_email(c)
        if correo:
            destinatarios.append(c)

    total = len(destinatarios)
    if total == 0:
        raise HTTPException(status_code=400, detail="No hay destinatarios válidos (revisa columna Correo/Email).")

    # 2) crear encabezado
    idEncabezado = bll.db_dal.crear_encabezado(
        idUsuario=req.idUsuario,
        totalRegistros=total,
        descripcion=req.descripcion,
        remitente=req.senderEmail
    )

    # 3) crear detalles PENDIENTE en BD (sin enviar)
    ok, msg = bll.preparar_detalles_pendientes(
        idEncabezado=idEncabezado,
        subject=req.subject,
        body=req.body,
        senderEmail=req.senderEmail,
        images_folder=request.app.state.IMAGES_FOLDER,
        excel_path=EmailClickBLL.excel_file_path,
    )

    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "message": "Envío registrado en BD (worker lo procesará)",
        "idEncabezado": idEncabezado,
        "detalle": msg
    }

@router.post("/programar_envio")
async def programar_envio(req: ProgramarRequest, request: Request):
    scheduler = request.app.state.scheduler
    bll = EmailClickBLL()

    ok, msg = bll.programar_envio(
        scheduler,
        req.subject, req.body,
        req.fecha_envio,
        req.senderEmail,
        request.app.state.IMAGES_FOLDER
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.get("/track/{idDetalle}")
async def track_click(idDetalle: int, request: Request, a: int = 1):
    bll = EmailClickBLL()

    ip = request.headers.get("x-forwarded-for") or request.client.host
    ua = request.headers.get("user-agent", "")

    bll.db_dal.registrar_click(
        idDetalle=idDetalle,
        area=a,
        ip=ip,
        user_agent=ua
    )

    destino = bll.db_dal.obtener_click_url(idDetalle)
    if not destino:
        return RedirectResponse(
            url="https://optime.systemgroupglobal.com",
            status_code=302
        )

    # ✅ redirigir al link real
    return RedirectResponse(url=destino, status_code=302)
