from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.exception_handlers import register_exception_handlers
from app.integrations import DiscordOAuthStateValidationError
from app.utils import REQUEST_ID_HEADER_NAME, register_request_id_middleware


def test_request_id_middleware_adds_header_to_successful_responses() -> None:
    local_app = FastAPI()
    register_request_id_middleware(local_app)

    @local_app.get("/success")
    def success() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(local_app).get("/success")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER_NAME].startswith("req_")


def test_request_id_middleware_propagates_into_standard_error_contract() -> None:
    local_app = FastAPI()
    register_request_id_middleware(local_app)
    register_exception_handlers(local_app)

    @local_app.get("/failure")
    def failure() -> None:
        raise DiscordOAuthStateValidationError("expired_state")

    response = TestClient(local_app).get("/failure")

    assert response.status_code == 400
    assert response.headers[REQUEST_ID_HEADER_NAME].startswith("req_")
    assert response.json() == {
        "error": {
            "code": "discord_oauth_state_invalid",
            "message": "Discord OAuth callback state is invalid.",
            "details": {"reason": "expired_state"},
            "request_id": response.headers[REQUEST_ID_HEADER_NAME],
        }
    }


def test_request_id_middleware_reuses_non_empty_inbound_request_id_header() -> None:
    local_app = FastAPI()
    register_request_id_middleware(local_app)

    @local_app.get("/echo")
    def echo() -> dict[str, str]:
        return {"status": "ok"}

    response = TestClient(local_app).get(
        "/echo",
        headers={REQUEST_ID_HEADER_NAME: "req_client_supplied"},
    )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER_NAME] == "req_client_supplied"
