import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_models_empty(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/ml-models", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_upload_custom_model(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/ml-models",
        files={"file": ("custom.pt", b"fake-weights-bytes", "application/octet-stream")},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "custom.pt"
    assert data["format"] == "pt"
    assert data["source"] == "custom"
    assert data["is_default"] is False
    assert data["size_bytes"] == len(b"fake-weights-bytes")

    list_resp = await client.get("/api/v1/ml-models", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_upload_rejects_bad_extension(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/ml-models",
        files={"file": ("model.exe", b"not-a-model", "application/octet-stream")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_rejects_oversize(client: AsyncClient, auth_headers, monkeypatch):
    import app.modules.ml_models.router as router_module

    monkeypatch.setattr(router_module, "MAX_UPLOAD_SIZE", 10)  # 10 bytes, for the test
    resp = await client.post(
        "/api/v1/ml-models",
        files={"file": ("custom.pt", b"this-is-more-than-ten-bytes", "application/octet-stream")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_set_default_and_delete(client: AsyncClient, auth_headers):
    upload_resp = await client.post(
        "/api/v1/ml-models",
        files={"file": ("custom2.pt", b"weights", "application/octet-stream")},
        headers=auth_headers,
    )
    model_id = upload_resp.json()["id"]

    default_resp = await client.put(
        f"/api/v1/ml-models/{model_id}/default", headers=auth_headers
    )
    assert default_resp.status_code == 200
    assert default_resp.json()["is_default"] is True

    delete_resp = await client.delete(
        f"/api/v1/ml-models/{model_id}", headers=auth_headers
    )
    assert delete_resp.status_code == 204

    list_resp = await client.get("/api/v1/ml-models", headers=auth_headers)
    assert list_resp.json() == []


@pytest.mark.asyncio
async def test_cannot_delete_stock_model(client: AsyncClient, auth_headers, db_session):
    from app.modules.ml_models.service import register_stock_model

    stock = await register_stock_model(
        db_session, "yolov8n.pt", class_names=["person", "car"], make_default=True
    )
    await db_session.commit()

    resp = await client.delete(f"/api/v1/ml-models/{stock.id}", headers=auth_headers)
    assert resp.status_code == 400
