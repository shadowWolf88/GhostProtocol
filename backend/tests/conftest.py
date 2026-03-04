import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, patch

TEST_DB_URL = "postgresql+asyncpg://ghost:protocol@localhost:5432/ghostprotocol_test"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    from app.database import Base

    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def test_client(test_db):
    from app.main import app
    from app.core.dependencies import get_db

    async def override_db():
        yield test_db

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_player(test_client, test_db):
    response = await test_client.post("/api/v1/auth/register", json={
        "handle": "testoperator",
        "email": "test@ghost.protocol",
        "password": "testpassword123",
    })
    assert response.status_code == 201
    data = response.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from app.models.player import Player
    from sqlalchemy import select
    result = await test_db.execute(select(Player).where(Player.handle == "testoperator"))
    player = result.scalar_one()

    return {"player": player, "token": token, "headers": headers}


@pytest_asyncio.fixture
async def test_player_with_stats(test_player, test_db):
    from app.models.player import PlayerStats
    from sqlalchemy import select
    result = await test_db.execute(
        select(PlayerStats).where(PlayerStats.player_id == test_player["player"].id)
    )
    stats = result.scalar_one()
    stats.xp_exploitation = 10000
    stats.xp_social = 5000
    stats.crypto = 5000
    stats.energy = 100
    await test_db.commit()
    return test_player


@pytest_asyncio.fixture
async def test_node(test_db):
    from app.models.player import WorldNode
    node = WorldNode(
        node_key="test_corp_node",
        name="Test Corporation",
        description="A test target.",
        category="corporate",
        tier=1,
        vulnerability_score=80,
        patch_rate=1,
        defender_tier=1,
        heat_multiplier=1.0,
        base_crypto_reward=100,
        base_reputation_reward=10,
    )
    test_db.add(node)
    await test_db.commit()
    return node


@pytest.fixture
def mock_anthropic():
    with patch("app.services.ai_service._call_claude", new_callable=AsyncMock) as mock:
        mock.return_value = "Mock AI response for testing."
        yield mock
