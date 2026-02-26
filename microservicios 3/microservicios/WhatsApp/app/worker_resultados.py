import os, json, asyncio, aio_pika, logging
from datetime import datetime
from bll.numero_bll import ResultadoWhatsAppModel, procesar_resultado_automatizacionWhatsApp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

RABBIT_URL = os.getenv("RABBIT_URL")
EXCHANGE   = os.getenv("RABBIT_EXCHANGE", "whatsapp.resultados")
ROUTING_KEY= os.getenv("RABBIT_ROUTING_KEY", "result")
QUEUE      = os.getenv("RABBIT_QUEUE", "whatsapp.resultados.q")
DLX        = os.getenv("RABBIT_DLX", "whatsapp.resultados.dlx")
DLQ        = os.getenv("RABBIT_DLQ", "whatsapp.resultados.dlq")
PREFETCH   = int(os.getenv("RABBIT_PREFETCH", "1"))
MAX_RETRIES= int(os.getenv("RABBIT_MAX_RETRIES", "3"))

# Contador de mensajes procesados (se resetea cada vez que inicia el worker)
mensaje_count = 0

async def handle_message(message: aio_pika.IncomingMessage):
    global mensaje_count
    mensaje_count += 1
    msg_id = mensaje_count
    
    async with message.process(requeue=False):
        inicio = datetime.now()
        try:
            payload = json.loads(message.body.decode("utf-8"))
            logger.info(f"[MSG #{msg_id}] 📩 Recibido: {payload}")
            
            data = ResultadoWhatsAppModel(**payload)
            logger.info(f"[MSG #{msg_id}] ✅ Validado: indicativo={data.indicativo}, numero={data.numero}, tiene_whatsApp={data.tiene_whatsApp}")
            
            logger.info(f"[MSG #{msg_id}] 💾 Guardando en BD...")
            ok = procesar_resultado_automatizacionWhatsApp(data)
            
            duracion = (datetime.now() - inicio).total_seconds()
            
            if ok:
                logger.info(f"[MSG #{msg_id}] ✅ ÉXITO - Procesado en {duracion:.2f}s")
            else:
                logger.warning(f"[MSG #{msg_id}] ⚠️ FALLO - No se pudo guardar en {duracion:.2f}s")
                
        except Exception as e:
            duracion = (datetime.now() - inicio).total_seconds()
            logger.error(f"[MSG #{msg_id}] ❌ ERROR - {str(e)} (después de {duracion:.2f}s)")
            import traceback
            logger.error(f"[MSG #{msg_id}] 📜 Traceback:\n{traceback.format_exc()}")
            raise

async def main():
    try:
        logger.info("="*60)
        logger.info("🚀 INICIANDO WORKER DE RESULTADOS")
        logger.info("="*60)
        logger.info(f"📊 Contador de mensajes: INICIADO EN 0")
        logger.info(f"")
        logger.info(f"⚙️  CONFIGURACIÓN:")
        logger.info(f"   📦 Exchange: {EXCHANGE}")
        logger.info(f"   🔑 Routing Key: {ROUTING_KEY}")
        logger.info(f"   📬 Cola principal: {QUEUE}")
        logger.info(f"   💀 DLX: {DLX}")
        logger.info(f"   🪦 DLQ: {DLQ}")
        logger.info(f"   🔢 Prefetch: {PREFETCH}")
        logger.info(f"   🔁 Max Retries: {MAX_RETRIES}")
        logger.info(f"")
        
        conn = await aio_pika.connect_robust(RABBIT_URL)
        ch = await conn.channel()
        await ch.set_qos(prefetch_count=PREFETCH)
        
        dlx = await ch.declare_exchange(DLX, aio_pika.ExchangeType.DIRECT, durable=True)
        logger.info(f"✅ DLX declarado: {DLX}")
        
        dlq = await ch.declare_queue(DLQ, durable=True)
        await dlq.bind(dlx, routing_key=QUEUE)
        logger.info(f"✅ DLQ declarada y vinculada: {DLQ}")
        
        exchange = await ch.declare_exchange(EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)
        logger.info(f"✅ Exchange principal declarado: {EXCHANGE}")
        
        queue = await ch.declare_queue(QUEUE, durable=True, arguments={"x-dead-letter-exchange": DLX})
        logger.info(f"✅ Cola principal declarada: {QUEUE}")
        
        await queue.bind(exchange, routing_key=ROUTING_KEY)
        logger.info(f"✅ Cola vinculada al exchange con routing_key: {ROUTING_KEY}")
        
        info = await queue.declare()
        logger.info(f"")
        logger.info(f"📊 Estado de la cola:")
        logger.info(f"   📨 Mensajes pendientes: {info.message_count}")
        logger.info(f"   👥 Consumidores activos: {info.consumer_count}")
        logger.info(f"")
        
        await queue.consume(handle_message)
        logger.info("="*60)
        logger.info("✅ WORKER LISTO - Esperando mensajes...")
        logger.info("="*60)
        logger.info("")
        
        await asyncio.Future()
        
    except Exception as e:
        logger.error(f"❌ Error fatal al iniciar worker: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    asyncio.run(main())
