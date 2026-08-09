import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus, DocumentType


class DocumentVerifyRequest(BaseModel):
    status: DocumentStatus = Field(description="Must be 'verified' or 'rejected'.")
    notes: str | None = Field(default=None, max_length=2000)


class DocumentOut(BaseModel):
    """
    List/summary view — deliberately excludes ocr_raw_text and
    ocr_extracted_fields to minimize exposure surface on bulk-listing
    requests. Use DocumentDetailOut for the single-document view.
    """
    id: uuid.UUID
    loan_application_id: uuid.UUID
    document_type: DocumentType
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    ocr_confidence: float | None = None
    uploaded_at: datetime
    verified_by: uuid.UUID | None = None
    verifier_name: str | None = None
    verified_at: datetime | None = None
    verification_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailOut(DocumentOut):
    ocr_raw_text: str | None = None
    ocr_extracted_fields: dict | None = None
    ocr_error_message: str | None = None