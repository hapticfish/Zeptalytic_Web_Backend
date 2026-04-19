from __future__ import annotations

from app.utils import REQUEST_ID_HEADER_NAME


def assert_standard_error_response(
    response,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, object],
) -> None:
    assert response.status_code == status_code
    payload = response.json()
    request_id = payload["error"]["request_id"]

    assert request_id
    assert response.headers[REQUEST_ID_HEADER_NAME] == request_id
    assert payload == {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }
