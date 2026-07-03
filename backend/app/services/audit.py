import json
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def write_audit_log(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: int | str,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    audit_log = AuditLog(
        actor_user_id=actor.user_id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata_json=json.dumps(metadata or {}, separators=(",", ":")),
        ip_address=request.client.host if request and request.client else None,
    )
    db.add(audit_log)
