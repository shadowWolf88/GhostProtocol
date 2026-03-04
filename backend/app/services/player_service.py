import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import Player, PlayerStats, PsychState, Device
from app.schemas.player import PlayerRegister
from app.core.security import hash_password, verify_password


async def create_player(db: AsyncSession, data: PlayerRegister) -> Player:
    player = Player(
        handle=data.handle,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(player)
    await db.flush()

    stats = PlayerStats(
        player_id=player.id,
        crypto=500,
    )
    db.add(stats)

    psych = PsychState(
        player_id=player.id,
        last_updated=datetime.utcnow(),
    )
    db.add(psych)

    device = Device(
        player_id=player.id,
        name="Burner Laptop #1",
        device_type="laptop",
        mac_fingerprint=f"MAC-{uuid.uuid4().hex[:12].upper()}",
        firmware_version="1.0.0",
        forensic_trace_level=0,
    )
    db.add(device)

    await db.commit()
    await db.refresh(player)
    return player


async def authenticate_player(db: AsyncSession, email: str, password: str) -> Player | None:
    result = await db.execute(select(Player).where(Player.email == email))
    player = result.scalar_one_or_none()
    if player and verify_password(password, player.hashed_password):
        return player
    return None


async def get_player_full_profile(db: AsyncSession, player_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(Player).where(Player.id == player_id)
    )
    player = result.scalar_one_or_none()
    if not player:
        return {}

    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = stats_result.scalar_one_or_none()

    psych_result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = psych_result.scalar_one_or_none()

    return {"player": player, "stats": stats, "psych": psych}


async def update_last_active(db: AsyncSession, player_id: uuid.UUID):
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if player:
        player.last_active = datetime.utcnow()
        await db.commit()


async def get_player_by_handle(db: AsyncSession, handle: str) -> Player | None:
    result = await db.execute(select(Player).where(Player.handle == handle))
    return result.scalar_one_or_none()


async def get_player_stats(db: AsyncSession, player_id: uuid.UUID) -> PlayerStats | None:
    result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    return result.scalar_one_or_none()


async def get_player_psych(db: AsyncSession, player_id: uuid.UUID) -> PsychState | None:
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    return result.scalar_one_or_none()


async def get_player_devices(db: AsyncSession, player_id: uuid.UUID) -> list[Device]:
    result = await db.execute(select(Device).where(Device.player_id == player_id))
    return list(result.scalars().all())
