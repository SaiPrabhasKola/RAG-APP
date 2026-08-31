from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    qdrant_url:str = "http://localhost:6333"

settings = Settings()