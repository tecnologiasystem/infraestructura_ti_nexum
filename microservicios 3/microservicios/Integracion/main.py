from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from app.config.database import config
from app.bll.integracion_bll import integrar_datos
from app.api.integracion_api import router

# Inicialización de la aplicación FastAPI
"""
Se crea una instancia de FastAPI que será la base para la API.
Luego, se incluye el router definido en `integracion_api` para gestionar las rutas relacionadas con la integración.
"""
app = FastAPI()
app.include_router(router)

# Configuración del logging
"""
Se configura el logging para registrar eventos en un archivo `logs/integracion.log`.
El nivel de log es INFO, y el formato incluye la fecha, nivel y mensaje.
Esto permite monitorear el funcionamiento y errores de la aplicación.
"""
logging.basicConfig(
    filename="logs/integracion.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Programación de tareas periódicas con APScheduler
"""
Se crea un scheduler de tareas en segundo plano (BackgroundScheduler),
que ejecutará la función `integrar_datos` según la configuración definida en `config["tareas"]`.

Para cada tarea en la configuración:
- `dias_semana`: días de la semana para ejecutar la tarea (0 = lunes, 6 = domingo).
- `horas`: horas del día para la ejecución.
- `minutos`: minutos dentro de la hora para ejecutar.
- `nombre`: identificador de la tarea para poder gestionarla.

La tarea se programa con un trigger 'cron' que permite especificar días, horas y minutos de ejecución.
Finalmente, se inicia el scheduler para que comience a ejecutar las tareas programadas en segundo plano.
"""
scheduler = BackgroundScheduler()

for tarea in config.get("tareas", []):
    dias = tarea.get("dias_semana", [0,1,2,3,4,5,6])
    horas = tarea.get("horas", [0])
    minutos = tarea.get("minutos", [0])
    nombre = tarea.get("nombre", "job_sin_nombre")

    scheduler.add_job(
        integrar_datos,
        'cron',
        day_of_week=','.join(map(str, dias)),
        hour=','.join(map(str, horas)),
        minute=','.join(map(str, minutos)),
        id=nombre
    )

scheduler.start()
"""
El scheduler queda activo en segundo plano, ejecutando la función `integrar_datos` según el cron definido.
Esto permite que la integración de datos se realice automáticamente sin intervención manual.
"""

