import uuid
from datetime import datetime
from pydantic import BaseModel


class HeatDomain(BaseModel):
    domain: str
    level: int
    decay_rate: float
    last_incident_at: datetime | None


class HeatStatus(BaseModel):
    player_id: uuid.UUID
    domains: dict[str, HeatDomain]
    total_heat: float
    threat_tier: int
    threat_tier_name: str
    threat_description: str
    is_dark_web_burned: bool
    estimated_time_to_decay_safe: float
    go_dark_until: datetime | None = None
