import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.schemas.economy import PurchaseRequest
from app.services.economy_service import (
    get_wallet, list_market_items, purchase_market_item,
    launder_crypto, launder_preview, get_transaction_history,
)

router = APIRouter(prefix="/economy", tags=["economy"])


@router.get("/wallet")
async def wallet(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await get_wallet(db, player.id)


@router.get("/transactions")
async def transactions(
    limit: int = Query(default=20, le=100),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    txs = await get_transaction_history(db, player.id, limit)
    return [
        {
            "id": str(t.id),
            "amount": t.amount,
            "currency": t.currency,
            "description": t.description,
            "created_at": t.created_at.isoformat(),
        }
        for t in txs
    ]


@router.get("/market")
async def market(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    listings = await list_market_items(db)
    return [
        {
            "id": str(l.id),
            "item_type": l.item_type,
            "item_name": l.item_name,
            "description": l.description,
            "price_crypto": l.price_crypto,
            "quantity": l.quantity,
            "seller_handle": "DARKNET" if l.seller_player_id is None else "PLAYER",
            "effect_data": l.effect_data,
            "expires_at": l.expires_at.isoformat() if l.expires_at else None,
        }
        for l in listings
    ]


@router.get("/market/{item_type}")
async def market_by_type(
    item_type: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    listings = await list_market_items(db, item_type)
    return [
        {
            "id": str(l.id),
            "item_type": l.item_type,
            "item_name": l.item_name,
            "description": l.description,
            "price_crypto": l.price_crypto,
            "quantity": l.quantity,
            "seller_handle": "DARKNET",
            "effect_data": l.effect_data,
        }
        for l in listings
    ]


@router.post("/market/buy")
async def buy_item(
    purchase: PurchaseRequest,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await purchase_market_item(db, player.id, purchase.listing_id, purchase.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    from app.services.onboarding_service import check_onboarding_trigger
    onboarding = await check_onboarding_trigger(player.id, "market_buy")

    return {**result, "onboarding": onboarding}


@router.post("/launder")
async def launder(
    body: dict,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    amount = body.get("amount", 0)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")
    try:
        return await launder_crypto(db, player.id, amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/launder/preview")
async def launder_chain_preview(
    amount: int = Query(..., gt=0),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await launder_preview(db, player.id, amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
