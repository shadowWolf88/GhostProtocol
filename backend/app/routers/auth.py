from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db, get_current_player
from app.core.security import create_access_token
from app.models.player import Player
from app.schemas.player import PlayerRegister, PlayerLogin, TokenResponse, PlayerProfile, PlayerStatsSchema, PsychStateSchema
from app.services.player_service import create_player, authenticate_player, get_player_full_profile, update_last_active

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: PlayerRegister, db: AsyncSession = Depends(get_db)):
    handle_check = await db.execute(select(Player).where(Player.handle == data.handle))
    if handle_check.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Handle already claimed in the network.")

    email_check = await db.execute(select(Player).where(Player.email == data.email))
    if email_check.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Signal already registered.")

    player = await create_player(db, data)
    token = create_access_token(player.id, player.handle)
    return TokenResponse(
        access_token=token,
        player_id=player.id,
        handle=player.handle,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: PlayerLogin, db: AsyncSession = Depends(get_db)):
    player = await authenticate_player(db, data.email, data.password)
    if not player:
        raise HTTPException(status_code=401, detail="Access denied. Signal not recognized.")

    await update_last_active(db, player.id)
    token = create_access_token(player.id, player.handle)
    return TokenResponse(
        access_token=token,
        player_id=player.id,
        handle=player.handle,
    )


@router.get("/me", response_model=PlayerProfile)
async def me(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    profile = await get_player_full_profile(db, player.id)
    return PlayerProfile(
        id=player.id,
        handle=player.handle,
        email=player.email,
        created_at=player.created_at,
        last_active=player.last_active,
        stats=PlayerStatsSchema.model_validate(profile["stats"]) if profile.get("stats") else None,
        psych=PsychStateSchema.model_validate(profile["psych"]) if profile.get("psych") else None,
    )


@router.post("/logout")
async def logout(player: Player = Depends(get_current_player)):
    return {"message": "Signal terminated."}
