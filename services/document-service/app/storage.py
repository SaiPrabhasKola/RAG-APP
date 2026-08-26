from minio import Minio

from app.config import settings


client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=False,
)


def ensure_bucket(bucket_name: str):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


def upload_file(
    bucket_name: str,
    object_name: str,
    file_path: str,
):
    ensure_bucket(bucket_name)

    client.fput_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=file_path,
    )

def upload_document(
    file_data,
    object_name: str,
    content_type: str,
):
    ensure_bucket(settings.minio_bucket)

    client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=object_name,
        data=file_data,
        length=-1,
        part_size=10 * 1024 * 1024,
        content_type=content_type,
    )