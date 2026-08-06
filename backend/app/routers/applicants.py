from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.applicant import ApplicantProfileOut, ApplicantProfileUpsert
from app.services.applicant_service import get_applicant_by_user_id, upsert_applicant_profile

router = APIRouter(prefix="/applicants", tags=["Applicants"])


@router.get("/me", response_model=ApplicantProfileOut)
def read_my_profile(
    current_user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantProfileOut:
    profile = get_applicant_by_user_id(db, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No applicant profile yet. Submit a loan application, or PATCH this "
            "endpoint, to create one.",
        )
    return profile


@router.patch("/me", response_model=ApplicantProfileOut)
def update_my_profile(
    payload: ApplicantProfileUpsert,
    current_user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantProfileOut:
    return upsert_applicant_profile(db, current_user, payload)