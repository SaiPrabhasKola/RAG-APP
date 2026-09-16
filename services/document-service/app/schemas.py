from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    content_type: str
    size: int
    status: str
    created_at: datetime


class DocumentStatusUpdate(BaseModel):
    status: Literal["processing", "empty", "failed"]
