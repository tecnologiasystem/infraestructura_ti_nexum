# Plantilla Excel para WhatsApp RPA

## Ubicación del archivo:
C:\WhatsApp\numeros.xlsx

## Estructura del Excel:

| Indicativo | Numero     | Resultado | FechaValidacion      |
|------------|------------|-----------|----------------------|
| +57        | 3001234567 |           |                      |
| +57        | 3109876543 |           |                      |
| +1         | 5551234567 |           |                      |

## Columnas:

### A - Indicativo (String)
Código de país con el símbolo +
Ejemplos: +57, +1, +52, +34

### B - Numero (String)  
Número de teléfono sin espacios ni guiones
Ejemplos: 3001234567, 5551234567

### C - Resultado (String)
Será llenado por el RPA
Valores: "SI" o "NO"

### D - FechaValidacion (String)
Será llenado por el RPA
Formato: yyyy-MM-dd HH:mm:ss
Ejemplo: 2025-12-05 14:30:25

## Instrucciones:

1. Crear carpeta: C:\WhatsApp\
2. Guardar este archivo como: numeros.xlsx
3. Llenar solo las columnas A y B
4. Dejar C y D vacías
5. El RPA llenará automáticamente C y D

## Ejemplo de archivo listo:

Indicativo | Numero     | Resultado | FechaValidacion
+57        | 3001234567 |           |
+57        | 3109876543 |           |
+57        | 3152223333 |           |

