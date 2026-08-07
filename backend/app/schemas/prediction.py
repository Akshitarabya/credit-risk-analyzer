import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.loan_application import Recommendation, RiskCategory


class RiskFactor(BaseModel):
    feature: str
    impact: float
    direction: str


class LoanPredictionOut(BaseModel):
    loan_application_id: uuid.UUID
    risk_score: int
    risk_category: RiskCategory
    recommendation: Recommendation
    prediction_timestamp: datetime
    model_version: str
    top_risk_factors: list[RiskFactor]

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())