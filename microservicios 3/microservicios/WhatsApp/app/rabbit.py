import os, aio_pika

_state = {"conn": None, "channel": None, "exchange": None}

async def rabbit_connect():
    url = os.getenv("RABBIT_URL")
    ex = os.getenv("RABBIT_EXCHANGE", "whatsapp.resultados")
    prefetch = int(os.getenv("RABBIT_PREFETCH", "1"))

    conn = await aio_pika.connect_robust(url)
    ch = await conn.channel()
    await ch.set_qos(prefetch_count=prefetch)

    exchange = await ch.declare_exchange(
        ex, type=aio_pika.ExchangeType.DIRECT, durable=True
    )
    _state.update(conn=conn, channel=ch, exchange=exchange)

async def rabbit_close():
    if _state["conn"]:
        await _state["conn"].close()

async def rabbit_publish(routing_key: str, body: bytes, headers: dict | None = None):
    if not _state["exchange"]:
        raise RuntimeError("RabbitMQ no conectado")
    msg = aio_pika.Message(
        body=body,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        headers=headers or {},
    )
    await _state["exchange"].publish(msg, routing_key=routing_key)

# =========================
# NUEVA: Cola de números disponibles
# =========================
async def rabbit_publish_to_queue(queue_name: str, body: bytes, headers: dict | None = None):
    """
    Publica un mensaje directamente a una cola (sin exchange).
    Usado para la cola de números disponibles.
    """
    if not _state["channel"]:
        raise RuntimeError("RabbitMQ no conectado")
    
    # Declarar la cola como durable
    queue = await _state["channel"].declare_queue(queue_name, durable=True)
    
    msg = aio_pika.Message(
        body=body,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        headers=headers or {},
    )
    await _state["channel"].default_exchange.publish(msg, routing_key=queue_name)

async def rabbit_consume_from_queue(queue_name: str, timeout: float = 5.0):
    """
    Consume un único mensaje de la cola especificada.
    Retorna el mensaje si existe, o None si no hay mensajes disponibles.
    
    Args:
        queue_name: Nombre de la cola
        timeout: Tiempo máximo de espera en segundos
    """
    if not _state["channel"]:
        raise RuntimeError("RabbitMQ no conectado")
    
    # Declarar la cola (si no existe)
    queue = await _state["channel"].declare_queue(queue_name, durable=True)
    
    try:
        # Obtener un mensaje con timeout
        message = await queue.get(timeout=timeout, fail=False)
        if message:
            await message.ack()  # Confirmar que se procesó
            return message.body.decode("utf-8")
        return None
    except Exception:
        return None
