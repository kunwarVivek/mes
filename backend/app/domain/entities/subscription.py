"""
Subscription domain entities - Business logic and value objects

Contains subscription domain models with business rules and validation.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

    def get_display_name(self) -> str:
        """Get human-readable tier name"""
        return self.value.replace("_", " ").title()


class SubscriptionStatus(str, Enum):
    """Subscription lifecycle status"""
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"

    def is_active_state(self) -> bool:
        """Check if subscription allows access to system"""
        return self in (SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE)

    def requires_payment_action(self) -> bool:
        """Check if status indicates payment issues"""
        return self in (SubscriptionStatus.PAST_DUE, SubscriptionStatus.SUSPENDED)


class BillingCycle(str, Enum):
    """Billing frequency"""
    MONTHLY = "monthly"
    ANNUAL = "annual"

    def get_months(self) -> int:
        """Get number of months in billing cycle"""
        return 1 if self == BillingCycle.MONTHLY else 12

    def get_discount_multiplier(self) -> float:
        """Get discount factor for annual billing"""
        return 1.0 if self == BillingCycle.MONTHLY else 0.83  # ~17% annual discount


class InvoiceStatus(str, Enum):
    """Invoice payment status"""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOID = "void"
    UNCOLLECTIBLE = "uncollectible"

    def is_outstanding(self) -> bool:
        """Check if invoice needs payment"""
        return self in (InvoiceStatus.OPEN, InvoiceStatus.PAST_DUE)


class AddOnType(str, Enum):
    """Types of subscription add-ons"""
    EXTRA_USERS = "extra_users"
    EXTRA_PLANTS = "extra_plants"
    EXTRA_STORAGE_GB = "extra_storage_gb"

    def get_display_name(self) -> str:
        """Get human-readable add-on name"""
        names = {
            AddOnType.EXTRA_USERS: "Additional Users",
            AddOnType.EXTRA_PLANTS: "Additional Plants",
            AddOnType.EXTRA_STORAGE_GB: "Additional Storage (GB)"
        }
        return names[self]


@dataclass(frozen=True)
class UsageLimits:
    """
    Resource usage limits for a subscription tier

    NULL/None values indicate unlimited resources (Enterprise tier)
    """
    max_users: Optional[int] = None
    max_plants: Optional[int] = None
    storage_limit_gb: Optional[int] = None

    def __post_init__(self):
        """Validate limits are non-negative"""
        if self.max_users is not None and self.max_users < 0:
            raise ValueError("max_users cannot be negative")
        if self.max_plants is not None and self.max_plants < 0:
            raise ValueError("max_plants cannot be negative")
        if self.storage_limit_gb is not None and self.storage_limit_gb < 0:
            raise ValueError("storage_limit_gb cannot be negative")

    def is_unlimited(self) -> bool:
        """Check if all limits are unlimited"""
        return all([
            self.max_users is None,
            self.max_plants is None,
            self.storage_limit_gb is None
        ])

    def has_user_limit(self) -> bool:
        """Check if user limit is set"""
        return self.max_users is not None

    def has_plant_limit(self) -> bool:
        """Check if plant limit is set"""
        return self.max_plants is not None

    def has_storage_limit(self) -> bool:
        """Check if storage limit is set"""
        return self.storage_limit_gb is not None


@dataclass
class CurrentUsage:
    """
    Current resource usage for an organization
    """
    current_users: int = 0
    current_plants: int = 0
    storage_used_gb: Decimal = Decimal("0.00")
    measured_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate usage is non-negative"""
        if self.current_users < 0:
            raise ValueError("current_users cannot be negative")
        if self.current_plants < 0:
            raise ValueError("current_plants cannot be negative")
        if self.storage_used_gb < 0:
            raise ValueError("storage_used_gb cannot be negative")


@dataclass
class LimitViolation:
    """
    Represents a resource that has exceeded its limit
    """
    resource: str  # "users", "plants", "storage"
    limit: int
    current: int
    overage: int

    def get_message(self) -> str:
        """Get user-friendly violation message"""
        return f"{self.resource.title()} limit exceeded: {self.current}/{self.limit} (over by {self.overage})"


@dataclass
class Subscription:
    """
    Subscription domain entity - Core business logic for subscriptions

    Business Rules:
    - Trial period is 14 days by default
    - One subscription per organization
    - NULL limits = unlimited (Enterprise)
    - Add-ons increase base tier limits
    - Suspended/past_due subscriptions block system access
    """
    id: int
    organization_id: int
    tier: SubscriptionTier
    status: SubscriptionStatus
    billing_cycle: Optional[BillingCycle]

    # Trial management
    trial_starts_at: Optional[datetime]
    trial_ends_at: Optional[datetime]
    trial_converted: bool = False

    # Stripe integration
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

    # Billing period
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    billing_email: Optional[str] = None

    # Resource limits
    limits: UsageLimits = field(default_factory=UsageLimits)

    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == SubscriptionStatus.TRIAL

    def is_active(self) -> bool:
        """Check if subscription allows system access"""
        return self.status.is_active_state()

    def is_trial_expired(self) -> bool:
        """Check if trial period has ended"""
        if not self.is_trial() or self.trial_ends_at is None:
            return False
        return datetime.utcnow() > self.trial_ends_at

    def get_days_until_trial_expiry(self) -> Optional[int]:
        """Calculate days remaining in trial"""
        if not self.is_trial() or self.trial_ends_at is None:
            return None

        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)

    def can_convert_from_trial(self) -> bool:
        """Check if trial can be converted to paid"""
        return (
            self.status == SubscriptionStatus.TRIAL and
            not self.trial_converted
        )

    def check_usage_against_limits(
        self,
        usage: CurrentUsage,
        extra_limits: Optional[UsageLimits] = None
    ) -> List[LimitViolation]:
        """
        Check current usage against subscription limits

        Args:
            usage: Current resource usage
            extra_limits: Additional limits from add-ons

        Returns:
            List of limit violations (empty if within limits)
        """
        violations: List[LimitViolation] = []

        # Calculate total limits (base + add-ons)
        total_user_limit = self.limits.max_users
        total_plant_limit = self.limits.max_plants
        total_storage_limit = self.limits.storage_limit_gb

        if extra_limits:
            if total_user_limit is not None and extra_limits.max_users:
                total_user_limit += extra_limits.max_users
            if total_plant_limit is not None and extra_limits.max_plants:
                total_plant_limit += extra_limits.max_plants
            if total_storage_limit is not None and extra_limits.storage_limit_gb:
                total_storage_limit += extra_limits.storage_limit_gb

        # Check user limit
        if total_user_limit is not None and usage.current_users > total_user_limit:
            violations.append(LimitViolation(
                resource="users",
                limit=total_user_limit,
                current=usage.current_users,
                overage=usage.current_users - total_user_limit
            ))

        # Check plant limit
        if total_plant_limit is not None and usage.current_plants > total_plant_limit:
            violations.append(LimitViolation(
                resource="plants",
                limit=total_plant_limit,
                current=usage.current_plants,
                overage=usage.current_plants - total_plant_limit
            ))

        # Check storage limit
        if total_storage_limit is not None and float(usage.storage_used_gb) > total_storage_limit:
            violations.append(LimitViolation(
                resource="storage",
                limit=total_storage_limit,
                current=int(usage.storage_used_gb),
                overage=int(usage.storage_used_gb) - total_storage_limit
            ))

        return violations

    def is_within_limits(
        self,
        usage: CurrentUsage,
        extra_limits: Optional[UsageLimits] = None
    ) -> bool:
        """Check if usage is within subscription limits"""
        return len(self.check_usage_against_limits(usage, extra_limits)) == 0

    def requires_payment(self) -> bool:
        """Check if subscription requires payment action"""
        return self.status.requires_payment_action()

    def can_cancel(self) -> bool:
        """Check if subscription can be cancelled"""
        return self.status in (
            SubscriptionStatus.TRIAL,
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE
        )

    def get_subscription_age_days(self) -> int:
        """Get number of days since subscription created"""
        delta = datetime.utcnow() - self.created_at
        return delta.days


@dataclass
class Invoice:
    """
    Invoice domain entity - Billing and payment tracking
    """
    id: int
    organization_id: int
    subscription_id: int

    # Stripe integration
    stripe_invoice_id: Optional[str]
    stripe_payment_intent_id: Optional[str]

    # Invoice details
    invoice_number: str
    amount_due_cents: int  # in cents
    amount_paid_cents: int  # in cents
    currency: str = "USD"

    # Status and dates
    status: InvoiceStatus = InvoiceStatus.DRAFT
    invoice_date: datetime = field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # PDF URL
    invoice_pdf_url: Optional[str] = None

    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def get_amount_due_dollars(self) -> Decimal:
        """Convert amount due from cents to dollars"""
        return Decimal(self.amount_due_cents) / 100

    def get_amount_paid_dollars(self) -> Decimal:
        """Convert amount paid from cents to dollars"""
        return Decimal(self.amount_paid_cents) / 100

    def get_balance_dollars(self) -> Decimal:
        """Get outstanding balance in dollars"""
        return self.get_amount_due_dollars() - self.get_amount_paid_dollars()

    def is_paid(self) -> bool:
        """Check if invoice is fully paid"""
        return self.status == InvoiceStatus.PAID

    def is_overdue(self) -> bool:
        """Check if invoice is past due date"""
        if self.due_date is None or self.is_paid():
            return False
        return datetime.utcnow() > self.due_date

    def get_days_until_due(self) -> Optional[int]:
        """Calculate days until due date"""
        if self.due_date is None or self.is_paid():
            return None

        delta = self.due_date - datetime.utcnow()
        return delta.days


@dataclass
class SubscriptionAddOn:
    """
    Subscription add-on - Additional purchased capacity
    """
    id: int
    subscription_id: int
    add_on_type: AddOnType
    quantity: int
    unit_price_cents: int

    # Stripe integration
    stripe_price_id: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    removed_at: Optional[datetime] = None

    def is_active(self) -> bool:
        """Check if add-on is currently active"""
        return self.removed_at is None

    def get_total_monthly_cost_dollars(self) -> Decimal:
        """Calculate total monthly cost in dollars"""
        return Decimal(self.quantity * self.unit_price_cents) / 100

    def get_unit_price_dollars(self) -> Decimal:
        """Get unit price in dollars"""
        return Decimal(self.unit_price_cents) / 100
