import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit_log import AuditAction, AuditResourceType


class AuditLogOut(BaseModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_name: str | None = None
    action: AuditAction
    resource_type: AuditResourceType
    resource_id: uuid.UUID | None
    details: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int
    limit: int
    offset: int