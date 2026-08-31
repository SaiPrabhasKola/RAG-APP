from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import settings

client = QdrantClient(
    url=settings.qdrant_url
)

COLLECTION_NAME = "document_chunks"
VECTOR_SIZE = 768

def ensure_collection():
    collections = client.get_collections().collections

    exists = any(
        collection.name == COLLECTION_NAME
        for collection in collections
    )

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )
        print(f"Created Qdrant collection: {COLLECTION_NAME}")

def upsert_chunk(
    point_id:str,
    vector:list[float],
    payload:dict
):
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
        ]
    )