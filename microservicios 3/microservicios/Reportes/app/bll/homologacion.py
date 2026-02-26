from app.dal.data_access import get_data_from_table

def obtener_datos_filtrados(tabla: str, filtros=None, columnas=None, offset: int = 0, limit: int = 50):
    try:
        
        resultados, total = get_data_from_table(tabla, filtros or {}, offset, limit)

        
        if columnas:
            resultados = [
                {col: row.get(col) for col in columnas if col in row}
                for row in resultados
            ]

        return {
            "offset": offset,
            "limit": limit,
            "total_registros": total,
            "resultados": resultados
        }

    except Exception as e:
        return {"error": str(e)}
