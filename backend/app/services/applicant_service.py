from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.applicant import Applicant
from app.models.user import User
from app.schemas.applicant import ApplicantProfileUpsert


def get_applicant_by_user_id(db: Session, user_id) -> Applicant | None:
    stmt = select(Applicant).where(Applicant.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def upsert_applicant_profile(db: Session, user: User, payload: ApplicantProfileUpsert) -> Applicant:
    """
    Creates the applicant's profile on first use, or updates it in place on
    subsequent calls (e.g. income changed since their last application).
    """
    applicant = get_applicant_by_user_id(db, user.id)

    if applicant is None:
        applicant = Applicant(user_id=user.id, **payload.model_dump())
        db.add(applicant)
    else:
        for field, value in payload.model_dump().items():
            setattr(applicant, field, value)

    db.commit()
    db.refresh(applicant)
    return applicant