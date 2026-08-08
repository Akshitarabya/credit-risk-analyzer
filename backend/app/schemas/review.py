import enum

from pydantic import BaseModel, Field


class DecisionAction(str, enum.Enum):
    """
    The verb a staff member submits. Distinct from LoanStatus/FinalDecision
    on the model: this is "what the staff member is asking to happen",
    which review_service.py then validates against the current state before
    translating it into the actual status/final_decision columns.
    """
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class ReviewDecisionRequest(BaseModel):
    decision: DecisionAction
    notes: str | None = Field(default=None, max_length=2000)


class ReviewNotesRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=2000)