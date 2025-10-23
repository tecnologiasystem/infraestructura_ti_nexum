from app.config.database import get_connection
from rapidfuzz import process, fuzz
from typing import Tuple, List, Optional

"""
Función segura para imprimir cadenas, evitando errores con caracteres no ASCII.
"""
def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'ignore').decode())

"""
Aseguramos que la salida estándar soporte UTF-8 para imprimir caracteres especiales correctamente.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ——————————————————————————————————————————————
# CACHÉ EN MEMORIA

"""
Variables globales que almacenan nombres y apellidos comunes desde la base de datos.
Se cargan una sola vez y luego son reutilizadas para mejorar el rendimiento.
"""
_nombres_cache: List[str] = []
_apellidos_cache: List[str] = []

def _cargar_cache_nombres_apellidos():
    """
    Carga en memoria todos los nombres y apellidos desde la tabla NombresComunes.
    Esta función es ejecutada al inicio del módulo para inicializar las cachés.
    """
    global _nombres_cache, _apellidos_cache
    safe_print(" _cargar_cache_nombres_apellidos(): arrancando carga en memoria")    
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT nombre, apellido FROM NombresComunes")
        filas = cur.fetchall()
        _nombres_cache = [f[0].strip() for f in filas if f[0]]
        _apellidos_cache = [f[1].strip() for f in filas if f[1]]
        safe_print(f" Caché inicializada: {_nombres_cache.__len__()} nombres, {_apellidos_cache.__len__()} apellidos")
    finally:
        cur.close()
        conn.close()

"""
Inicializamos la caché de nombres y apellidos al cargar el archivo.
"""
_cargar_cache_nombres_apellidos()

def insertar_solo_nombre(nombre: str) -> bool:
    """
    Inserta un nombre en la base de datos y actualiza la caché local.

    Retorna:
    - True si se insertó correctamente.
    - False si hubo algún error.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        nombre_cap = nombre.strip().capitalize()
        cur.execute(
            "INSERT INTO NombresComunes (nombre, apellido) VALUES (?, NULL)",
            (nombre_cap,)
        )
        conn.commit()
        _nombres_cache.append(nombre_cap)
        safe_print(f" Agregado NOMBRE a caché y BD: '{nombre_cap}'")
        return True
    except Exception as e:
        safe_print(f" Error insertando nombre '{nombre}': {e}")
        return False
    finally:
        cur.close()
        conn.close()

def insertar_solo_apellido(apellido: str) -> bool:
    """
    Inserta un apellido en la base de datos y actualiza la caché local.

    Retorna:
    - True si se insertó correctamente.
    - False si hubo algún error.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        apellido_cap = apellido.strip().capitalize()
        cur.execute(
            "INSERT INTO NombresComunes (nombre, apellido) VALUES (NULL, ?)",
            (apellido_cap,)
        )
        conn.commit()
        _apellidos_cache.append(apellido_cap)
        safe_print(f" Agregado APELLIDO a caché y BD: '{apellido_cap}'")
        return True
    except Exception as e:
        safe_print(f" Error insertando apellido '{apellido}': {e}")
        return False
    finally:
        cur.close()
        conn.close()

def buscar_nombre_exacto(palabra: str, nombres_bd: List[str]) -> Optional[str]:
    """
    Busca si la palabra coincide exactamente (sin distinguir mayúsculas) con un nombre existente.

    Retorna:
    - El nombre coincidente si lo encuentra, o None si no lo encuentra.
    """
    palabra_clean = palabra.strip().lower()
    for nombre in nombres_bd:
        if nombre.lower() == palabra_clean:
            return nombre
    return None

def buscar_nombre_similar(palabra: str, nombres_bd: List[str], umbral: int = 80) -> Optional[str]:
    """
    Busca el nombre más similar usando fuzzy matching.

    Parámetros:
    - palabra: string a comparar.
    - nombres_bd: lista de nombres contra la cual comparar.
    - umbral: valor mínimo de similitud para aceptar una coincidencia.

    Retorna:
    - El nombre más similar o None si no hay coincidencias por encima del umbral.
    """
    if not nombres_bd:
        return None
    resultado = process.extractOne(
        palabra,
        nombres_bd,
        scorer=fuzz.ratio,
        score_cutoff=umbral
    )
    return resultado[0] if resultado else None

def verificar_es_nombre_o_apellido(
    palabra: str,
    nombres_bd: List[str],
    apellidos_bd: List[str]
) -> str:
    """
    Determina si una palabra es más probable que sea un nombre o un apellido.
    Se basa en coincidencias parciales y longitud de la palabra.

    Retorna:
    - 'nombre' o 'apellido' según la estimación.
    """
    pl = palabra.lower().strip()
    sim_nombres = [n for n in nombres_bd if pl in n.lower() or n.lower() in pl]
    sim_apellidos = [a for a in apellidos_bd if pl in a.lower() or a.lower() in pl]
    if len(sim_nombres) > len(sim_apellidos):
        return 'nombre'
    if len(sim_apellidos) > len(sim_nombres):
        return 'apellido'
    return 'apellido' if len(palabra) > 7 else 'nombre'

def procesar_nombre_completo_mejorado_v2(nombre_completo: str) -> Tuple[str, str]:
    """
    Procesa un nombre completo y devuelve el primer nombre y el primer apellido identificados.

    Lógica:
    - Divide el nombre completo en partes significativas (>3 letras).
    - Intenta identificar la mejor combinación nombre-apellido usando:
        - Coincidencia exacta
        - Fuzzy matching
        - Heurística si no hay coincidencias fuertes
    - Si encuentra una combinación nueva, la inserta en la base de datos y actualiza caché.

    Retorna:
    - Tuple (nombre, apellido)
    """
    if not nombre_completo or not nombre_completo.strip():
        return '', ''

    partes = [p.strip() for p in nombre_completo.split() if len(p.strip()) > 3]
    if len(partes) < 2:
        return (partes[0].capitalize(), '') if partes else ('', '')

    nombres_bd = _nombres_cache
    apellidos_bd = _apellidos_cache
    safe_print("[INFO] Procesando nombre con múltiples partes...")

    mejor_nombre, mejor_apellido, mejor_score = '', '', -1

    for i, parte_nombre in enumerate(partes):
        for j, parte_apellido in enumerate(partes):
            if i == j:
                continue

            score = 0
            cand_nom = ''
            cand_ape = ''

            """
            Intentamos determinar el nombre
            """
            if len(parte_nombre) > 3:
                ext_nom = buscar_nombre_exacto(parte_nombre, nombres_bd)
                if ext_nom and len(ext_nom) > 3:
                    cand_nom, score = ext_nom, score + 100
                else:
                    sim_nom = buscar_nombre_similar(parte_nombre, nombres_bd, umbral=85)
                    if sim_nom and len(sim_nom) > 3:
                        cand_nom, score = sim_nom, score + 70
                    elif verificar_es_nombre_o_apellido(parte_nombre, nombres_bd, apellidos_bd) == 'nombre':
                        cand_nom, score = parte_nombre.capitalize(), score + 20

            """
            Intentamos determinar el apellido
            """
            if len(parte_apellido) > 3:
                ext_ape = buscar_nombre_exacto(parte_apellido, apellidos_bd)
                if ext_ape and len(ext_ape) > 3:
                    cand_ape, score = ext_ape, score + 100
                else:
                    sim_ape = buscar_nombre_similar(parte_apellido, apellidos_bd, umbral=85)
                    if sim_ape and len(sim_ape) > 3:
                        cand_ape, score = sim_ape, score + 70
                    elif verificar_es_nombre_o_apellido(parte_apellido, nombres_bd, apellidos_bd) == 'apellido':
                        cand_ape, score = parte_apellido.capitalize(), score + 20

            if cand_nom and cand_ape and score > mejor_score:
                mejor_nombre, mejor_apellido, mejor_score = cand_nom, cand_ape, score

    """
    Si no encontramos una buena combinación, usamos los dos primeros valores como fallback
    """
    if not mejor_nombre or not mejor_apellido:
        if len(partes) >= 2:
            mejor_nombre = partes[0].capitalize()
            mejor_apellido = partes[1].capitalize()
        else:
            return '', ''

    """
    Intentamos insertar los nombres nuevos si no están ya en la BD
    """
    try:
        if mejor_nombre and not buscar_nombre_exacto(mejor_nombre, nombres_bd):
            insertar_solo_nombre(mejor_nombre)
        if mejor_apellido and not buscar_nombre_exacto(mejor_apellido, apellidos_bd):
            insertar_solo_apellido(mejor_apellido)
    except Exception as e:
        safe_print(f"[WARN] No se pudo insertar nombre o apellido: {e}")

    safe_print(f" Resultado final: '{mejor_nombre}' + '{mejor_apellido}'")
    safe_print("-" * 60)
    return mejor_nombre, mejor_apellido
