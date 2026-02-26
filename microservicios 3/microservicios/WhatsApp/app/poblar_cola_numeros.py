"""
Script para poblar la cola de RabbitMQ con números disponibles.
Este script debe ejecutarse cada vez que se cargue un nuevo archivo Excel
o cuando se necesite repoblar la cola.
"""
import os
import sys
import asyncio
import json
import aio_pika
from dotenv import load_dotenv

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rabbit import rabbit_connect, rabbit_close, rabbit_publish_to_queue
from app.dal.numero_dal import obtener_detalles_pendientes_por_encabezado

load_dotenv()

RABBIT_NUMEROS_QUEUE = os.getenv("RABBIT_NUMEROS_QUEUE", "whatsapp.numeros.disponibles")


async def poblar_cola_numeros(id_encabezado: int = None):
    """
    Puebla la cola de RabbitMQ con todos los números disponibles.
    
    Args:
        id_encabezado: Si se especifica, solo agrega números de ese encabezado.
                       Si es None, agrega todos los números disponibles.
    """
    # Si se especificó un encabezado, usar el método optimizado
    if id_encabezado is not None:
        await poblar_cola_desde_encabezado(id_encabezado)
        return
    
    print("⚠️  Este método carga TODOS los números pendientes de TODOS los encabezados")
    print("⚠️  Para cargar un encabezado específico, usa: python poblar_cola_numeros.py --encabezado <ID>")
    
    # Por ahora, redirigir a usar --encabezado
    print("\n❌ Por favor especifica el ID del encabezado con --encabezado")
    return


async def obtener_numeros_en_cola():
    """
    Lee todos los números que están actualmente en la cola de RabbitMQ
    sin eliminarlos (usando basic_get con requeue=True).
    Retorna un set de números para comparación rápida.
    """
    numeros_en_cola = set()
    conn = await aio_pika.connect_robust(os.getenv("RABBIT_URL"))
    ch = await conn.channel()
    
    try:
        queue = await ch.declare_queue(RABBIT_NUMEROS_QUEUE, durable=True)
        
        # Leer todos los mensajes sin eliminarlos
        while True:
            message = await queue.get(timeout=1.0, fail=False)
            if not message:
                break
            
            try:
                body = message.body.decode("utf-8")
                data = json.loads(body)
                numero = data.get("numero", "")
                if numero:
                    numeros_en_cola.add(numero)
                
                # IMPORTANTE: Reencolar el mensaje (no eliminarlo)
                await message.reject(requeue=True)
            except:
                await message.reject(requeue=True)
        
    finally:
        await conn.close()
    
    return numeros_en_cola


async def poblar_cola_desde_encabezado(id_encabezado: int, force_reload: bool = False):
    """
    Puebla la cola solo con números de un encabezado específico.
    Solo carga los números que NO están ya en la cola (evita duplicados).
    
    Args:
        id_encabezado: ID del encabezado a procesar
        force_reload: Si es True, purga la cola y recarga todo
    """
    print(f"🔗 Conectando a RabbitMQ...")
    await rabbit_connect()
    
    try:
        # Verificar cuántos mensajes hay en la cola
        conn = await aio_pika.connect_robust(os.getenv("RABBIT_URL"))
        ch = await conn.channel()
        queue = await ch.declare_queue(RABBIT_NUMEROS_QUEUE, durable=True)
        info = await queue.declare()
        mensajes_en_cola = info.message_count
        await conn.close()
        
        print(f"📊 Mensajes actuales en cola: {mensajes_en_cola}")
        
        # Obtener números pendientes de la BD
        print(f"📦 Obteniendo números pendientes del encabezado {id_encabezado}...")
        detalles = obtener_detalles_pendientes_por_encabezado(id_encabezado)
        
        if not detalles:
            print("⚠️  No hay números pendientes para este encabezado")
            return
        
        print(f"📊 Se encontraron {len(detalles)} números pendientes en BD")
        
        # Si hay mensajes en cola y no es force_reload, obtener cuáles ya están
        numeros_a_cargar = detalles
        if mensajes_en_cola > 0 and not force_reload:
            print(f"🔍 Verificando cuáles números ya están en la cola...")
            numeros_en_cola = await obtener_numeros_en_cola()
            print(f"   📋 Números ya en cola: {len(numeros_en_cola)}")
            
            # Filtrar solo los que NO están en la cola
            numeros_a_cargar = [
                d for d in detalles 
                if d.get("numero", "") not in numeros_en_cola
            ]
            
            print(f"   ✅ Números nuevos a cargar: {len(numeros_a_cargar)}")
            
            if len(numeros_a_cargar) == 0:
                print("✅ Todos los números ya están en la cola. No hay nada que agregar.")
                return
        
        # Publicar solo los números faltantes
        print(f"🚀 Publicando {len(numeros_a_cargar)} números en la cola '{RABBIT_NUMEROS_QUEUE}'...")
        
        count = 0
        for detalle in numeros_a_cargar:
            mensaje = {
                "idEncabezado": id_encabezado,
                "indicativo": detalle.get("indicativo", ""),
                "numero": detalle.get("numero", "")
            }
            
            await rabbit_publish_to_queue(
                queue_name=RABBIT_NUMEROS_QUEUE,
                body=json.dumps(mensaje, ensure_ascii=False).encode("utf-8")
            )
            count += 1
            
            if count % 100 == 0:
                print(f"   ✅ {count}/{len(numeros_a_cargar)} números publicados...")
        
        print(f"✅ Se agregaron {count} números nuevos a la cola")
        print(f"📬 Total en cola ahora: ~{mensajes_en_cola + count} mensajes")
        print(f"📬 Las máquinas pueden consumir del encabezado {id_encabezado}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await rabbit_close()
        print("🔌 Conexión cerrada")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Poblar cola de números disponibles en RabbitMQ")
    parser.add_argument(
        "--encabezado", 
        type=int, 
        help="ID del encabezado específico (opcional)"
    )
    
    args = parser.parse_args()
    
    if args.encabezado:
        print(f"🎯 Poblando cola solo para encabezado {args.encabezado}")
        asyncio.run(poblar_cola_desde_encabezado(args.encabezado))
    else:
        print("🎯 Poblando cola con todos los números disponibles")
        asyncio.run(poblar_cola_numeros())
