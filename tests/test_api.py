import pytest
from httpx import AsyncClient, ASGITransport
from mtronaut.main import app

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "<h1>Mtronaut - Network Analysis Web Interface</h1>" in response.text