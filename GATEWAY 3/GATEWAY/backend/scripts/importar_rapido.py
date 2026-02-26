"""
Script rápido para importar CSV - Ejecuta directamente sin argumentos
"""

import pyodbc
import pandas as pd
from datetime import datetime

# CONFIGURACIÓN - Edita esto según tu archivo
ARCHIVO_CSV = r"c:\Users\j.castillo\Downloads\Base Datos para WhatsApp 19112025.csv"
NOMBRE_ORIGEN = "Base Datos para WhatsApp 19112025.csv"

# Configuración de la base de datos
DB_CONFIG = {
    'DRIVER': '{ODBC Driver 17 for SQL Server}',
    'SERVER': '172.18.73.22,1433',
    'DATABASE': 'Natalia-Whatsapp',
    'UID': 'whatsapp',
    'PWD': 'whatsapp123+'
}

def limpiar_numerico(valor):
    """Convierte valores numéricos del CSV"""
    if pd.isna(valor) or valor == '' or valor == 'NULL':
        return None
    if isinstance(valor, str):
        valor = valor.strip().replace(',', '.')
        if valor == '' or valor.upper() == 'NULL':
            return None
    try:
        return float(valor)
    except:
        return None

def limpiar_texto(valor):
    """Limpia valores de texto"""
    if pd.isna(valor) or valor == 'NULL' or valor == '':
        return None
    return str(valor).strip()

print("="*60)
print("IMPORTACIÓN DE CSV A ConsolidadoCampañasNatalia")
print("="*60)
print(f"\n📂 Archivo: {ARCHIVO_CSV}")
print(f"🔌 Servidor: {DB_CONFIG['SERVER']}")
print(f"💾 Base de datos: {DB_CONFIG['DATABASE']}")

# Leer CSV
print("\n📖 Leyendo archivo CSV...")
df = pd.read_csv(ARCHIVO_CSV, sep=';', encoding='utf-8')
print(f"✅ {len(df)} registros encontrados")

# Conectar a BD
print("\n🔗 Conectando a SQL Server...")
conn_str = f"DRIVER={DB_CONFIG['DRIVER']};SERVER={DB_CONFIG['SERVER']};DATABASE={DB_CONFIG['DATABASE']};UID={DB_CONFIG['UID']};PWD={DB_CONFIG['PWD']}"
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
print("✅ Conexión establecida")

# Query de inserción
insert_query = """
    INSERT INTO [NEXUM].[dbo].[ConsolidadoCampañasNatalia] (
        Campaña, Nombre_del_cliente, Cedula, Telefono, Ultimos_digitos,
        Producto, banco, Saldo_total, Capital, Intereses,
        Oferta_1, Oferta_2, Oferta_3, Oferta_4,
        Hasta_3_cuotas, Hasta_6_cuotas, Hasta_12_cuotas, Hasta_18_cuotas,
        NumerodeObligacion, Email,
        Descuento_3_cuotas, Descuento_6_cuotas, Descuento_12_cuotas, Descuento_18_cuotas,
        Inbound, Hasta_2_cuotas, Hasta_4_cuotas, FechaCargue, origen_archivo, Pago_flexible
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

insertados = 0
errores = 0
fecha_cargue = datetime.now()

print("\n📥 Insertando registros...")
print("-" * 60)

for idx, row in df.iterrows():
    try:
        valores = (
            limpiar_texto(row.get('Campaña')),
            limpiar_texto(row.get('Nombre_del_cliente')),
            limpiar_texto(row.get('Cedula')),
            limpiar_texto(row.get('Telefono')),
            limpiar_texto(row.get('Ultimos_digitos')),
            limpiar_texto(row.get('Producto')),
            limpiar_texto(row.get('banco')),
            limpiar_numerico(row.get('Saldo_total')),
            limpiar_numerico(row.get('Capital')),
            limpiar_numerico(row.get('Intereses')),
            limpiar_numerico(row.get('Oferta_1')),
            limpiar_numerico(row.get('Oferta_2')),
            limpiar_numerico(row.get('Oferta_3')),
            limpiar_numerico(row.get('Oferta_4')),
            limpiar_numerico(row.get('Hasta_3_cuotas')),
            limpiar_numerico(row.get('Hasta_6_cuotas')),
            limpiar_numerico(row.get('Hasta_12_cuotas')),
            limpiar_numerico(row.get('Hasta_18_cuotas')),
            limpiar_texto(row.get('NumerodeObligacion')),
            limpiar_texto(row.get('Email')),
            limpiar_numerico(row.get('Descuento_3_cuotas')),
            limpiar_numerico(row.get('Descuento_6_cuotas')),
            limpiar_numerico(row.get('Descuento_12_cuotas')),
            limpiar_numerico(row.get('Descuento_18_cuotas')),
            limpiar_texto(row.get('Inbound')),
            limpiar_numerico(row.get('Hasta_2_cuotas')),
            limpiar_numerico(row.get('Hasta_4_cuotas')),
            fecha_cargue,
            NOMBRE_ORIGEN,
            limpiar_texto(row.get('Pago_flexible'))
        )
        
        cursor.execute(insert_query, valores)
        insertados += 1
        
        if insertados % 100 == 0:
            print(f"⏳ Procesados: {insertados}/{len(df)}")
            
    except Exception as e:
        errores += 1
        print(f"❌ Error en registro {idx + 2}: {str(e)[:100]}")

# Commit
print("\n💾 Guardando cambios...")
conn.commit()
cursor.close()
conn.close()

# Resumen
print("\n" + "="*60)
print("✅ IMPORTACIÓN COMPLETADA")
print("="*60)
print(f"✅ Registros insertados: {insertados}")
print(f"❌ Errores: {errores}")
print(f"📁 Archivo: {NOMBRE_ORIGEN}")
print(f"🕐 Fecha: {fecha_cargue.strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)
