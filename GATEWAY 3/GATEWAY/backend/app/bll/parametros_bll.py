from app.dal.parametros_dal import consultar_parametros, obtener_encabezados_completados, obtener_valor_token

def obtener_parametros(modulo=None, nombre=None):
    return consultar_parametros(modulo, nombre)

def calcular_tokens_usados():
    encabezados = obtener_encabezados_completados()
    valor_token = obtener_valor_token("TokenRunt", "Consulta")

    resultado = []

    for enc in encabezados:
        tokens_gastados = enc["totalRegistros"] * valor_token
        resultado.append({
            **enc,
            "tokensGastados": round(tokens_gastados, 2)
        })

    return resultado