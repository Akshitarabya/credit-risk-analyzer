"""
Scoring service: turns a raw ML probability into the business-facing
outputs (risk_score, risk_category, recommendation) and persists them.

This is deliberately a separate layer from ml_service.py: ml_service.py
knows nothing about "APPROVED" or thresholds like 30/70 — those are
business/policy decisions, not ML mechanics, and keeping them here means
the thresholds (or the rule below) can change without touching the model
code at all.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.applicant import Applicant
from app.models.loan_application import LoanApplication, LoanStatus, Recommendation, RiskCategory
from app.services import ml_service

# --- Risk category thresholds (risk_score is 0-100) ---
LOW_RISK_MAX = 30      # score < 30  -> LOW
HIGH_RISK_MIN = 70     # score >= 70 -> HIGH
                       # 30 <= score < 70 -> MEDIUM

# --- Sanity-check rule layer, on top of the model ---
# A real bank never lets a statistical model be the only thing standing
# between an applicant and a loan decision. This is intentionally a single,
# simple, explainable guardrail (not a full rules engine) that overrides
# the model when the loan amount is wildly out of proportion to income.
MAX_LOAN_TO_INCOME_RATIO = 5.0


def _categorize(risk_score: int) -> RiskCategory:
    if risk_score < LOW_RISK_MAX:
        return RiskCategory.LOW
    if risk_score < HIGH_RISK_MIN:
        return RiskCategory.MEDIUM
    return RiskCategory.HIGH


def _recommend(risk_category: RiskCategory) -> Recommendation:
    return {
        RiskCategory.LOW: Recommendation.APPROVED,
        RiskCategory.MEDIUM: Recommendation.REVIEW,
        RiskCategory.HIGH: Recommendation.REJECT,
    }[risk_category]


def score_loan_application(db: Session, loan_application: LoanApplication, applicant: Applicant) -> LoanApplication:
    """
    Computes and persists the risk prediction for a loan application.
    Called synchronously right after a loan application is created —
    a single model prediction takes well under a second, so no background
    job queue is needed here.
    """
    applicant_data = {
        "annual_income": applicant.annual_income,
        "existing_debt": applicant.existing_debt,
        "credit_history_years": applicant.credit_history_years,
        "employment_status": applicant.employment_status.value,
    }
    loan_data = {
        "loan_amount": loan_application.loan_amount,
        "loan_tenure_months": loan_application.loan_tenure_months,
        "loan_purpose": loan_application.loan_purpose.value,
    }

    features = ml_service.build_feature_vector(applicant_data, loan_data)
    probability_of_default = ml_service.predict_default_probability(features)
    top_factors = ml_service.top_contributing_factors(features)

    risk_score = round(probability_of_default * 100)
    risk_category = _categorize(risk_score)
    recommendation = _recommend(risk_category)

    # Sanity-check rule layer: an oversized loan relative to income forces a
    # REJECT recommendation regardless of what the model alone concluded.
    loan_to_income = float(loan_application.loan_amount) / float(applicant.annual_income)
    if loan_to_income > MAX_LOAN_TO_INCOME_RATIO:
        risk_category = RiskCategory.HIGH
        recommendation = Recommendation.REJECT

    loan_application.risk_score = risk_score
    loan_application.risk_category = risk_category
    loan_application.recommendation = recommendation
    loan_application.prediction_timestamp = datetime.now(timezone.utc)
    loan_application.model_version = ml_service.get_model_version()
    loan_application.top_risk_factors = top_factors
    loan_application.status = LoanStatus.SCORED

    db.add(loan_application)
    db.commit()
    db.refresh(loan_application)
    return loan_application