"""
Subscription Service - Business logic for subscription management

Handles subscription lifecycle: trial creation, conversion to paid,
upgrades/downgrades, cancellation, and status management.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.subscription import (
    SubscriptionModel,
    SubscriptionUsageModel,
    SubscriptionAddOnModel
)
from app.domain.entities.subscription import (
    SubscriptionTier,
    SubscriptionStatus,
    BillingCycle,
    UsageLimits
)
from app.config.pricing import (
    get_tier_limits,
    TRIAL_DURATION_DAYS,
    TRIAL_DEFAULT_TIER
)
from app.core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    BusinessRuleException
)


logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service for managing subscription operations

    Dependency Injection: Inject SQLAlchemy session
    """

    def __init__(self, db: Session):
        """
        Initialize subscription service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_subscription(self, organization_id: int) -> SubscriptionModel:
        """
        Get current subscription for an organization

        Args:
            organization_id: Organization ID

        Returns:
            SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
        """
        subscription = self.db.query(SubscriptionModel).filter(
            SubscriptionModel.organization_id == organization_id
        ).first()

        if not subscription:
            logger.error(f"Subscription not found for organization {organization_id}")
            raise ResourceNotFoundException(
                f"No subscription found for organization {organization_id}"
            )

        return subscription

    def create_trial_subscription(
        self,
        organization_id: int,
        tier: SubscriptionTier = TRIAL_DEFAULT_TIER,
        trial_duration_days: int = TRIAL_DURATION_DAYS
    ) -> SubscriptionModel:
        """
        Create a trial subscription for an organization

        Args:
            organization_id: Organization ID
            tier: Starting tier (default: Starter)
            trial_duration_days: Trial duration (default: 14 days)

        Returns:
            Created SubscriptionModel

        Raises:
            BusinessRuleException: If subscription already exists
        """
        # Check if subscription already exists
        existing = self.db.query(SubscriptionModel).filter(
            SubscriptionModel.organization_id == organization_id
        ).first()

        if existing:
            logger.warning(f"Subscription already exists for organization {organization_id}")
            raise BusinessRuleException(
                f"Organization {organization_id} already has a subscription"
            )

        # Get tier limits
        limits = get_tier_limits(tier)

        # Create trial subscription
        now = datetime.utcnow()
        trial_ends = now + timedelta(days=trial_duration_days)

        subscription = SubscriptionModel(
            organization_id=organization_id,
            tier=tier.value,
            status=SubscriptionStatus.TRIAL.value,
            billing_cycle=None,  # No billing during trial
            trial_starts_at=now,
            trial_ends_at=trial_ends,
            trial_converted=False,
            max_users=limits.max_users,
            max_plants=limits.max_plants,
            storage_limit_gb=limits.storage_limit_gb
        )

        self.db.add(subscription)
        self.db.flush()

        # Create initial usage record
        usage = SubscriptionUsageModel(
            organization_id=organization_id,
            current_users=0,
            current_plants=0,
            storage_used_gb=0.00
        )
        self.db.add(usage)
        self.db.commit()

        logger.info(
            f"Created trial subscription for organization {organization_id}, "
            f"tier={tier.value}, expires={trial_ends}"
        )

        return subscription

    def convert_trial_to_paid(
        self,
        organization_id: int,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        billing_cycle: BillingCycle,
        tier: Optional[SubscriptionTier] = None
    ) -> SubscriptionModel:
        """
        Convert trial subscription to paid subscription

        Args:
            organization_id: Organization ID
            stripe_subscription_id: Stripe subscription ID
            stripe_customer_id: Stripe customer ID
            billing_cycle: Monthly or annual billing
            tier: Optional tier upgrade during conversion

        Returns:
            Updated SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
            BusinessRuleException: If subscription cannot be converted
        """
        subscription = self.get_subscription(organization_id)

        # Validate can convert
        if subscription.status != SubscriptionStatus.TRIAL.value:
            raise BusinessRuleException(
                f"Cannot convert subscription with status {subscription.status}"
            )

        if subscription.trial_converted:
            raise BusinessRuleException("Trial already converted to paid subscription")

        # Update subscription
        now = datetime.utcnow()
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.trial_converted = True
        subscription.billing_cycle = billing_cycle.value
        subscription.stripe_customer_id = stripe_customer_id
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.current_period_start = now

        # Set period end based on billing cycle
        if billing_cycle == BillingCycle.MONTHLY:
            subscription.current_period_end = now + timedelta(days=30)
        else:
            subscription.current_period_end = now + timedelta(days=365)

        # Apply tier upgrade if provided
        if tier:
            limits = get_tier_limits(tier)
            subscription.tier = tier.value
            subscription.max_users = limits.max_users
            subscription.max_plants = limits.max_plants
            subscription.storage_limit_gb = limits.storage_limit_gb

        self.db.commit()

        logger.info(
            f"Converted trial to paid for organization {organization_id}, "
            f"tier={subscription.tier}, billing={billing_cycle.value}"
        )

        return subscription

    def upgrade_subscription(
        self,
        organization_id: int,
        new_tier: SubscriptionTier,
        stripe_subscription_id: Optional[str] = None
    ) -> SubscriptionModel:
        """
        Upgrade subscription to a higher tier

        Args:
            organization_id: Organization ID
            new_tier: New subscription tier
            stripe_subscription_id: Optional Stripe subscription ID for update

        Returns:
            Updated SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
            BusinessRuleException: If upgrade is invalid
        """
        subscription = self.get_subscription(organization_id)

        # Validate can upgrade
        if subscription.status not in [
            SubscriptionStatus.TRIAL.value,
            SubscriptionStatus.ACTIVE.value
        ]:
            raise BusinessRuleException(
                f"Cannot upgrade subscription with status {subscription.status}"
            )

        # Get new limits
        new_limits = get_tier_limits(new_tier)

        # Update subscription
        subscription.tier = new_tier.value
        subscription.max_users = new_limits.max_users
        subscription.max_plants = new_limits.max_plants
        subscription.storage_limit_gb = new_limits.storage_limit_gb

        if stripe_subscription_id:
            subscription.stripe_subscription_id = stripe_subscription_id

        self.db.commit()

        logger.info(
            f"Upgraded subscription for organization {organization_id} to tier {new_tier.value}"
        )

        return subscription

    def downgrade_subscription(
        self,
        organization_id: int,
        new_tier: SubscriptionTier,
        stripe_subscription_id: Optional[str] = None
    ) -> SubscriptionModel:
        """
        Downgrade subscription to a lower tier

        Args:
            organization_id: Organization ID
            new_tier: New subscription tier
            stripe_subscription_id: Optional Stripe subscription ID for update

        Returns:
            Updated SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
            BusinessRuleException: If downgrade would exceed current usage
        """
        subscription = self.get_subscription(organization_id)

        # Validate can downgrade
        if subscription.status != SubscriptionStatus.ACTIVE.value:
            raise BusinessRuleException(
                f"Cannot downgrade subscription with status {subscription.status}"
            )

        # Get new limits
        new_limits = get_tier_limits(new_tier)

        # Check if current usage exceeds new limits
        latest_usage = self.db.query(SubscriptionUsageModel).filter(
            SubscriptionUsageModel.organization_id == organization_id
        ).order_by(SubscriptionUsageModel.measured_at.desc()).first()

        if latest_usage:
            violations = []
            if new_limits.max_users and latest_usage.current_users > new_limits.max_users:
                violations.append(
                    f"Current users ({latest_usage.current_users}) exceeds new limit ({new_limits.max_users})"
                )
            if new_limits.max_plants and latest_usage.current_plants > new_limits.max_plants:
                violations.append(
                    f"Current plants ({latest_usage.current_plants}) exceeds new limit ({new_limits.max_plants})"
                )
            if new_limits.storage_limit_gb and float(latest_usage.storage_used_gb) > new_limits.storage_limit_gb:
                violations.append(
                    f"Current storage ({latest_usage.storage_used_gb}GB) exceeds new limit ({new_limits.storage_limit_gb}GB)"
                )

            if violations:
                raise BusinessRuleException(
                    f"Cannot downgrade: {'; '.join(violations)}"
                )

        # Update subscription
        subscription.tier = new_tier.value
        subscription.max_users = new_limits.max_users
        subscription.max_plants = new_limits.max_plants
        subscription.storage_limit_gb = new_limits.storage_limit_gb

        if stripe_subscription_id:
            subscription.stripe_subscription_id = stripe_subscription_id

        self.db.commit()

        logger.info(
            f"Downgraded subscription for organization {organization_id} to tier {new_tier.value}"
        )

        return subscription

    def cancel_subscription(
        self,
        organization_id: int,
        immediate: bool = False
    ) -> SubscriptionModel:
        """
        Cancel subscription

        Args:
            organization_id: Organization ID
            immediate: If True, cancel immediately. If False, cancel at period end

        Returns:
            Updated SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
            BusinessRuleException: If subscription cannot be cancelled
        """
        subscription = self.get_subscription(organization_id)

        # Validate can cancel
        if subscription.status in [
            SubscriptionStatus.CANCELLED.value,
            SubscriptionStatus.SUSPENDED.value
        ]:
            raise BusinessRuleException(
                f"Cannot cancel subscription with status {subscription.status}"
            )

        now = datetime.utcnow()

        if immediate:
            subscription.status = SubscriptionStatus.CANCELLED.value
            subscription.cancelled_at = now
            logger.info(f"Immediately cancelled subscription for organization {organization_id}")
        else:
            # Cancel at period end - Stripe handles this
            subscription.cancelled_at = subscription.current_period_end
            logger.info(
                f"Scheduled cancellation for organization {organization_id} at {subscription.current_period_end}"
            )

        self.db.commit()

        return subscription

    def suspend_subscription(self, organization_id: int) -> SubscriptionModel:
        """
        Suspend subscription (typically for payment failures)

        Args:
            organization_id: Organization ID

        Returns:
            Updated SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
        """
        subscription = self.get_subscription(organization_id)

        subscription.status = SubscriptionStatus.SUSPENDED.value
        self.db.commit()

        logger.warning(f"Suspended subscription for organization {organization_id}")

        return subscription

    def reactivate_subscription(self, organization_id: int) -> SubscriptionModel:
        """
        Reactivate a suspended subscription

        Args:
            organization_id: Organization ID

        Returns:
            Updated SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
            BusinessRuleException: If subscription is not suspended
        """
        subscription = self.get_subscription(organization_id)

        if subscription.status != SubscriptionStatus.SUSPENDED.value:
            raise BusinessRuleException(
                f"Cannot reactivate subscription with status {subscription.status}"
            )

        subscription.status = SubscriptionStatus.ACTIVE.value
        self.db.commit()

        logger.info(f"Reactivated subscription for organization {organization_id}")

        return subscription

    def is_trial_expired(self, organization_id: int) -> bool:
        """
        Check if trial subscription has expired

        Args:
            organization_id: Organization ID

        Returns:
            True if trial expired, False otherwise
        """
        try:
            subscription = self.get_subscription(organization_id)

            if subscription.status != SubscriptionStatus.TRIAL.value:
                return False

            if subscription.trial_ends_at is None:
                return False

            return datetime.utcnow() > subscription.trial_ends_at

        except ResourceNotFoundException:
            return False

    def get_days_until_trial_expiry(self, organization_id: int) -> Optional[int]:
        """
        Get number of days until trial expires

        Args:
            organization_id: Organization ID

        Returns:
            Days until expiry, or None if not in trial
        """
        try:
            subscription = self.get_subscription(organization_id)

            if subscription.status != SubscriptionStatus.TRIAL.value:
                return None

            if subscription.trial_ends_at is None:
                return None

            delta = subscription.trial_ends_at - datetime.utcnow()
            return max(0, delta.days)

        except ResourceNotFoundException:
            return None

    def get_total_limits_with_addons(
        self,
        organization_id: int
    ) -> UsageLimits:
        """
        Calculate total subscription limits including active add-ons

        Args:
            organization_id: Organization ID

        Returns:
            UsageLimits with total limits (base + add-ons)

        Raises:
            ResourceNotFoundException: If subscription not found
        """
        subscription = self.get_subscription(organization_id)

        # Get active add-ons
        active_addons = self.db.query(SubscriptionAddOnModel).filter(
            and_(
                SubscriptionAddOnModel.subscription_id == subscription.id,
                SubscriptionAddOnModel.removed_at.is_(None)
            )
        ).all()

        # Start with base limits
        total_users = subscription.max_users
        total_plants = subscription.max_plants
        total_storage = subscription.storage_limit_gb

        # Add add-on quantities
        for addon in active_addons:
            if addon.add_on_type == "extra_users" and total_users is not None:
                total_users += addon.quantity
            elif addon.add_on_type == "extra_plants" and total_plants is not None:
                total_plants += addon.quantity
            elif addon.add_on_type == "extra_storage_gb" and total_storage is not None:
                total_storage += addon.quantity

        return UsageLimits(
            max_users=total_users,
            max_plants=total_plants,
            storage_limit_gb=total_storage
        )

    def update_billing_email(
        self,
        organization_id: int,
        billing_email: str
    ) -> SubscriptionModel:
        """
        Update billing email for subscription

        Args:
            organization_id: Organization ID
            billing_email: New billing email address

        Returns:
            Updated SubscriptionModel

        Raises:
            ResourceNotFoundException: If subscription not found
            ValidationException: If email is invalid
        """
        if not billing_email or "@" not in billing_email:
            raise ValidationException("Invalid email address")

        subscription = self.get_subscription(organization_id)
        subscription.billing_email = billing_email
        self.db.commit()

        logger.info(f"Updated billing email for organization {organization_id}")

        return subscription
