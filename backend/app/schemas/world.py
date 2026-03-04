import uuid
from datetime import datetime
from pydantic import BaseModel


class WorldNodeSchema(BaseModel):
    id: uuid.UUID
    node_key: str
    name: str
    description: str
    category: str
    tier: int
    vulnerability_score: int
    patch_rate: int
    defender_tier: int
    heat_multiplier: float
    base_crypto_reward: int
    base_reputation_reward: int
    last_breached_at: datetime | None

    model_config = {"from_attributes": True}


class WorldNodeListItem(BaseModel):
    id: uuid.UUID
    node_key: str
    name: str
    category: str
    tier: int
    vulnerability_score: int
    is_accessible: bool
    alert_level: int = 0

    model_config = {"from_attributes": True}


class NodeIntelReport(BaseModel):
    node: WorldNodeSchema
    current_alert_level: int
    estimated_success_chance: float
    recommended_approach: str
    risk_assessment: str
    defender_profile: str
