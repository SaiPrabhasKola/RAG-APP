from google import genai

from app.config import settings

client = genai.Client(api_key=settings.gemini_api_key)

async def generate_answer(prompt:str):
    response = await client.aio.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text