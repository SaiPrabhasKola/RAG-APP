from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    rabbitmq_url:str = "amqp://rag:rag@localhost:5672/"
    qdrant_url: str = "http://localhost:6333"


settings = Settings()