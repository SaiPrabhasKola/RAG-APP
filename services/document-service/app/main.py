import os
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException,status,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import condecimal

from app.database import Base, engine, get_db
from app.models import Document
from app.publisher import publish_document_job
from app.schemas import DocumentStatusUpdate, DocumentSummary

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.storage import delete_document, upload_document

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Document Service"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:4173",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.post("/documents", status_code=status.HTTP_202_ACCEPTED)
def create_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    start_time = time.perf_counter()

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for now."
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required."
        )

    document_id = uuid.uuid4()

    object_key = f"documents/{document_id}/original_pdf"

    try:
        upload_document(
            file_data=file.file,
            object_name=object_key,
            content_type=file.content_type
        )

        document = Document(
            id=document_id,
            filename=file.filename,
            content_type=file.content_type,
            storage_key=object_key,
            size=0,
            status="uploaded"
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        publish_document_job(
            document_id=str(document_id),
            object_key=document.storage_key
        )

        elapsed = (time.perf_counter() - start_time) * 1000

        print(
            f"[{document_id}] upload completed "
            f"in {elapsed:.2f}ms"
        )

        return {
            "doc_id": str(document_id),
            "status": document.status
        }

    except SQLAlchemyError as exc:
        db.rollback()

        try:
            delete_document(object_key)
        except Exception:
            pass

        print(f"[{document_id}] database error: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document metadata."
        )

    except Exception as exc:
        db.rollback()

        try:
            delete_document(object_key)
        except Exception:
            pass

        print(f"[{document_id}] document upload failed: {exc}")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload or queue document."
        )


def to_summary(document: Document) -> DocumentSummary:
    return DocumentSummary(
        doc_id=str(document.id),
        filename=document.filename,
        content_type=document.content_type,
        size=document.size,
        status=document.status,
        created_at=document.created_at
    )


@app.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    documents = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [to_summary(document) for document in documents]


@app.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    document = db.get(Document, doc_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    storage_key = document.storage_key

    db.delete(document)
    db.commit()

    try:
        delete_document(storage_key)
    except Exception as exc:
        print(f"[{doc_id}] failed to remove object {storage_key}: {exc}")

    return None


@app.get("/documents/{doc_id}", response_model=DocumentSummary)
def get_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    document = db.get(Document, doc_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    return to_summary(document)


@app.patch("/documents/{doc_id}/status", response_model=DocumentSummary)
def update_document_status(
    doc_id: uuid.UUID,
    update: DocumentStatusUpdate,
    db: Session = Depends(get_db)
):
    document = db.get(Document, doc_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    previous = document.status
    document.status = update.status

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()

        print(f"[{doc_id}] status update failed: {exc}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update document status."
        )

    db.refresh(document)

    print(f"[{doc_id}] status {previous} -> {document.status}")

    return to_summary(document)