import uuid
from datetime import datetime
from pydantic import BaseModel


class OperationCreate(BaseModel):
    node_key: str
    device_id: uuid.UUID
    identity_id: uuid.UUID | None = None
    approach: str = "technical"


class OperationPhaseAction(BaseModel):
    phase_action: str
    parameters: dict = {}


class PhaseOutcome(BaseModel):
    phase: str
    success: bool
    narrative: str
    artifacts_generated: list[str]
    xp_partial: dict
    heat_generated: int
    next_phase_unlocked: bool
    can_abort: bool
    next_phase: str | None = None


class OperationStatus(BaseModel):
    id: uuid.UUID
    status: str
    current_phase: str
    node_key: str
    approach: str
    phase_data: dict
    heat_generated: int
    artifacts_left: list
    started_at: datetime
    estimated_completion: str | None = None

    model_config = {"from_attributes": True}


class OperationResult(BaseModel):
    operation_id: uuid.UUID
    status: str
    xp_awarded: dict
    crypto_earned: int
    reputation_earned: int
    artifacts_left: list
    heat_generated: int
    narrative: str
    phases_completed: list[str]
