import json

import pika

from app.config import settings
from app.storage import get_pdf
from app.extractor import extract_text
from app.chunker import chunk_pages


def process_message(channel, method, props, body):
    message = json.loads(body)

    document_id = message["document_id"]
    object_key = message["object_key"]

    print(f"received doc: {document_id}")
    print(f"received obj: {object_key}")

    pdf_data = get_pdf(object_key)

    pages = extract_text(pdf_data)

    chunks = chunk_pages(pages)

    print(f"created {len(chunks)} chunks")

    for chunk_index, chunk in enumerate(chunks, start=1):

        embedding_message = {
            "document_id": document_id,
            "page_number": chunk["page_number"],
            "chunk_index": chunk_index,
            "text": chunk["text"]
        }

        channel.basic_publish(
            exchange="",
            routing_key="document.embed",
            body=json.dumps(embedding_message),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        print(
            f"sent chunk {chunk_index} "
            f"from page {chunk['page_number']} "
            f"to embedding queue"
        )

    channel.basic_ack(
        delivery_tag=method.delivery_tag
    )


def start_consumer():
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.rabbitmq_url)
    )

    channel = connection.channel()

    channel.queue_declare(
        queue="document.process",
        durable=True
    )

    channel.queue_declare(
        queue="document.embed",
        durable=True
    )

    channel.basic_consume(
        queue="document.process",
        on_message_callback=process_message,
        auto_ack=False
    )

    print("Document Process Worker started")
    print("Waiting for messages...")

    channel.start_consuming()