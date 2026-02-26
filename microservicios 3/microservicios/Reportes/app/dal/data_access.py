import pyodbc
import re
from app.config.config import DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD, ALLOWED_TABLES

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def get_connection():
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}'
    )
    return conn

def get_data_from_table(tabla: str, filtros: dict, offset: int, limit: int):
    """
    Lee datos de una tabla permitida aplicando filtros LIKE parametrizados.
    """
    table_sql = _ensure_allowed(tabla)

    conn = get_connection()
    try:
        cursor = conn.cursor()

        where_clauses = []
        params = []

        # Filtros: { columna: "valor" } -> LOWER(col) LIKE LOWER(?)
        for columna, valor in (filtros or {}).items():
            # Validar nombre de columna (evita inyección en identificadores)
            if not _IDENTIFIER_RE.match(columna):
                raise ValueError(f"Nombre de columna inválido: {columna}")
            where_clauses.append(f"LOWER([{columna}]) LIKE LOWER(?)")
            # Usamos comodines por defecto
            params.append(f"%{valor}%")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Consulta paginada y total
        query = f"""
            SELECT *
            FROM {table_sql}
            WHERE {where_sql}
            ORDER BY 1
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY;
        """
        total_query = f"SELECT COUNT(1) FROM {table_sql} WHERE {where_sql};"

        cursor.execute(total_query, params)
        total = cursor.fetchone()[0]

        cursor.execute(query, [*params, int(offset), int(limit)])
        cols = [c[0] for c in cursor.description]
        rows = [dict(zip(cols, r)) for r in cursor.fetchall()]

        return rows, total
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()
        
def get_table_names():
    """
    Devuelve la lista de tablas permitidas configuradas en ALLOWED_TABLES.
    """
    return list(ALLOWED_TABLES)

def get_table_columns(tabla: str):
    """
    Devuelve la lista de columnas (campos) de una tabla específica.
    
    Args:
        tabla: Nombre de la tabla (debe estar en ALLOWED_TABLES)
    
    Returns:
        Lista de nombres de columnas
    
    Raises:
        ValueError: Si la tabla no está permitida
    """
    # Verificar que la tabla esté permitida
    table_sql = _ensure_allowed(tabla)
    
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # Obtener información de las columnas usando INFORMATION_SCHEMA
        schema, tbl = _split_schema_table(tabla)
        
        if schema:
            query = """
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, 
                       IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            cursor.execute(query, [schema, tbl])
        else:
            query = """
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, 
                       IS_NULLABLE, COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            cursor.execute(query, [tbl])
        
        columns = []
        for row in cursor.fetchall():
            col_info = {
                "nombre": row[0],
                "tipo": row[1],
                "longitud": row[2] if row[2] else None,
                "nullable": row[3] == "YES",
                "default": row[4] if row[4] else None
            }
            columns.append(col_info)
        
        return columns
        
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()

def get_all_tables_with_columns():
    """
    Devuelve todas las tablas permitidas con sus respectivas columnas.
    
    Returns:
        Dict con estructura: {"tabla": [columnas]}
    """
    result = {}
    for tabla in ALLOWED_TABLES:
        try:
            columns = get_table_columns(tabla)
            result[tabla] = columns
        except Exception as e:
            result[tabla] = {"error": str(e)}
    
    return result

def _split_schema_table(name: str):
    """
    Devuelve (schema, table). Acepta 'schema.table' o 'table'.
    """
    parts = name.split('.', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, name

def _quote_ident(schema: str | None, table: str) -> str:
    """
    En SQL Server, escapamos identificadores con corchetes.
    Validamos que solo tengan letras, números y guion bajo.
    """
    def ok(s): return bool(_IDENTIFIER_RE.match(s))
    if schema and not ok(schema):
        raise ValueError("Esquema inválido.")
    if not ok(table):
        raise ValueError("Tabla inválida.")
    if schema:
        return f"[{schema}].[{table}]"
    return f"[{table}]"

def _normalize_allowed(name: str) -> str:
    """
    Normaliza el nombre como aparece en ALLOWED_TABLES para comparar.
    """
    return name.strip().lower()

def _ensure_allowed(tabla: str) -> str:
    """
    Verifica que 'tabla' esté en ALLOWED_TABLES (case-insensitive) y
    devuelve el nombre listo para usar en SQL con corchetes.
    """
    wanted = _normalize_allowed(tabla)
    mapping = { _normalize_allowed(t): t for t in ALLOWED_TABLES }
    if wanted not in mapping:
        raise ValueError(f"La tabla '{tabla}' no está permitida.")
    # Separar en esquema y tabla para entrecorchetar
    schema, tbl = _split_schema_table(mapping[wanted])
    return _quote_ident(schema, tbl)