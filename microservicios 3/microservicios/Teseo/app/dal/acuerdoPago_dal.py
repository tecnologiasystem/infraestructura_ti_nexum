from typing import List, Tuple, Optional, Dict, Any
import traceback
from app.config.database import get_connection, get_connectionAcuerdo

def insertar_acuerdos_lote(param_rows: List[Tuple], chunk_size: int = 500) -> Tuple[int, int]:
    """
    Inserta acuerdos en lotes con mejor manejo de errores
    """
    if not param_rows:
        return (0, 0)

    total = len(param_rows)
    ok = 0
    errores = []

    with get_connection() as conn:
        cur = conn.cursor()
        
        for i in range(0, total, chunk_size):
            bloque = param_rows[i:i+chunk_size]
            
            try:
                conn.autocommit = False
                
                for idx, params in enumerate(bloque):
                    try:
                        print(f"Insertando fila {i+idx+1}: {params}")
                        
                        cur.execute("""
                        EXEC dbo.SP_CRUD_AcuerdosPagoTeseo
                        @Accion=?,
                        @id=?,
                        @NumeroDNI=?,
                        @IdentificacionAsesor=?,
                        @CodigoEstado=?,
                        @CodigoCanal=?,
                        @CodigoGestion=?,
                        @TelefonoContacto=?,
                        @Direccion=?,
                        @FechaPromesa=?,
                        @ValorPromesa=?,
                        @NumeroObligacion=?,
                        @FechaHoraGestion=?,
                        @Observaciones=?
                        """, params)
                        
                        while True:
                            if cur.description:
                                results = cur.fetchall()
                                results
                            if not cur.nextset():
                                break
                                
                    except Exception as row_error:
                        error_msg = f"Error en fila {i+idx+1}: {str(row_error)} - Datos: {params}"
                        print(f"🔥 {error_msg}")
                        errores.append(error_msg)
                        conn.rollback()
                        conn.autocommit = True
                        break  
                else:
                    conn.commit()
                    ok += len(bloque)
                    
            except Exception as block_error:
                error_msg = f"Error en bloque {i//chunk_size + 1}: {str(block_error)}"
                print(f"🔥 {error_msg}")
                errores.append(error_msg)
                conn.rollback()
            finally:
                conn.autocommit = True

    if errores:
        print(f"\n⚠️ Se encontraron {len(errores)} errores:")
        for error in errores:
            print(f"  - {error}")
            
        if ok == 0:
            raise Exception(f"No se pudo insertar ningún registro. Errores: {'; '.join(errores[:3])}")

    print(f"✅ Proceso completado: {ok}/{total} filas insertadas correctamente")
    return (ok, total)

def obtener_dni(estado: Optional[str] = "Pendiente") -> Optional[str]:
    """
    Retorna un DNI aleatorio de la tabla AcuerdosPagoTeseo.
    Si 'estado' es None, ignora el filtro por estado.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT TOP 1 NumeroDNI
            FROM dbo.AcuerdosPagoTeseo
            WHERE ISNULL(LTRIM(RTRIM(NumeroDNI)),'') <> ''
              AND (? IS NULL OR Estado = ?)
            ORDER BY NEWID();
        """, (estado, estado))
        row = cur.fetchone()
        return row[0] if row else None
    
def pop_dni(estado_from: Optional[str] = "PENDIENTE",
                      estado_to: Optional[str] = "ENVIADO") -> Optional[str]:
    """
    Toma 1 DNI aleatorio en estado_from y lo marca a estado_to de forma ATÓMICA.
    Retorna el NumeroDNI o None si no hay disponible.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            ;WITH cte AS (
                SELECT TOP 1 *
                FROM dbo.AcuerdosPagoTeseo WITH (ROWLOCK, READPAST, UPDLOCK)
                WHERE ISNULL(LTRIM(RTRIM(NumeroDNI)),'') <> ''
                  AND (? IS NULL OR Estado = ?)
                ORDER BY NEWID()
            )
            UPDATE cte
               SET Estado = ISNULL(?, Estado)
            OUTPUT inserted.NumeroDNI;
        """, (estado_from, estado_from, estado_to))
        row = cur.fetchone()
        return row[0] if row else None
    
    
def pop_acuerdo(
    *, solo_activos: bool = True, exige_estado: Optional[str] = "ACTIVO"
) -> Optional[Dict[str, Any]]:
    """
    ATÓMICO: toma TOP 1 con enviada pendiente (ISNULL(enviada,0)=0),
    lo marca enviada=1 y devuelve el registro actualizado (dict).
    Retorna None si no hay pendientes.
    """
    filtros = ["ISNULL(ap.enviada,0) = 0"]
    params: List[Any] = []

    if solo_activos:
        filtros.append("ISNULL(ap.activo,0) = 1")
    if exige_estado is not None:
        filtros.append("ap.estado = ?")
        params.append(exige_estado)

    where_clause = " AND ".join(filtros) if filtros else "1=1"

    sql = f"""
    ;WITH cte AS (
        SELECT TOP 1 ap.id
        FROM turnosvirtuales_dev.dbo.acuerdos_pago ap WITH (ROWLOCK, READPAST, UPDLOCK)
        WHERE {where_clause}
        ORDER BY NEWID()
    )
    UPDATE ap
       SET ap.enviada   = 1,
           ap.updated_at = GETDATE()
    OUTPUT
        inserted.numero_acuerdo,
        inserted.nombre_cliente,
        inserted.documento,
        inserted.celular,
        inserted.plan_seleccionado,
        inserted.monto_acordado,
        inserted.saldo_original,
        inserted.fecha_acuerdo,
        inserted.fecha_limite_pago,
        inserted.estado,
        inserted.activo,
        inserted.banco,
        inserted.producto,
        inserted.observaciones,
        inserted.created_at,
        inserted.updated_at
    FROM turnosvirtuales_dev.dbo.acuerdos_pago ap
    INNER JOIN cte ON cte.id = ap.id;
    """

    cols = [
        "numero_acuerdo","nombre_cliente","documento","celular",
        "plan_seleccionado","monto_acordado","saldo_original",
        "fecha_acuerdo","fecha_limite_pago","estado","activo",
        "banco","producto","observaciones","created_at","updated_at"
    ]

    with get_connectionAcuerdo() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        if not row:
            return None
        return {cols[i]: row[i] for i in range(len(cols))}