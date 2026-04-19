from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import (
    get_audit_hook,
    get_discord_integration_service,
    get_rate_limiter,
    require_normal_authenticated_session_context,
)
from app.core.config import settings
from app.schemas.integrations import (
    DiscordConnectInitiationResponse,
    DiscordIntegrationReadResponse,
)
from app.services import AuthenticatedSessionContext, DiscordIntegrationService
from app.utils.audit import AuditHook, emit_audit_event
from app.utils.rate_limits import (
    InMemoryRateLimiter,
    build_authenticated_rate_limit_key,
    build_discord_callback_rate_limit_policy,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/discord", response_model=DiscordIntegrationReadResponse)
def get_discord_integration_status(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
) -> DiscordIntegrationReadResponse:
    return service.get_integration(context.account_id)


@router.post("/discord/connect", response_model=DiscordConnectInitiationResponse)
def initiate_discord_connect(
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> DiscordConnectInitiationResponse:
    emit_audit_event(
        audit_hook,
        request=request,
        action="integrations.discord_connect",
        outcome="attempt",
        account_id=context.account_id,
    )
    response = DiscordConnectInitiationResponse(
        authorization_url=service.build_connect_url(context.account_id)
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="integrations.discord_connect",
        outcome="success",
        account_id=context.account_id,
    )
    return response


@router.get("/discord/callback", response_model=DiscordIntegrationReadResponse)
def complete_discord_connect(
    request: Request,
    code: str = Query(min_length=1),
    state: str | None = Query(default=None),
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> DiscordIntegrationReadResponse:
    rate_limiter.check(
        action="discord_callback",
        key=build_authenticated_rate_limit_key(request, account_id=context.account_id),
        policy=build_discord_callback_rate_limit_policy(settings),
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="integrations.discord_callback",
        outcome="attempt",
        account_id=context.account_id,
        metadata={"state_present": state is not None},
    )
    response = service.complete_oauth_callback(context.account_id, code=code, state=state)
    emit_audit_event(
        audit_hook,
        request=request,
        action="integrations.discord_callback",
        outcome="success",
        account_id=context.account_id,
        metadata={"state_present": state is not None},
    )
    return response


@router.post("/discord/disconnect", response_model=DiscordIntegrationReadResponse)
def disconnect_discord_integration(
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> DiscordIntegrationReadResponse:
    emit_audit_event(
        audit_hook,
        request=request,
        action="integrations.discord_disconnect",
        outcome="attempt",
        account_id=context.account_id,
    )
    response = service.disconnect_discord_account(context.account_id)
    emit_audit_event(
        audit_hook,
        request=request,
        action="integrations.discord_disconnect",
        outcome="success",
        account_id=context.account_id,
    )
    return response
