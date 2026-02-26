"""
Script de prueba para verificar el sistema de cola de números.
Simula múltiples máquinas consumiendo números simultáneamente.
"""
import asyncio
import aiohttp
import time
from collections import defaultdict

API_URL = "http://localhost:8000"  # Ajusta según tu configuración
NUM_MAQUINAS = 15  # Simula 15 máquinas
NUMEROS_POR_MAQUINA = 10  # Cada máquina intenta obtener 10 números


async def consumir_numeros(session, maquina_id, resultados):
    """Simula una máquina consumiendo números."""
    numeros_obtenidos = []
    
    for i in range(NUMEROS_POR_MAQUINA):
        try:
            async with session.get(f"{API_URL}/automatizacionWhatsApp/porNumero") as response:
                if response.status == 200:
                    data = await response.json()
                    numero = data.get("numero")
                    numeros_obtenidos.append(numero)
                    print(f"✅ Máquina {maquina_id}: obtuvo número {numero}")
                elif response.status == 404:
                    print(f"⚠️  Máquina {maquina_id}: no hay más números disponibles")
                    break
                else:
                    print(f"❌ Máquina {maquina_id}: error {response.status}")
        except Exception as e:
            print(f"❌ Máquina {maquina_id}: excepción - {e}")
        
        # Pequeña pausa para simular procesamiento
        await asyncio.sleep(0.1)
    
    resultados[maquina_id] = numeros_obtenidos


async def main():
    print("🚀 Iniciando prueba de sistema de cola")
    print(f"   - Simulando {NUM_MAQUINAS} máquinas")
    print(f"   - Cada máquina intenta obtener {NUMEROS_POR_MAQUINA} números")
    print(f"   - Total esperado: {NUM_MAQUINAS * NUMEROS_POR_MAQUINA} números\n")
    
    inicio = time.time()
    resultados = {}
    
    async with aiohttp.ClientSession() as session:
        # Crear tareas para todas las máquinas (concurrencia)
        tareas = [
            consumir_numeros(session, maquina_id, resultados)
            for maquina_id in range(1, NUM_MAQUINAS + 1)
        ]
        
        # Ejecutar todas las tareas en paralelo
        await asyncio.gather(*tareas)
    
    fin = time.time()
    
    # Análisis de resultados
    print("\n" + "="*60)
    print("📊 RESULTADOS DE LA PRUEBA")
    print("="*60)
    
    total_obtenidos = sum(len(nums) for nums in resultados.values())
    todos_los_numeros = [num for nums in resultados.values() for num in nums]
    numeros_unicos = set(todos_los_numeros)
    duplicados = len(todos_los_numeros) - len(numeros_unicos)
    
    print(f"\n✅ Números obtenidos: {total_obtenidos}")
    print(f"✅ Números únicos: {len(numeros_unicos)}")
    print(f"{'❌' if duplicados > 0 else '✅'} Duplicados encontrados: {duplicados}")
    print(f"⏱️  Tiempo total: {fin - inicio:.2f} segundos")
    print(f"📈 Velocidad: {total_obtenidos / (fin - inicio):.2f} números/segundo")
    
    # Distribución por máquina
    print("\n📋 Distribución por máquina:")
    for maquina_id in sorted(resultados.keys()):
        nums = resultados[maquina_id]
        print(f"   Máquina {maquina_id:2d}: {len(nums):3d} números")
    
    # Verificar duplicados
    if duplicados > 0:
        print(f"\n❌ ¡ATENCIÓN! Se encontraron {duplicados} números duplicados:")
        contador = defaultdict(int)
        for num in todos_los_numeros:
            contador[num] += 1
        
        for num, count in contador.items():
            if count > 1:
                print(f"   - Número {num}: {count} veces")
    else:
        print("\n✅ ¡PERFECTO! No se encontraron duplicados")
        print("   El sistema de cola está funcionando correctamente")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Prueba interrumpida por el usuario")
