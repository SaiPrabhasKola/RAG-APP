from pydantic import BaseModel


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5
    document_id: str | None = None


class RetrievalResult(BaseModel):
    score: float
    rerank_score: float
    document_id: str
    page_number: int
    chunk_index: int
    text: str


class RetrievalResponse(BaseModel):
    results: list[RetrievalResult]