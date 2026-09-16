from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    rabbitmq_url:str = "amqp://rag:rag@localhost:5672/"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "ragadmin"
    minio_secret_key: str = "ragpassword"
    minio_bucket: str = "documents"
    document_service_url: str = "http://localhost:8000"


settings = Settings()
