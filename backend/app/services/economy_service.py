import uuid
import math
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import PlayerStats, MarketListing, Transaction, PlayerInventory
from app.schemas.economy import WalletStatus, LaunderingChain, LaunderingStep
from app.services.skill_service import get_player_skill_level
from app.services.heat_service import add_heat
from app.data.constants import GAME_CONSTANTS


async def get_wallet(db: AsyncSession, player_id: uuid.UUID) -> WalletStatus:
    result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = result.scalar_one_or_none()
    if not stats:
        return WalletStatus(fiat=0, crypto=0, privacy_coin=0, reputation=0)
    return WalletStatus(
        fiat=stats.fiat,
        crypto=stats.crypto,
        privacy_coin=stats.privacy_coin,
        reputation=stats.reputation,
    )


async def transfer_funds(
    db: AsyncSession,
    player_id: uuid.UUID,
    currency: str,
    amount: int,
    description: str,
    reference_id: uuid.UUID | None = None,
) -> Transaction:
    result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = result.scalar_one_or_none()
    if not stats:
        raise ValueError("Player stats not found")

    current = getattr(stats, currency, None)
    if current is None:
        raise ValueError(f"Invalid currency: {currency}")

    if amount < 0 and abs(amount) > current:
        raise ValueError(f"Insufficient {currency} balance")

    setattr(stats, currency, current + amount)

    tx = Transaction(
        player_id=player_id,
        amount=amount,
        currency=currency,
        description=description,
        reference_id=reference_id,
    )
    db.add(tx)
    await db.commit()
    return tx


async def launder_crypto(
    db: AsyncSession,
    player_id: uuid.UUID,
    amount: int,
) -> LaunderingChain:
    result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = result.scalar_one_or_none()
    if not stats:
        raise ValueError("Player not found")

    if stats.crypto < amount:
        raise ValueError("Insufficient crypto")

    eco_level = get_player_skill_level(stats, "economics")

    num_steps = max(1, 5 - math.floor(eco_level / 10))
    step_fee_pct = max(0.01, 0.08 - (eco_level * 0.0005))
    heat_per_step = max(1, 3 - math.floor(eco_level / 15))

    steps = []
    running_amount = amount
    total_fees = 0
    total_heat = 0

    for i in range(num_steps):
        fee_amount = int(running_amount * step_fee_pct)
        amount_out = running_amount - fee_amount

        from_currency = "crypto" if i < num_steps - 1 else "crypto"
        to_currency = "privacy_coin" if i == num_steps - 1 else "crypto"

        steps.append(LaunderingStep(
            step_number=i + 1,
            from_currency=from_currency,
            to_currency=to_currency,
            amount_in=running_amount,
            fee_percentage=round(step_fee_pct * 100, 2),
            fee_amount=fee_amount,
            amount_out=amount_out,
            heat_generated=heat_per_step,
        ))

        total_fees += fee_amount
        total_heat += heat_per_step
        running_amount = amount_out

    stats.crypto -= amount
    stats.privacy_coin += running_amount

    tx = Transaction(
        player_id=player_id,
        amount=-amount,
        currency="crypto",
        description=f"Laundering: {amount} crypto → {running_amount} privacy coin ({num_steps} steps)",
    )
    db.add(tx)

    await db.commit()
    await add_heat(db, player_id, "intelligence", total_heat)

    return LaunderingChain(
        steps=steps,
        total_input=amount,
        total_output=running_amount,
        total_fees=total_fees,
        total_heat=total_heat,
        skill_level=eco_level,
    )


async def launder_preview(
    db: AsyncSession,
    player_id: uuid.UUID,
    amount: int,
) -> LaunderingChain:
    result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = result.scalar_one_or_none()
    if not stats:
        raise ValueError("Player not found")

    eco_level = get_player_skill_level(stats, "economics")
    num_steps = max(1, 5 - math.floor(eco_level / 10))
    step_fee_pct = max(0.01, 0.08 - (eco_level * 0.0005))
    heat_per_step = max(1, 3 - math.floor(eco_level / 15))

    steps = []
    running_amount = amount
    total_fees = 0
    total_heat = 0

    for i in range(num_steps):
        fee_amount = int(running_amount * step_fee_pct)
        amount_out = running_amount - fee_amount
        steps.append(LaunderingStep(
            step_number=i + 1,
            from_currency="crypto",
            to_currency="privacy_coin" if i == num_steps - 1 else "crypto",
            amount_in=running_amount,
            fee_percentage=round(step_fee_pct * 100, 2),
            fee_amount=fee_amount,
            amount_out=amount_out,
            heat_generated=heat_per_step,
        ))
        total_fees += fee_amount
        total_heat += heat_per_step
        running_amount = amount_out

    return LaunderingChain(
        steps=steps,
        total_input=amount,
        total_output=running_amount,
        total_fees=total_fees,
        total_heat=total_heat,
        skill_level=eco_level,
    )


async def list_market_items(db: AsyncSession, filter_type: str | None = None) -> list[MarketListing]:
    query = select(MarketListing).where(MarketListing.is_active == True)
    if filter_type:
        query = query.where(MarketListing.item_type == filter_type)
    result = await db.execute(query)
    return list(result.scalars().all())


async def purchase_market_item(
    db: AsyncSession,
    player_id: uuid.UUID,
    listing_id: uuid.UUID,
    quantity: int = 1,
) -> dict:
    listing_result = await db.execute(select(MarketListing).where(MarketListing.id == listing_id))
    listing = listing_result.scalar_one_or_none()
    if not listing or not listing.is_active:
        raise ValueError("Listing not found or no longer available")

    if listing.quantity != -1 and listing.quantity < quantity:
        raise ValueError("Insufficient quantity available")

    total_cost = listing.price_crypto * quantity

    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = stats_result.scalar_one_or_none()
    if not stats or stats.crypto < total_cost:
        raise ValueError("Insufficient crypto balance")

    stats.crypto -= total_cost

    tx = Transaction(
        player_id=player_id,
        amount=-total_cost,
        currency="crypto",
        description=f"Market purchase: {listing.item_name} x{quantity}",
        reference_id=listing.id,
    )
    db.add(tx)

    inv_result = await db.execute(
        select(PlayerInventory).where(
            PlayerInventory.player_id == player_id,
            PlayerInventory.item_name == listing.item_name,
        )
    )
    existing = inv_result.scalar_one_or_none()
    if existing:
        existing.quantity += quantity
    else:
        inv = PlayerInventory(
            player_id=player_id,
            item_type=listing.item_type,
            item_name=listing.item_name,
            quantity=quantity,
            effect_data=listing.effect_data,
            uses_remaining=listing.effect_data.get("uses", -1),
        )
        db.add(inv)

    if listing.quantity != -1:
        listing.quantity -= quantity
        if listing.quantity <= 0:
            listing.is_active = False

    await db.commit()

    return {
        "purchased": listing.item_name,
        "quantity": quantity,
        "cost": total_cost,
        "message": f"Acquired: {listing.item_name}. Transfer confirmed.",
    }


async def get_transaction_history(
    db: AsyncSession, player_id: uuid.UUID, limit: int = 20
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.player_id == player_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
