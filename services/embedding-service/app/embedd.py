from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-base-en-v1.5"

model = SentenceTransformer(MODEL_NAME)


def embed_document(text: str) -> list[float]:
    vector = model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()