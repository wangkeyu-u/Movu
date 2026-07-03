from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    audit_id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: str
    metadata_json: str | None
    ip_address: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
