import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.loan_application import LoanStatus
from app.models.user import User, UserRole
from app.schemas.loan import LoanApplicationCreate, LoanApplicationDetailOut, LoanApplicationOut
from app.schemas.prediction import LoanPredictionOut
from app.services.loan_service import (
    LoanApplicationAccessDeniedError,
    LoanApplicationNotFoundError,
    create_loan_application,
    get_loan_application,
    list_all_loan_applications,
    list_my_loan_applications,
)
from app.services.ml_service import ModelNotAvailableError

router = APIRouter(prefix="/loans", tags=["Loan Applications"])


@router.post("", response_model=LoanApplicationOut, status_code=status.HTTP_201_CREATED)
def submit_loan_application(
    payload: LoanApplicationCreate,
    current_user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> LoanApplicationOut:
    try:
        return create_loan_application(db, current_user, payload)
    except ModelNotAvailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


# NOTE: "/me" is registered before "/{loan_application_id}" deliberately —
# otherwise FastAPI would try to parse "me" as a UUID path parameter and
# fail with a 422 instead of reaching this route.
@router.get("/me", response_model=list[LoanApplicationOut])
def list_my_applications(
    current_user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> list[LoanApplicationOut]:
    return list_my_loan_applications(db, current_user)


@router.get("/{loan_application_id}", response_model=LoanApplicationDetailOut)
def read_loan_application(
    loan_application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LoanApplicationDetailOut:
    try:
        return get_loan_application(db, current_user, loan_application_id)
    except LoanApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LoanApplicationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{loan_application_id}/prediction", response_model=LoanPredictionOut)
def read_loan_prediction(
    loan_application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LoanPredictionOut:
    """
    A focused view of just the risk prediction for an application — the
    same underlying data is also embedded in GET /loans/{id}, but this
    endpoint exists for callers that only want the prediction itself.
    """
    try:
        loan_application = get_loan_application(db, current_user, loan_application_id)
    except LoanApplicationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LoanApplicationAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    if loan_application.risk_score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This application has not been scored yet.",
        )

    return LoanPredictionOut(
        loan_application_id=loan_application.id,
        risk_score=loan_application.risk_score,
        risk_category=loan_application.risk_category,
        recommendation=loan_application.recommendation,
        prediction_timestamp=loan_application.prediction_timestamp,
        model_version=loan_application.model_version,
        top_risk_factors=loan_application.top_risk_factors or [],
    )


@router.get("", response_model=list[LoanApplicationOut])
def list_all_applications(
    status_filter: LoanStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> list[LoanApplicationOut]:
    return list_all_loan_applications(db, status_filter)