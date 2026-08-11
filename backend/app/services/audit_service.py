"""
Audit service: a single reusable helper for recording audit events, plus the
filtered/paginated read used by the staff-facing endpoint.

`log_action()` deliberately only stages the entry (`db.add()`, no commit) —
callers invoke it in the middle of their own existing transaction (right
before their existing `db.commit()`), so the audit entry is committed
atomically with the action it describes: if the surrounding transaction
rolls back, the audit entry never persists either, and there is no
window where an action succeeds but its log doesn't (or vice versa).

`details` must stay small and non-sensitive: illustrative business facts
(a loan amount, a risk category, a document type) — never credentials,
tokens, file contents, or OCR text. See AuditLog's own docstring.
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditAction, AuditLog, AuditResourceType
from app.models.user import User
from app.schemas.audit_log import AuditLogOut


def log_action(
    db: Session,
    actor: User | None,
    action: AuditAction,
    resource_type: AuditResourceType,
    resource_id: uuid.UUID | None,
    details: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor.id if actor is not None else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(entry)
    return entry


def _to_audit_log_out(entry: AuditLog) -> AuditLogOut:
    result = AuditLogOut.model_validate(entry)
    if entry.actor is not None:
        result.actor_name = entry.actor.full_name
    return result


def list_audit_logs(
    db: Session,
    action: AuditAction | None = None,
    resource_type: AuditResourceType | None = None,
    actor_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLogOut], int]:
    filters = []
    if action is not None:
        filters.append(AuditLog.action == action)
    if resource_type is not None:
        filters.append(AuditLog.resource_type == resource_type)
    if actor_id is not None:
        filters.append(AuditLog.actor_id == actor_id)

    total = db.execute(
        select(func.count()).select_from(AuditLog).where(*filters)
    ).scalar_one()

    stmt = (
        select(AuditLog)
        .options(joinedload(AuditLog.actor))
        .where(*filters)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    entries = db.execute(stmt).unique().scalars().all()

    return [_to_audit_log_out(entry) for entry in entries], total