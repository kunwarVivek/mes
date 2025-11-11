"""
Feature Gating - Tier-based feature access control

Controls which features are available to different subscription tiers.
Provides decorators and functions for enforcing feature access.
"""
from functools import wraps
from typing import Callable, List, Optional
from enum import Enum
from sqlalchemy.orm import Session
import logging

from app.domain.entities.subscription import SubscriptionTier, SubscriptionStatus
from app.models.subscription import SubscriptionModel
from app.core.exceptions import BusinessRuleException


logger = logging.getLogger(__name__)


class TierFeatures(str, Enum):
    """
    Feature flags for subscription tiers

    Each feature is available to specific tiers.
    Features are cumulative (higher tiers include lower tier features).
    """
    # Starter features (available to all tiers)
    BASIC_PRODUCTION_TRACKING = "basic_production_tracking"
    WORK_ORDER_MANAGEMENT = "work_order_management"
    INVENTORY_MANAGEMENT = "inventory_management"
    BASIC_REPORTING = "basic_reporting"
    EMAIL_SUPPORT = "email_support"

    # Professional features (Professional + Enterprise)
    ADVANCED_SCHEDULING = "advanced_scheduling"
    QUALITY_MANAGEMENT = "quality_management"
    CUSTOM_FIELDS = "custom_fields"
    WORKFLOW_AUTOMATION = "workflow_automation"
    ADVANCED_ANALYTICS = "advanced_analytics"
    PRIORITY_SUPPORT = "priority_support"
    NCR_MANAGEMENT = "ncr_management"
    INSPECTION_PLANS = "inspection_plans"

    # Enterprise features (Enterprise only)
    WHITE_LABELING = "white_labeling"
    SSO_SAML = "sso_saml"
    API_ACCESS = "api_access"
    DEDICATED_ACCOUNT_MANAGER = "dedicated_account_manager"
    PHONE_SUPPORT_24_7 = "phone_support_24_7"
    CUSTOM_SLA = "custom_sla"
    UNLIMITED_RESOURCES = "unlimited_resources"

    def get_display_name(self) -> str:
        """Get human-readable feature name"""
        return self.value.replace("_", " ").title()


# ============================================================================
# FEATURE MATRIX - Define which features are available to which tiers
# ============================================================================

FEATURE_MATRIX = {
    # Starter tier features
    SubscriptionTier.STARTER: [
        TierFeatures.BASIC_PRODUCTION_TRACKING,
        TierFeatures.WORK_ORDER_MANAGEMENT,
        TierFeatures.INVENTORY_MANAGEMENT,
        TierFeatures.BASIC_REPORTING,
        TierFeatures.EMAIL_SUPPORT,
    ],

    # Professional tier features (includes Starter)
    SubscriptionTier.PROFESSIONAL: [
        # Starter features
        TierFeatures.BASIC_PRODUCTION_TRACKING,
        TierFeatures.WORK_ORDER_MANAGEMENT,
        TierFeatures.INVENTORY_MANAGEMENT,
        TierFeatures.BASIC_REPORTING,
        TierFeatures.EMAIL_SUPPORT,
        # Professional-specific features
        TierFeatures.ADVANCED_SCHEDULING,
        TierFeatures.QUALITY_MANAGEMENT,
        TierFeatures.CUSTOM_FIELDS,
        TierFeatures.WORKFLOW_AUTOMATION,
        TierFeatures.ADVANCED_ANALYTICS,
        TierFeatures.PRIORITY_SUPPORT,
        TierFeatures.NCR_MANAGEMENT,
        TierFeatures.INSPECTION_PLANS,
    ],

    # Enterprise tier features (includes all)
    SubscriptionTier.ENTERPRISE: [
        # All Starter features
        TierFeatures.BASIC_PRODUCTION_TRACKING,
        TierFeatures.WORK_ORDER_MANAGEMENT,
        TierFeatures.INVENTORY_MANAGEMENT,
        TierFeatures.BASIC_REPORTING,
        TierFeatures.EMAIL_SUPPORT,
        # All Professional features
        TierFeatures.ADVANCED_SCHEDULING,
        TierFeatures.QUALITY_MANAGEMENT,
        TierFeatures.CUSTOM_FIELDS,
        TierFeatures.WORKFLOW_AUTOMATION,
        TierFeatures.ADVANCED_ANALYTICS,
        TierFeatures.PRIORITY_SUPPORT,
        TierFeatures.NCR_MANAGEMENT,
        TierFeatures.INSPECTION_PLANS,
        # Enterprise-specific features
        TierFeatures.WHITE_LABELING,
        TierFeatures.SSO_SAML,
        TierFeatures.API_ACCESS,
        TierFeatures.DEDICATED_ACCOUNT_MANAGER,
        TierFeatures.PHONE_SUPPORT_24_7,
        TierFeatures.CUSTOM_SLA,
        TierFeatures.UNLIMITED_RESOURCES,
    ]
}


# ============================================================================
# FEATURE ACCESS FUNCTIONS
# ============================================================================

def check_feature_access(
    organization_id: int,
    feature: TierFeatures,
    db: Session
) -> bool:
    """
    Check if organization has access to a feature

    Args:
        organization_id: Organization ID
        feature: Feature to check
        db: Database session

    Returns:
        True if organization has access, False otherwise
    """
    try:
        # Get subscription
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.organization_id == organization_id
        ).first()

        if not subscription:
            logger.warning(f"No subscription found for organization {organization_id}")
            return False

        # Check subscription status
        if subscription.status not in [
            SubscriptionStatus.TRIAL.value,
            SubscriptionStatus.ACTIVE.value
        ]:
            logger.warning(
                f"Subscription for organization {organization_id} is not active: {subscription.status}"
            )
            return False

        # Get tier
        tier = SubscriptionTier(subscription.tier)

        # Check feature matrix
        allowed_features = FEATURE_MATRIX.get(tier, [])
        has_access = feature in allowed_features

        if not has_access:
            logger.info(
                f"Feature '{feature.value}' not available for organization {organization_id} "
                f"(tier: {tier.value})"
            )

        return has_access

    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        return False


def get_available_features(tier: SubscriptionTier) -> List[TierFeatures]:
    """
    Get list of features available for a tier

    Args:
        tier: Subscription tier

    Returns:
        List of available features
    """
    return FEATURE_MATRIX.get(tier, [])


def get_missing_features(
    current_tier: SubscriptionTier,
    target_tier: SubscriptionTier
) -> List[TierFeatures]:
    """
    Get features that would be gained by upgrading

    Args:
        current_tier: Current subscription tier
        target_tier: Target upgrade tier

    Returns:
        List of features in target tier but not in current tier
    """
    current_features = set(FEATURE_MATRIX.get(current_tier, []))
    target_features = set(FEATURE_MATRIX.get(target_tier, []))

    return list(target_features - current_features)


def get_required_tier_for_feature(feature: TierFeatures) -> Optional[SubscriptionTier]:
    """
    Get minimum tier required for a feature

    Args:
        feature: Feature to check

    Returns:
        Minimum required tier, or None if feature doesn't exist
    """
    for tier in [SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]:
        if feature in FEATURE_MATRIX.get(tier, []):
            return tier
    return None


# ============================================================================
# DECORATORS
# ============================================================================

def require_tier(required_tier: SubscriptionTier):
    """
    Decorator to enforce minimum subscription tier

    Usage:
        @require_tier(SubscriptionTier.PROFESSIONAL)
        def create_custom_field(organization_id: int, db: Session):
            # Function code

    Args:
        required_tier: Minimum required subscription tier

    Raises:
        BusinessRuleException: If organization tier is insufficient
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract organization_id and db from function arguments
            organization_id = kwargs.get('organization_id') or (args[0] if args else None)
            db = kwargs.get('db') or (args[1] if len(args) > 1 else None)

            if organization_id is None or db is None:
                raise BusinessRuleException(
                    "require_tier decorator requires organization_id and db parameters"
                )

            # Get subscription
            subscription = db.query(SubscriptionModel).filter(
                SubscriptionModel.organization_id == organization_id
            ).first()

            if not subscription:
                raise BusinessRuleException(
                    f"No subscription found for organization {organization_id}"
                )

            # Check subscription status
            if subscription.status not in [
                SubscriptionStatus.TRIAL.value,
                SubscriptionStatus.ACTIVE.value
            ]:
                raise BusinessRuleException(
                    f"Subscription is not active. Current status: {subscription.status}"
                )

            # Check tier
            current_tier = SubscriptionTier(subscription.tier)
            tier_order = {
                SubscriptionTier.STARTER: 1,
                SubscriptionTier.PROFESSIONAL: 2,
                SubscriptionTier.ENTERPRISE: 3
            }

            if tier_order[current_tier] < tier_order[required_tier]:
                raise BusinessRuleException(
                    f"This feature requires {required_tier.get_display_name()} tier or higher. "
                    f"Current tier: {current_tier.get_display_name()}"
                )

            # Execute function
            return func(*args, **kwargs)

        return wrapper
    return decorator


def require_feature(required_feature: TierFeatures):
    """
    Decorator to enforce feature access

    Usage:
        @require_feature(TierFeatures.CUSTOM_FIELDS)
        def create_custom_field(organization_id: int, db: Session):
            # Function code

    Args:
        required_feature: Required feature

    Raises:
        BusinessRuleException: If organization doesn't have feature access
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract organization_id and db from function arguments
            organization_id = kwargs.get('organization_id') or (args[0] if args else None)
            db = kwargs.get('db') or (args[1] if len(args) > 1 else None)

            if organization_id is None or db is None:
                raise BusinessRuleException(
                    "require_feature decorator requires organization_id and db parameters"
                )

            # Check feature access
            has_access = check_feature_access(organization_id, required_feature, db)

            if not has_access:
                required_tier = get_required_tier_for_feature(required_feature)
                raise BusinessRuleException(
                    f"This feature is not available in your subscription tier. "
                    f"Required tier: {required_tier.get_display_name() if required_tier else 'Unknown'}"
                )

            # Execute function
            return func(*args, **kwargs)

        return wrapper
    return decorator


def require_active_subscription(func: Callable) -> Callable:
    """
    Decorator to require an active subscription

    Usage:
        @require_active_subscription
        def create_work_order(organization_id: int, db: Session):
            # Function code

    Raises:
        BusinessRuleException: If subscription is not active
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract organization_id and db from function arguments
        organization_id = kwargs.get('organization_id') or (args[0] if args else None)
        db = kwargs.get('db') or (args[1] if len(args) > 1 else None)

        if organization_id is None or db is None:
            raise BusinessRuleException(
                "require_active_subscription decorator requires organization_id and db parameters"
            )

        # Get subscription
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.organization_id == organization_id
        ).first()

        if not subscription:
            raise BusinessRuleException(
                f"No subscription found for organization {organization_id}"
            )

        # Check subscription status
        if subscription.status not in [
            SubscriptionStatus.TRIAL.value,
            SubscriptionStatus.ACTIVE.value
        ]:
            raise BusinessRuleException(
                f"Your subscription is {subscription.status}. "
                "Please update your payment method or contact support."
            )

        # Execute function
        return func(*args, **kwargs)

    return wrapper


# ============================================================================
# FEATURE BLOCKING EXAMPLES
# ============================================================================

# Block features for specific tiers:
# - Custom fields: Blocked for Starter tier
# - Workflows: Blocked for Starter tier
# - White labeling: Enterprise only

def can_use_custom_fields(organization_id: int, db: Session) -> bool:
    """Check if organization can use custom fields (Professional+)"""
    return check_feature_access(organization_id, TierFeatures.CUSTOM_FIELDS, db)


def can_use_workflows(organization_id: int, db: Session) -> bool:
    """Check if organization can use workflow automation (Professional+)"""
    return check_feature_access(organization_id, TierFeatures.WORKFLOW_AUTOMATION, db)


def can_use_white_labeling(organization_id: int, db: Session) -> bool:
    """Check if organization can use white labeling (Enterprise only)"""
    return check_feature_access(organization_id, TierFeatures.WHITE_LABELING, db)
