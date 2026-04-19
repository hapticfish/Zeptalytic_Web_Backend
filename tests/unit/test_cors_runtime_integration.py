from fastapi.testclient import TestClient

from app.main import app
from app.utils import REQUEST_ID_HEADER_NAME


client = TestClient(app)


def test_preflight_request_allows_configured_vite_origin_with_credentials() -> None:
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers[REQUEST_ID_HEADER_NAME].startswith("req_")


def test_simple_request_echoes_configured_origin_and_credentials_headers() -> None:
    response = client.get(
        "/health",
        headers={"Origin": "http://127.0.0.1:5173"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers[REQUEST_ID_HEADER_NAME].startswith("req_")


def test_preflight_request_rejects_unconfigured_origin() -> None:
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers[REQUEST_ID_HEADER_NAME].startswith("req_")
