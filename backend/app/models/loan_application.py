"""
Loan application model.

One applicant can have multiple loan applications over time (e.g. they pay
one off and apply again), so this is a many-to-one relationship back to
`applicants`, not folded into that table.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LoanPurpose(str, enum.Enum):
    PERSONAL = "personal"
    AUTO = "auto"
    EDUCATION = "education"
    BUSINESS = "business"
    HOME = "home"


class LoanStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    SCORED = "scored"
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applicants.id"), nullable=False, index=True
    )
    loan_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    loan_purpose: Mapped[LoanPurpose] = mapped_column(
        Enum(LoanPurpose, name="loan_purpose", native_enum=True), nullable=False
    )
    loan_tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, name="loan_status", native_enum=True),
        nullable=False,
        default=LoanStatus.SUBMITTED,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    applicant: Mapped["Applicant"] = relationship(back_populates="loan_applications")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LoanApplication id={self.id} status={self.status}>"