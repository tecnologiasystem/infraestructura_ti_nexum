from fastapi import APIRouter, HTTPException
from app.api.models import FiltroRequest
from app.bll.homologacion import obtener_datos_filtrados
from app.dal.data_access import get_table_names, get_table_columns, get_all_tables_with_columns

router = APIRouter()

@router.post("/buscar")
def buscar(request: FiltroRequest):
    """
    Endpoint para buscar datos en una tabla específica con filtros opcionales.
    
    Body:
    {
        "tabla": "NombreDeLaTabla",
        "filtros": {"columna": "valor"},
        "columnas": ["col1", "col2"],
        "offset": 0,
        "limit": 50
    }
    """
    try:
        return obtener_datos_filtrados(
            tabla=request.tabla,
            filtros=request.filtros,
            columnas=request.columnas,
            offset=request.offset,
            limit=request.limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/tablas")
def listar_tablas():
    """
    Endpoint para obtener la lista de tablas disponibles para consulta.
    
    Retorna:
    {
        "tablas": ["Tabla1", "Tabla2", "Tabla3"]
    }
    """
    try:
        tablas = get_table_names()
        return {"tablas": tablas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo tablas: {str(e)}")

@router.get("/columnas/{tabla}")
def obtener_columnas(tabla: str):
    """
    Endpoint para obtener las columnas de una tabla específica.
    
    Parámetros:
        tabla: Nombre de la tabla
    
    Retorna:
    {
        "tabla": "NombreDeLaTabla",
        "columnas": [
            {
                "nombre": "id",
                "tipo": "int",
                "longitud": null,
                "nullable": false,
                "default": null
            },
            {
                "nombre": "email",
                "tipo": "varchar",
                "longitud": 255,
                "nullable": true,
                "default": null
            }
        ]
    }
    """
    try:
        columnas = get_table_columns(tabla)
        return {
            "tabla": tabla,
            "columnas": columnas
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo columnas: {str(e)}")

@router.get("/tablas-con-columnas")
def listar_tablas_con_columnas():
    try:
        tablas_columnas = get_all_tables_with_columns()
        return tablas_columnas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo tablas con columnas: {str(e)}")