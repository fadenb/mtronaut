import pytest
from httpx import AsyncClient, ASGITransport
from mtronaut.main import app, get_client_ip
from fastapi import Request
from unittest.mock import MagicMock
from fastapi.responses import JSONResponse

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "<h1>Network Analysis Toolkit</h1>" in response.text

@pytest.mark.asyncio
@pytest.mark.parametrize("client, expected_ip", [
    (None, None),
    (MagicMock(host="127.0.0.1"), "127.0.0.1"),
])
async def test_get_client_ip_unit(client, expected_ip):
    request = MagicMock(spec=Request)
    request.client = client
    response = await get_client_ip(request)
    assert isinstance(response, JSONResponse)
    # Manually construct the expected JSON string, handling the None case
    if expected_ip is None:
        expected_body = b'{"client_ip":null}'
    else:
        expected_body = f'{{"client_ip":"{expected_ip}"}}'.encode()
    assert response.body == expected_body