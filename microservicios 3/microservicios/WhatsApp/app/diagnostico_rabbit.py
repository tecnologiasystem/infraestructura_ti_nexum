"""
Script para diagnosticar y limpiar colas de RabbitMQ.
Útil cuando tienes múltiples colas o configuraciones incorrectas.
"""
import os
import asyncio
import aio_pika
from dotenv import load_dotenv

load_dotenv()

RABBIT_URL = os.getenv("RABBIT_URL")

async def diagnosticar_rabbitmq():
    """
    Conecta a RabbitMQ y muestra información de todas las colas y exchanges.
    """
    print("🔗 Conectando a RabbitMQ...")
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    
    try:
        print("\n" + "="*60)
        print("📊 DIAGNÓSTICO DE RABBITMQ")
        print("="*60)
        
        # Intentar obtener información de las colas principales
        colas_a_revisar = [
            "whatsapp.resultados.q",
            "whatsapp.resultados.dlq",
            "whatsapp.numeros.disponibles"
        ]
        
        print("\n📬 COLAS:")
        for nombre_cola in colas_a_revisar:
            try:
                # Declarar cola pasivamente (solo verifica si existe)
                queue = await ch.declare_queue(nombre_cola, durable=True, passive=False)
                info = await queue.declare()
                print(f"\n   ✅ {nombre_cola}")
                print(f"      - Mensajes: {info.message_count}")
                print(f"      - Consumidores: {info.consumer_count}")
            except Exception as e:
                print(f"\n   ❌ {nombre_cola}: {e}")
        
        # Verificar exchanges
        exchanges_a_revisar = [
            "whatsapp.resultados",
            "whatsapp.resultados.dlx"
        ]
        
        print("\n\n📦 EXCHANGES:")
        for nombre_exchange in exchanges_a_revisar:
            try:
                exchange = await ch.declare_exchange(
                    nombre_exchange, 
                    aio_pika.ExchangeType.DIRECT, 
                    durable=True,
                    passive=False
                )
                print(f"   ✅ {nombre_exchange} (tipo: DIRECT)")
            except Exception as e:
                print(f"   ❌ {nombre_exchange}: {e}")
        
        print("\n" + "="*60)
        
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")


async def purgar_cola(nombre_cola: str):
    """
    Elimina todos los mensajes de una cola específica.
    """
    print(f"🔗 Conectando a RabbitMQ...")
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    
    try:
        queue = await ch.get_queue(nombre_cola)
        result = await queue.purge()
        print(f"✅ Se eliminaron {result.message_count} mensajes de la cola '{nombre_cola}'")
    except Exception as e:
        print(f"❌ Error al purgar cola: {e}")
    finally:
        await conn.close()
        print("🔌 Conexión cerrada")


async def ver_mensajes_sin_consumir(nombre_cola: str, max_mensajes: int = 10):
    """
    Muestra los primeros mensajes de una cola sin eliminarlos.
    """
    print(f"🔗 Conectando a RabbitMQ...")
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    
    try:
        queue = await ch.get_queue(nombre_cola)
        
        print(f"\n📬 Primeros {max_mensajes} mensajes en '{nombre_cola}':\n")
        
        for i in range(max_mensajes):
            message = await queue.get(timeout=1.0, fail=False)
            if not message:
                print(f"   (No hay más mensajes)")
                break
            
            body = message.body.decode("utf-8")
            print(f"   Mensaje {i+1}:")
            print(f"   {body}\n")
            
            # IMPORTANTE: No hacer ACK para que el mensaje vuelva a la cola
            await message.reject(requeue=True)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()
        print("\n🔌 Conexión cerrada")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python diagnostico_rabbit.py diagnosticar")
        print("  python diagnostico_rabbit.py purgar <nombre_cola>")
        print("  python diagnostico_rabbit.py ver <nombre_cola> [max_mensajes]")
        sys.exit(1)
    
    comando = sys.argv[1]
    
    if comando == "diagnosticar":
        asyncio.run(diagnosticar_rabbitmq())
    
    elif comando == "purgar":
        if len(sys.argv) < 3:
            print("❌ Debes especificar el nombre de la cola")
            sys.exit(1)
        nombre_cola = sys.argv[2]
        asyncio.run(purgar_cola(nombre_cola))
    
    elif comando == "ver":
        if len(sys.argv) < 3:
            print("❌ Debes especificar el nombre de la cola")
            sys.exit(1)
        nombre_cola = sys.argv[2]
        max_mensajes = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        asyncio.run(ver_mensajes_sin_consumir(nombre_cola, max_mensajes))
    
    else:
        print(f"❌ Comando desconocido: {comando}")
        sys.exit(1)
