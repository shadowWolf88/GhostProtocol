import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class PrisonRecord(Base):
    __tablename__ = "prison_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), index=True)
    sentence_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    arrested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    release_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    charge_description: Mapped[str] = mapped_column(Text, nullable=False)
    time_served_bonus: Mapped[int] = mapped_column(Integer, default=0)
    informant_deal: Mapped[bool] = mapped_column(Boolean, default=False)
    escaped: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    broker_info_count: Mapped[int] = mapped_column(Integer, default=0)
    legal_fight_count: Mapped[int] = mapped_column(Integer, default=0)


class PrisonActivity(Base):
    __tablename__ = "prison_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cost_crypto: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
