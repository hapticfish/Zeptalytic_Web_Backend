from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import CursorPageResponse, MutationSuccessResponse


def _normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


def _normalize_required_text(value: object) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError("Value must not be empty")
    return normalized


def _normalize_billing_interval(value: object) -> str:
    normalized = _normalize_required_text(value).upper().replace("-", "_")

    aliases = {
        "MONTH": "MONTHLY",
        "MONTHLY": "MONTHLY",
        "ANNUAL": "ANNUAL",
        "YEAR": "ANNUAL",
        "YEARLY": "ANNUAL",
    }

    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError("billing_interval must be MONTHLY or ANNUAL") from exc


def _normalize_optional_billing_interval(value: object) -> str | None:
    if value is None:
        return None
    return _normalize_billing_interval(value)


def _normalize_payment_rail(value: object) -> str:
    normalized = _normalize_required_text(value).upper().replace("-", "_")

    aliases = {
        "STRIPE": "STRIPE",
        "CARD": "STRIPE",
        "COINBASE": "COINBASE_COMMERCE",
        "COINBASE_COMMERCE": "COINBASE_COMMERCE",
        "CRYPTO": "COINBASE_COMMERCE",
    }

    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError("payment_rail must be STRIPE or COINBASE_COMMERCE") from exc


def _normalize_optional_payment_rail(value: object) -> str | None:
    if value is None:
        return None
    return _normalize_payment_rail(value)


def _normalize_apply_mode(value: object) -> str:
    normalized = _normalize_required_text(value).upper().replace("-", "_")

    aliases = {
        "CHECKOUT": "CHECKOUT",
        "EXISTING_SUBSCRIPTION": "EXISTING_SUBSCRIPTION",
        "SUBSCRIPTION": "EXISTING_SUBSCRIPTION",
    }

    try:
        return aliases[normalized]
    except KeyError as exc:
        raise ValueError("apply_mode must be CHECKOUT or EXISTING_SUBSCRIPTION") from exc


def _validate_exactly_one_billing_subject(
    *,
    product_code: str | None,
    bundle_code: str | None,
) -> None:
    has_product = product_code is not None
    has_bundle = bundle_code is not None

    if has_product == has_bundle:
        raise ValueError("Exactly one of product_code or bundle_code is required")


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
    bundle_code: str | None = None
    commercial_subject_type: Literal["product", "bundle"] | None = None
    commercial_subject_code: str | None = None
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


class BillingPaymentMethodSetupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    success_url: str = Field(min_length=1, max_length=2048)
    cancel_url: str = Field(min_length=1, max_length=2048)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)
    customer_email: str | None = Field(default=None, min_length=3, max_length=320)
    customer_name: str | None = Field(default=None, min_length=1, max_length=256)
    metadata: dict[str, object] | None = None

    @field_validator("success_url", "cancel_url", mode="before")
    @classmethod
    def _normalize_required_text_fields(cls, value: object) -> str:
        return _normalize_required_text(value)

    @field_validator("idempotency_key", "customer_email", "customer_name", mode="before")
    @classmethod
    def _normalize_optional_text_fields(cls, value: object) -> str | None:
        return _normalize_optional_text(value)


class BillingTransactionsResponse(BaseModel):
    pay_integration_status: Literal["available", "projection_only", "unavailable"]
    pay_transactions: BillingTransactionsPage


class BillingActionResult(BaseModel):
    status: str | None = None

    pay_redirect_url: str | None = None
    pay_session_id: str | None = None
    pay_client_secret: str | None = None
    provider: str | None = None
    created_customer: bool | None = None

    product_code: str | None = None
    bundle_code: str | None = None
    plan_code: str | None = None
    billing_interval: str | None = None
    payment_rail: str | None = None
    effective_at: datetime | None = None

    valid: bool | None = None
    promo_code: str | None = None
    normalized_code: str | None = None
    offer_code: str | None = None
    source_type: str | None = None
    source_key: str | None = None
    provider_subscription_id: str | None = None
    provider_discount_id: str | None = None
    discount_type: str | None = None
    discount_percent: int | None = None
    discount_amount_cents: int | None = None
    discount_months: int | None = None
    currency: str | None = None
    expires_at: datetime | None = None


class BillingActionInitiationResponse(MutationSuccessResponse):
    action: Literal[
        "checkout",
        "payment_method_setup",
        "subscription_change",
        "subscription_cancel",
        "subscription_restart",
        "promo_code_validation",
        "promo_code_apply",
        "discount_offer_claim",
    ]
    pay_result: BillingActionResult | None = None


class BillingCheckoutInitiationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    purchase_type: Literal["product", "bundle"] | None = None
    product_code: str | None = Field(default=None, min_length=1, max_length=128)
    plan_code: str | None = Field(default=None, min_length=1, max_length=128)
    bundle_code: str | None = Field(default=None, min_length=1, max_length=128)
    billing_interval: str = Field(min_length=1, max_length=32)
    payment_rail: str = Field(default="STRIPE", min_length=1, max_length=64)
    success_url: str | None = Field(default=None, min_length=1, max_length=2048)
    cancel_url: str | None = Field(default=None, min_length=1, max_length=2048)
    promo_code: str | None = Field(default=None, min_length=1, max_length=128)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("product_code", "plan_code", "bundle_code", "promo_code", "idempotency_key", mode="before")
    @classmethod
    def _normalize_optional_text_fields(cls, value: object) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("billing_interval", mode="before")
    @classmethod
    def _normalize_billing_interval_field(cls, value: object) -> str:
        return _normalize_billing_interval(value)

    @field_validator("payment_rail", mode="before")
    @classmethod
    def _normalize_payment_rail_field(cls, value: object) -> str:
        return _normalize_payment_rail(value)

    @model_validator(mode="after")
    def _validate_contract(self) -> "BillingCheckoutInitiationRequest":
        inferred_purchase_type = self.purchase_type
        if inferred_purchase_type is None:
            inferred_purchase_type = "bundle" if self.bundle_code is not None else "product"
            self.purchase_type = inferred_purchase_type

        if inferred_purchase_type == "product":
            if not self.product_code or not self.plan_code:
                raise ValueError("purchase_type=product requires product_code and plan_code")
            if self.bundle_code is not None:
                raise ValueError("purchase_type=product does not allow bundle_code")

        if inferred_purchase_type == "bundle":
            if not self.bundle_code:
                raise ValueError("purchase_type=bundle requires bundle_code")
            if self.product_code is not None or self.plan_code is not None:
                raise ValueError("purchase_type=bundle does not allow product_code or plan_code")

        if self.payment_rail == "STRIPE" and (not self.success_url or not self.cancel_url):
            raise ValueError("success_url and cancel_url are required when payment_rail=STRIPE")

        return self


class BillingSubscriptionChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_code: str | None = Field(default=None, min_length=1, max_length=128)
    bundle_code: str | None = Field(default=None, min_length=1, max_length=128)
    target_plan_code: str | None = Field(default=None, min_length=1, max_length=128)
    target_bundle_code: str | None = Field(default=None, min_length=1, max_length=128)
    target_billing_interval: str = Field(min_length=1, max_length=32)
    payment_rail: str | None = Field(default=None, min_length=1, max_length=64)
    success_url: str | None = Field(default=None, min_length=1, max_length=2048)
    cancel_url: str | None = Field(default=None, min_length=1, max_length=2048)
    promo_code: str | None = Field(default=None, min_length=1, max_length=128)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator(
        "product_code",
        "bundle_code",
        "target_plan_code",
        "target_bundle_code",
        "promo_code",
        "idempotency_key",
        mode="before",
    )
    @classmethod
    def _normalize_optional_text_fields(cls, value: object) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("target_billing_interval", mode="before")
    @classmethod
    def _normalize_target_billing_interval_field(cls, value: object) -> str:
        return _normalize_billing_interval(value)

    @field_validator("payment_rail", mode="before")
    @classmethod
    def _normalize_payment_rail_field(cls, value: object) -> str | None:
        return _normalize_optional_payment_rail(value)

    @model_validator(mode="after")
    def _validate_contract(self) -> "BillingSubscriptionChangeRequest":
        _validate_exactly_one_billing_subject(
            product_code=self.product_code,
            bundle_code=self.bundle_code,
        )

        has_target_plan = self.target_plan_code is not None
        has_target_bundle = self.target_bundle_code is not None
        if has_target_plan == has_target_bundle:
            raise ValueError("Exactly one of target_plan_code or target_bundle_code is required")

        return self


class BillingSubscriptionLifecycleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_code: str | None = Field(default=None, min_length=1, max_length=128)
    bundle_code: str | None = Field(default=None, min_length=1, max_length=128)
    reason: str | None = Field(default=None, max_length=512)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("product_code", "bundle_code", "reason", "idempotency_key", mode="before")
    @classmethod
    def _normalize_optional_text_fields(cls, value: object) -> str | None:
        return _normalize_optional_text(value)

    @model_validator(mode="after")
    def _validate_contract(self) -> "BillingSubscriptionLifecycleRequest":
        _validate_exactly_one_billing_subject(
            product_code=self.product_code,
            bundle_code=self.bundle_code,
        )
        return self


class BillingPromoCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    promo_code: str = Field(min_length=1, max_length=128)
    product_code: str | None = Field(default=None, min_length=1, max_length=128)
    bundle_code: str | None = Field(default=None, min_length=1, max_length=128)
    plan_code: str | None = Field(default=None, min_length=1, max_length=128)
    billing_interval: str | None = Field(default=None, min_length=1, max_length=32)
    payment_rail: str | None = Field(default=None, min_length=1, max_length=64)
    apply_mode: str = Field(default="CHECKOUT", min_length=1, max_length=64)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("promo_code", "product_code", "bundle_code", "plan_code", "idempotency_key", mode="before")
    @classmethod
    def _normalize_optional_text_fields(cls, value: object) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("billing_interval", mode="before")
    @classmethod
    def _normalize_billing_interval_field(cls, value: object) -> str | None:
        return _normalize_optional_billing_interval(value)

    @field_validator("payment_rail", mode="before")
    @classmethod
    def _normalize_payment_rail_field(cls, value: object) -> str | None:
        return _normalize_optional_payment_rail(value)

    @field_validator("apply_mode", mode="before")
    @classmethod
    def _normalize_apply_mode_field(cls, value: object) -> str:
        return _normalize_apply_mode(value)

    @model_validator(mode="after")
    def _validate_contract(self) -> "BillingPromoCodeRequest":
        _validate_exactly_one_billing_subject(
            product_code=self.product_code,
            bundle_code=self.bundle_code,
        )
        return self


class BillingDiscountOfferClaimRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    product_code: str | None = Field(default=None, min_length=1, max_length=128)
    bundle_code: str | None = Field(default=None, min_length=1, max_length=128)
    offer_code: str = Field(default="RETENTION_10_NEXT_MONTH", min_length=1, max_length=128)
    source_type: str = Field(default="RETENTION_OFFER", min_length=1, max_length=128)
    source_key: str = Field(default="RETENTION_10_NEXT_MONTH", min_length=1, max_length=128)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("product_code", "bundle_code", "idempotency_key", mode="before")
    @classmethod
    def _normalize_optional_text_fields(cls, value: object) -> str | None:
        return _normalize_optional_text(value)

    @field_validator("offer_code", "source_type", "source_key", mode="before")
    @classmethod
    def _normalize_required_text_fields(cls, value: object) -> str:
        return _normalize_required_text(value)

    @model_validator(mode="after")
    def _validate_contract(self) -> "BillingDiscountOfferClaimRequest":
        _validate_exactly_one_billing_subject(
            product_code=self.product_code,
            bundle_code=self.bundle_code,
        )
        return self