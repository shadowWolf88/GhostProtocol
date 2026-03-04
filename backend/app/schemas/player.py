import uuid
import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class PlayerRegister(BaseModel):
    handle: str
    email: EmailStr
    password: str

    @field_validator("handle")
    @classmethod
    def validate_handle(cls, v):
        if not 3 <= len(v) <= 32:
            raise ValueError("Handle must be 3-32 characters")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Handle may only contain letters, numbers, underscores, and hyphens")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Passphrase must be at least 8 characters")
        return v


class PlayerLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    player_id: uuid.UUID
    handle: str


class PlayerStatsSchema(BaseModel):
    xp_social: int
    xp_exploitation: int
    xp_cryptography: int
    xp_hardware: int
    xp_counterintel: int
    xp_economics: int
    fiat: int
    crypto: int
    privacy_coin: int
    reputation: int
    energy: int
    max_energy: int

    model_config = {"from_attributes": True}


class PsychStateSchema(BaseModel):
    stress: int
    paranoia: int
    sleep_debt: int
    ego: int
    burnout: int
    trust_index: int
    focus: int
    stimulant_dependency: int
    sedative_dependency: int

    model_config = {"from_attributes": True}


class DeviceSchema(BaseModel):
    id: uuid.UUID
    name: str
    device_type: str
    forensic_trace_level: int
    is_compromised: bool
    is_destroyed: bool
    under_surveillance: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class IdentitySchema(BaseModel):
    id: uuid.UUID
    alias: str
    cover_story: str
    documents_quality: int
    is_burned: bool
    heat_accumulated: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PlayerProfile(BaseModel):
    id: uuid.UUID
    handle: str
    email: str
    created_at: datetime
    last_active: datetime | None
    stats: PlayerStatsSchema | None = None
    psych: PsychStateSchema | None = None

    model_config = {"from_attributes": True}


class PlayerPublicProfile(BaseModel):
    handle: str
    reputation: int
    created_at: datetime

    model_config = {"from_attributes": True}
