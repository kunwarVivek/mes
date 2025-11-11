"""
Pydantic schemas for Subscription and Billing API endpoints.

These schemas define request/response models for subscription management,
billing operations, usage tracking, and webhook events.
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


# ============================================================================
# ENUMS
# ============================================================================

class TierEnum(str, Enum):
    """Subscription tier enumeration."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class StatusEnum(str, Enum):
    """Subscription status enumeration."""
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"


class BillingCycleEnum(str, Enum):
    """Billing cycle enumeration."""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class InvoiceStatusEnum(str, Enum):
    """Invoice status enumeration."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class CreateCheckoutRequest(BaseModel):
    """Request schema for creating Stripe checkout session."""

    tier: TierEnum = Field(..., description="Subscription tier to purchase")
    billing_cycle: BillingCycleEnum = Field(..., description="Billing cycle (monthly or annual)")
    success_url: Optional[str] = Field(
        None,
        description="Custom success URL (defaults to /billing/success)"
    )
    cancel_url: Optional[str] = Field(
        None,
        description="Custom cancel URL (defaults to /pricing)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tier": "professional",
                "billing_cycle": "monthly",
                "success_url": "https://app.example.com/billing/success",
                "cancel_url": "https://app.example.com/pricing"
            }
        }


class CreatePortalRequest(BaseModel):
    """Request schema for creating customer portal session."""

    return_url: Optional[str] = Field(
        None,
        description="URL to return to after portal session (defaults to /billing)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "return_url": "https://app.example.com/billing"
            }
        }


class UpgradeSubscriptionRequest(BaseModel):
    """Request schema for upgrading subscription tier."""

    new_tier: TierEnum = Field(..., description="New subscription tier")
    billing_cycle: Optional[BillingCycleEnum] = Field(
        None,
        description="Billing cycle (if changing)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "new_tier": "enterprise",
                "billing_cycle": "annual"
            }
        }


class CancelSubscriptionRequest(BaseModel):
    """Request schema for cancelling subscription."""

    immediate: bool = Field(
        False,
        description="Cancel immediately (true) or at period end (false)"
    )
    reason: Optional[str] = Field(
        None,
        description="Cancellation reason",
        max_length=500
    )

    class Config:
        json_schema_extra = {
            "example": {
                "immediate": False,
                "reason": "Moving to a different solution"
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class CheckoutSessionResponse(BaseModel):
    """Response schema for checkout session creation."""

    checkout_url: str = Field(..., description="Stripe checkout URL")
    session_id: str = Field(..., description="Stripe checkout session ID")
    expires_at: int = Field(..., description="Expiration timestamp (Unix)")

    class Config:
        json_schema_extra = {
            "example": {
                "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
                "session_id": "cs_test_123456789",
                "expires_at": 1699564800
            }
        }


class PortalSessionResponse(BaseModel):
    """Response schema for customer portal session."""

    portal_url: str = Field(..., description="Stripe customer portal URL")

    class Config:
        json_schema_extra = {
            "example": {
                "portal_url": "https://billing.stripe.com/p/session/test_123456789"
            }
        }


class UsageLimitsResponse(BaseModel):
    """Response schema for subscription limits."""

    max_users: Optional[int] = Field(None, description="Maximum users (null = unlimited)")
    max_plants: Optional[int] = Field(None, description="Maximum plants (null = unlimited)")
    storage_limit_gb: Optional[int] = Field(None, description="Storage limit in GB (null = unlimited)")

    class Config:
        json_schema_extra = {
            "example": {
                "max_users": 25,
                "max_plants": 5,
                "storage_limit_gb": 100
            }
        }


class CurrentUsageResponse(BaseModel):
    """Response schema for current usage."""

    current_users: int = Field(..., description="Current number of active users")
    current_plants: int = Field(..., description="Current number of active plants")
    storage_used_gb: Decimal = Field(..., description="Storage used in GB")
    measured_at: datetime = Field(..., description="When usage was measured")

    class Config:
        json_schema_extra = {
            "example": {
                "current_users": 12,
                "current_plants": 2,
                "storage_used_gb": 45.67,
                "measured_at": "2024-11-11T10:30:00Z"
            }
        }


class ResourceUsageDetail(BaseModel):
    """Detailed usage information for a specific resource."""

    current: int = Field(..., description="Current usage")
    limit: Optional[int] = Field(None, description="Usage limit (null = unlimited)")
    percentage: Optional[float] = Field(None, description="Usage percentage (null if unlimited)")
    available: Optional[int] = Field(None, description="Remaining capacity (null if unlimited)")

    class Config:
        json_schema_extra = {
            "example": {
                "current": 12,
                "limit": 25,
                "percentage": 48.0,
                "available": 13
            }
        }


class UsageResponse(BaseModel):
    """Response schema for detailed usage information."""

    users: ResourceUsageDetail
    plants: ResourceUsageDetail
    storage: Dict[str, Any] = Field(..., description="Storage usage details")
    within_limits: bool = Field(..., description="Whether usage is within limits")
    violations: List[str] = Field(default_factory=list, description="List of limit violations")

    class Config:
        json_schema_extra = {
            "example": {
                "users": {
                    "current": 12,
                    "limit": 25,
                    "percentage": 48.0,
                    "available": 13
                },
                "plants": {
                    "current": 2,
                    "limit": 5,
                    "percentage": 40.0,
                    "available": 3
                },
                "storage": {
                    "current_gb": 45.67,
                    "limit_gb": 100,
                    "percentage": 45.7,
                    "available_gb": 54.33
                },
                "within_limits": True,
                "violations": []
            }
        }


class SubscriptionResponse(BaseModel):
    """Response schema for subscription details."""

    id: int
    organization_id: int
    tier: TierEnum
    status: StatusEnum
    billing_cycle: Optional[BillingCycleEnum]

    # Trial information
    trial_starts_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    trial_converted: bool
    days_until_trial_expiry: Optional[int] = Field(
        None,
        description="Days remaining in trial (null if not in trial)"
    )

    # Billing period
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    billing_email: Optional[str]

    # Stripe integration
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]

    # Resource limits
    limits: UsageLimitsResponse

    # Current usage
    current_usage: Optional[CurrentUsageResponse]

    # Audit fields
    created_at: datetime
    updated_at: Optional[datetime]
    cancelled_at: Optional[datetime]

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "organization_id": 456,
                "tier": "professional",
                "status": "active",
                "billing_cycle": "monthly",
                "trial_starts_at": None,
                "trial_ends_at": None,
                "trial_converted": True,
                "days_until_trial_expiry": None,
                "current_period_start": "2024-11-01T00:00:00Z",
                "current_period_end": "2024-12-01T00:00:00Z",
                "billing_email": "billing@example.com",
                "stripe_customer_id": "cus_123456789",
                "stripe_subscription_id": "sub_123456789",
                "limits": {
                    "max_users": 25,
                    "max_plants": 5,
                    "storage_limit_gb": 100
                },
                "current_usage": {
                    "current_users": 12,
                    "current_plants": 2,
                    "storage_used_gb": 45.67,
                    "measured_at": "2024-11-11T10:30:00Z"
                },
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-11-01T00:00:00Z",
                "cancelled_at": None
            }
        }


class InvoiceResponse(BaseModel):
    """Response schema for invoice details."""

    id: int
    invoice_number: str
    stripe_invoice_id: Optional[str]

    # Amounts
    amount_due: Decimal = Field(..., description="Amount due in dollars")
    amount_paid: Decimal = Field(..., description="Amount paid in dollars")
    currency: str

    # Status and dates
    status: InvoiceStatusEnum
    invoice_date: datetime
    due_date: Optional[datetime]
    paid_at: Optional[datetime]

    # PDF
    invoice_pdf_url: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "id": 789,
                "invoice_number": "INV-2024-001",
                "stripe_invoice_id": "in_123456789",
                "amount_due": 199.00,
                "amount_paid": 199.00,
                "currency": "USD",
                "status": "paid",
                "invoice_date": "2024-11-01T00:00:00Z",
                "due_date": "2024-11-15T00:00:00Z",
                "paid_at": "2024-11-02T10:30:00Z",
                "invoice_pdf_url": "https://invoice.stripe.com/i/acct_.../test_123"
            }
        }


class InvoiceListResponse(BaseModel):
    """Response schema for invoice list."""

    invoices: List[InvoiceResponse]
    total_count: int
    has_more: bool

    class Config:
        json_schema_extra = {
            "example": {
                "invoices": [],
                "total_count": 5,
                "has_more": False
            }
        }


class LimitCheckResponse(BaseModel):
    """Response schema for limit check."""

    allowed: bool = Field(..., description="Whether the action is allowed")
    reason: Optional[str] = Field(None, description="Reason if action is not allowed")
    current_usage: Optional[int] = Field(None, description="Current usage for the resource")
    limit: Optional[int] = Field(None, description="Limit for the resource (null = unlimited)")

    class Config:
        json_schema_extra = {
            "example": {
                "allowed": True,
                "reason": None,
                "current_usage": 12,
                "limit": 25
            }
        }


class SubscriptionActionResponse(BaseModel):
    """Generic response for subscription actions (upgrade, cancel, etc.)."""

    success: bool
    message: str
    subscription: SubscriptionResponse

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Subscription upgraded successfully",
                "subscription": {}
            }
        }


# ============================================================================
# WEBHOOK SCHEMAS
# ============================================================================

class WebhookEventResponse(BaseModel):
    """Response schema for webhook event processing."""

    received: bool = True
    event_id: str
    event_type: str
    processed: bool
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "received": True,
                "event_id": "evt_123456789",
                "event_type": "customer.subscription.updated",
                "processed": True,
                "message": "Subscription updated successfully"
            }
        }
