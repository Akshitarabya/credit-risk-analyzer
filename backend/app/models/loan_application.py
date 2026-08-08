"""
Loan application model.

One applicant can have multiple loan applications over time (e.g. they pay
one off and apply again), so this is a many-to-one relationship back to
`applicants`, not folded into that table.

Risk prediction fields (added in Module 3) are nullable because they're
populated immediately after creation by the scoring service, not supplied
by the client — a freshly-inserted row exists, briefly, before scoring runs.

Review workflow fields (added in Module 4) are nullable for the same
reason: a staff decision happens after scoring, not at creation. Note that
"Under Review" in the product's workflow language is deliberately the same
value as the existing LoanStatus.MANUAL_REVIEW from Module 2/3 — there was
already a status meaning exactly this, so Module 4 reuses it rather than
introducing a duplicate.
"""
import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import JSON
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


class RiskCategory(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(str, enum.Enum):
    APPROVED = "approved"
    REVIEW = "review"
    REJECT = "reject"


class FinalDecision(str, enum.Enum):
    """
    Distinct from `status`: `status` tracks the full lifecycle (including
    the non-terminal MANUAL_REVIEW state), while `final_decision` is only
    ever set once, the moment the application reaches a terminal state.
    Its presence is what "locks" an application against further edits.
    """
    APPROVED = "approved"
    REJECTED = "rejected"


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

    # --- Risk prediction fields (Module 3) ---
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_category: Mapped[RiskCategory | None] = mapped_column(
        Enum(RiskCategory, name="risk_category", native_enum=True), nullable=True
    )
    recommendation: Mapped[Recommendation | None] = mapped_column(
        Enum(Recommendation, name="recommendation", native_enum=True), nullable=True
    )
    prediction_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    top_risk_factors: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # --- Staff review workflow fields (Module 4) ---
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_decision: Mapped[FinalDecision | None] = mapped_column(
        Enum(FinalDecision, name="final_decision", native_enum=True), nullable=True, index=True
    )

    applicant: Mapped["Applicant"] = relationship(back_populates="loan_applications")
    # One-directional on purpose: `User` (Module 1) is not modified to add a
    # matching back_populates — a staff member's reviewed applications
    # aren't a concept Module 1's User model needs to know about.
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewer_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LoanApplication id={self.id} status={self.status}>"