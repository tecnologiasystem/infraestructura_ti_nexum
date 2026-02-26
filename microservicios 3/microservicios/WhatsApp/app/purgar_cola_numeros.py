"""
Script simple para purgar (vaciar) la cola de números disponibles.
"""
import os
import asyncio
import aio_pika

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://developmentit:Bogotacolombia2025+@localhost:5672/")
RABBIT_NUMEROS_QUEUE = os.getenv("RABBIT_NUMEROS_QUEUE", "whatsapp.numeros.disponibles")


async def purgar_cola():
    """
    Elimina todos los mensajes de la cola de números disponibles.
    """
    print("🔗 Conectando a RabbitMQ...")
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    
    try:
        # Declarar la cola
        queue = await ch.declare_queue(RABBIT_NUMEROS_QUEUE, durable=True)
        
        # Purgar (eliminar todos los mensajes)
        result = await queue.purge()
        
        print(f"✅ Se eliminaron {result.message_count} mensajes de la cola '{RABBIT_NUMEROS_QUEUE}'")
        print("   La cola ahora está vacía y lista para nuevos números")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print("🔌 Conexión cerrada")


if __name__ == "__main__":
    print("🗑️  PURGAR COLA DE NÚMEROS")
    print("="*60)
    asyncio.run(purgar_cola())
