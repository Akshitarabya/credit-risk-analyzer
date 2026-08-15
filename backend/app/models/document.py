"""
Document model.

One document row per (loan_application_id, document_type) — the unique
constraint below enforces that re-uploading means delete-then-upload, not
ambiguous multiple "versions" of the same document type sitting around.

The actual file bytes are never stored here (or anywhere in the database) —
only a server-generated path reference + hash. See app/core/file_storage.py
for where the bytes actually live.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentType(str, enum.Enum):
    ID_PROOF = "id_proof"
    INCOME_PROOF = "income_proof"
    BANK_STATEMENT = "bank_statement"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    OCR_FAILED = "ocr_failed"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Document(Base):
    __tablename__ = "documents"

    __table_args__ = (
        UniqueConstraint(
            "loan_application_id",
            "document_type",
            name="uq_document_loan_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    loan_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loan_applications.id"),
        nullable=False,
        index=True,
    )

    document_type: Mapped[DocumentType] = mapped_column(
        Enum(
            DocumentType,
            name="document_type",
            native_enum=True,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
    )

    # File metadata.
    # original_filename is display-only and is NEVER used to build
    # a filesystem path.
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            name="document_status",
            native_enum=True,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        default=DocumentStatus.UPLOADED,
        index=True,
    )

    # --- OCR results ---

    ocr_raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ocr_extracted_fields: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    ocr_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    ocr_error_message: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    ocr_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- Upload / verification audit trail ---

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    verification_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    loan_application: Mapped["LoanApplication"] = relationship()

    uploader: Mapped["User"] = relationship(
        foreign_keys=[uploaded_by]
    )

    verifier: Mapped["User | None"] = relationship(
        foreign_keys=[verified_by]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Document id={self.id} "
            f"type={self.document_type} "
            f"status={self.status}>"
        )