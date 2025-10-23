from datetime import datetime
"""
Importa el módulo `datetime` del estándar de Python.
Este se usará para registrar las fechas y horas en las que se inicia y finaliza un proceso de integración.
"""

from app.config.database import conectar_sql, CONFIG_NEXUM, CONFIG_OLAP, CONFIG_INTEGRACION
"""
Importa los elementos necesarios desde el módulo interno `app.config.database`.

- `conectar_sql`: Función que permite establecer conexión con una base de datos SQL Server.
- `CONFIG_NEXUM`, `CONFIG_OLAP`, `CONFIG_INTEGRACION`: Diccionarios de configuración que contienen los parámetros
  de conexión (host, usuario, contraseña, base de datos, etc.) para las tres bases usadas:
  - `NEXUM`: Origen principal de datos.
  - `OLAP`: Base destino para análisis o procesamiento.
  - `INTEGRACION`: Otra fuente externa que también alimenta NEXUM u OLAP.
"""

def log_integracion(cursor, origen, destino, tabla, fecha_inicio, fecha_fin, registros, estado, mensaje_error=None):
    """
    Esta función registra un evento de integración de datos en la tabla `ControlIntegracion`.
    Sirve como bitácora para saber qué se integró, desde dónde, hacia dónde, cuántos registros, 
    cuándo inició y finalizó, y si fue exitoso o fallido.

    Parámetros:
    - `cursor`: Objeto cursor para ejecutar la sentencia SQL sobre la base de datos.
    - `origen`: Nombre del origen de los datos (por ejemplo 'NEXUM' o 'INTEGRACION').
    - `destino`: Nombre del destino de los datos (por ejemplo 'OLAP' o 'NEXUM').
    - `tabla`: Nombre de la tabla que se está integrando.
    - `fecha_inicio`: Objeto datetime que representa el momento en que comenzó la integración.
    - `fecha_fin`: Objeto datetime que representa el momento en que finalizó la integración.
    - `registros`: Número de registros que se intentaron insertar.
    - `estado`: Texto que indica si la integración fue 'Exitoso' o 'Fallido'.
    - `mensaje_error`: (Opcional) Mensaje de error si ocurrió una excepción.

    Esta función se llama desde cada bloque de inserción para dejar trazabilidad en la base.
    """
    cursor.execute("""
        INSERT INTO ControlIntegracion (
            origen, destino, tabla, fechaInicio, fechaFin, registros, estado, mensajeError
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (origen, destino, tabla, fecha_inicio, fecha_fin, registros, estado, mensaje_error))
    """
    Ejecuta una sentencia SQL parametrizada (con `?`) para insertar un nuevo registro en la tabla
    `ControlIntegracion` con todos los detalles del proceso de integración actual.
    """


#----- OLAP: DE NEXUM A OLAP ------------------------------------------------------------------------------------------------
def obtener_datos_nexum_a_olap():
    """
    Esta función se conecta a la base de datos NEXUM utilizando la configuración definida
    en `CONFIG_NEXUM`. El propósito es extraer datos recientes de diversas tablas dentro
    de NEXUM, para posteriormente integrarlos en la base OLAP.

    Esta función será la encargada de ejecutar varias consultas SQL que traen la información 
    de las últimas 24 horas (normalmente usando filtros por fecha) para alimentar procesos 
    de análisis, reportes o consolidación de datos en otra base.
    """
    
    conn = conectar_sql(CONFIG_NEXUM)
    """
    Llama a la función `conectar_sql` usando como parámetro la configuración específica
    de la base de datos NEXUM (`CONFIG_NEXUM`). Esto devuelve un objeto de conexión 
    (normalmente un pyodbc.Connection o similar) que permite interactuar con la base.
    """

    cursor = conn.cursor()
    """
    A partir de la conexión establecida (`conn`), se crea un cursor.
    El cursor es el objeto que se usa para ejecutar comandos SQL sobre la base.
    Cada `cursor.execute(...)` va a correr una consulta y permitir obtener los datos
    con `fetchall()` o `fetchone()`.
    """


        # Reporte llamada
    """
    Sección encargada de extraer los datos de llamadas desde la tabla `ReporteLlamada`
    en la base de datos NEXUM. Solo se extraen las llamadas que ocurrieron en las últimas 24 horas.
    Esto se hace aplicando un filtro en la columna `date_call` con `DATEADD(day, -1, GETDATE())`.
    """

    cursor.execute("""
        SELECT [id_agent], [agent_name], [date_call], [phone_code], [telephone],
               [customer_id], [customer_id2], [time_sec], [time_min], [call_cod_id],
               [status_name], [tipo], [hang_up], [campaign_id], [campaign_name],
               [list_id], [lead_id], [uniqueid], [tipo_llamada], [comments]
        FROM [NEXUM].[dbo].[ReporteLlamada]
        WHERE date_call >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL sobre la tabla `ReporteLlamada` de NEXUM para obtener las llamadas
    registradas en el último día. Se seleccionan múltiples columnas relevantes para análisis
    de desempeño, gestión y trazabilidad de las llamadas realizadas.

    La cláusula `WHERE date_call >= DATEADD(day, -1, GETDATE())` asegura que solo se incluyan
    registros cuya fecha de llamada (`date_call`) sea igual o posterior a hace 24 horas
    respecto al momento actual.
    """

    datos_reporte_llamada = cursor.fetchall()
    """
    Con `fetchall()` se obtienen todos los registros devueltos por la consulta y se guardan
    en la variable `datos_reporte_llamada`, que ahora contiene una lista de tuplas con toda
    la información de llamadas recientes.
    Esta variable luego será usada para insertar esos datos en OLAP o para validación.
    """

    # Areas
    """
    Esta sección extrae los datos de la tabla `areas` en la base de datos NEXUM.
    Se filtran únicamente los registros que hayan sido modificados o creados en las últimas 24 horas,
    utilizando la columna `fechaIntegracion` como referencia de tiempo.
    """

    cursor.execute("""
        SELECT [idArea], [nombreArea], [activo]
        FROM [NEXUM].[dbo].[areas]
        WHERE fechaIntegracion >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta sobre la tabla `areas` para traer:
    - `idArea`: Identificador único del área.
    - `nombreArea`: Nombre descriptivo del área.
    - `activo`: Estado lógico (por ejemplo, 1 = activa, 0 = inactiva).

    La condición `fechaIntegracion >= DATEADD(day, -1, GETDATE())` garantiza
    que solo se incluyan registros cuya integración haya ocurrido en las últimas 24 horas.
    """

    datos_areas = cursor.fetchall()
    """
    Recupera todos los resultados devueltos por la consulta anterior y los almacena
    en la variable `datos_areas`, la cual contiene una lista de tuplas.
    Esta información será posteriormente transferida a la base OLAP.
    """


    # Campana
    """
    Esta sección se encarga de extraer los registros recientes de la tabla `campana`
    desde la base de datos NEXUM. Se filtrarán las campañas creadas en las últimas 24 horas
    usando la columna `fechaCreacion` como criterio.
    """

    cursor.execute("""
        SELECT [idCampana], [descripcionCampana], [fechaCreacion], [estado]
        FROM [NEXUM].[dbo].[campana]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta sobre la tabla `campana` para traer:
    - `idCampana`: Identificador único de la campaña.
    - `descripcionCampana`: Nombre o descripción de la campaña.
    - `fechaCreacion`: Fecha en la que fue registrada la campaña.
    - `estado`: Estado lógico de la campaña (activa/inactiva u otros posibles estados).

    El filtro `fechaCreacion >= DATEADD(day, -1, GETDATE())` limita los resultados
    a campañas creadas desde hace un día hasta ahora.
    """

    datos_campana = cursor.fetchall()
    """
    Recupera todos los registros devueltos por la consulta anterior y los almacena
    en la variable `datos_campana`, que será usada posteriormente para insertar
    esta información en la base de datos OLAP.
    """


    # Canal
    """
    Esta sección extrae los registros recientes de la tabla `canal` en la base de datos NEXUM.
    Solo se consideran aquellos canales que fueron creados en las últimas 24 horas, usando
    la columna `fechaCreacion` como criterio de filtrado.
    """

    cursor.execute("""
        SELECT [idCanal], [canal], [descripcion]
        FROM [NEXUM].[dbo].[canal]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL para seleccionar tres columnas de la tabla `canal`:
    - `idCanal`: Identificador único del canal.
    - `canal`: Código o nombre corto del canal.
    - `descripcion`: Descripción detallada del canal.

    Se aplica un filtro `fechaCreacion >= DATEADD(day, -1, GETDATE())` para extraer
    solo los registros creados dentro de las últimas 24 horas.
    """

    datos_canal = cursor.fetchall()
    """
    Recupera todos los resultados de la consulta ejecutada y los guarda en la variable `datos_canal`.
    Esta lista de tuplas será utilizada más adelante para integrarse en la base OLAP.
    """


    # Cargue Focos
    """
    Esta sección se encarga de extraer los registros recientes desde la tabla `cargueFocos`
    en la base de datos NEXUM. Solo se toman aquellos registros cuya fecha (`fecha`) sea
    dentro de las últimas 24 horas.
    """

    cursor.execute("""
        SELECT [id], [nombreCliente], [cedula], [telefono], [producto],
               [entidad], [saldoTotal], [capital], [oferta1], [oferta2],
               [oferta3], [cuotas3], [cuotas6], [cuotas12]
        FROM [NEXUM].[dbo].[cargueFocos]
        WHERE fecha >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta sobre la tabla `cargueFocos` para obtener:
    - `id`: Identificador del registro.
    - `nombreCliente`: Nombre del cliente cargado.
    - `cedula`: Documento de identidad del cliente.
    - `telefono`: Número de teléfono asociado.
    - `producto`: Producto ofrecido.
    - `entidad`: Institución relacionada al producto.
    - `saldoTotal`, `capital`: Valores financieros asociados al cliente.
    - `oferta1`, `oferta2`, `oferta3`: Ofertas comerciales aplicables.
    - `cuotas3`, `cuotas6`, `cuotas12`: Opciones de pago en cuotas.

    El filtro `fecha >= DATEADD(day, -1, GETDATE())` asegura que solo se incluyan
    registros agregados o modificados en las últimas 24 horas.
    """

    datos_cargueFocos = cursor.fetchall()
    """
    Se recuperan todos los resultados de la consulta y se almacenan en la variable `datos_cargueFocos`.
    Este conjunto de datos será posteriormente transferido a la base OLAP para su análisis.
    """


    # Chat Mensajes
    """
    Esta sección extrae los mensajes recientes desde la tabla `ChatMensajes` de la base de datos NEXUM.
    Solo se consideran los mensajes enviados en las últimas 24 horas usando como referencia la columna `fechaEnvio`.
    """

    cursor.execute("""
        SELECT [idChat], [idRemitente], [idDestinatario], [mensaje], [fechaEnvio],
               [estado], [idCampana], [fileName], [fileAdjunto]
        FROM [NEXUM].[dbo].[ChatMensajes]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL sobre la tabla `ChatMensajes` para recuperar:
    - `idChat`: Identificador del mensaje.
    - `idRemitente`: ID del usuario que envió el mensaje.
    - `idDestinatario`: ID del usuario o grupo destinatario.
    - `mensaje`: Contenido del mensaje de texto.
    - `fechaEnvio`: Fecha y hora de envío del mensaje.
    - `estado`: Estado del mensaje (por ejemplo, leído/no leído).
    - `idCampana`: Campaña asociada al mensaje (si aplica).
    - `fileName`: Nombre del archivo adjunto (si existe).
    - `fileAdjunto`: Contenido codificado del archivo adjunto (por ejemplo en base64).

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` asegura que se traigan solo los mensajes recientes.
    """

    datos_chatMensajes = cursor.fetchall()
    """
    Se obtienen todos los registros de la consulta y se almacenan en la variable `datos_chatMensajes`.
    Esta información luego será insertada en la base OLAP para su análisis o seguimiento de comunicación.
    """


    # FamiSanarDetalle
    """
    Esta sección extrae los registros recientes de la tabla `FamiSanarDetalle` en la base NEXUM.
    El objetivo es capturar todos los datos enviados en las últimas 24 horas, utilizando la columna `fechaEnvio`
    como referencia temporal para el filtro.
    """

    cursor.execute("""
        SELECT [idDetalle], [idEncabezado], [cedula], [nombres], [apellidos], [estado],
               [IPS], [convenio], [tipo], [categoria], [semanas], [fechaNacimiento], [edad], 
               [sexo], [direccion], [telefono], [departamento], [municipio], [causal], [numItem]
        FROM [NEXUM].[dbo].[FamiSanarDetalle]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se ejecuta una consulta SQL para traer múltiples columnas desde la tabla `FamiSanarDetalle`, entre ellas:
    - `idDetalle`: ID único del detalle.
    - `idEncabezado`: Clave foránea que enlaza con el encabezado principal.
    - `cedula`, `nombres`, `apellidos`: Datos personales del usuario.
    - `estado`, `IPS`, `convenio`: Información médica o institucional.
    - `tipo`, `categoria`, `semanas`, `fechaNacimiento`, `edad`, `sexo`: Datos clínicos o demográficos.
    - `direccion`, `telefono`, `departamento`, `municipio`: Datos de ubicación y contacto.
    - `causal`, `numItem`: Información adicional del caso.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` asegura que solo se traigan registros del último día.
    """

    datos_famiSanarDetalle = cursor.fetchall()
    """
    Todos los registros devueltos por la consulta se almacenan en la variable `datos_famiSanarDetalle`,
    que contiene una lista de tuplas con todos los datos necesarios para posterior integración en OLAP.
    """


    # FamiSanarEncabezado
    """
    Esta sección extrae los registros recientes desde la tabla `FamiSanarEncabezado` de la base NEXUM.
    Se usa la columna `fechaEnvio` para filtrar los encabezados que hayan sido enviados en las últimas 24 horas.
    """

    cursor.execute("""
        SELECT [idEncabezado], [automatizacion], [idUsuario], [fechaCargue], [totalRegistros]
        FROM [NEXUM].[dbo].[FamiSanarEncabezado]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL para obtener los campos clave del encabezado:
    - `idEncabezado`: Identificador único del encabezado del cargue.
    - `automatizacion`: Valor que indica si fue un proceso automático (booleano o texto).
    - `idUsuario`: ID del usuario que realizó el cargue.
    - `fechaCargue`: Fecha en la que se subió el archivo con los datos.
    - `totalRegistros`: Cantidad total de registros cargados en ese evento.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` garantiza que solo se incluyan encabezados cargados
    desde hace 24 horas o menos.
    """

    datos_famiSanarEncabezado = cursor.fetchall()
    """
    Se obtienen todos los registros devueltos por la consulta y se almacenan en la variable `datos_famiSanarEncabezado`.
    Esta lista se utilizará posteriormente para ser replicada en la base de datos OLAP junto a su detalle correspondiente.
    """


    # Nombres Comunes
    """
    Esta sección extrae registros recientes desde la tabla `NombresComunes` en la base NEXUM.
    El objetivo es obtener los nombres y apellidos comunes que fueron registrados o actualizados
    durante las últimas 24 horas.
    """

    cursor.execute("""
        SELECT [idNombres], [nombre], [apellido]
        FROM [NEXUM].[dbo].[NombresComunes]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL para obtener:
    - `idNombres`: Identificador único del nombre registrado.
    - `nombre`: Nombre propio (ej. Juan, María).
    - `apellido`: Apellido correspondiente (ej. Pérez, Gómez).

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` permite extraer únicamente los registros recientes.
    Esto asegura que se trabaje solo con datos nuevos o modificados en las últimas 24 horas.
    """

    datos_nombresComunes = cursor.fetchall()
    """
    Se obtienen todos los resultados devueltos por la consulta y se almacenan en la variable `datos_nombresComunes`.
    Esta lista de tuplas será utilizada más adelante para insertarse en la base OLAP si corresponde.
    """


    # Roles
    """
    Esta sección extrae los registros recientes desde la tabla `roles` en la base de datos NEXUM.
    Solo se consideran los roles que hayan sido creados o actualizados en las últimas 24 horas,
    utilizando el campo `fechaEnvio` como filtro temporal.
    """

    cursor.execute("""
        SELECT [idRol], [rol], [activo]
        FROM [NEXUM].[dbo].[roles]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL para recuperar los siguientes campos:
    - `idRol`: Identificador único del rol.
    - `rol`: Nombre o descripción del rol (por ejemplo, Administrador, Asesor, Supervisor).
    - `activo`: Estado lógico del rol (1 = activo, 0 = inactivo).

    Se usa el filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` para traer solo los registros
    con cambios recientes en el último día.
    """

    datos_roles = cursor.fetchall()
    """
    Obtiene todos los registros resultantes de la consulta y los guarda en la variable `datos_roles`.
    Esta información se usará para sincronizar los roles entre NEXUM y la base OLAP.
    """


    # Rues Detalle
    """
    Esta sección se encarga de extraer los datos recientes de la tabla `RuesDetalle`
    en la base de datos NEXUM. Se filtran los registros que hayan sido enviados
    (es decir, cargados o modificados) en las últimas 24 horas usando la columna `fechaEnvio`.
    """

    cursor.execute("""
        SELECT [idDetalle], [idEncabezado], [cedula], [nombre], [identificacion],
               [categoria], [camaraComercio], [numeroMatricula], [actividadEconomica], 
               [numItem]
        FROM [NEXUM].[dbo].[RuesDetalle]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL sobre la tabla `RuesDetalle` para traer:
    - `idDetalle`: Identificador único del detalle dentro del RUES.
    - `idEncabezado`: Clave foránea que relaciona este detalle con su encabezado.
    - `cedula`, `nombre`, `identificacion`: Información básica del contribuyente o empresa.
    - `categoria`: Tipo o grupo al que pertenece.
    - `camaraComercio`: Cámara de comercio correspondiente.
    - `numeroMatricula`: Número de matrícula mercantil.
    - `actividadEconomica`: Actividad económica principal registrada.
    - `numItem`: Número de ítem en el lote o archivo.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` garantiza que solo se incluyan
    registros nuevos o modificados en las últimas 24 horas.
    """

    datos_ruesDetalle = cursor.fetchall()
    """
    Se obtienen todos los resultados devueltos por la consulta y se almacenan
    en la variable `datos_ruesDetalle`. Esta lista será usada para insertar la información
    en la base OLAP como parte del proceso de integración.
    """


    # Rues Encabezado
    """
    Esta sección extrae los registros recientes desde la tabla `RuesEncabezado` en la base de datos NEXUM.
    Se obtienen únicamente aquellos encabezados que fueron enviados (creados o modificados)
    en las últimas 24 horas, usando como referencia el campo `fechaEnvio`.
    """

    cursor.execute("""
        SELECT [idEncabezado], [automatizacion], [idUsuario], [fechaCargue], [totalRegistros]
               FROM [NEXUM].[dbo].[RuesEncabezado]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL sobre la tabla `RuesEncabezado` para obtener:
    - `idEncabezado`: Identificador principal del cargue RUES.
    - `automatizacion`: Indicador de si el proceso fue automatizado (puede ser booleano o texto).
    - `idUsuario`: ID del usuario que cargó el archivo o información.
    - `fechaCargue`: Fecha en la que se subió el archivo o se realizó la carga de datos.
    - `totalRegistros`: Número total de registros incluidos en ese encabezado de cargue.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` limita los resultados a los registros
    cargados en las últimas 24 horas.
    """

    datos_ruesEncabezado = cursor.fetchall()
    """
    Recupera todos los resultados devueltos por la consulta y los almacena en la variable `datos_ruesEncabezado`.
    Esta lista de tuplas se usará para insertar la información en la base OLAP durante el proceso de integración.
    """


    # Runt Detalle
    """
    Esta sección extrae los registros recientes de la tabla `RuntDetalle` desde la base de datos NEXUM.
    Solo se incluyen los registros cuya fecha de envío (`fechaEnvio`) sea dentro de las últimas 24 horas.
    Esta información corresponde al detalle de vehículos registrados en el sistema RUNT.
    """

    cursor.execute("""
        SELECT [idDetalle], [idEncabezado], [cedula], [placaVehiculo], [tipoServicio], [estadoVehiculo],
               [claseVehiculo], [marca], [modelo], [numeroSerie], [numeroChasis], [cilindraje],
               [tipoCombustible], [autoridadTransito], [linea], [color], [numeroMotor], [numeroVIN],
               [tipoCarroceria], [polizaSOAT], [revisionTecnomecanica], [limitacionesPropiedad],
               [garantiasAFavorDe], [numItem]
               FROM [NEXUM].[dbo].[RuntDetalle]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta sobre la tabla `RuntDetalle` para obtener:
    - `idDetalle`: Identificador del detalle.
    - `idEncabezado`: Identificador del encabezado al que pertenece este detalle.
    - `cedula`: Documento del propietario o usuario.
    - `placaVehiculo`: Placa del vehículo registrado.
    - `tipoServicio`, `estadoVehiculo`, `claseVehiculo`: Información técnica y administrativa del vehículo.
    - `marca`, `modelo`, `numeroSerie`, `numeroChasis`, `cilindraje`: Datos del vehículo físico.
    - `tipoCombustible`: Tipo de combustible usado (gasolina, diésel, etc.).
    - `autoridadTransito`: Organismo de tránsito que lo registra.
    - `linea`, `color`, `numeroMotor`, `numeroVIN`: Más datos técnicos.
    - `tipoCarroceria`, `polizaSOAT`, `revisionTecnomecanica`: Estado legal del vehículo.
    - `limitacionesPropiedad`, `garantiasAFavorDe`: Información jurídica relevante.
    - `numItem`: Número de ítem dentro del cargue.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` garantiza que solo se traigan los registros más recientes.
    """

    datos_runtDetalle = cursor.fetchall()
    """
    Recupera todos los resultados de la consulta y los guarda en la variable `datos_runtDetalle`.
    Esta lista de tuplas contiene los detalles por vehículo, listos para ser integrados en la base OLAP.
    """


    # Runt Encabezado
    """
    Esta sección extrae los registros recientes de la tabla `RuntEncabezado` desde la base de datos NEXUM.
    Se filtran los encabezados que hayan sido enviados en las últimas 24 horas,
    utilizando como criterio la columna `fechaEnvio`.
    """

    cursor.execute("""
        SELECT [idEncabezado], [automatizacion], [idUsuario], [fechaCargue], [totalRegistros]
               FROM [NEXUM].[dbo].[RuntEncabezado]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL para obtener los campos clave del encabezado del cargue RUNT:
    - `idEncabezado`: Identificador único del encabezado.
    - `automatizacion`: Indica si el proceso de carga fue automático.
    - `idUsuario`: ID del usuario que realizó el proceso.
    - `fechaCargue`: Fecha en la que se subieron los registros.
    - `totalRegistros`: Cantidad total de detalles (vehículos) que se cargaron.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` limita los resultados
    a los encabezados cargados o modificados en las últimas 24 horas.
    """

    datos_runtEncabezado = cursor.fetchall()
    """
    Todos los resultados obtenidos se almacenan en la variable `datos_runtEncabezado`.
    Esta información se usará para insertar los encabezados en la base OLAP como parte del proceso de integración.
    """


    # Super Notariado Detalle
    """
    Esta sección extrae los registros recientes desde la tabla `SuperNotariadoDetalle` en la base NEXUM.
    Se filtran los detalles enviados en las últimas 24 horas, usando el campo `fechaEnvio`
    para asegurar que solo se integren los registros nuevos o actualizados.
    """

    cursor.execute("""
        SELECT [idDetalle], [idEncabezado], [CC], [numItem], [ciudad], [matricula], [direccion], [vinculadoA]
        FROM [NEXUM].[dbo].[SuperNotariadoDetalle]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se ejecuta una consulta SQL que obtiene los siguientes campos:
    - `idDetalle`: Identificador del detalle del registro.
    - `idEncabezado`: Identificador que relaciona el detalle con su encabezado.
    - `CC`: Documento de identidad del titular.
    - `numItem`: Número del ítem dentro del lote o archivo.
    - `ciudad`: Ciudad donde está registrado el bien.
    - `matricula`: Número de matrícula inmobiliaria.
    - `direccion`: Dirección del bien.
    - `vinculadoA`: Persona o entidad a la que está vinculado el bien.

    La cláusula `WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())` garantiza que se obtengan
    únicamente los registros procesados o modificados en las últimas 24 horas.
    """

    datos_superNotariadoDetalle = cursor.fetchall()
    """
    Se recuperan todos los registros devueltos por la consulta y se guardan
    en la variable `datos_superNotariadoDetalle`, que contiene una lista de tuplas
    con los detalles de propiedades o bienes registrados para ser integrados en OLAP.
    """


    # Super Notariado Encabezado
    """
    Esta sección se encarga de extraer los registros recientes desde la tabla `SuperNotariadoEncabezado`
    de la base de datos NEXUM. Se filtran los encabezados cargados o modificados en las últimas 24 horas,
    utilizando la columna `fechaEnvio` como criterio de inclusión.
    """

    cursor.execute("""
        SELECT  [idEncabezado], [automatizacion], [idUsuario], [fechaCargue], [totalRegistros]
               FROM [NEXUM].[dbo].[SuperNotariadoEncabezado]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Ejecuta una consulta SQL que obtiene:
    - `idEncabezado`: Identificador principal del lote de carga.
    - `automatizacion`: Indicador de si el proceso fue realizado automáticamente (por robot o sistema).
    - `idUsuario`: Usuario responsable del cargue de datos.
    - `fechaCargue`: Fecha en que se subió el archivo o lote de información.
    - `totalRegistros`: Número total de detalles asociados a ese encabezado.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` permite traer únicamente los encabezados
    que fueron enviados o modificados en el último día.
    """

    datos_superNotariadoEncabezado = cursor.fetchall()
    """
    Los resultados obtenidos se almacenan en la variable `datos_superNotariadoEncabezado`,
    una lista de tuplas que contiene todos los encabezados recientes listos para integrarse
    en la base de datos OLAP como parte del proceso de consolidación.
    """


    # Unificado
    """
    Esta sección extrae los registros recientes de la tabla `unificado` en la base de datos NEXUM.
    Esta tabla parece contener una consolidación o mezcla de varias fuentes de llamadas o interacciones.
    Se filtran los datos enviados en las últimas 24 horas mediante la columna `fechaEnvio`.
    """

    cursor.execute("""
        SELECT  [id_agent], [agent_name], [date_call], [phone_code], [telephone], [customer_id], [customer_id2],
                [time_sec], [time_min], [call_cod_id], [status_name], [tipo], [hang_up], [campaign_id], [campaign_name],
                [list_id], [lead_id], [uniqueid], [tipo_llamada], [comments]
               FROM [NEXUM].[dbo].[unificado]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se ejecuta una consulta SQL para extraer todos los campos relevantes relacionados con llamadas o gestiones:
    - `id_agent`, `agent_name`: Información del agente que realizó la llamada.
    - `date_call`, `phone_code`, `telephone`: Detalles de la llamada realizada.
    - `customer_id`, `customer_id2`: Identificadores de cliente.
    - `time_sec`, `time_min`: Duración de la llamada en segundos y minutos.
    - `call_cod_id`, `status_name`: Código de llamada y su estado.
    - `tipo`, `hang_up`, `tipo_llamada`: Detalles del tipo de contacto y su cierre.
    - `campaign_id`, `campaign_name`: Campaña asociada.
    - `list_id`, `lead_id`: Lista y lead relacionado.
    - `uniqueid`: Identificador único de la llamada.
    - `comments`: Comentarios adicionales o anotaciones.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` permite obtener solo registros del último día.
    """

    datos_unificado = cursor.fetchall()
    """
    Los resultados de la consulta se almacenan en la variable `datos_unificado`, que contiene
    una lista de tuplas con la información consolidada de llamadas o interacciones.
    Estos datos luego se usarán para integrarse en la base OLAP.
    """


    # Usuarios
    """
    Esta sección extrae los registros recientes desde la tabla `Usuarios` de la base de datos NEXUM.
    Se incluyen únicamente los usuarios que hayan sido creados o modificados en las últimas 24 horas,
    utilizando la columna `fechaEnvio` como filtro de referencia.
    """

    cursor.execute("""
        SELECT [id], [usuario], [clave], [activo]
               FROM [NEXUM].[dbo].[Usuarios]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se ejecuta una consulta SQL que obtiene los siguientes campos:
    - `id`: Identificador único del usuario.
    - `usuario`: Nombre de usuario o login.
    - `clave`: Contraseña del usuario (posiblemente en texto plano o encriptada, según implementación).
    - `activo`: Estado del usuario (1 = activo, 0 = inactivo).

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` asegura que solo se extraigan
    los usuarios que fueron agregados o actualizados en las últimas 24 horas.
    """

    datos_usuarios = cursor.fetchall()
    """
    Se obtienen todos los registros retornados por la consulta y se almacenan en la variable `datos_usuarios`.
    Esta información será utilizada para sincronizar la base OLAP con los usuarios actuales del sistema NEXUM.
    """


    # Usuarios App
    """
    Esta sección extrae los registros recientes desde la tabla `UsuariosApp` en la base de datos NEXUM.
    Esta tabla contiene los usuarios del sistema de la aplicación (frontend o administración).
    Solo se extraen aquellos registros cuya `fechaEnvio` sea de las últimas 24 horas.
    """

    cursor.execute("""
        SELECT [idUsuarioApp], [nombre], [username], [correo], [cargo], [idArea],
               [idRol], [activo]
               FROM [NEXUM].[dbo].[UsuariosApp]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    La consulta SQL recupera los siguientes campos:
    - `idUsuarioApp`: Identificador único del usuario de la aplicación.
    - `nombre`: Nombre completo del usuario.
    - `username`: Nombre de usuario con el que inicia sesión.
    - `correo`: Dirección de correo electrónico.
    - `cargo`: Rol o posición ocupada (descripción textual).
    - `idArea`: Área a la que pertenece (clave foránea).
    - `idRol`: Rol asignado dentro del sistema (clave foránea).
    - `activo`: Estado lógico del usuario (1 = activo, 0 = inactivo).

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` garantiza que se traigan
    solo usuarios nuevos o actualizados en el último día.
    """

    datos_usuariosApp = cursor.fetchall()
    """
    Se recuperan todos los registros de la consulta y se guardan en la variable `datos_usuariosApp`.
    Esta información se usará posteriormente para actualizar o sincronizar la base OLAP con los usuarios activos.
    """


    # Usuarios Campanas
    """
    Esta última sección extrae los registros de la tabla `UsuariosCampanas` desde la base NEXUM.
    Esta tabla relaciona a los usuarios con las campañas a las que están asignados.
    Solo se traen las relaciones cargadas o modificadas en las últimas 24 horas.
    """

    cursor.execute("""
        SELECT [idUsuarioApp], [idCampana]
               FROM [NEXUM].[dbo].[UsuariosCampanas]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se consulta la tabla `UsuariosCampanas` y se recuperan:
    - `idUsuarioApp`: ID del usuario asignado.
    - `idCampana`: ID de la campaña a la que pertenece.

    Se utiliza `fechaEnvio >= DATEADD(day, -1, GETDATE())` para filtrar únicamente los registros recientes.
    """

    datos_usuariosCampanas = cursor.fetchall()
    """
    Se obtienen todos los registros y se almacenan en la variable `datos_usuariosCampanas`.
    """

    conn.close()
    """
    Se cierra la conexión a la base de datos NEXUM tras haber ejecutado todas las consultas de extracción.
    """

    return (
        datos_reporte_llamada, datos_areas, datos_campana,
        datos_canal, datos_cargueFocos, datos_chatMensajes,
        datos_famiSanarDetalle, datos_famiSanarEncabezado,
        datos_nombresComunes, datos_roles, datos_ruesDetalle,
        datos_ruesEncabezado, datos_runtDetalle, datos_runtEncabezado,
        datos_superNotariadoDetalle, datos_superNotariadoEncabezado,
        datos_unificado, datos_usuarios, datos_usuariosApp, datos_usuariosCampanas
    )
    """
    Retorna una tupla con todos los datasets extraídos desde la base NEXUM.
    Estos datos serán utilizados como entrada para la función de inserción en OLAP.
    """

# ------------------------------------------------------------------------------------------------
# INSERCIÓN: INSERTA LOS DATOS EXTRAÍDOS DE NEXUM EN LA BASE OLAP
# ------------------------------------------------------------------------------------------------
def insertar_datos_destino_nexum_a_olap(
    datos_reporte_llamada, datos_areas, datos_campana,
    datos_canal, datos_cargueFocos, datos_chatMensajes,
    datos_famiSanarDetalle, datos_famiSanarEncabezado,
    datos_nombresComunes, datos_roles, datos_ruesDetalle,
    datos_ruesEncabezado, datos_runtDetalle, datos_runtEncabezado,
    datos_superNotariadoDetalle, datos_superNotariadoEncabezado,
    datos_unificado, datos_usuarios, datos_usuariosApp, datos_usuariosCampanas
):
    """
    Esta función se encarga de recibir todos los datos extraídos desde NEXUM y cargarlos
    en la base OLAP. Cada conjunto de datos se inserta en su tabla correspondiente
    mediante la función auxiliar `insertar_tabla`.

    También se registra un log de control de integración por cada tabla procesada,
    usando la función `log_integracion`.
    """
    conn = conectar_sql(CONFIG_OLAP)
    """
    Se establece una conexión a la base de datos OLAP.
    """

    cursor = conn.cursor()
    """
    Se obtiene el cursor para ejecutar sentencias SQL en la base OLAP.
    """

    def insertar_tabla(nombre_tabla, datos, query_insert):
        """
        Esta función auxiliar realiza la inserción de un conjunto de datos en una tabla específica de OLAP.
        También registra en la tabla `ControlIntegracion` el resultado del proceso: exitoso o fallido.
        
        Parámetros:
        - `nombre_tabla`: nombre de la tabla destino.
        - `datos`: lista de tuplas con los registros a insertar.
        - `query_insert`: sentencia SQL con parámetros `?` para la inserción.
        """
        try:
            fecha_inicio = datetime.now()
            registros = 0

            for fila in datos:
                cursor.execute(query_insert, tuple(fila))
                registros += 1

            fecha_fin = datetime.now()
            log_integracion(cursor, "NEXUM", "OLAP", nombre_tabla, fecha_inicio, fecha_fin, registros, "Exitoso")
            """
            Si no hay errores, se registra en el log de integración con estado exitoso.
            """

        except Exception as e:
            fecha_fin = datetime.now()
            log_integracion(cursor, "NEXUM", "OLAP", nombre_tabla, fecha_inicio, fecha_fin, 0, "Fallido", str(e))
            """
            En caso de error, se registra en el log de integración como fallido, junto con el mensaje del error.
            """


    # Reporte Llamada
    """
    Inserta en la tabla `ReporteLlamada` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla contiene el histórico de llamadas realizadas por los agentes, incluyendo detalles
    técnicos y administrativos de cada interacción.
    """

    insertar_tabla("ReporteLlamada", datos_reporte_llamada, """
        INSERT INTO ReporteLlamada (
            id_agent, agent_name, date_call, phone_code, telephone,
            customer_id, customer_id2, time_sec, time_min, call_cod_id,
            status_name, tipo, hang_up, campaign_id, campaign_name,
            list_id, lead_id, uniqueid, tipo_llamada, comments
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Llama a la función `insertar_tabla` pasando:
    - `"ReporteLlamada"`: nombre de la tabla destino en OLAP.
    - `datos_reporte_llamada`: lista de tuplas obtenida desde NEXUM.
    - La sentencia SQL parametrizada con 20 columnas, en el mismo orden que en la tabla original.

    Cada fila es insertada individualmente con `cursor.execute(...)`, y al final se registra
    en la tabla `ControlIntegracion` si el proceso fue exitoso o fallido.
    """


    # Areas
    """
    Inserta en la tabla `Areas` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla representa las áreas o departamentos organizacionales del sistema (por ejemplo: Comercial, Legal, Cobranza).
    """

    insertar_tabla("Areas", datos_areas, """
        INSERT INTO Areas (
            idArea, nombreArea, activo
        ) VALUES (?, ?, ?)
    """)
    """
    Se utiliza la función `insertar_tabla` enviando:
    - `"Areas"`: nombre de la tabla de destino en OLAP.
    - `datos_areas`: lista de tuplas obtenida desde NEXUM.
    - Sentencia SQL que contiene 3 parámetros:
        - `idArea`: Identificador único del área.
        - `nombreArea`: Nombre o descripción textual.
        - `activo`: Estado lógico (1 = activa, 0 = inactiva).

    Cada fila es insertada con un `cursor.execute(...)` y se registra el proceso en `ControlIntegracion`.
    En caso de error, se documenta el fallo con su mensaje.
    """


    # Campana
    """
    Inserta en la tabla `Campana` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla contiene información sobre las campañas activas o históricas gestionadas
    dentro del sistema (por ejemplo: Campañas de cobranza, fidelización, encuestas, etc.).
    """

    insertar_tabla("Campana", datos_campana, """
        INSERT INTO Campana (
            idCampana, descripcionCampana, fechaCreacion, estado
        ) VALUES (?, ?, ?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"Campana"`: nombre de la tabla en OLAP.
    - `datos_campana`: lista de tuplas con los datos traídos desde NEXUM.
    - La sentencia SQL espera 4 valores por registro:
        - `idCampana`: Identificador de la campaña.
        - `descripcionCampana`: Texto descriptivo.
        - `fechaCreacion`: Fecha de alta de la campaña.
        - `estado`: Estado de la campaña (activo, inactivo, finalizado, etc.).

    El proceso registra un log en `ControlIntegracion`, indicando si fue exitoso o fallido.
    """


    # Canal
    """
    Inserta en la tabla `Canal` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla almacena los diferentes canales de contacto a través de los cuales se puede interactuar
    con los clientes o usuarios (por ejemplo: WhatsApp, Email, Telefónico, etc.).
    """

    insertar_tabla("Canal", datos_canal, """
        INSERT INTO Canal (
            idCanal, canal, descripcion
        ) VALUES (?, ?, ?)
    """)
    """
    Se invoca la función `insertar_tabla` con:
    - `"Canal"`: nombre de la tabla destino en OLAP.
    - `datos_canal`: lista de registros obtenidos desde NEXUM.
    - La sentencia SQL incluye 3 columnas:
        - `idCanal`: Identificador único del canal.
        - `canal`: Nombre del canal (ej. 'SMS').
        - `descripcion`: Descripción opcional o detallada del canal.

    Por cada fila insertada, se registra el resultado (éxito o fallo) en la tabla `ControlIntegracion`.
    """


    # Cargue Focos
    """
    Inserta en la tabla `CargueFocos` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla contiene información detallada de los clientes potenciales o actuales a los que se aplican
    campañas específicas, junto con sus datos financieros y ofertas comerciales.
    """

    insertar_tabla("CargueFocos", datos_cargueFocos, """
        INSERT INTO CargueFocos (
            id, nombreCliente, cedula, telefono, producto, entidad, saldoTotal,
            capital, oferta1, oferta2, oferta3, cuotas3, cuotas6, cuotas12
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"CargueFocos"`: nombre de la tabla destino en OLAP.
    - `datos_cargueFocos`: registros obtenidos desde NEXUM.
    - La consulta espera 14 columnas por fila:
        - `id`: Identificador del registro.
        - `nombreCliente`: Nombre del cliente asociado.
        - `cedula`: Número de documento.
        - `telefono`: Número de contacto principal.
        - `producto`, `entidad`: Producto financiero y entidad que lo ofrece.
        - `saldoTotal`, `capital`: Valores económicos relacionados con la deuda o producto.
        - `oferta1`, `oferta2`, `oferta3`: Ofertas comerciales personalizadas.
        - `cuotas3`, `cuotas6`, `cuotas12`: Simulaciones de pago a diferentes plazos.

    Cada inserción se registra en la tabla de control con estado exitoso o fallido según el resultado.
    """

    # Chat Mensajes
    """
    Inserta en la tabla `ChatMensajes` de OLAP todos los mensajes de chat extraídos desde NEXUM.
    Esta tabla almacena las conversaciones entre usuarios, incluyendo mensajes individuales, grupales
    o relacionados con campañas automatizadas.
    """

    insertar_tabla("ChatMensajes", datos_chatMensajes, """
        INSERT INTO ChatMensajes (
            idChat, idRemitente, idDestinatario, mensaje, fechaEnvio,
            estado, idCampana, fileName, fileAdjunto
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"ChatMensajes"`: nombre de la tabla en la base OLAP.
    - `datos_chatMensajes`: lista de mensajes obtenidos de NEXUM.
    - La sentencia SQL incluye 9 columnas:
        - `idChat`: Identificador del mensaje.
        - `idRemitente`: Usuario que envió el mensaje.
        - `idDestinatario`: Receptor del mensaje (puede ser otro usuario o un grupo).
        - `mensaje`: Texto del mensaje.
        - `fechaEnvio`: Fecha y hora en que fue enviado.
        - `estado`: Estado del mensaje (ej. leído/no leído).
        - `idCampana`: Campaña a la que está asociado (si aplica).
        - `fileName`: Nombre del archivo adjunto (si existe).
        - `fileAdjunto`: Contenido del archivo en binario.

    La inserción se registra en la tabla `ControlIntegracion` indicando si fue exitosa o fallida.
    """


    # FamiSanar Detalle
    """
    Inserta en la tabla `FamiSanarDetalle` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla contiene el detalle de afiliados y beneficiarios del programa FamiSanar, incluyendo
    información personal, médica y administrativa.
    """

    insertar_tabla("FamiSanarDetalle", datos_famiSanarDetalle, """
        INSERT INTO FamiSanarDetalle (
            idDetalle, idEncabezado, cedula, nombres, apellidos, estado, IPS,
            convenio, tipo, categoria, semanas, fechaNacimiento, edad, sexo,
            direccion, telefono, departamento, municipio, causal, numItem
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"FamiSanarDetalle"`: nombre de la tabla en OLAP.
    - `datos_famiSanarDetalle`: registros traídos de la base NEXUM.
    - La consulta SQL contiene 20 columnas:
        - `idDetalle`: Identificador del detalle.
        - `idEncabezado`: Referencia al encabezado del lote.
        - `cedula`, `nombres`, `apellidos`: Datos personales del afiliado.
        - `estado`: Estado del beneficiario (activo, retirado, etc.).
        - `IPS`, `convenio`: Entidad de salud y convenio correspondiente.
        - `tipo`, `categoria`: Clasificación del usuario dentro del programa.
        - `semanas`, `fechaNacimiento`, `edad`, `sexo`: Datos médicos y demográficos.
        - `direccion`, `telefono`, `departamento`, `municipio`: Ubicación de residencia.
        - `causal`: Motivo o condición relevante.
        - `numItem`: Número del ítem dentro del lote de datos.

    Cada registro es procesado individualmente, y el resultado queda registrado en `ControlIntegracion`.
    """

    # FamiSanarEncabezado
    """
    Inserta en la tabla `FamiSanarEncabezado` de OLAP todos los encabezados extraídos desde NEXUM.
    Esta tabla representa los lotes o agrupaciones de registros detallados del programa FamiSanar,
    que se complementan con la tabla `FamiSanarDetalle`.
    """

    insertar_tabla("FamiSanarEncabezado", datos_famiSanarEncabezado, """
        INSERT INTO FamiSanarEncabezado (
            idEncabezado, automatizacion, idUsuario, fechaCargue, totalRegistros
        ) VALUES (?, ?, ?, ?, ?)
    """)
    """
    Se utiliza `insertar_tabla` con los siguientes parámetros:
    - `"FamiSanarEncabezado"`: nombre de la tabla destino en OLAP.
    - `datos_famiSanarEncabezado`: registros obtenidos desde NEXUM.
    - Consulta SQL con 5 columnas:
        - `idEncabezado`: Identificador del lote o grupo de registros.
        - `automatizacion`: Indica si fue cargado automáticamente (1) o manualmente (0).
        - `idUsuario`: Usuario responsable de la carga.
        - `fechaCargue`: Fecha en que se procesó el lote.
        - `totalRegistros`: Número de registros que contiene ese lote (coincide con detalle).

    Se registra en `ControlIntegracion` el resultado de cada inserción, exitoso o fallido.
    """


    # Nombres Comunes
    """
    Inserta en la tabla `NombresComunes` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla contiene una lista de nombres y apellidos frecuentes en el sistema, usada comúnmente
    para procesos de validación, filtrado o clasificación automatizada de datos.
    """

    insertar_tabla("NombresComunes", datos_nombresComunes, """
        INSERT INTO NombresComunes (
            idNombres, nombre, apellido
        ) VALUES (?, ?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"NombresComunes"`: nombre de la tabla destino en OLAP.
    - `datos_nombresComunes`: lista de tuplas con los datos de nombres y apellidos.
    - La consulta SQL espera 3 columnas:
        - `idNombres`: Identificador único del registro.
        - `nombre`: Nombre común (ej. "Juan", "María").
        - `apellido`: Apellido común (ej. "Gómez", "Rodríguez").

    Esta tabla puede ser utilizada en algoritmos de detección de duplicados, corrección de datos
    o normalización de campos textuales. Como siempre, el resultado queda registrado en `ControlIntegracion`.
    """


    # Roles
    """
    Inserta en la tabla `Roles` de OLAP todos los registros extraídos desde la base NEXUM.
    Esta tabla define los diferentes perfiles o niveles de acceso del sistema, como por ejemplo:
    Administrador, Asesor, Coordinador, etc.
    """

    insertar_tabla("Roles", datos_roles, """
        INSERT INTO Roles (
            idRol, rol, activo
        ) VALUES (?, ?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"Roles"`: nombre de la tabla destino en OLAP.
    - `datos_roles`: lista de tuplas con los roles extraídos.
    - La sentencia SQL espera 3 columnas:
        - `idRol`: Identificador único del rol.
        - `rol`: Nombre o descripción del rol (ej. 'Administrador').
        - `activo`: Estado lógico del rol (1 = activo, 0 = inactivo).

    Esta tabla es clave para los sistemas de permisos y gestión de usuarios.
    El resultado de la inserción se registra en la tabla `ControlIntegracion`.
    """


    # Rues Detalle
    """
    Inserta en la tabla `RuesDetalle` de OLAP todos los registros detallados extraídos desde NEXUM.
    Esta tabla contiene información sobre la inscripción de personas o empresas en el Registro Único Empresarial y Social (RUES),
    con datos clave sobre su actividad económica y formalización empresarial.
    """

    insertar_tabla("RuesDetalle", datos_ruesDetalle, """
        INSERT INTO RuesDetalle (
            idDetalle, idEncabezado, cedula, nombre, identificacion, categoria,
            camaraComercio, numeroMatricula, actividadEconomica, numItem
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Se llama a `insertar_tabla` con:
    - `"RuesDetalle"`: nombre de la tabla destino en OLAP.
    - `datos_ruesDetalle`: lista de registros obtenidos desde NEXUM.
    - La sentencia SQL contiene 10 columnas:
        - `idDetalle`: Identificador del registro detallado.
        - `idEncabezado`: Referencia al lote o grupo del encabezado.
        - `cedula`: Documento del titular o representante.
        - `nombre`: Nombre completo de la persona o empresa.
        - `identificacion`: Tipo o número de identificación adicional.
        - `categoria`: Clasificación empresarial.
        - `camaraComercio`: Nombre de la cámara de comercio registrada.
        - `numeroMatricula`: Matrícula mercantil asignada.
        - `actividadEconomica`: Tipo de negocio o sector productivo.
        - `numItem`: Orden dentro del grupo/lote.

    Todos los registros procesados se registran en la tabla de auditoría `ControlIntegracion`.
    """


    # Rues Encabezado
    """
    Inserta en la tabla `RuesEncabezado` de OLAP todos los registros de encabezado extraídos desde NEXUM.
    Esta tabla representa los lotes de carga que agrupan los registros del `RuesDetalle`.
    Cada encabezado contiene metadatos sobre la carga del conjunto empresarial proveniente del RUES.
    """

    insertar_tabla("RuesEncabezado", datos_ruesEncabezado, """
        INSERT INTO RuesEncabezado (
            idEncabezado, automatizacion, idUsuario, fechaCargue, totalRegistros
        ) VALUES (?, ?, ?, ?, ?)
    """)
    """
    Se llama a `insertar_tabla` con:
    - `"RuesEncabezado"`: nombre de la tabla destino en OLAP.
    - `datos_ruesEncabezado`: lista de encabezados extraídos desde NEXUM.
    - La consulta SQL espera 5 columnas:
        - `idEncabezado`: ID único del lote de carga.
        - `automatizacion`: Indica si fue procesado automáticamente (1) o manualmente (0).
        - `idUsuario`: Usuario que ejecutó o cargó el lote.
        - `fechaCargue`: Fecha de carga del lote.
        - `totalRegistros`: Cantidad total de registros asociados al encabezado.

    Este encabezado se complementa con múltiples registros en la tabla `RuesDetalle`.
    El resultado de la inserción se audita en `ControlIntegracion`.
    """


    # Runt Detalle
    """
    Inserta en la tabla `RuntDetalle` de OLAP todos los registros extraídos desde NEXUM.
    Esta tabla contiene la información detallada de vehículos registrada en el sistema RUNT (Registro Único Nacional de Tránsito),
    incluyendo aspectos técnicos, de propiedad y de identificación vehicular.
    """

    insertar_tabla("RuntDetalle", datos_runtDetalle, """
        INSERT INTO RuntDetalle (
            idDetalle, idEncabezado, cedula, placaVehiculo, tipoServicio,
            estadoVehiculo, claseVehiculo, marca, modelo, numeroSerie,
            numeroChasis, cilindraje, tipoCombustible, autoridadTransito,
            linea, color, numeroMotor, numeroVIN, tipoCarroceria, polizaSOAT,
            revisionTecnomecanica, limitacionesPropiedad, garantiasAFavorDe, numItem
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"RuntDetalle"`: nombre de la tabla destino en OLAP.
    - `datos_runtDetalle`: lista de registros detallados extraídos desde NEXUM.
    - La consulta SQL inserta 24 columnas:
        - Datos del propietario: `cedula`.
        - Identificación vehicular: `placaVehiculo`, `numeroSerie`, `numeroChasis`, `numeroMotor`, `numeroVIN`.
        - Especificaciones del vehículo: `marca`, `modelo`, `claseVehiculo`, `tipoServicio`, `cilindraje`, `color`, `tipoCarroceria`, `linea`.
        - Información legal: `polizaSOAT`, `revisionTecnomecanica`, `limitacionesPropiedad`, `garantiasAFavorDe`.
        - Autoridad de tránsito que emitió el registro: `autoridadTransito`.
        - `idDetalle`, `idEncabezado`: Relación jerárquica con el lote principal.
        - `estadoVehiculo`, `numItem`: Estado general y posición en el lote.

    Cada inserción es registrada en la tabla `ControlIntegracion`, con información de éxito o fallo.
    """


    # Runt Encabezado
    """
    Inserta en la tabla `RuntEncabezado` de OLAP los registros de encabezado provenientes de NEXUM.
    Esta tabla representa los lotes o agrupaciones principales que contienen los detalles de vehículos
    del sistema RUNT, incluyendo metadatos de carga.
    """

    insertar_tabla("RuntEncabezado", datos_runtEncabezado, """
        INSERT INTO RuntEncabezado (
            idEncabezado, automatizacion, idUsuario, fechaCargue, totalRegistros
        ) VALUES (?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` recibe:
    - `"RuntEncabezado"`: tabla destino en OLAP.
    - `datos_runtEncabezado`: datos obtenidos desde NEXUM.
    - La sentencia SQL inserta 5 columnas:
        - `idEncabezado`: Identificador del lote.
        - `automatizacion`: Indica si la carga fue automática.
        - `idUsuario`: Usuario responsable.
        - `fechaCargue`: Fecha de carga.
        - `totalRegistros`: Número total de registros en el lote.

    Se registra el resultado de la inserción en la tabla `ControlIntegracion`.
    """

    # Super Notariado Detalle
    """
    Inserta en la tabla `SuperNotariadoDetalle` de OLAP todos los registros detallados extraídos desde NEXUM.
    Esta tabla contiene información legal y registral sobre propiedades, bienes o documentos
    administrados por el sistema de Super Notariado.
    """

    insertar_tabla("SuperNotariadoDetalle", datos_superNotariadoDetalle, """
        INSERT INTO SuperNotariadoDetalle (
            idDetalle, idEncabezado, CC, numItem, ciudad, matricula, direccion,
            vinculadoA
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Se llama a `insertar_tabla` con:
    - `"SuperNotariadoDetalle"`: tabla destino en OLAP.
    - `datos_superNotariadoDetalle`: registros detallados extraídos de NEXUM.
    - La consulta SQL inserta 8 columnas:
        - `idDetalle`: Identificador del registro.
        - `idEncabezado`: Referencia al lote o encabezado.
        - `CC`: Documento de identidad del titular.
        - `numItem`: Número del ítem dentro del lote.
        - `ciudad`: Ciudad donde está registrado el bien.
        - `matricula`: Número de matrícula inmobiliaria.
        - `direccion`: Dirección del bien.
        - `vinculadoA`: Persona o entidad vinculada al bien.

    Cada inserción se registra en la tabla `ControlIntegracion`.
    """


    # Super Notariado Encabezado
    """
    Inserta en la tabla `SuperNotariadoEncabezado` de OLAP los encabezados extraídos desde NEXUM.
    Esta tabla contiene los metadatos de los lotes o archivos cargados relacionados con registros
    de Super Notariado.
    """

    insertar_tabla("SuperNotariadoEncabezado", datos_superNotariadoEncabezado, """
        INSERT INTO SuperNotariadoEncabezado (
            idEncabezado, automatizacion, idUsuario, fechaCargue, totalRegistros
        ) VALUES (?, ?, ?, ?, ?)
    """)
    """
    Se llama a `insertar_tabla` con:
    - `"SuperNotariadoEncabezado"`: tabla destino en OLAP.
    - `datos_superNotariadoEncabezado`: datos de encabezado obtenidos de NEXUM.
    - La consulta SQL inserta 5 columnas:
        - `idEncabezado`: ID único del lote.
        - `automatizacion`: Indica si fue cargado automáticamente.
        - `idUsuario`: Usuario responsable.
        - `fechaCargue`: Fecha de la carga.
        - `totalRegistros`: Total de registros en el lote.

    La inserción se registra en la tabla `ControlIntegracion` con estado exitoso o fallido.
    """


    # Unificado
    """
    Inserta en la tabla `Unificado` de OLAP todos los registros consolidados extraídos desde NEXUM.
    Esta tabla parece representar un conjunto combinado o resumido de interacciones, llamadas o gestiones,
    unificando información proveniente de distintas fuentes.
    """

    insertar_tabla("Unificado", datos_unificado, """
        INSERT INTO Unificado (
            id_agent, agent_name, date_call, phone_code, telephone, customer_id,
            customer_id2, time_sec, time_min, call_cod_id, status_name, tipo,
            hang_up, campaign_id, campaign_name, list_id, lead_id, uniqueid,
            tipo_llamada, comments 
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` recibe:
    - `"Unificado"`: tabla destino en OLAP.
    - `datos_unificado`: registros extraídos desde NEXUM.
    - La sentencia SQL inserta 20 columnas, con detalles de llamadas, agentes, campañas,
      estados y comentarios asociados.

    Cada registro se inserta y se deja constancia en la tabla de auditoría `ControlIntegracion`.
    """


    # Usuarios
    """
    Inserta en la tabla `Usuarios` de OLAP todos los registros de usuarios extraídos desde NEXUM.
    Esta tabla contiene la información básica de los usuarios del sistema, incluyendo credenciales
    y estado activo/inactivo.
    """

    insertar_tabla("Usuarios", datos_usuarios, """
        INSERT INTO Usuarios (
            id, usuario, clave, activo
        ) VALUES (?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se invoca con:
    - `"Usuarios"`: nombre de la tabla destino en OLAP.
    - `datos_usuarios`: lista de tuplas con información de usuarios.
    - Consulta SQL con 4 columnas:
        - `id`: Identificador único del usuario.
        - `usuario`: Nombre o login del usuario.
        - `clave`: Contraseña del usuario (podría estar encriptada o en texto plano).
        - `activo`: Estado lógico del usuario (1 = activo, 0 = inactivo).

    La inserción de cada registro se registra en la tabla de auditoría `ControlIntegracion`.
    """


    # Usuarios App
    """
    Inserta en la tabla `UsuariosApp` de OLAP todos los registros de usuarios de la aplicación extraídos desde NEXUM.
    Esta tabla contiene información más detallada y específica del usuario, como correo, cargo, área y rol asignado.
    """

    insertar_tabla("UsuariosApp", datos_usuariosApp, """
        INSERT INTO UsuariosApp (
            idUsuarioApp, nombre, username, correo, cargo, idArea, idRol, activo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Se invoca `insertar_tabla` con:
    - `"UsuariosApp"`: nombre de la tabla destino.
    - `datos_usuariosApp`: lista de registros extraídos.
    - La sentencia SQL inserta 8 columnas:
        - `idUsuarioApp`: Identificador único del usuario en la app.
        - `nombre`: Nombre completo.
        - `username`: Nombre de usuario para login.
        - `correo`: Correo electrónico.
        - `cargo`: Cargo o posición dentro de la organización.
        - `idArea`: Área a la que pertenece (clave foránea).
        - `idRol`: Rol asignado (clave foránea).
        - `activo`: Estado lógico del usuario (1 = activo).

    Cada inserción queda registrada en la tabla `ControlIntegracion` para seguimiento.
    """

    # Usuarios Campanas
    """
    Inserta en la tabla `UsuariosCampanas` de OLAP los registros que relacionan usuarios con campañas.
    Esta tabla establece la asignación de cada usuario a una o varias campañas específicas.
    """

    insertar_tabla("UsuariosCampanas", datos_usuariosCampanas, """
        INSERT INTO UsuariosCampanas (
            idUsuarioApp, idCampana
        ) VALUES (?, ?)
    """)
    """
    Se llama a la función `insertar_tabla` con:
    - `"UsuariosCampanas"`: tabla destino en OLAP.
    - `datos_usuariosCampanas`: registros extraídos desde NEXUM.
    - La consulta SQL inserta dos columnas:
        - `idUsuarioApp`: Identificador del usuario.
        - `idCampana`: Identificador de la campaña asignada.

    Cada registro se inserta individualmente y se registra el resultado en `ControlIntegracion`.
    """

    conn.commit()
    """
    Se confirma la transacción para que todas las inserciones realizadas en OLAP queden guardadas permanentemente.
    """

    conn.close()
    """
    Se cierra la conexión a la base de datos OLAP para liberar recursos.
    """

#------ DE INTEGRACION A NEXUM-------------------------------------------------------------------------------------------------------
def obtener_datos_integracion_a_nexum():
    """
    Esta función establece la conexión con la base de datos INTEGRACION utilizando la configuración
    almacenada en `CONFIG_INTEGRACION`. El propósito es extraer los datos más recientes
    de esta base para transferirlos a NEXUM.

    La función crea un cursor que se usará para ejecutar consultas SQL dentro de esta conexión.
    """
    conn = conectar_sql(CONFIG_INTEGRACION)
    """
    Se conecta a la base de datos INTEGRACION usando los parámetros definidos en la configuración.
    """
    cursor = conn.cursor()
    """
    Se crea un cursor a partir de la conexión, que permitirá ejecutar consultas y comandos SQL.
    """

    
    # Campañas Gail
    """
    Esta sección ejecuta una consulta para obtener los datos recientes de la tabla `CampañasGail`
    desde la base de datos INTEGRACION. Se extraen solo las campañas que hayan sido creadas o modificadas
    en las últimas 24 horas, usando la columna `date_call` como filtro temporal.
    """

    cursor.execute("""
        SELECT [id], [idGail], [name], [description], [createdAt],
               [status], [Pais]
        FROM [Integracion].[dbo].[CampañasGail]
        WHERE date_call >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se ejecuta la consulta SQL que recupera:
    - `id`: Identificador único de la campaña.
    - `idGail`: Código interno o externo de la campaña.
    - `name`: Nombre descriptivo de la campaña.
    - `description`: Descripción detallada.
    - `createdAt`: Fecha de creación.
    - `status`: Estado actual (activo, inactivo, etc.).
    - `Pais`: País o región de aplicación.

    La condición `date_call >= DATEADD(day, -1, GETDATE())` limita la extracción a las últimas 24 horas.
    """

    datos_campañasGail = cursor.fetchall()
    """
    Los registros obtenidos se almacenan en la variable `datos_campañasGail`,
    lista de tuplas con toda la información para integrar posteriormente en NEXUM.
    """


    # Contactos Gail Nueva
    """
    Esta sección extrae los registros recientes desde la tabla `ContactosGail_Nueva1`
    en la base de datos INTEGRACION. Solo se obtienen los contactos que fueron creados o modificados
    en las últimas 24 horas, usando la columna `fechaCreacion` como filtro.
    """

    cursor.execute("""
        SELECT [id], [idGail], [idLista], [firstName], [lastName], [businessName],
               [source], [status], [telefonoMovil], [tipoTelefono], [banco], [cedula],
               [capital], [entidad], [oferta1], [oferta2], [oferta3], [producto],
               [intereses], [nombre_HMLG], [saldoTotal], [hasta6Cuotas], [hasta12Cuotas],
               [hasta18Cuotas], [ultimosDigitos], [tel2], [tel3], [pagoFlexible], [Pais]
        FROM [Integracion].[dbo].[ContactosGail_Nueva1]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    La consulta SQL selecciona múltiples columnas relacionadas con la información detallada
    de los contactos, tales como:
    - Identificadores internos (`id`, `idGail`, `idLista`).
    - Nombres y apellidos (`firstName`, `lastName`).
    - Información comercial (`businessName`, `source`, `status`).
    - Datos de contacto telefónico (`telefonoMovil`, `tipoTelefono`, `tel2`, `tel3`).
    - Información financiera y crediticia (`banco`, `cedula`, `capital`, `entidad`, `producto`, `intereses`).
    - Detalles de ofertas y saldos (`oferta1`, `oferta2`, `oferta3`, `saldoTotal`).
    - Campos adicionales (`pagoFlexible`, `Pais`, `nombre_HMLG`, `hasta6Cuotas`, etc.).

    El filtro `fechaCreacion >= DATEADD(day, -1, GETDATE())` asegura que se obtengan solo los datos recientes.
    """

    datos_contactosGail = cursor.fetchall()
    """
    Se recuperan todos los resultados de la consulta y se almacenan en la variable `datos_contactosGail`.
    Estos datos serán usados para insertar en la base NEXUM en etapas posteriores.
    """


       # Listas Contacto Gail
    """
    Esta sección extrae los registros recientes desde la tabla `ListasContactoGail` en la base INTEGRACION.
    Solo se obtienen los registros que hayan sido creados o modificados en las últimas 24 horas,
    usando la columna `fechaCreacion` como filtro temporal.
    """

    cursor.execute("""
        SELECT [id], [idLista], [name], [description], [idCampaña], [Pais]
        FROM [Integracion].[dbo].[ListasContactoGail]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    La consulta SQL recupera las siguientes columnas:
    - `id`: Identificador único del registro.
    - `idLista`: Identificador de la lista asociada.
    - `name`: Nombre de la lista.
    - `description`: Descripción textual de la lista.
    - `idCampaña`: Campaña asociada a la lista.
    - `Pais`: País o región de aplicación.

    El filtro `fechaCreacion >= DATEADD(day, -1, GETDATE())` garantiza que solo se extraigan registros recientes.
    """

    datos_listasContactoGail = cursor.fetchall()
    """
    Se almacenan todos los registros obtenidos en la variable `datos_listasContactoGail`.
    Esta lista de tuplas será utilizada para la posterior inserción en la base NEXUM.
    """


    # Reglas Remarcado Outcomes
    """
    Esta sección extrae los registros recientes desde la tabla `ReglasRemarcadoOutcomes`
    en la base INTEGRACION. Se obtienen únicamente las reglas creadas o modificadas en las últimas 24 horas,
    usando la columna `fechaCreacion` como filtro.
    """

    cursor.execute("""
        SELECT [id], [idRegla], [outcomeName], [definition], [Pais]
        FROM [Integracion].[dbo].[ReglasRemarcadoOutcomes]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    La consulta SQL obtiene:
    - `id`: Identificador único de la regla.
    - `idRegla`: Código o referencia interna de la regla.
    - `outcomeName`: Nombre del resultado o consecuencia de la regla.
    - `definition`: Definición o descripción detallada de la regla.
    - `Pais`: País o región a la que aplica la regla.

    El filtro `fechaCreacion >= DATEADD(day, -1, GETDATE())` limita la extracción a las últimas 24 horas.
    """

    datos_remarcadoOutcomes = cursor.fetchall()
    """
    Se almacenan todos los registros devueltos por la consulta en la variable `datos_remarcadoOutcomes`,
    que luego serán usados para insertar en NEXUM.
    """


    # Reglas Remarcado Gail
    """
    Esta sección extrae los registros recientes desde la tabla `ReglasRemarcadosGail` en la base INTEGRACION.
    Solo se obtienen las reglas que hayan sido creadas o modificadas en las últimas 24 horas,
    usando la columna `fecha` como filtro temporal.
    """

    cursor.execute("""
        SELECT [id], [idRegla], [name], [idCampaña], [status],
               [outreachMaxAttempts], [outreachMaxAttemptsForNumber], [Pais]
        FROM [Integracion].[dbo].[ReglasRemarcadosGail]
        WHERE fecha >= DATEADD(day, -1, GETDATE())
    """)
    """
    La consulta SQL obtiene las siguientes columnas:
    - `id`: Identificador único.
    - `idRegla`: Código interno de la regla.
    - `name`: Nombre o descripción breve.
    - `idCampaña`: Campaña asociada.
    - `status`: Estado actual de la regla.
    - `outreachMaxAttempts`: Número máximo de intentos de contacto.
    - `outreachMaxAttemptsForNumber`: Número máximo de intentos por número.
    - `Pais`: País o región de aplicación.

    El filtro `fecha >= DATEADD(day, -1, GETDATE())` asegura traer solo registros recientes.
    """

    datos_remarcadoGail = cursor.fetchall()
    """
    Se almacenan todos los resultados en la variable `datos_remarcadoGail` para su posterior integración en NEXUM.
    """


    # Reglas Remarcado System Actions
    """
    Esta sección extrae los registros recientes desde la tabla `ReglasRemarcadoSystemActions`
    en la base INTEGRACION. Solo se obtienen aquellas acciones de sistema asociadas a reglas
    que fueron creadas o modificadas en las últimas 24 horas, usando el campo `fechaEnvio`
    como filtro temporal.
    """

    cursor.execute("""
        SELECT [id], [idRegla], [outcomeName], [action], [delay],
               [maxAttempts], [Pais]
        FROM [Integracion].[dbo].[ReglasRemarcadoSystemActions]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    La consulta SQL obtiene:
    - `id`: Identificador único.
    - `idRegla`: Código de la regla asociada.
    - `outcomeName`: Nombre del resultado esperado.
    - `action`: Acción a realizar (ejemplo: llamada, mensaje).
    - `delay`: Tiempo de espera o retraso para la acción.
    - `maxAttempts`: Número máximo de intentos permitidos.
    - `Pais`: País o región de aplicación.

    El filtro `fechaEnvio >= DATEADD(day, -1, GETDATE())` limita la extracción a registros recientes.
    """

    datos_remarcadoSystem = cursor.fetchall()
    """
    Todos los registros obtenidos se almacenan en la variable `datos_remarcadoSystem`.
    Esta información será usada para integrarse en la base NEXUM posteriormente.
    """


    # Secuencias Gail
    cursor.execute("""
        SELECT [id], [idGail], [name], [description], [criteria], [status],
               [timezone], [idCampaña], [Pais]
        FROM [Integracion].[dbo].[SecuenciasGail]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    datos_secuenciasGail = cursor.fetchall()
    """
    Se extraen las secuencias recientes de la tabla `SecuenciasGail` en la base INTEGRACION.
    Estas secuencias contienen reglas o flujos definidos para la gestión de campañas o procesos automáticos.
    """

    conn.close()
    """
    Se cierra la conexión a la base INTEGRACION tras completar todas las consultas.
    """

    return (
        datos_campañasGail, datos_contactosGail, datos_listasContactoGail,
        datos_remarcadoOutcomes, datos_remarcadoGail, datos_remarcadoSystem,
        datos_secuenciasGail
    )
    """
    Se retorna una tupla con todos los datasets extraídos para usarse posteriormente en la inserción a NEXUM.
    """

def insertar_datos_destino_integracion_a_nexum(
    datos_campañasGail, datos_contactosGail, datos_listasContactoGail,
    datos_remarcadoOutcomes, datos_remarcadoGail, datos_remarcadoSystem,
    datos_secuenciasGail 
):
    """
    Esta función recibe los datos extraídos desde la base INTEGRACION y los inserta en la base NEXUM.
    Cada conjunto de datos es insertado en su tabla correspondiente mediante la función interna `insertar_tabla`.
    Se registra un log en la tabla `ControlIntegracion` por cada inserción realizada,
    indicando éxito o fallo.
    """
    conn = conectar_sql(CONFIG_NEXUM)
    """
    Se conecta a la base de datos NEXUM usando la configuración correspondiente.
    """
    cursor = conn.cursor()
    """
    Se obtiene un cursor para ejecutar comandos SQL en la base NEXUM.
    """

    def insertar_tabla(nombre_tabla, datos, query_insert):
        """
        Función auxiliar que inserta registros en la tabla destino y registra un log.
        
        Parámetros:
        - `nombre_tabla`: nombre de la tabla destino.
        - `datos`: lista de tuplas con los registros a insertar.
        - `query_insert`: consulta SQL parametrizada para la inserción.
        """
        try:
            fecha_inicio = datetime.now()
            registros = 0
            for fila in datos:
                cursor.execute(query_insert, tuple(fila))
                registros += 1
            fecha_fin = datetime.now()
            log_integracion(cursor, "INTEGRACION", "NEXUM", nombre_tabla, fecha_inicio, fecha_fin, registros, "Exitoso")
        except Exception as e:
            fecha_fin = datetime.now()
            log_integracion(cursor, "INTEGRACION", "NEXUM", nombre_tabla, fecha_inicio, fecha_fin, 0, "Fallido", str(e))


    # Campañas Gail
    """
    Inserta en la tabla `CampañasGail` de NEXUM todos los registros extraídos desde la base INTEGRACION.
    Esta tabla contiene la información básica y descriptiva de las campañas gestionadas,
    incluyendo identificadores, estado y país de aplicación.
    """

    insertar_tabla("CampañasGail", datos_campañasGail, """
        INSERT INTO CampañasGail (
            id, idGail, name, description, createdAt, status, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se llama con:
    - `"CampañasGail"`: nombre de la tabla destino en NEXUM.
    - `datos_campañasGail`: lista de registros extraídos.
    - La consulta SQL espera 7 columnas por registro:
        - `id`: Identificador único.
        - `idGail`: Código asociado a la campaña.
        - `name`: Nombre descriptivo.
        - `description`: Descripción detallada.
        - `createdAt`: Fecha de creación.
        - `status`: Estado actual.
        - `Pais`: País o región de aplicación.

    Cada registro es insertado individualmente y se registra el resultado en la tabla `ControlIntegracion`.
    """


    # Contactos Gail Nueva
    """
    Inserta en la tabla `ContactosGail_Nueva1` de NEXUM todos los registros extraídos desde INTEGRACION.
    Esta tabla almacena información detallada de contactos asociados a campañas,
    incluyendo datos personales, comerciales y financieros.
    """

    insertar_tabla("ContactosGail_Nueva1", datos_contactosGail, """
        INSERT INTO ContactosGail_Nueva1 (
            id, idGail, idLista, firstName, lastName, businessName,
            source, status, telefonoMovil, tipoTelefono, banco, cedula,
            capital, entidad, oferta1, oferta2, oferta3, producto, intereses,
            nombre_HMLG, saldoTotal, hasta6Cuotas, hasta12Cuotas, hasta18Cuotas,
            ultimosDigitos, tel2, tel3, pagoFlexible, Pais 
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` recibe:
    - `"ContactosGail_Nueva1"`: tabla destino en NEXUM.
    - `datos_contactosGail`: registros obtenidos desde INTEGRACION.
    - La consulta SQL inserta 29 columnas, incluyendo:
        - Identificadores y referencias internas (`id`, `idGail`, `idLista`).
        - Datos personales (`firstName`, `lastName`, `cedula`).
        - Información comercial y financiera (`businessName`, `source`, `banco`, `capital`, `entidad`, `producto`, `intereses`).
        - Teléfonos y opciones de pago (`telefonoMovil`, `tipoTelefono`, `pagoFlexible`).
        - Ofertas y saldos (`oferta1`, `oferta2`, `oferta3`, `saldoTotal`).
        - Otros campos auxiliares (`nombre_HMLG`, `hasta6Cuotas`, etc.).
        - `Pais`: país de origen o aplicación.

    Cada fila se inserta y el proceso queda registrado en la tabla `ControlIntegracion`.
    """


    # Listas Contacto Gail
    """
    Inserta en la tabla `ListasContactoGail` de NEXUM todos los registros extraídos desde INTEGRACION.
    Esta tabla contiene la información sobre las listas de contactos, que agrupan a los usuarios
    o clientes según campañas o criterios específicos.
    """

    insertar_tabla("ListasContactoGail", datos_listasContactoGail, """
        INSERT INTO ListasContactoGail (
            id, idLista, name, description, idCampaña, Pais
        ) VALUES (?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` recibe:
    - `"ListasContactoGail"`: nombre de la tabla destino en NEXUM.
    - `datos_listasContactoGail`: registros obtenidos desde INTEGRACION.
    - La consulta SQL inserta 6 columnas:
        - `id`: Identificador único del registro.
        - `idLista`: Identificador de la lista a la que pertenece.
        - `name`: Nombre descriptivo de la lista.
        - `description`: Descripción detallada de la lista.
        - `idCampaña`: Identificador de la campaña relacionada.
        - `Pais`: País o región de aplicación.

    Cada registro se inserta individualmente y se deja constancia en `ControlIntegracion`.
    """


    # Reglas Remarcado Outcomes
    """
    Inserta en la tabla `ReglasRemarcadoOutcomes` de NEXUM todos los registros extraídos desde INTEGRACION.
    Esta tabla contiene las reglas definidas para los outcomes o resultados esperados en procesos de gestión.
    """

    insertar_tabla("ReglasRemarcadoOutcomes", datos_remarcadoOutcomes, """
        INSERT INTO ReglasRemarcadoOutcomes (
            id, idRegla, outcomeName, definition, Pais
        ) VALUES (?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se invoca con:
    - `"ReglasRemarcadoOutcomes"`: tabla destino en NEXUM.
    - `datos_remarcadoOutcomes`: registros obtenidos.
    - La sentencia SQL inserta 5 columnas:
        - `id`: Identificador único.
        - `idRegla`: Código interno de la regla.
        - `outcomeName`: Nombre del resultado o efecto esperado.
        - `definition`: Definición o explicación de la regla.
        - `Pais`: País o región donde aplica la regla.

    Cada inserción se registra en la tabla `ControlIntegracion` para auditoría.
    """

    # Reglas Remarcado Gail
    """
    Inserta en la tabla `ReglasRemarcadosGail` de NEXUM todos los registros extraídos desde INTEGRACION.
    Esta tabla contiene las reglas definidas para la gestión de campañas, incluyendo límites y estados.
    """

    insertar_tabla("ReglasRemarcadosGail", datos_remarcadoGail, """
        INSERT INTO ReglasRemarcadosGail (
            id, idRegla, name, idCampaña, status, outreachMaxAttempts,
            outreachMaxAttemptsForNumber, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se llama con:
    - `"ReglasRemarcadosGail"`: tabla destino en NEXUM.
    - `datos_remarcadoGail`: lista de registros obtenidos.
    - La consulta SQL inserta 8 columnas:
        - `id`: Identificador único.
        - `idRegla`: Código interno de la regla.
        - `name`: Nombre descriptivo.
        - `idCampaña`: Campaña asociada.
        - `status`: Estado de la regla.
        - `outreachMaxAttempts`: Máximo de intentos totales.
        - `outreachMaxAttemptsForNumber`: Máximo de intentos por número.
        - `Pais`: País o región de aplicación.

    Cada inserción queda registrada en la tabla `ControlIntegracion` para auditoría.
    """


    # Reglas Remarcado System Actions
    """
    Inserta en la tabla `ReglasRemarcadoSystemActions` de NEXUM todos los registros extraídos desde INTEGRACION.
    Esta tabla contiene las acciones específicas que deben ejecutarse en el sistema en función de reglas definidas,
    con parámetros de tiempo y límites de intentos.
    """

    insertar_tabla("ReglasRemarcadoSystemActions", datos_remarcadoSystem, """
        INSERT INTO ReglasRemarcadoSystemActions (
            id, idRegla, outcomeName, action, delay, maxAttempts, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` recibe:
    - `"ReglasRemarcadoSystemActions"`: tabla destino en NEXUM.
    - `datos_remarcadoSystem`: registros extraídos.
    - La consulta SQL inserta 7 columnas:
        - `id`: Identificador único.
        - `idRegla`: Código de la regla asociada.
        - `outcomeName`: Nombre del resultado o situación.
        - `action`: Acción a ejecutar (por ejemplo, llamada, mensaje).
        - `delay`: Retraso o tiempo de espera antes de la acción.
        - `maxAttempts`: Número máximo de intentos permitidos.
        - `Pais`: País o región donde aplica.

    Cada registro insertado queda registrado en la tabla de control para auditoría.
    """


    # Secuencias Gail
    """
    Inserta en la tabla `SecuenciasGail` de NEXUM todos los registros extraídos desde INTEGRACION.
    Esta tabla contiene las secuencias o flujos de reglas y criterios usados para la gestión automatizada
    de campañas o procesos dentro del sistema.
    """

    insertar_tabla("SecuenciasGail", datos_secuenciasGail, """
        INSERT INTO SecuenciasGail (
            id, idGail, name, description, criteria, status, timezone,
            idCampaña, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se invoca con:
    - `"SecuenciasGail"`: tabla destino en NEXUM.
    - `datos_secuenciasGail`: lista de registros extraídos.
    - La consulta SQL inserta 9 columnas:
        - `id`: Identificador único de la secuencia.
        - `idGail`: Código asociado.
        - `name`: Nombre descriptivo.
        - `description`: Descripción detallada.
        - `criteria`: Criterios o condiciones para la secuencia.
        - `status`: Estado de la secuencia (activo, inactivo).
        - `timezone`: Zona horaria asociada.
        - `idCampaña`: Campaña vinculada.
        - `Pais`: País o región de aplicación.

    Cada inserción se registra en la tabla `ControlIntegracion` para control y auditoría.
    """

    conn.commit()
    """
    Se confirma la transacción para guardar permanentemente todos los registros insertados en NEXUM.
    """

    conn.close()
    """
    Se cierra la conexión a la base de datos NEXUM para liberar recursos.
    """


#------ DE INTEGRACION A OLAP--------------------------------------------------------------------------------------------------------
def obtener_datos_integracion_a_olap():
    """
    Esta función conecta con la base de datos INTEGRACION para extraer datos recientes
    que serán integrados en la base OLAP. Se realiza una consulta para obtener la información
    de campañas recientes creadas o modificadas en las últimas 24 horas.
    """
    conn = conectar_sql(CONFIG_INTEGRACION)
    """
    Se establece la conexión con la base INTEGRACION usando la configuración predefinida.
    """
    cursor = conn.cursor()
    """
    Se obtiene un cursor para ejecutar comandos SQL y extraer datos.
    """

    # Campañas Gail
    """
    Ejecuta una consulta para obtener las campañas recientes dentro de las últimas 24 horas,
    usando el campo `date_call` para filtrar.
    """
    cursor.execute("""
        SELECT [id], [idGail], [name], [description], [createdAt],
               [status], [Pais]
        FROM [Integracion].[dbo].[CampañasGail]
        WHERE date_call >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se seleccionan las columnas clave:
    - `id`: Identificador único.
    - `idGail`: Código de campaña.
    - `name`: Nombre.
    - `description`: Descripción.
    - `createdAt`: Fecha de creación.
    - `status`: Estado.
    - `Pais`: País de aplicación.

    El filtro asegura traer solo campañas recientes.
    """
    datos_campañasGail = cursor.fetchall()
    """
    Se almacenan los resultados en la variable `datos_campañasGail`.
    """


        # Contactos Gail Nueva
    """
    Esta sección extrae los registros recientes de la tabla `ContactosGail_Nueva1`
    en la base INTEGRACION. Solo se obtienen los contactos creados o modificados en las últimas 24 horas,
    usando la columna `fechaCreacion` como filtro temporal.
    """
    cursor.execute("""
        SELECT [id], [idGail], [idLista], [firstName], [lastName], [businessName],
               [source], [status], [telefonoMovil], [tipoTelefono], [banco], [cedula],
               [capital], [entidad], [oferta1], [oferta2], [oferta3], [producto],
               [intereses], [nombre_HMLG], [saldoTotal], [hasta6Cuotas], [hasta12Cuotas],
               [hasta18Cuotas], [ultimosDigitos], [tel2], [tel3], [pagoFlexible], [Pais]
        FROM [Integracion].[dbo].[ContactosGail_Nueva1]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se seleccionan campos clave de información personal, financiera y comercial,
    incluyendo identificadores, nombres, teléfonos, ofertas y estado.
    """
    datos_contactosGail = cursor.fetchall()
    """
    Los resultados se almacenan en la variable `datos_contactosGail`.
    """

    # Listas Contacto Gail
    """
    Esta sección extrae los registros recientes de la tabla `ListasContactoGail` en la base INTEGRACION,
    filtrando por fecha de creación para obtener solo los datos de las últimas 24 horas.
    """
    cursor.execute("""
        SELECT [id], [idLista], [name], [description], [idCampaña], [Pais]
        FROM [Integracion].[dbo].[ListasContactoGail]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se obtienen columnas referentes a la identificación, nombre, descripción,
    campaña asociada y país.
    """
    datos_listasContactoGail = cursor.fetchall()
    """
    Los datos extraídos se almacenan en la variable `datos_listasContactoGail`
    para su posterior uso en la inserción en OLAP.
    """

        # Reglas Remarcado Outcomes
    """
    Esta sección extrae las reglas recientes desde la tabla `ReglasRemarcadoOutcomes`
    en la base INTEGRACION, filtrando por fecha de creación para obtener solo las últimas 24 horas.
    """
    cursor.execute("""
        SELECT [id], [idRegla], [outcomeName], [definition], [Pais]
        FROM [Integracion].[dbo].[ReglasRemarcadoOutcomes]
        WHERE fechaCreacion >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se seleccionan columnas que identifican y describen cada regla,
    junto con el país o región de aplicación.
    """
    datos_remarcadoOutcomes = cursor.fetchall()
    """
    Los registros extraídos se almacenan en la variable `datos_remarcadoOutcomes`.
    """

    # Reglas Remarcado Gail
    """
    Esta sección obtiene las reglas de remarcar específicas de Gail desde la tabla `ReglasRemarcadosGail`
    en la base INTEGRACION, filtrando por fecha para solo traer datos recientes.
    """
    cursor.execute("""
        SELECT [id], [idRegla], [name], [idCampaña], [status],
               [outreachMaxAttempts], [outreachMaxAttemptsForNumber], [Pais]
        FROM [Integracion].[dbo].[ReglasRemarcadosGail]
        WHERE fecha >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se obtienen columnas que incluyen información de la regla, campaña asociada,
    estado y límites de intentos de contacto.
    """
    datos_remarcadoGail = cursor.fetchall()
    """
    Los datos recuperados se guardan en la variable `datos_remarcadoGail`.
    """

    # Reglas Remarcado System Actions
    """
    Esta sección extrae las acciones de sistema relacionadas con reglas definidas,
    desde la tabla `ReglasRemarcadoSystemActions` en la base INTEGRACION.
    Solo se obtienen los registros creados o modificados en las últimas 24 horas,
    usando la columna `fechaEnvio` como filtro temporal.
    """
    cursor.execute("""
        SELECT [id], [idRegla], [outcomeName], [action], [delay],
               [maxAttempts], [Pais]
        FROM [Integracion].[dbo].[ReglasRemarcadoSystemActions]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    """
    Se seleccionan columnas clave que describen:
    - Identificador único.
    - Regla asociada.
    - Nombre del resultado.
    - Acción a ejecutar.
    - Retraso antes de la acción.
    - Máximo de intentos permitidos.
    - País o región de aplicación.
    """
    datos_remarcadoSystem = cursor.fetchall()
    """
    Los datos obtenidos se almacenan en la variable `datos_remarcadoSystem`
    para su posterior integración en la base NEXUM.
    """


        # Secuencias Gail
    """
    Extrae los registros recientes de la tabla `SecuenciasGail` en la base INTEGRACION.
    Estas secuencias representan flujos o reglas definidas para la gestión de campañas
    o procesos automáticos.
    """
    cursor.execute("""
        SELECT [id], [idGail], [name], [description], [criteria], [status],
               [timezone], [idCampaña], [Pais]
        FROM [Integracion].[dbo].[SecuenciasGail]
        WHERE fechaEnvio >= DATEADD(day, -1, GETDATE())
    """)
    datos_secuenciasGail = cursor.fetchall()
    """
    Se almacenan los registros extraídos en la variable `datos_secuenciasGail`.
    """

    conn.close()
    """
    Se cierra la conexión a la base INTEGRACION tras finalizar la extracción de datos.
    """

    return (
        datos_campañasGail, datos_contactosGail, datos_listasContactoGail,
        datos_remarcadoOutcomes, datos_remarcadoGail, datos_remarcadoSystem,
        datos_secuenciasGail
    )
    """
    Se retorna una tupla con todos los datasets extraídos para usar en la inserción a OLAP.
    """

def insertar_datos_destino_integracion_a_olap(
    datos_campañasGail, datos_contactosGail, datos_listasContactoGail,
    datos_remarcadoOutcomes, datos_remarcadoGail, datos_remarcadoSystem,
    datos_secuenciasGail 
):
    """
    Esta función recibe los datos extraídos desde la base INTEGRACION y los inserta en la base OLAP.
    Cada conjunto de datos se inserta en su tabla correspondiente mediante la función interna `insertar_tabla`.
    Se registra un log de integración por cada tabla procesada, indicando éxito o fallo.
    """
    conn = conectar_sql(CONFIG_OLAP)
    """
    Se establece conexión con la base OLAP usando la configuración definida.
    """
    cursor = conn.cursor()
    """
    Se obtiene un cursor para ejecutar comandos SQL en OLAP.
    """

    def insertar_tabla(nombre_tabla, datos, query_insert):
        """
        Función auxiliar para insertar datos en una tabla específica y registrar la integración.
        
        Parámetros:
        - `nombre_tabla`: nombre de la tabla destino.
        - `datos`: lista de tuplas con los registros a insertar.
        - `query_insert`: sentencia SQL parametrizada para inserción.
        """
        try:
            fecha_inicio = datetime.now()
            registros = 0
            for fila in datos:
                cursor.execute(query_insert, tuple(fila))
                registros += 1
            fecha_fin = datetime.now()
            log_integracion(cursor, "INTEGRACION", "OLAP", nombre_tabla, fecha_inicio, fecha_fin, registros, "Exitoso")
        except Exception as e:
            fecha_fin = datetime.now()
            log_integracion(cursor, "INTEGRACION", "OLAP", nombre_tabla, fecha_inicio, fecha_fin, 0, "Fallido", str(e))

    # Campañas Gail
    """
    Inserta los registros extraídos de `CampañasGail` desde INTEGRACION a la tabla homónima en OLAP.
    Cada registro contiene información básica y descriptiva de campañas gestionadas.
    """

    insertar_tabla("CampañasGail", datos_campañasGail, """
        INSERT INTO CampañasGail (
            id, idGail, name, description, createdAt, status, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se llama con:
    - `"CampañasGail"`: nombre de la tabla destino en OLAP.
    - `datos_campañasGail`: lista de registros extraídos.
    - Consulta SQL con 7 columnas correspondientes a la estructura de la tabla.

    Cada inserción se realiza fila por fila y se registra en la tabla `ControlIntegracion`.
    """

    # Contactos Gail Nueva
    """
    Inserta los registros de contactos recientes extraídos desde la tabla `ContactosGail_Nueva1`
    en INTEGRACION a la tabla equivalente en OLAP.
    Contiene datos personales, financieros y de contacto para campañas.
    """

    insertar_tabla("ContactosGail_Nueva1", datos_contactosGail, """
        INSERT INTO ContactosGail_Nueva1 (
            id, idGail, idLista, firstName, lastName, businessName,
            source, status, telefonoMovil, tipoTelefono, banco, cedula,
            capital, entidad, oferta1, oferta2, oferta3, producto, intereses,
            nombre_HMLG, saldoTotal, hasta6Cuotas, hasta12Cuotas, hasta18Cuotas,
            ultimosDigitos, tel2, tel3, pagoFlexible, Pais 
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se invoca con:
    - `"ContactosGail_Nueva1"`: tabla destino en OLAP.
    - `datos_contactosGail`: lista de tuplas con registros extraídos.
    - Consulta SQL parametrizada con 29 columnas que corresponden a la estructura.

    Cada fila es insertada y el proceso queda registrado en `ControlIntegracion`.
    """

        # Listas Contacto Gail
    """
    Inserta en la tabla `ListasContactoGail` de OLAP los registros extraídos desde INTEGRACION.
    Esta tabla contiene las listas de contactos asociadas a campañas o criterios específicos.
    """

    insertar_tabla("ListasContactoGail", datos_listasContactoGail, """
        INSERT INTO ListasContactoGail (
            id, idLista, name, description, idCampaña, Pais
        ) VALUES (?, ?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` se llama con:
    - `"ListasContactoGail"`: tabla destino en OLAP.
    - `datos_listasContactoGail`: lista de registros extraídos.
    - Consulta SQL con 6 columnas:
        - `id`: Identificador del registro.
        - `idLista`: ID de la lista.
        - `name`: Nombre de la lista.
        - `description`: Descripción detallada.
        - `idCampaña`: Campaña asociada.
        - `Pais`: País o región.

    Cada inserción se registra en la tabla `ControlIntegracion`.
    """

    # Reglas Remarcado Outcomes
    """
    Inserta en la tabla `ReglasRemarcadoOutcomes` de OLAP los registros extraídos desde INTEGRACION.
    Contiene reglas definidas para outcomes o resultados esperados en procesos.
    """

    insertar_tabla("ReglasRemarcadoOutcomes", datos_remarcadoOutcomes, """
        INSERT INTO ReglasRemarcadoOutcomes (
            id, idRegla, outcomeName, definition, Pais
        ) VALUES (?, ?, ?, ?, ?)
    """)
    """
    La función `insertar_tabla` recibe:
    - `"ReglasRemarcadoOutcomes"`: tabla destino en OLAP.
    - `datos_remarcadoOutcomes`: lista de registros extraídos.
    - Consulta SQL con 5 columnas que describen cada regla.

    El proceso queda auditado en `ControlIntegracion`.
    """


    # Reglas Remarcado Gail
    """
    Inserta en la tabla `ReglasRemarcadosGail` de OLAP todos los registros extraídos desde INTEGRACION.
    Contiene reglas específicas para la gestión de campañas, con límites de intentos y estados.
    """
    insertar_tabla("ReglasRemarcadosGail", datos_remarcadoGail, """
        INSERT INTO ReglasRemarcadosGail (
            id, idRegla, name, idCampaña, status, outreachMaxAttempts,
            outreachMaxAttemptsForNumber, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Parámetros y estructura:
    - `id`: Identificador único.
    - `idRegla`: Código interno.
    - `name`: Nombre de la regla.
    - `idCampaña`: Campaña asociada.
    - `status`: Estado (activo/inactivo).
    - `outreachMaxAttempts`: Máximo total de intentos.
    - `outreachMaxAttemptsForNumber`: Máximo de intentos por número.
    - `Pais`: País o región de aplicación.
    """

    # Reglas Remarcado System Actions
    """
    Inserta en la tabla `ReglasRemarcadoSystemActions` las acciones del sistema basadas en reglas,
    con parámetros de acción, retraso y límites de intentos.
    """
    insertar_tabla("ReglasRemarcadoSystemActions", datos_remarcadoSystem, """
        INSERT INTO ReglasRemarcadoSystemActions (
            id, idRegla, outcomeName, action, delay, maxAttempts, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Parámetros:
    - `id`: Identificador único.
    - `idRegla`: Código de la regla.
    - `outcomeName`: Resultado esperado.
    - `action`: Acción a ejecutar.
    - `delay`: Retraso en la acción.
    - `maxAttempts`: Máximo de intentos.
    - `Pais`: País o región.
    """

    # Secuencias Gail
    """
    Inserta en la tabla `SecuenciasGail` las secuencias o flujos de reglas usados para campañas.
    """
    insertar_tabla("SecuenciasGail", datos_secuenciasGail, """
        INSERT INTO SecuenciasGail (
            id, idGail, name, description, criteria, status, timezone,
            idCampaña, Pais
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """)
    """
    Parámetros:
    - `id`: Identificador único.
    - `idGail`: Código asociado.
    - `name`: Nombre de la secuencia.
    - `description`: Descripción.
    - `criteria`: Criterios de la secuencia.
    - `status`: Estado (activo/inactivo).
    - `timezone`: Zona horaria.
    - `idCampaña`: Campaña vinculada.
    - `Pais`: País o región.

    Al finalizar, se confirma la transacción con `commit()` y se cierra la conexión.
    """

    conn.commit()
    """
    Se confirma la transacción para guardar todos los registros insertados.
    """

    conn.close()
    """
    Se cierra la conexión a la base OLAP para liberar recursos.
    """
