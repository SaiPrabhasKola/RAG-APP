from minio import Minio

from app.config import settings

client = Minio(
    settings.minio_endpoint,
    access_key= settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False
)

def get_pdf(obj_key:str)->bytes:
    response = client.get_object(
        settings.minio_bucket,
        obj_key
    )

    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()