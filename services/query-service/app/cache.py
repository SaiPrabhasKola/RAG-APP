import json
import hashlib

import redis.asyncio as redis

from app.config import settings

client = redis.from_url(
    settings.redis_url,
    decode_responses= True,
    protocol=2
)
async def get_cached_result(key:str):
    data = await client.get(key)

    print("SETTING CACHE:", key)

    if data is None:
        return None

    return json.loads(data)

async def set_cached_result(key:str, data:dict,ttl:int = 300):
    await client.set(
        key,
        json.dumps(data),
        ex=ttl
    )

def build_cache_key(
    query: str,
    document_id: str | None,
    top_k: int
) -> str:

    normalized_query = " ".join(query.lower().split())

    raw_key = f"{normalized_query}:{document_id}:{top_k}"

    query_hash = hashlib.sha256(
        raw_key.encode()
    ).hexdigest()

    return f"query:{query_hash}"