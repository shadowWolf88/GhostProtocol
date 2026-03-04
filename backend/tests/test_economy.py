import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_wallet_initial_balance(test_client, test_player):
    response = await test_client.get(
        "/api/v1/economy/wallet",
        headers=test_player["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["crypto"] == 500


@pytest.mark.asyncio
async def test_transaction_recorded(test_client, test_player, test_db):
    from app.services.economy_service import transfer_funds
    player = test_player["player"]
    await transfer_funds(test_db, player.id, "crypto", 100, "Test credit")

    response = await test_client.get(
        "/api/v1/economy/transactions",
        headers=test_player["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_laundering_chain_steps_by_skill_level(test_db, test_player):
    from app.services.economy_service import launder_preview
    from app.models.player import PlayerStats
    from sqlalchemy import select
    import uuid

    player_id = test_player["player"].id

    result = await test_db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = result.scalar_one()

    stats.xp_economics = 0
    await test_db.commit()

    chain_low = await launder_preview(test_db, player_id, 1000)
    stats.xp_economics = 30000
    await test_db.commit()
    chain_high = await launder_preview(test_db, player_id, 1000)

    assert len(chain_low.steps) >= len(chain_high.steps)
    assert chain_high.total_fees <= chain_low.total_fees


@pytest.mark.asyncio
async def test_purchase_item_insufficient_funds(test_client, test_player, test_db):
    from app.models.player import MarketListing
    listing = MarketListing(
        item_type="tool",
        item_name="Expensive Tool",
        description="Too expensive",
        price_crypto=99999,
        quantity=-1,
    )
    test_db.add(listing)
    await test_db.commit()

    response = await test_client.post(
        "/api/v1/economy/market/buy",
        json={"listing_id": str(listing.id), "quantity": 1},
        headers=test_player["headers"],
    )
    assert response.status_code == 400
