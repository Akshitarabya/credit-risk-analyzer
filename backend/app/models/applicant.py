"""
Applicant financial/employment profile.

Kept as its own table (not columns on `users`) because it's data specific
to the lending domain, 1:1 with a `users` row whose role is 'applicant',
and is exactly what the ML model will read features from starting Module 3.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmploymentStatus(str, enum.Enum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"


class Applicant(Base):
    __tablename__ = "applicants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    annual_income: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
    )

    employment_status: Mapped[EmploymentStatus] = mapped_column(
        Enum(
    EmploymentStatus,
    name="employment_status",
    native_enum=True,
    values_callable=lambda enum_class: [member.value for member in enum_class],
),
        nullable=False,
    )

    existing_debt: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=0,
    )

    credit_history_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    loan_applications: Mapped[list["LoanApplication"]] = relationship(
        back_populates="applicant",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Applicant id={self.id} user_id={self.user_id}>"