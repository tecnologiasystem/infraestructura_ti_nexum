from Juridica.app.config import get_db_connection

"""
Esta línea importa la función `get_db_connection` desde el módulo de configuración
de la aplicación Juridica.

- `get_db_connection` es probablemente una función que establece y retorna una conexión
  a la base de datos configurada para la aplicación Juridica.
- Se usa para centralizar y reutilizar la lógica de conexión, evitando repetir código
  y facilitando el manejo de conexiones a la base de datos en distintos módulos.
- Esto mejora la mantenibilidad y facilita la actualización de detalles de conexión
  (como credenciales o rutas) en un solo lugar.

Uso típico:
- En funciones o clases que necesiten consultar o modificar datos en la base de datos,
  se invoca `get_db_connection()` para obtener un objeto conexión reutilizable.
"""
