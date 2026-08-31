from fastapi import FastAPI

from app.retrive import retrieve
from app.schemas import RetrievalRequest, RetrievalResponse


app = FastAPI(
    title="RAG Retrieval Service"
)


@app.post("/retrieve", response_model=RetrievalResponse)
def retrieve_documents(
    request: RetrievalRequest
):

    results = retrieve(
        query=request.query,
        top_k=request.top_k,
        document_id=request.document_id
    )

    return {
        "results": results
    }