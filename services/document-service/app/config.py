from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/rag_db"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "ragadmin"
    minio_secret_key: str = "ragpassword"
    minio_bucket:str = "documents"

    rabbitmq_url:str = "amqp://rag:rag@localhost:5762/"

settings = Settings()