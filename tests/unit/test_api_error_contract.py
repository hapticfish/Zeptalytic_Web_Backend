from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_invalid_uuid_returns_standard_validation_error_shape() -> None:
    response = client.get("/api/v1/rewards/not-a-uuid/summary")

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Request validation failed."
    assert payload["error"]["details"] == {
        "errors": [
            {
                "loc": ["path", "account_id"],
                "msg": payload["error"]["details"]["errors"][0]["msg"],
                "type": "uuid_parsing",
            }
        ]
    }
