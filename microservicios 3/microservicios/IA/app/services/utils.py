from io import BytesIO
from docx import Document
import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import cv2
import numpy as np

"""
Se importan las librerías necesarias para el procesamiento de archivos:
- BytesIO: permite tratar archivos como flujos de bytes.
- docx.Document: se usa para leer archivos .docx.
- pdfplumber: extrae texto directamente de PDFs con contenido digital.
- PIL (Image): manipulación de imágenes.
- pytesseract: OCR (Reconocimiento Óptico de Caracteres).
- pdf2image: convierte páginas de PDF en imágenes para OCR.
- cv2 y numpy: preprocesamiento de imágenes (blanco y negro, umbral adaptativo).
"""

"""Ruta del ejecutable Tesseract OCR (ajustar según el entorno del sistema)"""
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\j.salgar\AppData\Local\Programs\Tesseract-OCR"

async def procesar_pdf(file):
    """
    Procesa un archivo PDF:
    - Intenta primero extraer texto directamente usando pdfplumber.
    - Si no se encuentra texto (por ejemplo, es escaneado), convierte las páginas en imágenes
      y extrae el texto usando OCR (Tesseract).
    
    Devuelve: el texto combinado del PDF.
    """
    archivo = file.read()
    texto = ""

    """Extracción normal usando pdfplumber"""
    with pdfplumber.open(BytesIO(archivo)) as pdf:
        for pagina in pdf.pages:
            contenido_pagina = pagina.extract_text()
            if contenido_pagina:
                texto += contenido_pagina

    """Si el texto está vacío (PDF escaneado), usar OCR"""
    if not texto.strip():
        imagenes = convert_from_bytes(archivo)
        for imagen in imagenes:
            texto += pytesseract.image_to_string(imagen)

    return texto

async def procesar_word(file):
    """
    Procesa un archivo .docx (Word):
    - Lee el contenido de todos los párrafos.
    - Devuelve el texto concatenado.
    """
    archivo = file.read()
    doc = Document(BytesIO(archivo))
    texto = ""

    for parrafo in doc.paragraphs:
        texto += parrafo.text

    return texto

async def procesar_imagen(file):
    """
    Procesa una imagen (JPG, PNG, etc.):
    - Usa pytesseract para extraer texto por OCR directamente.
    - No realiza preprocesamiento adicional.
    """
    archivo = file.read()
    imagen = Image.open(BytesIO(archivo))
    texto = pytesseract.image_to_string(imagen)
    return texto

async def procesar_imagen_manuscrita(file):
    """
    Procesa una imagen manuscrita o escaneada con posible baja calidad:
    - Convierte la imagen a escala de grises.
    - Aplica umbral adaptativo para mejorar el contraste (mejora la precisión del OCR).
    - Ejecuta Tesseract OCR con el lenguaje latino activado.
    - Devuelve el texto reconocido.
    """
    archivo = file.read()
    imagen = Image.open(BytesIO(archivo))

    """Convertir imagen a escala de grises"""
    imagen_cv = cv2.cvtColor(np.array(imagen), cv2.COLOR_RGB2GRAY)

    """Aplicar umbral adaptativo para binarizar"""
    imagen_cv = cv2.adaptiveThreshold(
        imagen_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    """Ejecutar OCR"""
    texto = pytesseract.image_to_string(imagen_cv, lang="eng+script/latin")
    return texto

