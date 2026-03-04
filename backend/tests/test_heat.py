import pytest
from unittest.mock import AsyncMock, patch
import uuid


@pytest.mark.asyncio
async def test_heat_added_correctly(test_db):
    from app.services.heat_service import add_heat, get_player_heat
    from app.models.player import Player

    player_id = uuid.uuid4()
    player = Player(id=player_id, handle="heat_test_2", email="heat2@test.com", hashed_password="x")
    test_db.add(player)
    await test_db.commit()

    with patch("app.services.redis_service.get_go_dark", new_callable=AsyncMock, return_value=None):
        with patch("app.services.redis_service.set_player_surveillance", new_callable=AsyncMock):
            await add_heat(test_db, player_id, "local_leo", 25)
            status = await get_player_heat(test_db, player_id)

    assert status.domains["local_leo"].level == 25


@pytest.mark.asyncio
async def test_threat_tier_calculation(test_db):
    from app.services.heat_service import add_heat, get_player_heat
    from app.models.player import Player

    player_id = uuid.uuid4()
    player = Player(id=player_id, handle="tier_test", email="tier@test.com", hashed_password="x")
    test_db.add(player)
    await test_db.commit()

    with patch("app.services.redis_service.get_go_dark", new_callable=AsyncMock, return_value=None):
        with patch("app.services.redis_service.set_player_surveillance", new_callable=AsyncMock):
            status = await get_player_heat(test_db, player_id)
            assert status.threat_tier == 1

            await add_heat(test_db, player_id, "federal", 80)
            await add_heat(test_db, player_id, "intelligence", 60)
            status = await get_player_heat(test_db, player_id)
            assert status.threat_tier >= 3


@pytest.mark.asyncio
async def test_go_dark_multiplies_decay():
    from app.services.heat_service import _calculate_decay
    from app.data.constants import GAME_CONSTANTS

    base_level = 50.0
    decay_rate = 2.0
    hours = 10.0

    normal_decay = _calculate_decay(base_level, decay_rate, hours, 1.0)
    dark_decay = _calculate_decay(base_level, decay_rate, hours, GAME_CONSTANTS["GO_DARK_DECAY_MULTIPLIER"])

    assert dark_decay < normal_decay
    assert dark_decay == _calculate_decay(base_level, decay_rate * 3, hours, 1.0)


@pytest.mark.asyncio
async def test_heat_decay_preview(test_client, test_player):
    with patch("app.services.redis_service.get_go_dark", new_callable=AsyncMock, return_value=None):
        response = await test_client.get(
            "/api/v1/heat/preview?hours=24",
            headers=test_player["headers"],
        )
    assert response.status_code == 200
    data = response.json()
    assert "projected" in data
    assert "current_tier" in data
