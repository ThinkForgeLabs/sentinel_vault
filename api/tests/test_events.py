import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_events_empty(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/events", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_event_stats(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/events/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_today" in data
    assert "by_type" in data
    assert "alerted_count" in data