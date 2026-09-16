import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.retrive import count_chunks, retrieve
from app.schemas import (
    ChunkCountRequest,
    ChunkCountResponse,
    RetrievalRequest,
    RetrievalResponse,
)


app = FastAPI(
    title="RAG Retrieval Service"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:4173",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post("/documents/chunk-counts", response_model=ChunkCountResponse)
def document_chunk_counts(
    request: ChunkCountRequest
):
    return {
        "counts": count_chunks(request.document_ids)
    }