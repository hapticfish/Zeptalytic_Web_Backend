from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import CursorPageResponse, MutationSuccessResponse


class BillingAddressSummary(BaseModel):
    address_id: UUID
    address_type: Literal["billing", "shipping"]
    label: str | None = None
    full_name: str
    formatted_address: str | None = None
    country_code: str
    is_primary: bool


class BillingAddressBookSummary(BaseModel):
    source: Literal["parent_owned"] = "parent_owned"
    total_saved_count: int = Field(ge=0)
    addresses: list[BillingAddressSummary] = Field(default_factory=list)


class BillingPaymentMethodSummary(BaseModel):
    source: Literal["pay_live", "pay_projection"]
    provider: str
    method_type: str
    display_label: str
    brand: str | None = None
    last4: str | None = None
    wallet_first4: str | None = None
    wallet_last4: str | None = None
    exp_month: int | None = Field(default=None, ge=1, le=12)
    exp_year: int | None = Field(default=None, ge=2000, le=9999)
    cardholder_name: str | None = None
    billing_country: str | None = None
    paypal_email_masked: str | None = None
    is_default: bool
    last_used_at: datetime | None = None
    status: str


class BillingSubscriptionSummary(BaseModel):
    source: Literal["pay_projection", "pay_live"]
    product_code: str
    product_name: str
    plan_code: str
    subscription_status: str
    billing_interval: str
    current_charge_amount_cents: int | None = None
    currency: str | None = None
    next_payment_at: datetime | None = None
    cancel_at_period_end: bool = False


class BillingTransactionSummary(BaseModel):
    source: Literal["pay_live", "pay_projection"]
    occurred_at: datetime
    description: str
    amount_cents: int
    currency: str
    status: str | None = None
    product_code: str | None = None


class BillingTransactionsPage(CursorPageResponse[BillingTransactionSummary]):
    pass


class BillingSnapshotPayProjectionSummary(BaseModel):
    source: Literal["pay_projection"] = "pay_projection"
    subscribed_products: list[BillingSubscriptionSummary] = Field(default_factory=list)
    current_payment_method: BillingPaymentMethodSummary | None = None


class BillingSnapshotResponse(BaseModel):
    pay_integration_status: Literal["available", "projection_only", "unavailable"]
    pay_projection_billing: BillingSnapshotPayProjectionSummary | None = None
    parent_billing_addresses: BillingAddressBookSummary


class BillingSubscriptionsResponse(BaseModel):
    pay_integration_status: Literal["available", "projection_only", "unavailable"]
    pay_subscriptions: list[BillingSubscriptionSummary] = Field(default_factory=list)


class BillingPaymentMethodsResponse(BaseModel):
    pay_integration_status: Literal["available", "projection_only", "unavailable"]
    pay_payment_methods: list[BillingPaymentMethodSummary] = Field(default_factory=list)


class BillingTransactionsResponse(BaseModel):
    pay_integration_status: Literal["available", "projection_only", "unavailable"]
    pay_transactions: BillingTransactionsPage


class BillingActionResult(BaseModel):
    pay_redirect_url: str | None = None
    pay_session_id: str | None = None
    pay_client_secret: str | None = None


class BillingActionInitiationResponse(MutationSuccessResponse):
    action: Literal[
        "checkout",
        "subscription_change",
        "subscription_cancel",
        "subscription_restart",
        "promo_code_validation",
        "promo_code_apply",
    ]
    pay_result: BillingActionResult | None = None


class BillingCheckoutInitiationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_code: str = Field(min_length=1, max_length=64)
    plan_code: str = Field(min_length=1, max_length=128)
    billing_interval: str = Field(min_length=1, max_length=32)
    success_url: str = Field(min_length=1, max_length=2048)
    cancel_url: str = Field(min_length=1, max_length=2048)
    promo_code: str | None = Field(default=None, min_length=1, max_length=64)


class BillingSubscriptionChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_code: str = Field(min_length=1, max_length=64)
    target_plan_code: str = Field(min_length=1, max_length=128)
    target_billing_interval: str = Field(min_length=1, max_length=32)
    promo_code: str | None = Field(default=None, min_length=1, max_length=64)


class BillingSubscriptionLifecycleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_code: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=512)


class BillingPromoCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    promo_code: str = Field(min_length=1, max_length=64)
    product_code: str | None = Field(default=None, min_length=1, max_length=64)
    plan_code: str | None = Field(default=None, min_length=1, max_length=128)
