"""
Document service: the business logic layer for uploads, listing, deletion,
and staff verification. Calls file_storage.py (disk I/O) and ocr_service.py
(text extraction) — mirrors the same layering scoring_service.py established
in Module 3 (business logic orchestrates; the lower-level modules don't
know about each other or about HTTP).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.file_storage import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    delete_document_file,
    save_document_file,
    sniff_mime_type,
    validate_file_size,
)
from app.models.document import Document, DocumentStatus, DocumentType
from app.models.loan_application import LoanApplication
from app.models.user import User, UserRole
from app.services import ocr_service
from app.services.ocr_service import OCRExtractionError
from app.models.audit_log import AuditAction, AuditResourceType
from app.services.audit_service import log_action


class DuplicateDocumentTypeError(Exception):
    """Raised when a document of this type already exists for this loan application."""
    pass


class DocumentNotFoundError(Exception):
    pass


class DocumentAccessDeniedError(Exception):
    pass


class DocumentAlreadyVerifiedError(Exception):
    """Raised when trying to delete or re-verify a document that's already VERIFIED."""
    pass


class LoanAlreadyDecidedError(Exception):
    """Raised when trying to verify a document on a loan that already has a final decision."""
    pass


def upload_document(
    db: Session,
    loan_application: LoanApplication,
    uploader: User,
    document_type: DocumentType,
    content: bytes,
    declared_filename: str,
) -> Document:
    """
    Validates, stores, and OCR-processes an uploaded document, in that
    order. OCR failure does not fail the upload — it's recorded as
    OCR_FAILED so the file is still stored and available for staff to
    inspect manually. Validation failures (bad type, oversized) do fail
    the upload, since those mean nothing usable was actually received.
    """
    validate_file_size(len(content))
    mime_type = sniff_mime_type(content)  # ignores the client's declared Content-Type entirely

    stored_filename, file_hash = save_document_file(loan_application.id, content, mime_type)

    document = Document(
        loan_application_id=loan_application.id,
        document_type=document_type,
        original_filename=declared_filename[:255],  # display-only, never used as a path
        stored_filename=stored_filename,
        mime_type=mime_type,
        file_size_bytes=len(content),
        file_hash=file_hash,
        status=DocumentStatus.UPLOADED,
        uploaded_by=uploader.id,
    )

    try:
        ocr_result = ocr_service.extract_text(content, mime_type)
        document.ocr_raw_text = ocr_result.raw_text
        document.ocr_extracted_fields = ocr_result.extracted_fields
        document.ocr_confidence = ocr_result.confidence
        document.ocr_processed_at = datetime.now(timezone.utc)
        document.status = DocumentStatus.UPLOADED
    except OCRExtractionError as exc:
        document.status = DocumentStatus.OCR_FAILED
        document.ocr_error_message = str(exc)
        document.ocr_processed_at = datetime.now(timezone.utc)

    db.add(document)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        delete_document_file(loan_application.id, stored_filename)  # don't leave an orphaned file on disk
        raise DuplicateDocumentTypeError(
            f"A '{document_type.value}' document already exists for this application. "
            "Delete it before uploading a replacement."
        ) from exc

    db.refresh(document)

    # Own small commit, same reasoning as loan_service.create_loan_application:
    # document.id isn't populated until after the insert above has committed.
    log_action(
        db,
        actor=uploader,
        action=AuditAction.DOCUMENT_UPLOADED,
        resource_type=AuditResourceType.DOCUMENT,
        resource_id=document.id,
        details={"document_type": document_type.value, "status": document.status.value},
    )
    db.commit()

    return document


def list_documents(db: Session, loan_application_id: uuid.UUID) -> list[Document]:
    stmt = (
        select(Document)
        .options(joinedload(Document.verifier))
        .where(Document.loan_application_id == loan_application_id)
        .order_by(Document.uploaded_at.asc())
    )
    return list(db.execute(stmt).unique().scalars().all())


def get_document(
    db: Session, loan_application_id: uuid.UUID, document_id: uuid.UUID
) -> Document:
    """
    Defense in depth beyond the caller's loan-ownership check: this also
    verifies the document actually belongs to the loan_application_id in
    the URL, not just that a document with this ID exists somewhere. This
    stops a theoretical ID-confusion attack where someone owns loan A and
    tries to reach a document that actually belongs to loan B via loan A's
    path.
    """
    stmt = (
        select(Document)
        .options(joinedload(Document.verifier))
        .where(Document.id == document_id, Document.loan_application_id == loan_application_id)
    )
    document = db.execute(stmt).unique().scalar_one_or_none()
    if document is None:
        raise DocumentNotFoundError(f"Document {document_id} was not found on this application.")
    return document


def delete_document(
    db: Session, loan_application_id: uuid.UUID, document_id: uuid.UUID, current_user: User
) -> None:
    document = get_document(db, loan_application_id, document_id)

    is_staff = current_user.role in (UserRole.STAFF, UserRole.ADMIN)
    if document.status == DocumentStatus.VERIFIED and not is_staff:
        raise DocumentAlreadyVerifiedError(
            "This document has been verified and can no longer be deleted."
        )

    # Captured before delete: the ORM object is expired/unusable for reads
    # immediately after db.delete(), so anything the audit entry needs must
    # be read out first.
    deleted_document_type = document.document_type.value

    delete_document_file(loan_application_id, document.stored_filename)
    db.delete(document)
    log_action(
        db,
        actor=current_user,
        action=AuditAction.DOCUMENT_DELETED,
        resource_type=AuditResourceType.DOCUMENT,
        resource_id=document_id,
        details={"document_type": deleted_document_type},
    )
    db.commit()


def verify_document(
    db: Session,
    loan_application: LoanApplication,
    document_id: uuid.UUID,
    reviewer: User,
    new_status: DocumentStatus,
    notes: str | None,
) -> Document:
    if new_status not in (DocumentStatus.VERIFIED, DocumentStatus.REJECTED):
        raise ValueError("new_status must be VERIFIED or REJECTED.")

    if loan_application.final_decision is not None:
        raise LoanAlreadyDecidedError(
            "This loan application already has a final decision; its documents can no longer be reviewed."
        )

    document = get_document(db, loan_application.id, document_id)

    document.status = new_status
    document.verified_by = reviewer.id
    document.verified_at = datetime.now(timezone.utc)
    if notes is not None:
        document.verification_notes = notes

    db.add(document)
    log_action(
        db,
        actor=reviewer,
        action=AuditAction.DOCUMENT_VERIFIED
        if new_status == DocumentStatus.VERIFIED
        else AuditAction.DOCUMENT_REJECTED,
        resource_type=AuditResourceType.DOCUMENT,
        resource_id=document.id,
        details={"document_type": document.document_type.value, "has_notes": notes is not None},
    )
    db.commit()
    db.refresh(document)
    return document