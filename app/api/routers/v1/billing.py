from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_billing_summary_service, require_authenticated_session_context
from app.schemas.billing import (
    BillingActionInitiationResponse,
    BillingCheckoutInitiationRequest,
    BillingPaymentMethodsResponse,
    BillingPromoCodeRequest,
    BillingSnapshotResponse,
    BillingSubscriptionChangeRequest,
    BillingSubscriptionLifecycleRequest,
    BillingSubscriptionsResponse,
    BillingTransactionsResponse,
)
from app.services import AuthenticatedSessionContext, BillingSummaryService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/snapshot", response_model=BillingSnapshotResponse)
def get_billing_snapshot(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingSnapshotResponse:
    return service.get_snapshot(context.account_id)


@router.get("/subscriptions", response_model=BillingSubscriptionsResponse)
def list_billing_subscriptions(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingSubscriptionsResponse:
    return service.list_subscriptions(context.account_id)


@router.get("/payment-methods", response_model=BillingPaymentMethodsResponse)
def list_billing_payment_methods(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingPaymentMethodsResponse:
    return service.list_payment_methods(context.account_id)


@router.get("/transactions", response_model=BillingTransactionsResponse)
def list_billing_transactions(
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
    limit: int = Query(default=25, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> BillingTransactionsResponse:
    return service.list_transactions(context.account_id, limit=limit, cursor=cursor)


@router.post("/checkout", response_model=BillingActionInitiationResponse)
def initiate_billing_checkout(
    payload: BillingCheckoutInitiationRequest,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingActionInitiationResponse:
    return service.initiate_checkout(context.account_id, payload)


@router.post("/subscription-change", response_model=BillingActionInitiationResponse)
def initiate_billing_subscription_change(
    payload: BillingSubscriptionChangeRequest,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingActionInitiationResponse:
    return service.initiate_subscription_change(context.account_id, payload)


@router.post("/subscription-cancel", response_model=BillingActionInitiationResponse)
def initiate_billing_subscription_cancel(
    payload: BillingSubscriptionLifecycleRequest,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingActionInitiationResponse:
    return service.initiate_subscription_cancel(context.account_id, payload)


@router.post("/subscription-restart", response_model=BillingActionInitiationResponse)
def initiate_billing_subscription_restart(
    payload: BillingSubscriptionLifecycleRequest,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingActionInitiationResponse:
    return service.initiate_subscription_restart(context.account_id, payload)


@router.post("/promo-code/validate", response_model=BillingActionInitiationResponse)
def validate_billing_promo_code(
    payload: BillingPromoCodeRequest,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingActionInitiationResponse:
    return service.validate_promo_code(context.account_id, payload)


@router.post("/promo-code/apply", response_model=BillingActionInitiationResponse)
def apply_billing_promo_code(
    payload: BillingPromoCodeRequest,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
) -> BillingActionInitiationResponse:
    return service.apply_promo_code(context.account_id, payload)
