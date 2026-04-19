from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import (
    get_audit_hook,
    get_billing_summary_service,
    get_rate_limiter,
    require_authenticated_session_context,
)
from app.core.config import settings
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
from app.utils.audit import AuditHook, emit_audit_event
from app.utils.rate_limits import (
    InMemoryRateLimiter,
    build_authenticated_rate_limit_key,
    build_billing_action_rate_limit_policy,
)

router = APIRouter(prefix="/billing", tags=["billing"])


def _enforce_billing_rate_limit(
    *,
    request: Request,
    context: AuthenticatedSessionContext,
    rate_limiter: InMemoryRateLimiter,
    action: str,
) -> None:
    rate_limiter.check(
        action=action,
        key=build_authenticated_rate_limit_key(request, account_id=context.account_id),
        policy=build_billing_action_rate_limit_policy(settings),
    )


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
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> BillingActionInitiationResponse:
    _enforce_billing_rate_limit(
        request=request,
        context=context,
        rate_limiter=rate_limiter,
        action="billing_checkout",
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.checkout",
        outcome="attempt",
        account_id=context.account_id,
        metadata={
            "product_code": payload.product_code,
            "plan_code": payload.plan_code,
            "billing_interval": payload.billing_interval,
        },
    )
    result = service.initiate_checkout(context.account_id, payload)
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.checkout",
        outcome="success",
        account_id=context.account_id,
        metadata={
            "product_code": payload.product_code,
            "plan_code": payload.plan_code,
            "billing_interval": payload.billing_interval,
        },
    )
    return result


@router.post("/subscription-change", response_model=BillingActionInitiationResponse)
def initiate_billing_subscription_change(
    payload: BillingSubscriptionChangeRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> BillingActionInitiationResponse:
    _enforce_billing_rate_limit(
        request=request,
        context=context,
        rate_limiter=rate_limiter,
        action="billing_subscription_change",
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.subscription_change",
        outcome="attempt",
        account_id=context.account_id,
        metadata={"product_code": payload.product_code, "plan_code": payload.plan_code},
    )
    result = service.initiate_subscription_change(context.account_id, payload)
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.subscription_change",
        outcome="success",
        account_id=context.account_id,
        metadata={"product_code": payload.product_code, "plan_code": payload.plan_code},
    )
    return result


@router.post("/subscription-cancel", response_model=BillingActionInitiationResponse)
def initiate_billing_subscription_cancel(
    payload: BillingSubscriptionLifecycleRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> BillingActionInitiationResponse:
    _enforce_billing_rate_limit(
        request=request,
        context=context,
        rate_limiter=rate_limiter,
        action="billing_subscription_cancel",
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.subscription_cancel",
        outcome="attempt",
        account_id=context.account_id,
        metadata={"subscription_id": payload.subscription_id},
    )
    result = service.initiate_subscription_cancel(context.account_id, payload)
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.subscription_cancel",
        outcome="success",
        account_id=context.account_id,
        metadata={"subscription_id": payload.subscription_id},
    )
    return result


@router.post("/subscription-restart", response_model=BillingActionInitiationResponse)
def initiate_billing_subscription_restart(
    payload: BillingSubscriptionLifecycleRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> BillingActionInitiationResponse:
    _enforce_billing_rate_limit(
        request=request,
        context=context,
        rate_limiter=rate_limiter,
        action="billing_subscription_restart",
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.subscription_restart",
        outcome="attempt",
        account_id=context.account_id,
        metadata={"subscription_id": payload.subscription_id},
    )
    result = service.initiate_subscription_restart(context.account_id, payload)
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.subscription_restart",
        outcome="success",
        account_id=context.account_id,
        metadata={"subscription_id": payload.subscription_id},
    )
    return result


@router.post("/promo-code/validate", response_model=BillingActionInitiationResponse)
def validate_billing_promo_code(
    payload: BillingPromoCodeRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> BillingActionInitiationResponse:
    _enforce_billing_rate_limit(
        request=request,
        context=context,
        rate_limiter=rate_limiter,
        action="billing_promo_validate",
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.promo_validate",
        outcome="attempt",
        account_id=context.account_id,
        metadata={"product_code": payload.product_code},
    )
    result = service.validate_promo_code(context.account_id, payload)
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.promo_validate",
        outcome="success",
        account_id=context.account_id,
        metadata={"product_code": payload.product_code},
    )
    return result


@router.post("/promo-code/apply", response_model=BillingActionInitiationResponse)
def apply_billing_promo_code(
    payload: BillingPromoCodeRequest,
    request: Request,
    context: AuthenticatedSessionContext = Depends(require_authenticated_session_context),
    service: BillingSummaryService = Depends(get_billing_summary_service),
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    audit_hook: AuditHook = Depends(get_audit_hook),
) -> BillingActionInitiationResponse:
    _enforce_billing_rate_limit(
        request=request,
        context=context,
        rate_limiter=rate_limiter,
        action="billing_promo_apply",
    )
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.promo_apply",
        outcome="attempt",
        account_id=context.account_id,
        metadata={"product_code": payload.product_code},
    )
    result = service.apply_promo_code(context.account_id, payload)
    emit_audit_event(
        audit_hook,
        request=request,
        action="billing.promo_apply",
        outcome="success",
        account_id=context.account_id,
        metadata={"product_code": payload.product_code},
    )
    return result
