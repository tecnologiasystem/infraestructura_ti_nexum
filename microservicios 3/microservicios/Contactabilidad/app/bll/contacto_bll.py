from datetime import datetime, timedelta
import requests
import pandas as pd
from io import StringIO, BytesIO
from app.dal.contacto_dal import insertar_datos_llamadas

# URL base del servicio que provee los archivos de llamadas
URL = "http://172.18.74.30/detalle_llamadas"

def procesar_llamadas_por_rango(fecha_inicio: datetime, fecha_fin: datetime):
    """
    Procesa archivos de llamadas descargados desde un servicio HTTP para un rango de fechas dado.
    Cada día se descarga un archivo (CSV o Excel), se interpreta como DataFrame y se insertan sus filas en la BD.

    Parámetros:
    - fecha_inicio: Fecha inicial del rango
    - fecha_fin: Fecha final del rango

    Retorna:
    - Lista de diccionarios con resumen por cada fecha (filas insertadas o error)
    """
    fecha_actual = fecha_inicio  # Punto de partida para recorrer el rango día por día
    resumen = []  # Lista que irá almacenando el resumen de lo ocurrido por cada fecha

    while fecha_actual <= fecha_fin:
        """
        Se define el rango del día completo: desde las 00:00 hasta las 23:59
        """
        desde = fecha_actual.replace(hour=0, minute=0, second=0)
        hasta = fecha_actual.replace(hour=23, minute=59, second=59)

        try:
            """
            Diccionario con los parámetros que se enviarán al servidor como query string
            """
            payload = {
                "fecha_inicio": desde.strftime("%Y-%m-%dT%H:%M"),
                "fecha_fin": hasta.strftime("%Y-%m-%dT%H:%M")
            }

            """
            Cabeceras HTTP para simular una petición desde navegador y evitar bloqueos
            """
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, text/csv, */*",
                "Referer": "http://172.18.74.30/",
                "Connection": "keep-alive"
            }

            print(f"⏳ Consultando: {payload['fecha_inicio']} a {payload['fecha_fin']}")

            """
            Realiza la petición HTTP con timeout de 180 segundos (por si el archivo es muy grande)
            """
            response = requests.get(URL, params=payload, headers=headers, timeout=180)

            if response.status_code == 200:
                """
                Si la respuesta fue exitosa, detectamos el tipo de archivo devuelto por el encabezado Content-Type
                """
                content_type = response.headers.get("Content-Type", "")

                fecha_str = str(desde.date())  # Extraemos la fecha en formato YYYY-MM-DD
                filename = f"llamadas_{fecha_str}"  # Nombre del archivo local

                """
                Se define extensión dependiendo del tipo de contenido recibido
                """
                ext = ".xlsx" if "spreadsheetml" in content_type else ".csv"
                path = f"{filename}{ext}"

                """
                Guardamos el archivo recibido localmente (útil para depurar si hay errores)
                """
                with open(path, "wb") as f:
                    f.write(response.content)

                """
                Procesamos el archivo en memoria según el tipo
                """
                if "spreadsheetml" in content_type or path.endswith(".xlsx"):
                    df = pd.read_excel(BytesIO(response.content))
                elif "text/csv" in content_type:
                    decoded = response.content.decode("utf-8", errors="replace")
                    df = pd.read_csv(StringIO(decoded), sep=";", engine="python", on_bad_lines="warn")
                else:
                    raise ValueError("Formato de archivo no reconocido. No es CSV ni Excel.")

                print(f"📊 DataFrame recibido con {len(df)} filas")
                print(df.head())  # Muestra las primeras filas para verificar formato

                """
                Insertamos los datos del DataFrame a la base de datos
                """
                filas = insertar_datos_llamadas(df)

                """
                Guardamos el resumen de la jornada
                """
                resumen.append({"fecha": fecha_str, "filas_insertadas": filas})

            else:
                """
                Si la respuesta no fue 200, se guarda el error
                """
                resumen.append({
                    "fecha": str(desde.date()),
                    "error": f"Status {response.status_code}",
                    "detalle": response.text
                })

        except Exception as e:
            """
            Captura cualquier excepción que ocurra ese día y la guarda
            """
            resumen.append({"fecha": str(desde.date()), "error": str(e)})

        """
        Avanzamos al siguiente día
        """
        fecha_actual += timedelta(days=1)

    """
    Se devuelve el resumen completo de todos los días consultados
    """
    return resumen
