"""
Analytics service: staff/admin-facing aggregate statistics.

Every metric is computed with a single grouped SQL aggregate query (COUNT/AVG
with GROUP BY) rather than loading rows into Python and counting there — the
same "let the database do the work" principle already used in loan_service.py
list queries.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.loan_application import FinalDecision, LoanApplication, LoanStatus, RiskCategory
from app.schemas.analytics import AnalyticsSummaryOut, RiskCategoryCount, StatusCount, TrendPoint

TREND_WINDOW_DAYS = 30


def get_analytics_summary(db: Session) -> AnalyticsSummaryOut:
    total_applications = db.execute(
        select(func.count()).select_from(LoanApplication)
    ).scalar_one()

    status_rows = db.execute(
        select(LoanApplication.status, func.count())
        .group_by(LoanApplication.status)
    ).all()
    status_counts = [StatusCount(status=status, count=count) for status, count in status_rows]

    risk_rows = db.execute(
        select(LoanApplication.risk_category, func.count())
        .where(LoanApplication.risk_category.is_not(None))
        .group_by(LoanApplication.risk_category)
    ).all()
    risk_category_counts = [
        RiskCategoryCount(risk_category=category, count=count) for category, count in risk_rows
    ]

    average_loan_amount = db.execute(select(func.avg(LoanApplication.loan_amount))).scalar_one()
    average_risk_score = db.execute(
        select(func.avg(LoanApplication.risk_score)).where(LoanApplication.risk_score.is_not(None))
    ).scalar_one()

    decision_rows = dict(
        db.execute(
            select(LoanApplication.final_decision, func.count())
            .where(LoanApplication.final_decision.is_not(None))
            .group_by(LoanApplication.final_decision)
        ).all()
    )
    approved_count = decision_rows.get(FinalDecision.APPROVED, 0)
    rejected_count = decision_rows.get(FinalDecision.REJECTED, 0)
    total_decided = approved_count + rejected_count
    approval_rate = (approved_count / total_decided) if total_decided > 0 else None

    window_start = datetime.now(timezone.utc) - timedelta(days=TREND_WINDOW_DAYS)
    trend_rows = db.execute(
        select(func.date(LoanApplication.submitted_at), func.count())
        .where(LoanApplication.submitted_at >= window_start)
        .group_by(func.date(LoanApplication.submitted_at))
        .order_by(func.date(LoanApplication.submitted_at))
    ).all()
    applications_trend = [
        TrendPoint(date=trend_date, count=count) for trend_date, count in trend_rows
    ]

    return AnalyticsSummaryOut(
        total_applications=total_applications,
        status_counts=status_counts,
        risk_category_counts=risk_category_counts,
        average_loan_amount=float(average_loan_amount) if average_loan_amount is not None else None,
        average_risk_score=float(average_risk_score) if average_risk_score is not None else None,
        approved_count=approved_count,
        rejected_count=rejected_count,
        approval_rate=approval_rate,
        applications_trend=applications_trend,
    )