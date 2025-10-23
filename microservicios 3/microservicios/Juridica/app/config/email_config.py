import os
from dotenv import load_dotenv

"""
1. import os
   - Permite acceder a funcionalidades del sistema operativo, en particular a variables de entorno.

2. from dotenv import load_dotenv
   - Importa la función para cargar variables definidas en un archivo .env al entorno de ejecución.

3. load_dotenv()
   - Carga las variables del archivo .env al entorno, para que puedan ser leídas con os.getenv.

4. REMITENTE = os.getenv("REMITENTE")
   - Obtiene el valor de la variable de entorno 'REMITENTE', que típicamente es el email remitente.

5. PASSWORD = os.getenv("PASSWORD")
   - Obtiene la contraseña para la autenticación desde la variable de entorno 'PASSWORD'.

6. SERVER = os.getenv("SERVER", "smtp.office365.com")
   - Obtiene la dirección del servidor SMTP desde 'SERVER', usa el valor por defecto si no está definida.

7. PORT = int(os.getenv("PORT", 587))
   - Obtiene el puerto para el servidor SMTP, convierte el valor (string) a entero,
     usa 587 como puerto por defecto que es estándar para SMTP con TLS.
"""

load_dotenv()

REMITENTE = os.getenv("REMITENTE")
PASSWORD = os.getenv("PASSWORD")
SERVER = os.getenv("SERVER", "smtp.office365.com")
PORT = int(os.getenv("PORT", 587))
