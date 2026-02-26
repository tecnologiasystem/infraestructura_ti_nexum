"""
Script para importar datos del CSV a la tabla ConsolidadoCampañasNatalia

Uso:
    python scripts/importar_csv_natalia.py "ruta/al/archivo.csv"
    
Ejemplo:
    python scripts/importar_csv_natalia.py "c:/Users/j.castillo/Downloads/Base Datos para WhatsApp 19112025.csv"
"""

import pyodbc
import pandas as pd
import sys
from datetime import datetime
import os

# Configuración de la base de datos
DB_CONFIG = {
    'DRIVER': '{ODBC Driver 17 for SQL Server}',
    'SERVER': '172.18.73.22,1433',
    'DATABASE': 'Natalia-Whatsapp',
    'UID': 'whatsapp',
    'PWD': 'whatsapp123+'
}

def get_connection():
    """Establece conexión con SQL Server"""
    conn_str = f"DRIVER={DB_CONFIG['DRIVER']};SERVER={DB_CONFIG['SERVER']};DATABASE={DB_CONFIG['DATABASE']};UID={DB_CONFIG['UID']};PWD={DB_CONFIG['PWD']}"
    return pyodbc.connect(conn_str)

def limpiar_valor_numerico(valor):
    """Convierte valores numéricos del CSV a formato SQL"""
    if pd.isna(valor) or valor == '' or valor == 'NULL':
        return None
    
    # Si es string, limpiar
    if isinstance(valor, str):
        # Remover espacios y convertir coma a punto
        valor = valor.strip().replace(',', '.')
        if valor == '' or valor.upper() == 'NULL':
            return None
    
    try:
        return float(valor)
    except:
        return None

def limpiar_valor_texto(valor):
    """Limpia valores de texto"""
    if pd.isna(valor) or valor == 'NULL' or valor == '':
        return None
    return str(valor).strip()

def importar_csv(archivo_csv, nombre_origen=None):
    """
    Importa datos del CSV a la tabla ConsolidadoCampañasNatalia
    
    Args:
        archivo_csv (str): Ruta al archivo CSV
        nombre_origen (str): Nombre del archivo origen para registrar en la BD
    """
    
    # Verificar que el archivo existe
    if not os.path.exists(archivo_csv):
        print(f"❌ ERROR: El archivo '{archivo_csv}' no existe")
        return
    
    print(f"📂 Leyendo archivo: {archivo_csv}")
    
    # Si no se especifica nombre_origen, usar el nombre del archivo
    if nombre_origen is None:
        nombre_origen = os.path.basename(archivo_csv)
    
    try:
        # Leer CSV con pandas
        df = pd.read_csv(archivo_csv, sep=';', encoding='utf-8')
        total_filas = len(df)
        print(f"📊 Total de registros en CSV: {total_filas}")
        print(f"📋 Columnas encontradas: {list(df.columns)}")
        
        # Conectar a la base de datos
        print("\n🔌 Conectando a la base de datos...")
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ConsolidadoCampañasNatalia'
        """)
        if cursor.fetchone()[0] == 0:
            print("❌ ERROR: La tabla 'ConsolidadoCampañasNatalia' no existe")
            cursor.close()
            conn.close()
            return
        
        # Query de inserción (sin el campo id porque es autoincremental)
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
        
        # Contadores
        insertados = 0
        errores = 0
        fecha_cargue = datetime.now()
        
        print("\n📥 Insertando registros...")
        
        # Insertar cada fila
        for index, row in df.iterrows():
            try:
                valores = (
                    limpiar_valor_texto(row.get('Campaña')),
                    limpiar_valor_texto(row.get('Nombre_del_cliente')),
                    limpiar_valor_texto(row.get('Cedula')),
                    limpiar_valor_texto(row.get('Telefono')),
                    limpiar_valor_texto(row.get('Ultimos_digitos')),
                    limpiar_valor_texto(row.get('Producto')),
                    limpiar_valor_texto(row.get('banco')),
                    limpiar_valor_numerico(row.get('Saldo_total')),
                    limpiar_valor_numerico(row.get('Capital')),
                    limpiar_valor_numerico(row.get('Intereses')),
                    limpiar_valor_numerico(row.get('Oferta_1')),
                    limpiar_valor_numerico(row.get('Oferta_2')),
                    limpiar_valor_numerico(row.get('Oferta_3')),
                    limpiar_valor_numerico(row.get('Oferta_4')),
                    limpiar_valor_numerico(row.get('Hasta_3_cuotas')),
                    limpiar_valor_numerico(row.get('Hasta_6_cuotas')),
                    limpiar_valor_numerico(row.get('Hasta_12_cuotas')),
                    limpiar_valor_numerico(row.get('Hasta_18_cuotas')),
                    limpiar_valor_texto(row.get('NumerodeObligacion')),
                    limpiar_valor_texto(row.get('Email')),
                    limpiar_valor_numerico(row.get('Descuento_3_cuotas')),
                    limpiar_valor_numerico(row.get('Descuento_6_cuotas')),
                    limpiar_valor_numerico(row.get('Descuento_12_cuotas')),
                    limpiar_valor_numerico(row.get('Descuento_18_cuotas')),
                    limpiar_valor_texto(row.get('Inbound')),
                    limpiar_valor_numerico(row.get('Hasta_2_cuotas')),
                    limpiar_valor_numerico(row.get('Hasta_4_cuotas')),
                    fecha_cargue,
                    nombre_origen,
                    limpiar_valor_texto(row.get('Pago_flexible'))
                )
                
                cursor.execute(insert_query, valores)
                insertados += 1
                
                # Mostrar progreso cada 100 registros
                if insertados % 100 == 0:
                    print(f"  ⏳ Procesados: {insertados}/{total_filas}")
                
            except Exception as e:
                errores += 1
                print(f"  ⚠️ Error en fila {index + 2}: {str(e)}")
                if errores > 10:
                    print("  ❌ Demasiados errores, abortando...")
                    break
        
        # Commit de los cambios
        if errores < total_filas / 2:  # Si menos del 50% tiene errores, hacer commit
            conn.commit()
            print("\n✅ Cambios confirmados en la base de datos")
        else:
            conn.rollback()
            print("\n❌ Demasiados errores, cambios revertidos")
        
        # Cerrar conexión
        cursor.close()
        conn.close()
        
        # Resumen
        print("\n" + "="*50)
        print("📊 RESUMEN DE IMPORTACIÓN")
        print("="*50)
        print(f"✅ Registros insertados: {insertados}")
        print(f"❌ Registros con error: {errores}")
        print(f"📁 Archivo origen: {nombre_origen}")
        print(f"🕐 Fecha de cargue: {fecha_cargue.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ ERROR: Debes especificar la ruta del archivo CSV")
        print("\nUso:")
        print('  python scripts/importar_csv_natalia.py "ruta/al/archivo.csv"')
        print('\nEjemplo:')
        print('  python scripts/importar_csv_natalia.py "c:/Users/j.castillo/Downloads/Base Datos para WhatsApp 19112025.csv"')
        sys.exit(1)
    
    archivo = sys.argv[1]
    nombre_origen = sys.argv[2] if len(sys.argv) > 2 else None
    
    importar_csv(archivo, nombre_origen)
