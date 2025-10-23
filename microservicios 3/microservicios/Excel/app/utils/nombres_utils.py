import unicodedata
from rapidfuzz import process, fuzz
from utils.nombres_data import nombres_comunes, apellidos_comunes

"""
Función: normalizar
Descripción: 
    - Elimina tildes y acentos de un texto (descomposición Unicode NFD)
    - Convierte todo a minúsculas
    - Útil para comparaciones fuzzy más precisas
"""
def normalizar(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').lower()

"""
Función: es_aproximado
Descripción:
    - Verifica si una palabra es suficientemente parecida (por fuzzy matching) a alguna en una lista
    - Usa la función `extractOne` de `rapidfuzz` con el scorer `fuzz.ratio`
    - Devuelve True si el puntaje de similitud supera el umbral (por defecto: 90)
"""
def es_aproximado(palabra: str, lista: list, umbral: int = 90) -> bool:
    palabra_norm = normalizar(palabra)
    lista_norm = [normalizar(p) for p in lista]
    mejor, score, _ = process.extractOne(palabra_norm, lista_norm, scorer=fuzz.ratio)
    return score >= umbral

"""
Función: extraer_nombre_apellido_fuzzy
Descripción:
    - A partir de un string con nombre completo, intenta extraer el primer nombre y apellido más probables
    - Usa heurísticas y fuzzy matching para comparar con listas conocidas de nombres y apellidos comunes
    - Penaliza si un nombre parece más un apellido y viceversa
    - Retorna el mejor par (nombre, apellido) encontrado con la puntuación más alta
"""
def extraer_nombre_apellido_fuzzy(nombre_completo: str) -> tuple:
    if not isinstance(nombre_completo, str) or not nombre_completo.strip():
        return "", ""

    partes = nombre_completo.strip().split()
    mejor = {"nombre": partes[0], "apellido": partes[-1], "score": -999}

    for i, nombre in enumerate(partes):
        for j, apellido in enumerate(partes):
            if i == j:
                continue

            score = 0

            """
            Se suma puntuación si el nombre coincide con nombres comunes,
            y el apellido con apellidos comunes. Se penaliza si hay mezcla inversa.
            """
            if es_aproximado(nombre, nombres_comunes):
                score += 5
            if es_aproximado(apellido, apellidos_comunes):
                score += 5
            if es_aproximado(apellido, nombres_comunes) and apellido not in apellidos_comunes:
                score -= 5
            if es_aproximado(nombre, apellidos_comunes) and nombre not in nombres_comunes:
                score -= 5

            """
            Se actualiza el mejor par encontrado si este par tiene mayor score
            """
            if score > mejor["score"]:
                mejor = {"nombre": nombre, "apellido": apellido, "score": score}

    return mejor["nombre"].capitalize(), mejor["apellido"].capitalize()
