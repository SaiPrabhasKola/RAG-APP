from fileinput import filename
import uuid

from fastapi import Depends, FastAPI, HTTPException,status,UploadFile,File
from pydantic import condecimal

from app.database import Base, engine, get_db
from app.models import Document

from sqlalchemy.orm import Session

from app.storage import upload_document
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Document Service"
) 

@app.get("/health")
def health():
    return{
        "status": "Ok"
    }

@app.get("/storage-health")
def storageHealth():
    from app.storage import client

    buckets = client.list_buckets()

    return {
        "status":"ok",
        "buckets": [bucket.name for bucket in buckets]
    }

@app.post("/documents",status_code=status.HTTP_202_ACCEPTED)
def create_document(file: UploadFile = File(...),db: Session =  Depends(get_db)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail= "only PDF is supported for now"
        )
    document_id = uuid.uuid4()
    object_key = (
        f"documents/{document_id}/original_pdf"
    )

    upload_document(
        file_data=file.file,
        object_name= object_key,
        content_type=file.content_type
    )

    document = Document(
        id = document_id,
        filename = file.filename,
        content_type = file.content_type,
        storage_key = object_key,
        size = 0,
        status = "uploaded"
    )

    db.add(document)

    db.commit()

    db.refresh(document)

    return {
        "doc_id" : str(document_id),
        "status": document.status
    }

