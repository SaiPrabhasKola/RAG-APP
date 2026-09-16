import os
import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.client import retrive_documents, generate_answer
from app.schemas import QueryRequest, QueryResponse, Source
from app.cache import (
    build_cache_key,
    get_cached_result,
    set_cached_result,
)


app = FastAPI(title="RAG Query Service")

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


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    print(f"[{request_id}] query started")

    cache_key = build_cache_key(
    query=request.query,
    document_id=request.document_id,
    top_k=request.top_k
    )
    cached_result = await get_cached_result(cache_key)

    if cached_result is not None:
        print(f"[{request_id}] cache HIT")
        elapsed = (time.perf_counter() - start_time) * 1000
        print(f"[{request_id}] query completed in {elapsed:.2f}ms")
        return cached_result

    print(f"[{request_id}] cache MISS")
    results = await retrive_documents(
        query=request.query,
        top_k=request.top_k,
        document_id=request.document_id
    )

    sources_with_ids = [
        {
            "id": index,
            **result
        }
        for index, result in enumerate(results, start=1)
    ]

    generation_result = await generate_answer(
        query=request.query,
        sources=sources_with_ids
    )

    sources = [Source(**result) for result in sources_with_ids]

    response =  {
        "query": request.query,
        "answer": generation_result["answer"],
        "sources": [source.model_dump() for source in sources]
    }

    await set_cached_result(
    cache_key,
    response
    )
    elapsed = (time.perf_counter() - start_time) * 1000
    print(f"[{request_id}] query completed in {elapsed:.2f}ms")

    return response