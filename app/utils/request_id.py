from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request, Response

REQUEST_ID_HEADER_NAME = "X-Request-ID"


def build_request_id() -> str:
    return f"req_{uuid4().hex}"


def _request_id_from_header(request: Request) -> str | None:
    request_id = request.headers.get(REQUEST_ID_HEADER_NAME)
    if request_id is None:
        return None

    normalized_request_id = request_id.strip()
    if not normalized_request_id:
        return None

    return normalized_request_id


def register_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next) -> Response:
        request_id = _request_id_from_header(request) or build_request_id()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers.setdefault(REQUEST_ID_HEADER_NAME, request_id)
        return response
