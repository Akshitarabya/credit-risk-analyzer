"""
File storage utilities: saving/reading/deleting document bytes on disk, and
verifying what a file actually is by its content, not by trusting the
client-supplied Content-Type header (which is trivially spoofable).

Deliberately parallel to core/security.py: a low-level, dependency-free
utility module that business logic (document_service.py) calls into,
without knowing anything about HTTP or the database itself.
"""
import hashlib
import uuid
from pathlib import Path

from app.config import settings

# Magic bytes for the 3 file types this project accepts. Checked against the
# actual uploaded content — never the client's Content-Type header, which an
# attacker fully controls and can set to anything regardless of real content.
_MAGIC_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "application/pdf": (b"%PDF-",),
}

_EXTENSION_FOR_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}

ALLOWED_MIME_TYPES = tuple(_MAGIC_SIGNATURES.keys())


class UnsupportedFileTypeError(Exception):
    """Raised when the file's actual content doesn't match any allowed type."""
    pass


class FileTooLargeError(Exception):
    pass


def sniff_mime_type(content: bytes) -> str:
    """
    Determines the real MIME type from the file's magic bytes. This is the
    server-side defense against MIME-type spoofing: a client could label a
    malicious file as "application/pdf" in the upload request, but if the
    actual bytes don't start with %PDF-, this rejects it regardless of what
    the client claimed.
    """
    for mime_type, signatures in _MAGIC_SIGNATURES.items():
        if any(content.startswith(sig) for sig in signatures):
            return mime_type

    raise UnsupportedFileTypeError(
        "This file's content doesn't match any of the accepted types "
        "(JPEG, PNG, PDF), regardless of its filename or declared type."
    )


def validate_file_size(size_bytes: int) -> None:
    if size_bytes > settings.max_document_size_bytes:
        max_mb = settings.max_document_size_bytes / (1024 * 1024)
        raise FileTooLargeError(f"File exceeds the {max_mb:.0f} MB size limit.")


def _storage_root() -> Path:
    """
    Resolves the storage directory relative to the backend/ project root
    (three levels up from this file: app/core/file_storage.py -> backend/),
    so it works the same regardless of the process's current working
    directory when uvicorn/pytest is launched.
    """
    backend_root = Path(__file__).resolve().parent.parent.parent
    root = backend_root / settings.document_storage_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_document_file(loan_application_id: uuid.UUID, content: bytes, mime_type: str) -> tuple[str, str]:
    """
    Writes `content` to disk under a fully server-generated path — the
    caller's original filename is never used to build this path, which is
    what makes path traversal structurally impossible here rather than
    merely filtered.

    Returns (stored_filename, sha256_hex_digest).
    """
    extension = _EXTENSION_FOR_MIME[mime_type]
    stored_filename = f"{uuid.uuid4()}{extension}"

    loan_dir = _storage_root() / str(loan_application_id)
    loan_dir.mkdir(parents=True, exist_ok=True)

    file_path = loan_dir / stored_filename
    file_path.write_bytes(content)

    file_hash = hashlib.sha256(content).hexdigest()
    return stored_filename, file_hash


def read_document_file(loan_application_id: uuid.UUID, stored_filename: str) -> bytes:
    file_path = _storage_root() / str(loan_application_id) / stored_filename
    return file_path.read_bytes()


def get_document_file_path(loan_application_id: uuid.UUID, stored_filename: str) -> Path:
    return _storage_root() / str(loan_application_id) / stored_filename


def delete_document_file(loan_application_id: uuid.UUID, stored_filename: str) -> None:
    file_path = _storage_root() / str(loan_application_id) / stored_filename
    file_path.unlink(missing_ok=True)