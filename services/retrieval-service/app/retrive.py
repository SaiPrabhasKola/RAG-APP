from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.config import settings
from app.embedd import embed_query
from app.reranker import rerank


client = QdrantClient(
    url=settings.qdrant_url
)

COLLECTION_NAME = "document_chunks"

MAX_COUNT_IDS = 100


def retrieve(
    query: str,
    top_k: int = 5,
    document_id: str | None = None
) -> list[dict]:

    query_vector = embed_query(query)

    query_filter = None

    if document_id:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )

    candidates = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=max(top_k * 4, 20),
        with_payload=True
    ).points

    candidate_chunks = [
        {
            "score": result.score,
            "document_id": result.payload["document_id"],
            "page_number": result.payload["page_number"],
            "chunk_index": result.payload["chunk_index"],
            "text": result.payload["text"]
        }
        for result in candidates
    ]

    return rerank(
        query,
        candidate_chunks,
        top_k=top_k
    )


def count_chunks(document_ids: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}

    for document_id in document_ids[:MAX_COUNT_IDS]:
        try:
            counts[document_id] = client.count(
                collection_name=COLLECTION_NAME,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                exact=True
            ).count
        except Exception as exc:
            # Report 0 rather than failing the whole request: 0 means
            # "not known to be searchable", which is the safe default.
            print(f"chunk count failed for {document_id}: {exc}")
            counts[document_id] = 0

    return counts