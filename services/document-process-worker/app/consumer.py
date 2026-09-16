import json
import time

import pika

import traceback

from app.config import settings
from app.reporter import report_status
from app.storage import get_pdf
from app.extractor import extract_text
from app.chunker import chunk_pages

CONNECT_ATTEMPTS = 10
CONNECT_RETRY_DELAY = 3.0


def _reason(exc):
    inner = exc.args[0] if exc.args else exc
    return getattr(inner, "exception", None) or inner


def connect(parameters, attempts=CONNECT_ATTEMPTS, delay=CONNECT_RETRY_DELAY):
    for attempt in range(1, attempts + 1):
        try:
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError as exc:
            if attempt == attempts:
                raise
            print(
                f"rabbitmq connection failed (attempt {attempt}/{attempts}): "
                f"{_reason(exc)} - retrying in {delay}s"
            )
            time.sleep(delay)


def process_message(channel, method, props, body):
    document_id = None

    try:
        message = json.loads(body)

        document_id = message["document_id"]
        object_key = message["object_key"]

        print(f"received doc: {document_id}")
        print(f"received obj: {object_key}")

        report_status(document_id, "processing")

        pdf_data = get_pdf(object_key)

        pages = extract_text(pdf_data)

        chunks = chunk_pages(pages)

        print(f"\ncreated {len(chunks)} chunks")

        for chunk in chunks:

            embedding_message = {
                "document_id": document_id,
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "section": chunk["section"],
                "subsection": chunk["subsection"],
                "text": chunk["text"],
            }

            channel.basic_publish(
                exchange="",
                routing_key="document.embed",
                body=json.dumps(embedding_message),
                properties=pika.BasicProperties(
                    delivery_mode=2
                )
            )

        if not chunks:
            # Terminal: nothing to embed, so this document will never be
            # searchable. Report it rather than leaving it "processing".
            report_status(document_id, "empty")

        channel.basic_ack(
            delivery_tag=method.delivery_tag
        )

        print(f"document processed successfully: {document_id}")

    except Exception as exc:
        print(f"document processing failed: {exc}")
        traceback.print_exc()

        if document_id:
            report_status(document_id, "failed")

        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=True
        )


def start_consumer():
    parameters = pika.URLParameters(settings.rabbitmq_url)

    connection = connect(parameters)

    channel = connection.channel()

    # -------------------------
    # Declare queues
    # -------------------------
    channel.queue_declare(
        queue="document.process",
        durable=True
    )

    channel.queue_declare(
        queue="document.embed",
        durable=True
    )

    # -------------------------
    # Consume processed documents
    # -------------------------
    channel.basic_consume(
        queue="document.process",
        on_message_callback=process_message,
        auto_ack=False
    )

    print("Document Process Worker started")
    print("Waiting for messages...")

    channel.start_consuming()