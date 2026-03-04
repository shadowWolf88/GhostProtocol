import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    handle: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    stats: Mapped["PlayerStats"] = relationship("PlayerStats", back_populates="player", uselist=False)
    psych: Mapped["PsychState"] = relationship("PsychState", back_populates="player", uselist=False)
    devices: Mapped[list["Device"]] = relationship("Device", back_populates="player")
    identities: Mapped[list["Identity"]] = relationship("Identity", back_populates="player")
    operations: Mapped[list["Operation"]] = relationship("Operation", back_populates="player")


class PlayerStats(Base):
    __tablename__ = "player_stats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), unique=True)

    xp_social: Mapped[int] = mapped_column(Integer, default=0)
    xp_exploitation: Mapped[int] = mapped_column(Integer, default=0)
    xp_cryptography: Mapped[int] = mapped_column(Integer, default=0)
    xp_hardware: Mapped[int] = mapped_column(Integer, default=0)
    xp_counterintel: Mapped[int] = mapped_column(Integer, default=0)
    xp_economics: Mapped[int] = mapped_column(Integer, default=0)

    fiat: Mapped[int] = mapped_column(Integer, default=0)
    crypto: Mapped[int] = mapped_column(Integer, default=500)
    privacy_coin: Mapped[int] = mapped_column(Integer, default=0)
    reputation: Mapped[int] = mapped_column(Integer, default=0)

    energy: Mapped[int] = mapped_column(Integer, default=100)
    max_energy: Mapped[int] = mapped_column(Integer, default=100)
    energy_regen_rate: Mapped[int] = mapped_column(Integer, default=10)
    last_energy_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player: Mapped["Player"] = relationship("Player", back_populates="stats")


class PsychState(Base):
    __tablename__ = "psych_states"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), unique=True)

    stress: Mapped[int] = mapped_column(Integer, default=0)
    paranoia: Mapped[int] = mapped_column(Integer, default=20)
    sleep_debt: Mapped[int] = mapped_column(Integer, default=0)
    ego: Mapped[int] = mapped_column(Integer, default=50)
    burnout: Mapped[int] = mapped_column(Integer, default=0)
    trust_index: Mapped[int] = mapped_column(Integer, default=60)
    focus: Mapped[int] = mapped_column(Integer, default=80)
    stimulant_dependency: Mapped[int] = mapped_column(Integer, default=0)
    sedative_dependency: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    player: Mapped["Player"] = relationship("Player", back_populates="psych")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    device_type: Mapped[str] = mapped_column(String(20), nullable=False)
    mac_fingerprint: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    ip_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    firmware_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    forensic_trace_level: Mapped[int] = mapped_column(Integer, default=0)
    is_compromised: Mapped[bool] = mapped_column(Boolean, default=False)
    is_destroyed: Mapped[bool] = mapped_column(Boolean, default=False)
    under_surveillance: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    destroyed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    player: Mapped["Player"] = relationship("Player", back_populates="devices")


class Identity(Base):
    __tablename__ = "identities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"))
    alias: Mapped[str] = mapped_column(String(64), nullable=False)
    cover_story: Mapped[str] = mapped_column(Text, default="")
    documents_quality: Mapped[int] = mapped_column(Integer, default=50)
    is_burned: Mapped[bool] = mapped_column(Boolean, default=False)
    heat_accumulated: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    burned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    player: Mapped["Player"] = relationship("Player", back_populates="identities")


class WorldNode(Base):
    __tablename__ = "world_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    vulnerability_score: Mapped[int] = mapped_column(Integer, default=50)
    patch_rate: Mapped[int] = mapped_column(Integer, default=2)
    defender_tier: Mapped[int] = mapped_column(Integer, default=1)
    heat_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    base_crypto_reward: Mapped[int] = mapped_column(Integer, default=100)
    base_reputation_reward: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_breached_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"))
    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("world_nodes.id"))
    identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("identities.id"), nullable=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"))
    status: Mapped[str] = mapped_column(String(20), default="planning")
    approach: Mapped[str] = mapped_column(String(20), default="technical")
    phase_data: Mapped[dict] = mapped_column(JSON, default=dict)
    artifacts_left: Mapped[list] = mapped_column(JSON, default=list)
    heat_generated: Mapped[int] = mapped_column(Integer, default=0)
    xp_awarded: Mapped[dict] = mapped_column(JSON, default=dict)
    crypto_earned: Mapped[int] = mapped_column(Integer, default=0)
    reputation_earned: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fail_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    player: Mapped["Player"] = relationship("Player", back_populates="operations")
    node: Mapped["WorldNode"] = relationship("WorldNode")


class HeatRecord(Base):
    __tablename__ = "heat_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), index=True)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0)
    last_incident_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decay_rate: Mapped[float] = mapped_column(Float, default=5.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TraceArtifact(Base):
    __tablename__ = "trace_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), index=True)
    operation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("operations.id"), nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    node_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("world_nodes.id"), nullable=True)
    identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("identities.id"), nullable=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=3)
    is_wiped: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FactionNPC(Base):
    __tablename__ = "faction_npcs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    faction_key: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_requirement: Mapped[int] = mapped_column(Integer, default=0)


class PlayerFactionRelation(Base):
    __tablename__ = "player_faction_relations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), index=True)
    faction_key: Mapped[str] = mapped_column(String(32), nullable=False)
    standing: Mapped[int] = mapped_column(Integer, default=0)
    is_member: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class MarketListing(Base):
    __tablename__ = "market_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_player_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    item_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_crypto: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    effect_data: Mapped[dict] = mapped_column(JSON, default=dict)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PlayerInventory(Base):
    __tablename__ = "player_inventory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), index=True)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    item_name: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    effect_data: Mapped[dict] = mapped_column(JSON, default=dict)
    uses_remaining: Mapped[int] = mapped_column(Integer, default=-1)
    acquired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
