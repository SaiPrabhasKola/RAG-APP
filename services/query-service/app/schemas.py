from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    document_id: str | None= None

class Source(BaseModel):
    id:int
    document_id: str
    page_number:int
    chunk_index:int
    text: str
    score: float
    rerank_score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[Source]
