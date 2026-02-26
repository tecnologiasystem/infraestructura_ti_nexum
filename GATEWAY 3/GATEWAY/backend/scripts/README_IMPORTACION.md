# Script de Importación CSV a SQL Server

## Descripción
Script para importar datos desde archivos CSV a la tabla `ConsolidadoCampañasNatalia` en SQL Server.

## Requisitos
- Python 3.x
- pandas
- pyodbc
- ODBC Driver 17 for SQL Server

## Instalación de Dependencias
```bash
pip install pandas pyodbc
```

## Uso

### Forma 1: Usando el script directamente
```bash
python scripts/importar_csv_natalia.py "ruta/al/archivo.csv"
```

### Forma 2: Especificando nombre del origen
```bash
python scripts/importar_csv_natalia.py "ruta/al/archivo.csv" "Nombre del Origen"
```

## Ejemplos

### Ejemplo 1: Importar archivo básico
```bash
python scripts/importar_csv_natalia.py "c:/Users/j.castillo/Downloads/Base Datos para WhatsApp 19112025.csv"
```

### Ejemplo 2: Con nombre de origen personalizado
```bash
python scripts/importar_csv_natalia.py "c:/Users/j.castillo/Downloads/datos.csv" "Campaña Noviembre 2025"
```

## Formato del CSV

El archivo CSV debe tener las siguientes columnas (separadas por `;`):

- id (se ignora, es autoincremental en BD)
- Campaña
- Nombre_del_cliente
- Cedula
- Telefono
- Ultimos_digitos
- Producto
- banco
- Saldo_total
- Capital
- Intereses
- Oferta_1
- Oferta_2
- Oferta_3
- Oferta_4
- Hasta_3_cuotas
- Hasta_6_cuotas
- Hasta_12_cuotas
- Hasta_18_cuotas
- NumerodeObligacion
- Email
- Descuento_3_cuotas
- Descuento_6_cuotas
- Descuento_12_cuotas
- Descuento_18_cuotas
- Inbound
- Hasta_2_cuotas
- Hasta_4_cuotas
- FechaCargue (se ignora, se usa fecha actual)
- origen_archivo (se llena automáticamente)
- Pago_flexible

## Características

✅ **Validación de datos**
- Convierte valores numéricos automáticamente
- Maneja valores NULL correctamente
- Limpia espacios en blanco
- Convierte comas a puntos en números decimales

✅ **Manejo de errores**
- Muestra errores por fila
- Continúa procesando aunque haya errores
- Hace rollback si hay más de 50% de errores

✅ **Información detallada**
- Muestra progreso cada 100 registros
- Resumen final con estadísticas
- Registro de fecha de cargue automático
- Registro del archivo origen

## Resultado Esperado

```
📂 Leyendo archivo: c:/Users/j.castillo/Downloads/Base Datos para WhatsApp 19112025.csv
📊 Total de registros en CSV: 1801
📋 Columnas encontradas: ['id', 'Campaña', 'Nombre_del_cliente', ...]

🔌 Conectando a la base de datos...

📥 Insertando registros...
  ⏳ Procesados: 100/1801
  ⏳ Procesados: 200/1801
  ...
  ⏳ Procesados: 1800/1801

✅ Cambios confirmados en la base de datos

==================================================
📊 RESUMEN DE IMPORTACIÓN
==================================================
✅ Registros insertados: 1801
❌ Registros con error: 0
📁 Archivo origen: Base Datos para WhatsApp 19112025.csv
🕐 Fecha de cargue: 2025-11-20 10:30:45
==================================================
```

## Notas Importantes

⚠️ **Advertencias:**
- El script NO elimina datos existentes, solo inserta nuevos registros
- Si necesitas limpiar la tabla primero, ejecuta manualmente:
  ```sql
  TRUNCATE TABLE ConsolidadoCampañasNatalia
  ```
- El campo `id` se genera automáticamente (es IDENTITY)
- La `FechaCargue` siempre será la fecha/hora de ejecución del script
- El `origen_archivo` será el nombre del archivo CSV

## Troubleshooting

### Error: "No module named 'pyodbc'"
```bash
pip install pyodbc
```

### Error: "No module named 'pandas'"
```bash
pip install pandas
```

### Error: "ODBC Driver not found"
Instala el ODBC Driver 17 for SQL Server desde:
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Error: "Login failed"
Verifica las credenciales en el script:
- SERVER: 172.18.72.111,1433
- DATABASE: NEXUM
- UID: NEXUM
- PWD: (verificar contraseña)

## Verificación después de la importación

Para verificar que los datos se importaron correctamente:

```sql
-- Ver total de registros
SELECT COUNT(*) FROM ConsolidadoCampañasNatalia

-- Ver últimos registros insertados
SELECT TOP 10 * 
FROM ConsolidadoCampañasNatalia 
ORDER BY id DESC

-- Ver por archivo origen
SELECT origen_archivo, COUNT(*) as total
FROM ConsolidadoCampañasNatalia
GROUP BY origen_archivo

-- Ver por fecha de cargue
SELECT CAST(FechaCargue AS DATE) as fecha, COUNT(*) as total
FROM ConsolidadoCampañasNatalia
GROUP BY CAST(FechaCargue AS DATE)
ORDER BY fecha DESC
```
