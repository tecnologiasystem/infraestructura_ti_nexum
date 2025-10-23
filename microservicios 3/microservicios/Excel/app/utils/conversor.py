def numero_a_texto(numero, agregar_pesos=True):
    """
    Convierte un número entero en su representación textual en español.
    Por ejemplo: 1234 -> "mil doscientos treinta y cuatro pesos"

    Parámetros:
    - numero: int o valor convertible a int
    - agregar_pesos: si es True, se añade la palabra "pesos" al final

    Retorna:
    - Cadena con el número en texto (por ejemplo: "mil pesos")
    """
    try:
        """
        Convertimos a entero para asegurarnos que sea un número válido
        """
        numero = int(numero)

        """
        Caso especial para 0
        """
        if numero == 0:
            return "cero pesos" if agregar_pesos else "cero"

        """
        Caso especial para números negativos: se convierte el valor absoluto recursivamente
        """
        if numero < 0:
            return f"menos {numero_a_texto(-numero, agregar_pesos)}"

        """
        Definimos las palabras base para construir el número
        """
        unidades = ["", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
        decenas = ["", "diez", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
        centenas = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]
        diez_a_diecinueve = ["diez", "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho", "diecinueve"]

        texto = ""

        """
        Procesamos miles de millones
        """
        if numero >= 1_000_000_000:
            billones = numero // 1_000_000_000
            texto += "mil millones" if billones == 1 else f"{numero_a_texto(billones, False)} mil millones"
            numero %= 1_000_000_000
            if numero > 0: texto += " "

        """
        Procesamos millones
        """
        if numero >= 1_000_000:
            millones = numero // 1_000_000
            texto += "un millón" if millones == 1 else f"{numero_a_texto(millones, False)} millones"
            numero %= 1_000_000
            if numero > 0: texto += " "

        """
        Procesamos miles
        """
        if numero >= 1_000:
            miles = numero // 1_000
            texto += "mil" if miles == 1 else f"{numero_a_texto(miles, False)} mil"
            numero %= 1_000
            if numero > 0: texto += " "

        """
        Procesamos centenas
        """
        if numero >= 100:
            texto += "cien" if numero == 100 else f"{centenas[numero // 100]}"
            numero %= 100
            if numero > 0: texto += " "

        """
        Procesamos decenas y unidades
        """
        if numero >= 20:
            texto += f"{decenas[numero // 10]}"
            numero %= 10
            if numero > 0:
                texto += f" y {unidades[numero]}"
        elif numero >= 10:
            texto += f"{diez_a_diecinueve[numero - 10]}"
        elif numero > 0:
            """
            Regla especial: si el número es 1, y es lo único, o viene después de "mil", se dice "un"
            """
            if numero == 1 and (texto == "" or texto.endswith("mil ")):
                texto += "un"
            else:
                texto += f"{unidades[numero]}"

        """
        Añadimos la palabra "pesos" si está habilitado el flag
        """
        if agregar_pesos:
            texto += " pesos"

        return texto.strip()

    except Exception as e:
        """
        Si algo falla en el proceso (por ejemplo si no se puede convertir el número), se devuelve un valor genérico
        """
        return "No válido"
