"""
Script para eliminar y recrear las colas de RabbitMQ con la configuración correcta.
Ejecuta este script SOLO si el worker_resultados.py sigue fallando.
"""
import os
import asyncio
import aio_pika

RABBIT_URL = os.getenv("RABBIT_URL")
QUEUE      = os.getenv("RABBIT_QUEUE", "whatsapp.resultados.q")
DLX        = os.getenv("RABBIT_DLX", "whatsapp.resultados.dlx")
DLQ        = os.getenv("RABBIT_DLQ", "whatsapp.resultados.dlq")

async def reset_queues():
    """
    Elimina y recrea las colas de RabbitMQ con la configuración correcta.
    """
    print("🔗 Conectando a RabbitMQ...")
    conn = await aio_pika.connect_robust(RABBIT_URL)
    ch = await conn.channel()
    
    try:
        # Eliminar cola principal si existe
        print(f"🗑️  Eliminando cola: {QUEUE}")
        try:
            queue = await ch.get_queue(QUEUE)
            await queue.delete(if_unused=False, if_empty=False)
            print(f"✅ Cola {QUEUE} eliminada")
        except Exception as e:
            print(f"⚠️  Cola {QUEUE} no existe o ya fue eliminada: {e}")
        
        # Eliminar DLQ si existe
        print(f"🗑️  Eliminando DLQ: {DLQ}")
        try:
            dlq = await ch.get_queue(DLQ)
            await dlq.delete(if_unused=False, if_empty=False)
            print(f"✅ DLQ {DLQ} eliminada")
        except Exception as e:
            print(f"⚠️  DLQ {DLQ} no existe o ya fue eliminada: {e}")
        
        # Eliminar DLX si existe
        print(f"🗑️  Eliminando DLX: {DLX}")
        try:
            await ch.exchange_delete(DLX)
            print(f"✅ DLX {DLX} eliminado")
        except Exception as e:
            print(f"⚠️  DLX {DLX} no existe o ya fue eliminado: {e}")
        
        # Recrear todo con la configuración correcta
        print(f"\n📦 Recreando infraestructura...")
        
        # 1. Declarar DLX (tipo DIRECT)
        dlx = await ch.declare_exchange(DLX, aio_pika.ExchangeType.DIRECT, durable=True)
        print(f"✅ DLX creado: {DLX} (tipo: DIRECT)")
        
        # 2. Declarar DLQ y vincularla al DLX con routing_key
        dlq = await ch.declare_queue(DLQ, durable=True)
        await dlq.bind(dlx, routing_key=QUEUE)
        print(f"✅ DLQ creada y vinculada: {DLQ}")
        
        # 3. Declarar cola principal con DLX configurado
        queue = await ch.declare_queue(
            QUEUE,
            durable=True,
            arguments={"x-dead-letter-exchange": DLX}
        )
        print(f"✅ Cola principal creada: {QUEUE}")
        
        print(f"\n🎉 ¡Configuración completada exitosamente!")
        print(f"   - Cola principal: {QUEUE}")
        print(f"   - DLX: {DLX}")
        print(f"   - DLQ: {DLQ}")
        
    finally:
        await conn.close()
        print("🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(reset_queues())
