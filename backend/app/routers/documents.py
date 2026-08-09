import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.file_storage import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    get_document_file_path,
)
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.document import Document, DocumentType
from app.models.user import User, UserRole
from app.schemas.document import DocumentDetailOut, DocumentOut, DocumentVerifyRequest
from app.services.document_service import (
    DocumentAlreadyVerifiedError,
    DocumentNotFoundError,
    DuplicateDocumentTypeError,
    LoanAlreadyDecidedError,
    delete_document,
    get_document,
    list_documents,
    upload_document,
    verify_document,
)
from app.services.loan_service import (
    LoanApplicationAccessDeniedError,
    LoanApplicationNotFoundError,
    get_loan_application,
)

router = APIRouter(prefix="/loans", tags=["Documents"])


def _to_document_out(document: Document, schema_cls: type[DocumentOut] = DocumentOut) -> DocumentOut:
    """Same pattern as loans.py's _to_loan_out(): fills the read-only verifier_name
    convenience field from the eager-loaded relationship."""
    result = schema_cls.model_validate(document)
    if document.verifier is not None:
        result.verifier_name = document.verifier.full_name
    return result


def _get_owned_or_staff_loan(db: Session, user: User, loan_application_id: uuid.UUID):
    try:
        return get_loan_application(db, user, loan_application_id)
    except LoanApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LoanApplicationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/{loan_application_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_loan_document(
    loan_application_id: uuid.UUID,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> DocumentOut:
    loan_application = _get_owned_or_staff_loan(db, current_user, loan_application_id)

    content = await file.read()

    try:
        document = upload_document(
            db, loan_application, current_user, document_type, content, file.filename or "upload"
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc)
        ) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)
        ) from exc
    except DuplicateDocumentTypeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_document_out(document)


@router.get("/{loan_application_id}/documents", response_model=list[DocumentOut])
def list_loan_documents(
    loan_application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentOut]:
    _get_owned_or_staff_loan(db, current_user, loan_application_id)
    documents = list_documents(db, loan_application_id)
    return [_to_document_out(document) for document in documents]


@router.get(
    "/{loan_application_id}/documents/{document_id}", response_model=DocumentDetailOut
)
def read_loan_document(
    loan_application_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDetailOut:
    _get_owned_or_staff_loan(db, current_user, loan_application_id)
    try:
        document = get_document(db, loan_application_id, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _to_document_out(document, schema_cls=DocumentDetailOut)


@router.get("/{loan_application_id}/documents/{document_id}/file")
def download_loan_document_file(
    loan_application_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streams the original file bytes through an authenticated endpoint. The
    storage directory is deliberately never mounted as a public static file
    server — every byte served here passes through the same ownership
    check as every other document endpoint.
    """
    _get_owned_or_staff_loan(db, current_user, loan_application_id)
    try:
        document = get_document(db, loan_application_id, document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    file_path = get_document_file_path(loan_application_id, document.stored_filename)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The stored file is missing."
        )

    return FileResponse(
        path=file_path,
        media_type=document.mime_type,
        filename=document.original_filename,
    )


@router.delete(
    "/{loan_application_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_loan_document(
    loan_application_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    _get_owned_or_staff_loan(db, current_user, loan_application_id)
    try:
        delete_document(db, loan_application_id, document_id, current_user)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DocumentAlreadyVerifiedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch(
    "/{loan_application_id}/documents/{document_id}/verify", response_model=DocumentOut
)
def verify_loan_document(
    loan_application_id: uuid.UUID,
    document_id: uuid.UUID,
    payload: DocumentVerifyRequest,
    current_user: User = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> DocumentOut:
    loan_application = _get_owned_or_staff_loan(db, current_user, loan_application_id)

    try:
        document = verify_document(
            db, loan_application, document_id, current_user, payload.status, payload.notes
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LoanAlreadyDecidedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return _to_document_out(document)