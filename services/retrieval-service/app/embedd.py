from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-base-en-v1.5"

model = SentenceTransformer(MODEL_NAME)


def embed_query(query: str) -> list[float]:
    query = (
        "Represent this sentence for searching relevant passages: "
        + query
    )

    vector = model.encode(
        query,
        normalize_embeddings=True
    )

    return vector.tolist()