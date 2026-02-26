from typing import List, Tuple
from app.config.database import get_connection

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

