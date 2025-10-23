import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta, date
from app.dal.contactabilidad_dal import engine

"""
Este módulo contiene la lógica principal para:
- Cargar los datos necesarios desde SQL Server.
- Entrenar un modelo predictivo usando XGBoost para estimar la contactabilidad.
- Generar predicciones futuras para cada número telefónico, por día y hora.
- Evaluar el modelo mediante métricas clásicas (accuracy, precision, recall, F1, ROC AUC).

Librerías utilizadas:
- pandas: para manipulación de datos.
- xgboost: modelo de clasificación optimizado para alto rendimiento.
- sklearn: para codificación, métricas y división de datos.
- datetime: para trabajar con fechas y generar fechas futuras.
- contactabilidad_dal.engine: conexión SQLAlchemy hacia la base de datos.
"""


def calcular_proxima_fecha(dia_objetivo):
    """
    Calcula la próxima fecha (en formato YYYY-MM-DD) en que ocurrirá un día específico de la semana.

    Parámetros:
    - dia_objetivo (str): Día objetivo en inglés (por ejemplo, 'Monday', 'Tuesday', etc.)

    Lógica:
    - Se obtiene la fecha actual con date.today().
    - Se transforma el nombre del día objetivo a su índice correspondiente (0 = Monday, 6 = Sunday).
    - Se compara con el día actual de la semana para saber cuántos días faltan.
    - Si el día objetivo es hoy, se asume que se quiere la próxima ocurrencia (por eso suma 7).
    - Retorna la fecha futura formateada como string.

    Ejemplo:
    Si hoy es martes (índice 1) y el objetivo es 'Friday' (índice 4),
    entonces faltan 3 días y la función retornará la fecha del próximo viernes.
    """
    hoy = date.today()
    dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    objetivo_idx = dias.index(dia_objetivo)
    hoy_idx = hoy.weekday()
    dias_adelante = (objetivo_idx - hoy_idx + 7) % 7
    if dias_adelante == 0:
        dias_adelante = 7
    return (hoy + timedelta(days=dias_adelante)).strftime('%Y-%m-%d')


def cargar_datos(limit=5000):
    """
    Carga y preprocesa los datos necesarios para el modelo de predicción de contactabilidad.

    Parámetros:
    - limit (int): Número máximo de registros que se desean consultar desde la base de datos.

    Proceso:
    1. Se realiza la conexión con la base de datos a través del motor `engine`.
    2. Se consulta la tabla 'unificado' que contiene el historial de llamadas.
    3. Se consulta la tabla 'pesofin' que contiene las frases categorizadas con pesos (0 o 1),
       donde 1 representa un contacto exitoso y 0 un intento fallido.
    4. Se realiza una fusión (merge) entre los datos de llamadas y los pesos, 
       uniendo las filas por coincidencia entre `status_name` del historial y `frase` de la tabla de pesos.
    5. Si alguna de estas operaciones falla, se captura la excepción y retorna un DataFrame vacío.

    Retorna:
    - Un DataFrame con los datos de llamadas enriquecidos con la columna de `peso` correspondiente
      a cada `status_name`.
    """
    print("🔄 Cargando datos desde SQL...")
    try:
        df_llamadas = pd.read_sql(f"SELECT TOP({limit}) * FROM unificado", engine)
        print("✅ Datos de llamadas cargados")
        df_pesos = pd.read_sql("SELECT * FROM pesofin", engine)
        print("✅ Datos de pesos cargados")
    except Exception as e:
        print("❌ Error al conectar con la base de datos:", e)
        return pd.DataFrame()

    print("🔗 Uniendo datos...")
    merged = df_llamadas.merge(
        df_pesos[['frase', 'peso']],
        how='left',
        left_on='status_name',
        right_on='frase'
    )


    """
    6. Se filtran únicamente los registros que tienen un valor de peso válido (0 o 1), 
       ignorando los que no tengan esta clasificación.
    """
    df = merged[merged['peso'].isin([0, 1])].copy()

    """
    7. Se convierte la columna 'date_call' al tipo datetime para asegurar un correcto análisis temporal.
       - `dayfirst=True` asegura que el formato día/mes/año sea interpretado correctamente.
       - `errors='coerce'` convierte fechas inválidas en NaT (valores nulos de fecha).
    """
    df['date_call'] = pd.to_datetime(df['date_call'], dayfirst=True, errors='coerce')

    """
    8. Se eliminan las filas donde no se pudo convertir la fecha (es decir, donde 'date_call' es nulo).
    """
    df = df.dropna(subset=['date_call'])

    """
    9. Se extrae el nombre del día de la semana (ej. 'Monday') y la hora (0-23) de la fecha de la llamada,
       y se agregan como nuevas columnas para alimentar el modelo.
    """
    df['dia'] = df['date_call'].dt.day_name()
    df['hora'] = df['date_call'].dt.hour

    """
    10. Se imprime la cantidad de registros finales que serán utilizados para el entrenamiento.
    """
    print(f"📊 Datos listos: {len(df)} registros válidos")

    """
    11. Se devuelve un DataFrame con las columnas relevantes:
        - 'telephone': número de teléfono
        - 'dia': día de la semana
        - 'hora': hora del día
        - 'peso': si respondió (1) o no respondió (0)
    """
    return df[['telephone', 'dia', 'hora', 'peso']]


# 🧠 Entrenamiento del modelo con XGBoost
def entrenar_modelo(df):
    """
    Esta función entrena un modelo XGBoost para predecir la probabilidad de contacto exitoso.
    """

    print("🤖 Entrenando modelo con XGBoost...")

    """
    1. Se instancian dos codificadores LabelEncoder:
       - le_dia para convertir el nombre del día (ej: 'Monday') a un número entero.
       - le_tel para codificar cada número de teléfono con un valor numérico.
       Esto es necesario porque XGBoost no trabaja directamente con variables categóricas.
    """
    le_dia = LabelEncoder()
    le_tel = LabelEncoder()

    """
    2. Se crea una copia del DataFrame con las columnas relevantes para el modelo.
       Luego se agregan las columnas codificadas 'telefono_encoded' y 'dia_encoded'.
    """
    X = df[['telephone', 'dia', 'hora']].copy()
    X['telefono_encoded'] = le_tel.fit_transform(X['telephone'])
    X['dia_encoded'] = le_dia.fit_transform(X['dia'])

    """
    3. Se seleccionan las variables que se usarán como características (X) del modelo:
       - telefono_encoded: ID único para cada número.
       - dia_encoded: día de la semana en forma numérica.
       - hora: hora del día (0-23).
       La variable objetivo (y) será 'peso', que indica si contestó (1) o no (0).
    """
    X_model = X[['telefono_encoded', 'dia_encoded', 'hora']]
    y = df['peso']

    """
    4. Se configura y entrena el modelo XGBoostClassifier con parámetros ajustados para priorizar la precisión:
       - n_estimators=350: cantidad de árboles.
       - max_depth=7: profundidad máxima de cada árbol.
       - learning_rate=0.05: velocidad de aprendizaje (menor es más preciso, pero más lento).
       - scale_pos_weight=5: se da más peso a las clases positivas (1 = contestó).
       - subsample y colsample_bytree: reducción para evitar overfitting.
       - use_label_encoder=False y eval_metric='aucpr': métricas más precisas para desequilibrio.
    """
    model = XGBClassifier(
        n_estimators=350,
        max_depth=7,
        learning_rate=0.05,
        scale_pos_weight=5,
        subsample=0.9,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric='aucpr',
        random_state=42
    )

    """
    5. Se define un vector de pesos para las muestras:
       - Las clases positivas (respuesta = 1) reciben un peso mayor para que el modelo las tome más en serio.
    """
    sample_weights = y.map(lambda val: 5 if val == 1 else 1)

    """
    6. Se entrena el modelo usando los datos y los pesos.
    """
    model.fit(X_model, y, sample_weight=sample_weights)

    print("✅ Modelo entrenado con XGBoost")

    """
    7. Se devuelven el modelo y los codificadores para poder usarlos después en predicciones.
    """
    return model, le_tel, le_dia


# 🔮 Predicción por contacto y horario
def generar_predicciones(model, le_tel, le_dia, df):
    """
    Esta función genera predicciones de contacto exitoso por cada número telefónico,
    para cada día de la semana y cada hora del día. Se retorna solo la mejor predicción
    para cada teléfono (aquella con la probabilidad más alta que supere un umbral).
    """

    print("🔮 Generando predicciones futuras por número...")

    """
    1. Se extraen los teléfonos únicos del DataFrame de entrada.
       También se obtienen los días de la semana codificados y las 24 horas del día.
    """
    contactos = df['telephone'].unique()
    dias_semana = list(le_dia.classes_)
    horas = list(range(0, 24))

    """
    2. Se inicializa la lista de predicciones.
    """
    predicciones = []

    """
    3. Se realiza una predicción para cada combinación de:
       - Teléfono
       - Día de la semana
       - Hora (0 a 23)

       Por cada combinación, se calcula la probabilidad de que ese teléfono conteste
       en ese día y hora. Si la probabilidad supera el 98%, se guarda la predicción.
    """
    for tel in contactos:
        # Codificamos el número de teléfono
        tel_encoded = le_tel.transform([tel])[0]

        for dia in dias_semana:
            # Codificamos el día de la semana
            dia_encoded = le_dia.transform([dia])[0]

            for hora in horas:
                # Se construye el DataFrame de una sola fila para predecir
                X_pred = pd.DataFrame(
                    [[tel_encoded, dia_encoded, hora]],
                    columns=['telefono_encoded', 'dia_encoded', 'hora']
                )

                # Se obtiene la probabilidad de clase positiva (índice 1)
                prob = model.predict_proba(X_pred)[0][1] * 100

                # Se filtran solo las predicciones con alta probabilidad (≥ 98%)
                if prob >= 98:
                    predicciones.append({
                        'telefono': tel,
                        'dia': dia,
                        'hora': hora,
                        'probabilidad_contacto': round(prob, 1)
                    })


        """
    4. Se convierten las predicciones válidas (probabilidad ≥ 98%) a un DataFrame.
       Cada fila representa una combinación de teléfono, día y hora con alta probabilidad.
    """
    df_pred = pd.DataFrame(predicciones)

    print("✅ Predicciones generadas")

    """
    5. Se ordenan las predicciones por:
        - Teléfono (ascendente)
        - Probabilidad de contacto (descendente)
    
       Esto permite que la mejor predicción por cada teléfono quede en la primera posición.
    """
    mejores = df_pred.sort_values(['telefono', 'probabilidad_contacto'], ascending=[True, False])

    """
    6. Se agrupa el DataFrame por 'telefono' y se toma solo la primera fila de cada grupo,
       que corresponde a la mejor predicción para ese número.
    """
    mejores_final = mejores.groupby('telefono').first().reset_index()

    """
    7. A cada predicción se le agrega una columna con la 'fecha futura recomendada',
       la cual se calcula usando la función `calcular_proxima_fecha` según el día con mejor probabilidad.
    """
    mejores_final['fecha_futura_recomendada'] = mejores_final['dia'].apply(calcular_proxima_fecha)

    """
    8. Finalmente, se retorna el DataFrame que contiene:
        - El teléfono
        - El mejor día y hora para contactarlo
        - La probabilidad estimada
        - La fecha futura recomendada para intentarlo
    """
    return mejores_final


# 📊 Evaluación del modelo con umbral fijo alto (prioriza precisión)
def obtener_metricas():
    """
    Esta función entrena un modelo con una partición de los datos históricos
    y evalúa su rendimiento utilizando varias métricas (accuracy, precision, recall, etc).
    Se emplea un umbral de predicción alto para priorizar la precisión del modelo.
    """
    print("📅 Obteniendo métricas del modelo...")

    """
    1. Cargar los datos de llamadas con un límite de 5000 registros.
       Si ocurre algún error y el DataFrame resulta vacío, se retorna un mensaje de error.
    """
    df = cargar_datos(limit=5000)
    if df.empty:
        return {
            'error': 'No se pudo cargar la data para evaluar el modelo'
        }

    """
    2. Preparar codificadores LabelEncoder para convertir variables categóricas:
       - `dia` (nombre del día de la semana)
       - `telephone` (número de teléfono)
    """
    le_dia = LabelEncoder()
    le_tel = LabelEncoder()

    """
    3. Crear un nuevo DataFrame de entrada `X` con las columnas relevantes,
       luego se agregan las columnas codificadas para los algoritmos de ML.
    """
    X = df[['telephone', 'dia', 'hora']].copy()
    X['telefono_encoded'] = le_tel.fit_transform(X['telephone'])
    X['dia_encoded'] = le_dia.fit_transform(X['dia'])

    """
    4. Seleccionar las columnas finales para el modelo (`X_model`) y la variable objetivo (`y`).
    """
    X_model = X[['telefono_encoded', 'dia_encoded', 'hora']]
    y = df['peso']  # Etiqueta: 1 = contestó, 0 = no contestó

    """
    5. Dividir los datos en conjunto de entrenamiento (80%) y prueba (20%).
    """
    X_train, X_test, y_train, y_test = train_test_split(X_model, y, test_size=0.2, random_state=42)

    """
    6. Definir el modelo XGBoost con hiperparámetros ajustados para manejar desbalanceo.
    """
    model = XGBClassifier(
        n_estimators=350,
        max_depth=7,
        learning_rate=0.05,
        scale_pos_weight=5,
        subsample=0.9,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric='aucpr',
        random_state=42
    )

    """
    7. Crear pesos personalizados para las muestras de entrenamiento:
       Las respuestas positivas (peso=1) se ponderan más para mejorar la precisión.
    """
    sample_weights = y_train.map(lambda val: 5 if val == 1 else 1)

    """
    8. Entrenar el modelo usando los pesos definidos.
    """
    model.fit(X_train, y_train, sample_weight=sample_weights)

    """
    9. Obtener las probabilidades predichas para el conjunto de prueba.
       Luego aplicar un umbral de 0.98 para considerar una predicción como positiva.
    """
    y_prob = model.predict_proba(X_test)[:, 1]
    threshold = 0.98  # Umbral alto para priorizar precisión
    y_pred = (y_prob >= threshold).astype(int)

    print("✅ Métricas calculadas con umbral fijo (alta precisión)")

    """
    10. Calcular y retornar las métricas principales:
        - accuracy: proporción de predicciones correctas
        - precision: de los que predijo positivos, cuántos realmente lo fueron
        - recall: de todos los positivos reales, cuántos detectó
        - f1: balance entre precisión y recall
        - roc_auc: área bajo curva ROC
    """
    return {
        'threshold_usado': threshold,
        'accuracy': round(float(accuracy_score(y_test, y_pred)), 2),
        'precision': round(float(precision_score(y_test, y_pred)), 2),
        'recall': round(float(recall_score(y_test, y_pred)), 2),
        'f1': round(float(f1_score(y_test, y_pred)), 2),
        'roc_auc': round(float(roc_auc_score(y_test, y_prob)), 2)
    }
