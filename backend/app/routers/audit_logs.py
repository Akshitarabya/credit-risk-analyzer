import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.audit_log import AuditAction, AuditResourceType
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogListOut
from app.services.audit_service import list_audit_logs

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=AuditLogListOut)
def read_audit_logs(
    action: AuditAction | None = Query(default=None),
    resource_type: AuditResourceType | None = Query(default=None),
    actor_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(require_role(UserRole.STAFF, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AuditLogListOut:
    items, total = list_audit_logs(
        db,
        action=action,
        resource_type=resource_type,
        actor_id=actor_id,
        limit=limit,
        offset=offset,
    )
    return AuditLogListOut(items=items, total=total, limit=limit, offset=offset)