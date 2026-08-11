"""
Review service: the staff decision workflow.

Owns the state machine for moving a loan application from "scored" to a
final outcome. Kept separate from loan_service.py (creation/listing) and
scoring_service.py (ML) — this module knows about staff actions and
transition rules, and nothing else does.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.loan_application import FinalDecision, LoanApplication, LoanStatus
from app.models.user import User
from app.schemas.review import DecisionAction
from app.models.audit_log import AuditAction, AuditResourceType
from app.services.audit_service import log_action

# Maps the current status to the set of decisions a staff member may submit
# from that state. Any status not listed here (SUBMITTED, APPROVED,
# REJECTED) permits no staff-initiated transition at all.
ALLOWED_TRANSITIONS: dict[LoanStatus, set[DecisionAction]] = {
    LoanStatus.SCORED: {DecisionAction.APPROVED, DecisionAction.REJECTED, DecisionAction.MANUAL_REVIEW},
    LoanStatus.MANUAL_REVIEW: {DecisionAction.APPROVED, DecisionAction.REJECTED},
}

_STATUS_FOR_DECISION: dict[DecisionAction, LoanStatus] = {
    DecisionAction.APPROVED: LoanStatus.APPROVED,
    DecisionAction.REJECTED: LoanStatus.REJECTED,
    DecisionAction.MANUAL_REVIEW: LoanStatus.MANUAL_REVIEW,
}

_FINAL_DECISION_FOR_DECISION: dict[DecisionAction, FinalDecision | None] = {
    DecisionAction.APPROVED: FinalDecision.APPROVED,
    DecisionAction.REJECTED: FinalDecision.REJECTED,
    DecisionAction.MANUAL_REVIEW: None,  # not terminal — no final_decision yet
}

_AUDIT_ACTION_FOR_DECISION: dict[DecisionAction, AuditAction] = {
    DecisionAction.APPROVED: AuditAction.LOAN_DECISION_APPROVED,
    DecisionAction.REJECTED: AuditAction.LOAN_DECISION_REJECTED,
    DecisionAction.MANUAL_REVIEW: AuditAction.LOAN_DECISION_MANUAL_REVIEW,
}

PENDING_STATUSES = (LoanStatus.SCORED, LoanStatus.MANUAL_REVIEW)


class ApplicationAlreadyDecidedError(Exception):
    """Raised when trying to change an application that already has a final_decision."""
    pass


class ApplicationNotYetScoredError(Exception):
    """Raised when trying to review an application still stuck at SUBMITTED (no score yet)."""
    pass


class InvalidStatusTransitionError(Exception):
    """Raised when the requested decision isn't a legal move from the current status."""
    pass


def list_pending_applications(db: Session) -> list[LoanApplication]:
    """
    Applications awaiting a staff decision — scored but not yet finally
    decided. Ordered oldest-first (FIFO), the standard shape for a review
    queue: whoever has been waiting longest surfaces first.
    """
    stmt = (
        select(LoanApplication)
        .options(joinedload(LoanApplication.applicant), joinedload(LoanApplication.reviewer))
        .where(LoanApplication.status.in_(PENDING_STATUSES))
        .order_by(LoanApplication.submitted_at.asc())
    )
    return list(db.execute(stmt).unique().scalars().all())


def apply_review_decision(
    db: Session,
    loan_application: LoanApplication,
    reviewer: User,
    decision: DecisionAction,
    notes: str | None,
) -> LoanApplication:
    """
    Validates and applies a staff decision, in this order:
      1. Already finally decided? -> reject (no editing after final decision,
         this is also what stops a double approval).
      2. Still SUBMITTED (never scored)? -> reject (nothing to decide yet).
      3. Is `decision` a legal move from the current status? -> reject if not.
      4. Apply: set status, reviewer_id, reviewed_at, optional notes, and
         final_decision if this decision is terminal.
    """
    if loan_application.final_decision is not None:
        raise ApplicationAlreadyDecidedError(
            f"Application {loan_application.id} already has a final decision "
            f"({loan_application.final_decision.value}) and cannot be changed."
        )

    if loan_application.status == LoanStatus.SUBMITTED:
        raise ApplicationNotYetScoredError(
            f"Application {loan_application.id} has not been scored yet and cannot be reviewed."
        )

    allowed = ALLOWED_TRANSITIONS.get(loan_application.status, set())
    if decision not in allowed:
        raise InvalidStatusTransitionError(
            f"Cannot move application {loan_application.id} from "
            f"'{loan_application.status.value}' to '{decision.value}'."
        )

    loan_application.status = _STATUS_FOR_DECISION[decision]
    loan_application.reviewer_id = reviewer.id
    loan_application.reviewed_at = datetime.now(timezone.utc)
    if notes is not None:
        loan_application.review_notes = notes
    loan_application.final_decision = _FINAL_DECISION_FOR_DECISION[decision]

    db.add(loan_application)
    log_action(
        db,
        actor=reviewer,
        action=_AUDIT_ACTION_FOR_DECISION[decision],
        resource_type=AuditResourceType.LOAN_APPLICATION,
        resource_id=loan_application.id,
        details={"decision": decision.value, "has_notes": notes is not None},
    )
    db.commit()
    db.refresh(loan_application)
    return loan_application


def update_review_notes(
    db: Session, loan_application: LoanApplication, reviewer: User, notes: str
) -> LoanApplication:
    """
    Lets a staff member jot/update notes independently of making a final
    decision (e.g. while an application is still under review). Blocked
    once a final decision has been recorded — notes become part of the
    audit trail at that point, not something to keep editing.
    """
    if loan_application.final_decision is not None:
        raise ApplicationAlreadyDecidedError(
            f"Application {loan_application.id} already has a final decision "
            f"({loan_application.final_decision.value}); notes can no longer be edited."
        )

    loan_application.review_notes = notes
    if loan_application.reviewer_id is None:
        # First staff member to touch this application "claims" it as reviewer,
        # without that requiring a final decision yet.
        loan_application.reviewer_id = reviewer.id

    db.add(loan_application)
    db.commit()
    db.refresh(loan_application)
    return loan_application