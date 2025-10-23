import os
""" 
Obtiene el directorio actual donde está ubicado este archivo para usarlo como base 
en la construcción de rutas absolutas dentro del proyecto.
"""
current_dir = os.path.dirname(__file__)

""" 
Define la carpeta base donde se almacenarán todos los archivos subidos o generados 
por el sistema. Es una subcarpeta llamada 'uploads' dentro del directorio actual.
"""
UPLOAD_FOLDER = os.path.join(current_dir, 'uploads')

"""
Define la ruta completa para la carpeta donde se guardarán los archivos Excel jurídicos.
Se crea una subcarpeta 'ExcelJuridico' dentro de la carpeta base de uploads.
"""
UPLOAD_EXCEL_JURIDICO = os.path.join(UPLOAD_FOLDER, 'ExcelJuridico')

"""
Define la ruta para la carpeta que almacenará los archivos adjuntos relacionados con 
procesos jurídicos. Carpeta 'AdjuntosJuridico' dentro de uploads.
"""
UPLOAD_ADJUNTOS_JURIDICO = os.path.join(UPLOAD_FOLDER, 'AdjuntosJuridico')

"""
Define la ruta para guardar los documentos generados de cartas para impulso procesal.
Se usa la carpeta 'DocumentosImpulsoProcesal' dentro de uploads.
"""
UPLOAD_CARTAS_IMPULSO = os.path.join(UPLOAD_FOLDER, 'DocumentosImpulsoProcesal')

"""
Ruta para almacenar los archivos Excel usados específicamente para la ejecución
de procesos de impulso procesal. Carpeta 'Archivos_excel_impulso_Procesal' dentro de uploads.
"""
UPLOAD_EXCEL_EJECUCION_IMPULSO = os.path.join(UPLOAD_FOLDER, 'Archivos_excel_impulso_Procesal')

"""
Ruta para la carpeta que contiene archivos Excel de preforma o plantillas base 
para generar documentos o informes. Carpeta 'ExcelPreforma' dentro de uploads.
"""
UPLOAD_EXCEL_PREFORMA = os.path.join(UPLOAD_FOLDER, 'ExcelPreforma')

"""
Ruta para guardar los archivos adjuntos relacionados con vigilancia diaria.
Carpeta 'AdjuntosVigilanciaDia' dentro de uploads.
"""
UPLOAD_ADJUNTOS_VIGILANCIADIA = os.path.join(UPLOAD_FOLDER, 'AdjuntosVigilanciaDia')
