import pytest


@pytest.mark.asyncio
async def test_register_success(test_client):
    response = await test_client.post("/api/v1/auth/register", json={
        "handle": "ghostoperator",
        "email": "ghost@protocol.net",
        "password": "securepassword123",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["handle"] == "ghostoperator"


@pytest.mark.asyncio
async def test_register_duplicate_handle(test_client, test_player):
    response = await test_client.post("/api/v1/auth/register", json={
        "handle": "testoperator",
        "email": "different@email.com",
        "password": "password123",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client, test_player):
    response = await test_client.post("/api/v1/auth/register", json={
        "handle": "differenthandle",
        "email": "test@ghost.protocol",
        "password": "password123",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_handle_chars(test_client):
    response = await test_client.post("/api/v1/auth/register", json={
        "handle": "invalid handle!",
        "email": "valid@email.com",
        "password": "password123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(test_client, test_player):
    response = await test_client.post("/api/v1/auth/login", json={
        "email": "test@ghost.protocol",
        "password": "testpassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["handle"] == "testoperator"


@pytest.mark.asyncio
async def test_login_wrong_password(test_client, test_player):
    response = await test_client.post("/api/v1/auth/login", json={
        "email": "test@ghost.protocol",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(test_client, test_player):
    response = await test_client.get(
        "/api/v1/auth/me",
        headers=test_player["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["handle"] == "testoperator"
    assert "stats" in data
    assert "psych" in data


@pytest.mark.asyncio
async def test_me_unauthenticated(test_client):
    response = await test_client.get("/api/v1/auth/me")
    assert response.status_code == 401
