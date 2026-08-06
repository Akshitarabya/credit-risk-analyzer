import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.applicant import EmploymentStatus

MINIMUM_APPLICANT_AGE = 18


class ApplicantProfileUpsert(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    date_of_birth: date
    annual_income: float = Field(gt=0, description="Gross annual income in the local currency")
    employment_status: EmploymentStatus
    existing_debt: float = Field(ge=0, default=0)
    credit_history_years: int = Field(ge=0, le=100, default=0)

    @field_validator("date_of_birth")
    @classmethod
    def must_be_at_least_18(cls, value: date) -> date:
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < MINIMUM_APPLICANT_AGE:
            raise ValueError(f"Applicant must be at least {MINIMUM_APPLICANT_AGE} years old.")
        if value > today:
            raise ValueError("Date of birth cannot be in the future.")
        return value


class ApplicantProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    date_of_birth: date
    annual_income: float
    employment_status: EmploymentStatus
    existing_debt: float
    credit_history_years: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)