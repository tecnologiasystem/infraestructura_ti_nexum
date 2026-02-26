import os, pika

url = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost:5672/")
exchange = os.getenv("RABBIT_EXCHANGE", "whatsapp.resultados")
routing_key = os.getenv("RABBIT_ROUTING_KEY", "result")
queue = os.getenv("RABBIT_QUEUE", "whatsapp.resultados.q")
dlx = os.getenv("RABBIT_DLX", "whatsapp.resultados.dlx")
dlq = os.getenv("RABBIT_DLQ", "whatsapp.resultados.dlq")

params = pika.URLParameters(url)
conn = pika.BlockingConnection(params)
ch = conn.channel()

# Exchanges
ch.exchange_declare(exchange=exchange, durable=True, exchange_type="direct")
ch.exchange_declare(exchange=dlx, durable=True, exchange_type="direct")

# DLQ
ch.queue_declare(queue=dlq, durable=True)
ch.queue_bind(queue=dlq, exchange=dlx, routing_key="dead")

# Principal con DLX
args = {
    "x-dead-letter-exchange": dlx,
    "x-dead-letter-routing-key": "dead",
}
ch.queue_declare(queue=queue, durable=True, arguments=args)
ch.queue_bind(queue=queue, exchange=exchange, routing_key=routing_key)

print("✅ RabbitMQ listo (exchange/colas declarados).")
conn.close()
