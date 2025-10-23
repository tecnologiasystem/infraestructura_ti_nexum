from fastapi import APIRouter
from app.bll.integracion_bll import integrar_datos_nexum_a_olap, integrar_datos_integracion_a_nexum, integrar_datos_integracion_a_olap

"""
Importación de FastAPI y funciones de integración:
- APIRouter: permite definir rutas (endpoints) específicas para este microservicio.
- integrar_datos_nexum_a_olap: lógica que copia o sincroniza datos desde la base de datos NEXUM hacia OLAP.
- integrar_datos_integracion_a_nexum: lógica que copia o sincroniza datos desde una BD intermedia llamada "integración" hacia NEXUM.
- integrar_datos_integracion_a_olap: sincroniza datos desde integración hacia OLAP.
"""

router = APIRouter()

"""
Se crea una instancia del enrutador de FastAPI para registrar las rutas que este microservicio expondrá.
"""

@router.get("/")
def health_check():
    """
    Endpoint de prueba rápida ("ping").
    Permite verificar que el microservicio de integración está funcionando correctamente.
    Retorna un mensaje simple como confirmación.
    """
    return {"message": "Microservicio integración corriendo."}

#----- DE NEXUM A OLAP -------------------
@router.get("/lanzar-integracion_nexum_a_olap")
def lanzar_integracion_nexum_a_olap():
    """
    Ejecuta manualmente el proceso de integración desde la base de datos NEXUM hacia OLAP.
    Esta función llama al método de capa lógica (BLL) encargado de mover/copiar los datos.
    """
    integrar_datos_nexum_a_olap()
    return {"status": "Integración ejecutada"}

#----- DE INTEGRACION A NEXUM -------------------
@router.get("/lanzar-integracion_integracion_a_nexum")
def lanzar_integracion_a_nexum():
    """
    Ejecuta manualmente la integración desde la base de datos INTERMEDIA (integración) hacia NEXUM.
    Se usa típicamente para actualizar datos operativos en NEXUM desde un staging.
    """
    integrar_datos_integracion_a_nexum()
    return {"status": "Integración ejecutada"}

#----- DE INTEGRACION A OLAP -------------------
@router.get("/lanzar-integracion_integracion_a_olap")
def lanzar_integracion_a_olap():
    """
    Ejecuta manualmente la integración desde la base de datos INTERMEDIA hacia OLAP.
    Suele usarse cuando OLAP requiere datos de staging para consolidación o reportería.
    """
    integrar_datos_integracion_a_olap()
    return {"status": "Integración ejecutada"}
