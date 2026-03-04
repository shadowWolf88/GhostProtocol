import pytest
import uuid


@pytest.mark.asyncio
async def test_skill_level_from_xp():
    from app.services.skill_service import get_player_skill_level
    from app.models.player import PlayerStats

    stats = PlayerStats(player_id=uuid.uuid4(), xp_exploitation=0)
    assert get_player_skill_level(stats, "exploitation") == 0

    stats.xp_exploitation = 999
    assert get_player_skill_level(stats, "exploitation") == 0

    stats.xp_exploitation = 1000
    assert get_player_skill_level(stats, "exploitation") == 1

    stats.xp_exploitation = 10000
    assert get_player_skill_level(stats, "exploitation") == 10

    stats.xp_exploitation = 50000
    assert get_player_skill_level(stats, "exploitation") == 50


@pytest.mark.asyncio
async def test_abilities_unlock_by_tier():
    from app.services.skill_service import get_unlocked_abilities
    from app.models.player import PlayerStats

    stats = PlayerStats(player_id=uuid.uuid4(), xp_exploitation=0)
    unlocked = get_unlocked_abilities(stats)
    assert len(unlocked["exploitation"]) == 0

    stats.xp_exploitation = 10000
    unlocked = get_unlocked_abilities(stats)
    tier1_and_2 = [a for a in unlocked["exploitation"] if a["tier"] <= 2]
    assert len(tier1_and_2) == 2


@pytest.mark.asyncio
async def test_operation_modifiers_computed():
    from app.services.skill_service import get_operation_modifiers
    from app.models.player import PlayerStats

    stats = PlayerStats(player_id=uuid.uuid4(), xp_exploitation=1000)
    mods = get_operation_modifiers(stats)
    assert "exploit_success_bonus" in mods
    assert mods["exploit_success_bonus"] >= 0.05


@pytest.mark.asyncio
async def test_xp_award_correct_tree(test_db, test_player):
    from app.services.skill_service import award_skill_xp, get_player_skill_level
    from app.models.player import PlayerStats
    from sqlalchemy import select

    player_id = test_player["player"].id
    result = await test_db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = result.scalar_one()

    old_level = get_player_skill_level(stats, "social")
    award_result = await award_skill_xp(test_db, player_id, "social", 5000)

    assert award_result["tree"] == "social"
    assert award_result["xp_gained"] == 5000
    assert award_result["new_xp"] == 5000

    result = await test_db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    updated = result.scalar_one()
    assert updated.xp_social == 5000


@pytest.mark.asyncio
async def test_skills_endpoint(test_client, test_player):
    response = await test_client.get(
        "/api/v1/skills",
        headers=test_player["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    trees = {t["key"] for t in data}
    assert "social" in trees
    assert "exploitation" in trees
    assert "cryptography" in trees
    assert "hardware" in trees
    assert "counterintel" in trees
    assert "economics" in trees
