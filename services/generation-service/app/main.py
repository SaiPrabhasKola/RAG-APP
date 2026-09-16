import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.llm import generate_answer
from app.prompt import build_rag_prompt
from app.schemas import GenerationRequest,GenerationResponse

app = FastAPI(title="Rag Generation Service")

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

def build_context(sources)->str:
    context_parts = []

    for source in sources:
        context_parts.append(
            f"""Source:
[{source.id}]
Document_id: {source.document_id},
Page: {source.page_number},
Chunk: {source.chunk_index}


{source.text}
            """
        )
    return "\n\n----------------------\n\n".join(context_parts)


@app.post("/generate",response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    context = build_context(request.sources)

    prompt = build_rag_prompt(
        query=request.query,
        context=context
    )

    answer = await generate_answer(prompt)

    return GenerationResponse(
        query=request.query,
        answer=answer,
        sources=request.sources,
    )