import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_create_operation_success(test_client, test_player_with_stats, test_node, mock_anthropic):
    from app.models.player import Device
    from sqlalchemy import select
    player = test_player_with_stats["player"]

    result = await test_client.get(
        "/api/v1/players/me/devices",
        headers=test_player_with_stats["headers"],
    )
    devices = result.json()
    device_id = devices[0]["id"]

    with patch("app.services.redis_service.get_node_alert_level", new_callable=AsyncMock, return_value=0):
        response = await test_client.post(
            "/api/v1/operations",
            json={
                "node_key": "test_corp_node",
                "device_id": device_id,
                "approach": "technical",
            },
            headers=test_player_with_stats["headers"],
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recon"
    assert data["node_key"] == "test_corp_node"


@pytest.mark.asyncio
async def test_create_operation_invalid_node(test_client, test_player_with_stats, mock_anthropic):
    result = await test_client.get(
        "/api/v1/players/me/devices",
        headers=test_player_with_stats["headers"],
    )
    devices = result.json()
    device_id = devices[0]["id"]

    response = await test_client.post(
        "/api/v1/operations",
        json={
            "node_key": "nonexistent_node",
            "device_id": device_id,
        },
        headers=test_player_with_stats["headers"],
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_skill_level_from_xp(test_db):
    from app.services.skill_service import get_player_skill_level
    from app.models.player import PlayerStats
    import uuid

    stats = PlayerStats(
        player_id=uuid.uuid4(),
        xp_exploitation=0,
    )
    assert get_player_skill_level(stats, "exploitation") == 0

    stats.xp_exploitation = 1000
    assert get_player_skill_level(stats, "exploitation") == 1

    stats.xp_exploitation = 10000
    assert get_player_skill_level(stats, "exploitation") == 10


@pytest.mark.asyncio
async def test_psych_state_updates(test_db):
    from app.services.psych_service import update_psych_after_operation, apply_psych_consequences
    from app.models.player import PsychState, Player
    import uuid

    player_id = uuid.uuid4()
    player = Player(
        id=player_id,
        handle="test_psych_player",
        email="psych@test.com",
        hashed_password="hash",
    )
    psych = PsychState(
        player_id=player_id,
        stress=0,
        burnout=0,
        sleep_debt=0,
        last_updated=__import__("datetime").datetime.utcnow(),
    )
    test_db.add(player)
    test_db.add(psych)
    await test_db.commit()

    phase_results = [
        {"phase": "recon", "success": True, "heat_generated": 5},
        {"phase": "exploit", "success": True, "heat_generated": 20},
        {"phase": "persist", "success": True, "heat_generated": 15},
        {"phase": "monetize", "success": True, "heat_generated": 25},
    ]
    await update_psych_after_operation(test_db, player_id, phase_results)

    from sqlalchemy import select
    result = await test_db.execute(select(PsychState).where(PsychState.player_id == player_id))
    updated = result.scalar_one()
    assert updated.stress > 0
    assert updated.burnout > 0


@pytest.mark.asyncio
async def test_heat_increases_after_operation(test_db):
    from app.services.heat_service import add_heat, get_player_heat
    from app.models.player import Player
    import uuid

    player_id = uuid.uuid4()
    player = Player(
        id=player_id,
        handle="heat_test",
        email="heat@test.com",
        hashed_password="hash",
    )
    test_db.add(player)
    await test_db.commit()

    with patch("app.services.redis_service.get_go_dark", new_callable=AsyncMock, return_value=None):
        await add_heat(test_db, player_id, "federal", 30)
        status = await get_player_heat(test_db, player_id)

    assert status.domains["federal"].level == 30
    assert status.threat_tier >= 1
