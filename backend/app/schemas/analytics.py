from datetime import date as date_type

from pydantic import BaseModel

from app.models.loan_application import FinalDecision, LoanStatus, RiskCategory


class StatusCount(BaseModel):
    status: LoanStatus
    count: int


class RiskCategoryCount(BaseModel):
    risk_category: RiskCategory
    count: int


class TrendPoint(BaseModel):
    date: date_type
    count: int


class AnalyticsSummaryOut(BaseModel):
    total_applications: int
    status_counts: list[StatusCount]
    risk_category_counts: list[RiskCategoryCount]
    average_loan_amount: float | None
    average_risk_score: float | None
    approved_count: int
    rejected_count: int
    approval_rate: float | None  # approved_count / (approved_count + rejected_count)
    applications_trend: list[TrendPoint]  # daily counts, last 30 days