import json
import uuid

import pika

from app.config import settings
from app.embedd import embed_document
from app.qdrant import ensure_collection, upsert_chunk


def process_message(channel, method, properties, body):
    message = json.loads(body)

    document_id = message["document_id"]
    page_number = message["page_number"]
    chunk_index = message["chunk_index"]
    section = message.get("section")
    subsection = message.get("subsection")
    text = message["text"]

    print(
        f"Received chunk {chunk_index} "
        f"from document {document_id}"
    )

    vector = embed_document(text)

    point_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{document_id}:{page_number}:{chunk_index}"
        )
    )

    payload = {
        "document_id": document_id,
        "page_number": page_number,
        "chunk_index": chunk_index,
        "section": section,
        "subsection": subsection,
        "text": text,
    }

    upsert_chunk(
        point_id=point_id,
        vector=vector,
        payload=payload,
    )

    print(
        f"Stored chunk {chunk_index} "
        f"in Qdrant ({len(vector)}D)"
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
        queue="document.embed",
        durable=True
    )

    ensure_collection()

    channel.basic_consume(
        queue="document.embed",
        on_message_callback=process_message,
        auto_ack=False
    )

    print("Embedding Service started")
    print("Waiting for messages...")

    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()