"""
Audit log model.

Append-only by convention: nothing in this codebase ever updates or deletes
an AuditLog row.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditAction(str, enum.Enum):
    LOAN_APPLICATION_SUBMITTED = "loan_application_submitted"
    LOAN_DECISION_APPROVED = "loan_decision_approved"
    LOAN_DECISION_REJECTED = "loan_decision_rejected"
    LOAN_DECISION_MANUAL_REVIEW = "loan_decision_manual_review"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_VERIFIED = "document_verified"
    DOCUMENT_REJECTED = "document_rejected"
    DOCUMENT_DELETED = "document_deleted"


class AuditResourceType(str, enum.Enum):
    LOAN_APPLICATION = "loan_application"
    DOCUMENT = "document"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    action: Mapped[AuditAction] = mapped_column(
        Enum(
            AuditAction,
            name="audit_action",
            native_enum=True,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[AuditResourceType] = mapped_column(
        Enum(
            AuditResourceType,
            name="audit_resource_type",
            native_enum=True,
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ),
        nullable=False,
        index=True,
    )

    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    actor: Mapped["User | None"] = relationship(
        foreign_keys=[actor_id]
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} "
            f"action={self.action} "
            f"resource={self.resource_type}:{self.resource_id}>"
        )