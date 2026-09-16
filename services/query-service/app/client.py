import asyncio

from fastapi import HTTPException
import httpx

from app.config import settings


async def request_with_retry(
    method: str,
    url: str,
    json: dict,
    max_attempts: int = 3,
):
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.request(
                    method,
                    url,
                    json=json,
                )
                response.raise_for_status()
                return response

        except (httpx.TimeoutException, httpx.RequestError) as exc:
            if attempt == max_attempts - 1:
                raise exc

            await asyncio.sleep(0.5 * (2 ** attempt))

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500 and attempt < max_attempts - 1:
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue

            raise

async def retrive_documents(
        query:str,
        top_k:int,
        document_id:str | None = None
)->list[dict]:
    payload = {
        "query": query,
        "top_k": top_k,
        "document_id": document_id
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            
            response = await request_with_retry(
                "POST",
                f"{settings.retrieval_service_url}/retrieve",
                json=payload
            )
        
            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Retrieval service timed out"
        )
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="Retrieval service returned an error"
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to retrieval service"
        )


       
    return data["results"]

async def generate_answer(
    query: str,
    sources: list[dict]
) -> dict:

    payload = {
        "query": query,
        "sources": sources
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await request_with_retry(
            "POST",
            f"{settings.generation_service_url}/generate",
            json=payload
        )

        response.raise_for_status()

        return response.json()

    except httpx.TimeoutException:
        raise HTTPException(
        status_code=504,
        detail="Generation service timed out"
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
        status_code=502,
        detail="Generation service returned an error"
        )

    except httpx.RequestError:
        raise HTTPException(
        status_code=502,
        detail="Could not connect to generation service"
        )