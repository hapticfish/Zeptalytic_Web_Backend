from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.errors import build_error_response
from app.services.reward_notification_service import (
    RewardNotificationNotFoundError,
    RewardNotificationQueueNotFoundError,
)
from app.services.reward_objective_service import RewardObjectivesNotFoundError
from app.services.reward_summary_service import RewardSummaryNotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RewardSummaryNotFoundError, reward_summary_not_found_handler)
    app.add_exception_handler(RewardObjectivesNotFoundError, reward_objectives_not_found_handler)
    app.add_exception_handler(
        RewardNotificationQueueNotFoundError,
        reward_notification_queue_not_found_handler,
    )
    app.add_exception_handler(
        RewardNotificationNotFoundError,
        reward_notification_not_found_handler,
    )
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def reward_summary_not_found_handler(
    request: Request,
    exc: RewardSummaryNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_summary_not_found",
        message="Reward summary not found.",
        request_id=_request_id(request),
    )


async def reward_objectives_not_found_handler(
    request: Request,
    exc: RewardObjectivesNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_objectives_not_found",
        message="Reward objectives not found.",
        request_id=_request_id(request),
    )


async def reward_notification_queue_not_found_handler(
    request: Request,
    exc: RewardNotificationQueueNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_notification_queue_not_found",
        message="Reward notification queue not found.",
        request_id=_request_id(request),
    )


async def reward_notification_not_found_handler(
    request: Request,
    exc: RewardNotificationNotFoundError,
) -> JSONResponse:
    del exc
    return build_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="reward_notification_not_found",
        message="Reward notification not found.",
        request_id=_request_id(request),
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details = {
        "errors": [
            {
                "loc": list(error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
    }
    return build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="validation_error",
        message="Request validation failed.",
        details=details,
        request_id=_request_id(request),
    )
