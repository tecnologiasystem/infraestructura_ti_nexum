import pandas as pd
import pyodbc

"""
Establece la conexión a la base de datos SQL Server usando pyodbc.
Se especifica el driver ODBC, el servidor, la base de datos y las credenciales de usuario.
"""
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=172.18.72.111,1433;"
    "DATABASE=NEXUM;"
    "UID=NEXUM;"
    "PWD=NuevaContraseña123;"
)

"""
Crea un cursor para ejecutar comandos SQL en la conexión abierta.
"""
cursor = conn.cursor()

"""
Define la ruta completa del archivo Excel desde donde se leerán los datos.
"""
ruta_excel = r"C:\Users\developmentit\Documents\Usuarios 9.xlsx"

"""
Lee el archivo Excel con pandas, cargando los datos en un DataFrame.
Esto permite trabajar con los datos en memoria y manipularlos fácilmente.
"""
df = pd.read_excel(ruta_excel)

"""
Reemplaza los valores NaN (faltantes) con cadenas vacías para evitar errores al insertar datos.
"""
df.fillna("", inplace=True)

"""
Renombra columnas para estandarizar los nombres que se usarán para acceder a los datos.
Por ejemplo, la columna 'CORREOS' se renombra a 'correo'.
"""
df.rename(columns={
    "CORREOS": "correo",
    "Login": "usuario",
    "Contraseña": "contraseña",
}, inplace=True)

"""
Imprime en consola la lista de columnas del DataFrame después de renombrar,
para verificar que los nombres se aplicaron correctamente.
"""
print("Columnas después de renombrar:", df.columns.tolist())

"""
Itera fila por fila sobre el DataFrame para insertar cada usuario en la base de datos.
"""
for _, row in df.iterrows():
    """
    Extrae y limpia los datos necesarios de la fila actual:
    correo, usuario y contraseña, eliminando espacios al inicio y final.
    """
    correo = str(row["correo"]).strip()
    usuario = str(row["usuario"]).strip()
    contraseña = str(row["contraseña"]).strip()

    try:
        """
        Ejecuta el comando SQL INSERT para agregar un nuevo registro a la tabla usuariosConsulta.
        Se insertan correo, usuario, contraseña, estado (1 = activo) y la fecha actual.
        """
        cursor.execute("""
            INSERT INTO usuariosConsulta (correo, usuario, contraseña, estado, fechaUso)
            VALUES (?, ?, ?, 1, GETDATE())
        """, correo, usuario, contraseña)

        """
        Imprime un mensaje en consola confirmando la inserción exitosa de este usuario.
        """
        print(f"✅ Insertado usuario: {usuario}")

    except Exception as e:
        """
        Si ocurre un error al insertar, se captura la excepción y se imprime un mensaje
        con el detalle del error y el usuario afectado.
        """
        print(f"❌ Error al insertar usuario {usuario}: {e}")

"""
Confirma los cambios realizados en la base de datos (commit).
"""
conn.commit()

"""
Cierra el cursor y la conexión para liberar recursos y evitar bloqueos.
"""
cursor.close()
conn.close()
