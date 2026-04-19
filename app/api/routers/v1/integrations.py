from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_discord_integration_service,
    require_normal_authenticated_session_context,
)
from app.schemas.integrations import (
    DiscordConnectInitiationResponse,
    DiscordIntegrationReadResponse,
)
from app.services import AuthenticatedSessionContext, DiscordIntegrationService

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/discord", response_model=DiscordIntegrationReadResponse)
def get_discord_integration_status(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
) -> DiscordIntegrationReadResponse:
    return service.get_integration(context.account_id)


@router.post("/discord/connect", response_model=DiscordConnectInitiationResponse)
def initiate_discord_connect(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
) -> DiscordConnectInitiationResponse:
    return DiscordConnectInitiationResponse(
        authorization_url=service.build_connect_url(context.account_id)
    )


@router.get("/discord/callback", response_model=DiscordIntegrationReadResponse)
def complete_discord_connect(
    code: str = Query(min_length=1),
    state: str | None = Query(default=None),
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
) -> DiscordIntegrationReadResponse:
    return service.complete_oauth_callback(context.account_id, code=code, state=state)


@router.post("/discord/disconnect", response_model=DiscordIntegrationReadResponse)
def disconnect_discord_integration(
    context: AuthenticatedSessionContext = Depends(require_normal_authenticated_session_context),
    service: DiscordIntegrationService = Depends(get_discord_integration_service),
) -> DiscordIntegrationReadResponse:
    return service.disconnect_discord_account(context.account_id)
