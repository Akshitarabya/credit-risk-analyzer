import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.loan_application import LoanPurpose, LoanStatus
from app.schemas.applicant import ApplicantProfileOut, ApplicantProfileUpsert

MAX_TENURE_MONTHS = 360  # 30 years — generous upper bound, still a sanity limit


class LoanApplicationCreate(ApplicantProfileUpsert):
    """
    The submission payload for the one-page application form: the
    applicant's financial profile (inherited from ApplicantProfileUpsert)
    plus the loan-specific fields below, submitted together in one call.
    """
    loan_amount: float = Field(gt=0)
    loan_purpose: LoanPurpose
    loan_tenure_months: int = Field(gt=0, le=MAX_TENURE_MONTHS)


class LoanApplicationOut(BaseModel):
    id: uuid.UUID
    applicant_id: uuid.UUID
    loan_amount: float
    loan_purpose: LoanPurpose
    loan_tenure_months: int
    status: LoanStatus
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanApplicationDetailOut(LoanApplicationOut):
    applicant: ApplicantProfileOut