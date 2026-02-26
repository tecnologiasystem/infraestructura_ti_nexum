"""
Script para generar archivo SQL con INSERTs desde CSV
"""

import pandas as pd
from datetime import datetime
import os

# CONFIGURACIÓN
ARCHIVO_CSV = r"c:\Users\j.castillo\Downloads\Base Datos para WhatsApp 19112025.csv"
NOMBRE_ORIGEN = "Base Datos para WhatsApp 19112025.csv"
ARCHIVO_SALIDA = "scripts/inserts_consolidado.sql"

def limpiar_numerico(valor):
    """Convierte valores numéricos para SQL"""
    if pd.isna(valor) or valor == '' or valor == 'NULL':
        return "NULL"
    
    if isinstance(valor, str):
        # Limpiar espacios, comas y símbolos de porcentaje
        valor = valor.strip().replace(',', '.').replace('%', '')
        if valor == '' or valor.upper() == 'NULL':
            return "NULL"
            
    try:
        return str(float(valor))
    except:
        return "NULL"

def limpiar_entero(valor):
    """Convierte valores a entero para SQL"""
    if pd.isna(valor) or valor == '' or valor == 'NULL':
        return "NULL"
    try:
        # Convertir a float primero para manejar "123.0" y luego a int
        return str(int(float(str(valor).replace(',', '.'))))
    except:
        return "NULL"

def limpiar_texto(valor):
    """Limpia valores de texto para SQL"""
    if pd.isna(valor) or valor == 'NULL' or valor == '':
        return "NULL"
    valor_str = str(valor).strip().replace("'", "''") # Escapar comillas simples
    return f"'{valor_str}'"

print(f"📖 Leyendo archivo CSV: {ARCHIVO_CSV}")
try:
    df = pd.read_csv(ARCHIVO_CSV, sep=';', encoding='utf-8')
    print(f"✅ {len(df)} registros encontrados")

    fecha_cargue = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"✍️ Generando archivo SQL: {ARCHIVO_SALIDA}")
    
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        f.write("-- Script generado automáticamente\n")
        f.write(f"-- Fecha: {fecha_cargue}\n")
        f.write(f"-- Origen: {NOMBRE_ORIGEN}\n\n")
        f.write("USE [NEXUM]\nGO\n\n")
        
        # Escribir inserts en lotes de 100 para no saturar
        f.write("BEGIN TRANSACTION\n")
        
        count = 0
        for idx, row in df.iterrows():
            valores = [
                limpiar_entero(row.get('id')),
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
                f"'{fecha_cargue}'",
                f"'{NOMBRE_ORIGEN}'",
                limpiar_texto(row.get('Pago_flexible'))
            ]
            
            linea = f"INSERT INTO [dbo].[ConsolidadoCampañasNatalia] (id, Campaña, Nombre_del_cliente, Cedula, Telefono, Ultimos_digitos, Producto, banco, Saldo_total, Capital, Intereses, Oferta_1, Oferta_2, Oferta_3, Oferta_4, Hasta_3_cuotas, Hasta_6_cuotas, Hasta_12_cuotas, Hasta_18_cuotas, NumerodeObligacion, Email, Descuento_3_cuotas, Descuento_6_cuotas, Descuento_12_cuotas, Descuento_18_cuotas, Inbound, Hasta_2_cuotas, Hasta_4_cuotas, FechaCargue, origen_archivo, Pago_flexible) VALUES ({', '.join(valores)});\n"
            f.write(linea)
            
            count += 1
            if count % 100 == 0:
                f.write("\nCOMMIT TRANSACTION\nBEGIN TRANSACTION\n")
                print(f"  ⏳ Procesados: {count}")

        f.write("\nCOMMIT TRANSACTION\n")
        print(f"✅ Finalizado. Total: {count}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
