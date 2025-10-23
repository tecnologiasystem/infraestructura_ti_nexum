import logging
import time
from app.dal.integracion_dal import (
    obtener_datos_nexum_a_olap,
    insertar_datos_destino_nexum_a_olap,
    obtener_datos_integracion_a_nexum,
    insertar_datos_destino_integracion_a_nexum,
    obtener_datos_integracion_a_olap,
    insertar_datos_destino_integracion_a_olap
)

"""
Importa los módulos necesarios:
- logging: para registrar mensajes informativos o de error durante la ejecución del proceso de integración.
- time: para pausar temporalmente la ejecución en caso de error y aplicar reintentos.
- app.dal.integracion_dal: módulo que contiene todas las funciones de acceso a datos necesarias para extraer información de una base y cargarla en otra.
"""

#----- DE NEXUM A OLAP ----------------------
def integrar_datos_nexum_a_olap():
    """
    Función que extrae datos desde la base de datos NEXUM y los inserta en OLAP.
    Implementa una lógica de reintento en caso de fallo, con un máximo de 5 intentos.
    En cada intento fallido, espera 10 segundos antes de volver a intentarlo.
    """
    intento = 0
    max_intentos = 5

    while intento < max_intentos:
        try:
            """
            Se escribe en el log el inicio del proceso.
            """
            logging.info("Inicio integración.")

            """
            Se extraen los datos desde la base NEXUM mediante una función de la capa DAL.
            """
            datos = obtener_datos_nexum_a_olap()

            """
            Se insertan los datos extraídos en la base de datos OLAP usando la función correspondiente de la DAL.
            """
            insertar_datos_destino_nexum_a_olap(datos)

            """
            Se registra en los logs la cantidad de registros procesados.
            """
            logging.info(f"Integración finalizada. {len(datos)} registros procesados.")

            """
            Si todo sale bien, se rompe el ciclo y no se realizan más intentos.
            """
            break

        except Exception as e:
            """
            Si ocurre un error, se incrementa el contador de intentos y se escribe el error en los logs.
            """
            intento += 1
            logging.error(f"Error en intento {intento}: {str(e)}")

            """
            Espera de 10 segundos antes del próximo intento.
            """
            time.sleep(10)

#----- DE INTEGRACION A NEXUM ----------------------
def integrar_datos_integracion_a_nexum():
    """
    Función que extrae datos desde la base de datos INTERMEDIA (Integración) y los inserta en NEXUM.
    Usa la misma lógica de reintento que el proceso anterior para garantizar robustez en la ejecución.
    """
    intento = 0
    max_intentos = 5

    while intento < max_intentos:
        try:
            """
            Registro del inicio del proceso.
            """
            logging.info("Inicio integración.")

            """
            Obtención de datos desde la base INTERMEDIA.
            """
            datos = obtener_datos_integracion_a_nexum()

            """
            Inserción de los datos extraídos en la base de datos NEXUM.
            """
            insertar_datos_destino_integracion_a_nexum(datos)

            """
            Registro final del número de registros procesados.
            """
            logging.info(f"Integración finalizada. {len(datos)} registros procesados.")

            """
            Salida del ciclo en caso de éxito.
            """
            break

        except Exception as e:
            """
            Registro del error e incremento del intento.
            """
            intento += 1
            logging.error(f"Error en intento {intento}: {str(e)}")

            """
            Espera de 10 segundos antes de volver a intentar.
            """
            time.sleep(10)

#----- DE INTEGRACION A OLAP ----------------------
def integrar_datos_integracion_a_olap():
    """
    Función que extrae datos desde la base INTERMEDIA y los carga en la base de datos OLAP.
    También implementa reintentos para evitar que fallos temporales detengan el proceso.
    """
    intento = 0
    max_intentos = 5

    while intento < max_intentos:
        try:
            """
            Inicio del proceso, se registra en los logs.
            """
            logging.info("Inicio integración.")

            """
            Extracción de datos desde la base INTERMEDIA.
            """
            datos = obtener_datos_integracion_a_olap()

            """
            Inserción de los datos en la base de datos OLAP.
            """
            insertar_datos_destino_integracion_a_olap(datos)

            """
            Registro de cuántos datos fueron correctamente cargados.
            """
            logging.info(f"Integración finalizada. {len(datos)} registros procesados.")

            """
            Salida del ciclo de reintentos.
            """
            break

        except Exception as e:
            """
            Manejo del error y logueo del mismo.
            """
            intento += 1
            logging.error(f"Error en intento {intento}: {str(e)}")

            """
            Pausa de 10 segundos antes del siguiente intento.
            """
            time.sleep(10)
