from pydoc import text

from sentence_transformers import CrossEncoder

MODEL_NAME = "BAAI/bge-reranker-base"

model = CrossEncoder(MODEL_NAME)

def rerank(
    query:str,
    candidates:list[dict],
    top_k:int=5,
)->list[dict]:
    pairs = [
    [query, candidate["text"]]
    for candidate in candidates
]

    scores = model.predict(pairs)

    ranked = []

    for candidate,score in zip(candidates,scores):
        result = candidate.copy()
        result["rerank_score"] = float(score)
        ranked.append(result)

    ranked.sort(
        key=lambda result: result["rerank_score"],
        reverse=True
    )

    return ranked[:top_k]