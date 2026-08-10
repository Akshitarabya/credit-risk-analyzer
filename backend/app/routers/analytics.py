from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.analytics import AnalyticsSummaryOut
from app.services.analytics_service import get_analytics_summary

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryOut)
def read_analytics_summary(
    current_user: User = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AnalyticsSummaryOut:
    return get_analytics_summary(db)