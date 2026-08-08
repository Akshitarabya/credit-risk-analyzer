import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.loan_application import LoanApplication, LoanStatus
from app.models.user import User, UserRole
from app.schemas.applicant import ApplicantProfileUpsert
from app.schemas.loan import LoanApplicationCreate
from app.services.applicant_service import upsert_applicant_profile
from app.services.scoring_service import score_loan_application


class LoanApplicationNotFoundError(Exception):
    pass


class LoanApplicationAccessDeniedError(Exception):
    pass


def create_loan_application(
    db: Session, user: User, payload: LoanApplicationCreate
) -> LoanApplication:
    """
    Upserts the applicant's financial profile, creates a new loan
    application, and immediately scores it — this backs the single-page
    "financial profile + loan details" application form and means the
    applicant sees their risk assessment without a second round trip.
    """
    profile_payload = ApplicantProfileUpsert(
        **payload.model_dump(
            exclude={
                "loan_amount",
                "loan_purpose",
                "loan_tenure_months",
            }
        )
    )
    applicant = upsert_applicant_profile(db, user, profile_payload)

    loan_application = LoanApplication(
        applicant_id=applicant.id,
        loan_amount=payload.loan_amount,
        loan_purpose=payload.loan_purpose,
        loan_tenure_months=payload.loan_tenure_months,
        status=LoanStatus.SUBMITTED,
    )
    db.add(loan_application)
    db.commit()
    db.refresh(loan_application)

    loan_application = score_loan_application(db, loan_application, applicant)
    return loan_application


def list_my_loan_applications(
    db: Session, user: User
) -> list[LoanApplication]:
    stmt = (
        select(LoanApplication)
        .join(LoanApplication.applicant)
        .where(LoanApplication.applicant.has(user_id=user.id))
        .order_by(LoanApplication.submitted_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_loan_application(
    db: Session, user: User, loan_application_id: uuid.UUID
) -> LoanApplication:
    stmt = (
        select(LoanApplication)
        .options(
            joinedload(LoanApplication.applicant),
            joinedload(LoanApplication.reviewer),
        )
        .where(LoanApplication.id == loan_application_id)
    )
    loan_application = db.execute(stmt).unique().scalar_one_or_none()

    if loan_application is None:
        raise LoanApplicationNotFoundError(
            f"Loan application {loan_application_id} was not found."
        )

    is_owner = loan_application.applicant.user_id == user.id
    is_staff = user.role in (UserRole.STAFF, UserRole.ADMIN)

    if not (is_owner or is_staff):
        raise LoanApplicationAccessDeniedError(
            "You do not have permission to view this loan application."
        )

    return loan_application


def list_all_loan_applications(
    db: Session, status_filter: LoanStatus | None = None
) -> list[LoanApplication]:
    """Staff/admin only — enforced by the router's role dependency, not here."""
    stmt = (
        select(LoanApplication)
        .options(
            joinedload(LoanApplication.applicant),
            joinedload(LoanApplication.reviewer),
        )
        .order_by(LoanApplication.submitted_at.desc())
    )

    if status_filter is not None:
        stmt = stmt.where(LoanApplication.status == status_filter)

    return list(db.execute(stmt).unique().scalars().all())