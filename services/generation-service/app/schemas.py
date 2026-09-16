from pydantic import BaseModel

class Source(BaseModel):
    id:int
    document_id: str
    page_number:int
    chunk_index:int
    text:str
    score:float
    rerank_score:float


class GenerationRequest(BaseModel):
    query: str
    sources: list[Source]


class GenerationResponse(BaseModel):
    query:str
    answer:str
    sources:list[Source]