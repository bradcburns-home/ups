from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.server import app


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data


@pytest.mark.asyncio
async def test_api_status_success(transport):
    mock_data = {
        "ups_status": "OL",
        "battery_charge": 100.0,
        "ups_load": 23.0,
        "timestamp": "2026-03-14T15:00:00-04:00",
    }
    with patch("app.nut_client.query_ups", return_value=mock_data):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["ups_status"] == "OL"


@pytest.mark.asyncio
async def test_api_status_nut_error(transport):
    mock_data = {"status": "error", "message": "NUT daemon unreachable", "retryable": True}
    with patch("app.nut_client.query_ups", return_value=mock_data):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/status")
    assert resp.status_code == 503
    assert resp.json()["retryable"] is True


@pytest.mark.asyncio
async def test_api_history_success(transport):
    mock_data = {"readings": [{"timestamp": "2026-03-14T15:00:00-04:00", "battery_charge": 100.0}], "count": 1, "range": "24h"}
    with patch("app.bq_client.query_history", return_value=mock_data):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/history?range=24h")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


@pytest.mark.asyncio
async def test_api_history_invalid_range(transport):
    mock_data = {"status": "error", "message": "Invalid range '99h'", "retryable": False}
    with patch("app.bq_client.query_history", return_value=mock_data):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/history?range=99h")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_dashboard_page(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
    assert resp.status_code == 200
    assert "The Power Play" in resp.text
    assert "DTE" in resp.text


@pytest.mark.asyncio
async def test_404_page(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/nonexistent")
    assert resp.status_code == 404
    assert "reliable as DTE" in resp.text
