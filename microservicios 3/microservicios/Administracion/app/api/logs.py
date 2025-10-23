"""
Importa APIRouter desde FastAPI, que permite definir rutas agrupadas
para el módulo de logs u otras funcionalidades específicas.
"""
from fastapi import APIRouter, Query

"""
Importa StreamingResponse, que se usa para enviar archivos como respuesta
(descarga de Excel, por ejemplo) sin necesidad de almacenarlos en disco.
"""
from fastapi.responses import StreamingResponse

"""
Importa pandas, librería usada para manipular estructuras de datos
(tablas en memoria, como DataFrames) y generar archivos Excel.
"""
import pandas as pd

"""
Importa io, que permite trabajar con flujos de datos en memoria
como si fueran archivos (en este caso, para crear Excel en memoria).
"""
import io

"""
Importa funciones de la capa de lógica de negocio (BLL) para logs:
- exportar_logs_excel: genera los datos de logs en formato exportable.
- get_logs_login: consulta los registros de acceso (login) del sistema.
"""
from app.bll.logs_bll import exportar_logs_excel, get_logs_login

"""
Instancia del router para el módulo de logs.

Este objeto se utilizará para registrar todas las rutas relacionadas
con la gestión y exportación de logs dentro de la aplicación.
"""
router = APIRouter()


"""
Instancia del router FastAPI para el módulo de logs.
Permite agrupar todas las rutas relacionadas con auditoría y registros del sistema.
"""
router = APIRouter()


"""
Ruta GET que retorna todos los registros de inicio de sesión del sistema.

Este endpoint no recibe parámetros. Internamente consulta la capa BLL a través de la función
get_logs_login(), la cual accede a la base de datos y retorna una lista de accesos por usuario.

Etiqueta:
    - Logs
"""
@router.get("/iniciosesion", tags=["Logs"])
def ver_logs():
    return get_logs_login()


"""
Ruta GET que permite exportar los registros de inicio de sesión a un archivo Excel.

Parámetros opcionales (vía query string):
    usuario: nombre del usuario a filtrar (si se desea).
    desde: fecha de inicio del rango a exportar (formato string).
    hasta: fecha de fin del rango a exportar (formato string).

Proceso:
    1. Se llama a exportar_logs_excel() desde la capa BLL, que retorna los datos filtrados.
    2. Se convierte la lista de registros a un DataFrame de pandas.
    3. Se genera un archivo Excel en memoria utilizando io.BytesIO y pd.ExcelWriter.
    4. El archivo se retorna como descarga en la respuesta con StreamingResponse.

Etiqueta:
    - Logs
"""
@router.get("/iniciosesion/exportar", tags=["Logs"])
async def exportar_logs(
    usuario: str = Query(""),
    desde: str = Query(""),
    hasta: str = Query("")
):
    logs = exportar_logs_excel(usuario, desde, hasta)  # ✅ trae campañas incluidas
    df = pd.DataFrame(logs)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Logs")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=logs_inicio_sesion.xlsx"}
    )
