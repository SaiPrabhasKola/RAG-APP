import json

import pika

from app.config import settings


def publish_document_job(
        document_id: str,
        object_key: str
)->None:
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.rabbitmq_url)
    )
    channel = connection.channel()

    channel.queue_declare(
        queue="document.process",
        durable= True
    )

    message = {
        "document_id": document_id,
        "object_key": object_key
    }

    channel.basic_publish(
        exchange="",
        routing_key="document.process",
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,
        ),
    )

    connection.close()
