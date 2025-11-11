"""
Pricing Configuration for Subscription System

Defines pricing tiers, add-on costs, volume discounts, and helper functions
for calculating subscription costs.

All prices are in cents (integer) for precision.
"""
from typing import Dict, Optional, Tuple
from decimal import Decimal
from app.domain.entities.subscription import (
    SubscriptionTier,
    BillingCycle,
    AddOnType,
    UsageLimits
)


# ============================================================================
# PRICING TIERS
# ============================================================================

PRICING_TIERS: Dict[SubscriptionTier, Dict[str, any]] = {
    SubscriptionTier.STARTER: {
        "name": "Starter",
        "description": "Perfect for small teams getting started",
        "monthly_price_cents": 4900,  # $49/month
        "annual_price_cents": 49000,  # $490/year (~17% discount)
        "limits": {
            "max_users": 3,
            "max_plants": 1,
            "storage_limit_gb": 10
        },
        "features": [
            "Basic production tracking",
            "Work order management",
            "Inventory management",
            "Basic reporting",
            "Email support"
        ],
        "stripe_monthly_price_id": "price_starter_monthly",  # Replace with actual Stripe IDs
        "stripe_annual_price_id": "price_starter_annual"
    },
    SubscriptionTier.PROFESSIONAL: {
        "name": "Professional",
        "description": "For growing manufacturing operations",
        "monthly_price_cents": 19900,  # $199/month
        "annual_price_cents": 199000,  # $1,990/year (~17% discount)
        "limits": {
            "max_users": 25,
            "max_plants": 5,
            "storage_limit_gb": 100
        },
        "features": [
            "Everything in Starter",
            "Advanced production scheduling",
            "Quality management (NCR, inspections)",
            "Custom fields",
            "Workflow automation",
            "Advanced analytics",
            "Priority support"
        ],
        "stripe_monthly_price_id": "price_professional_monthly",
        "stripe_annual_price_id": "price_professional_annual"
    },
    SubscriptionTier.ENTERPRISE: {
        "name": "Enterprise",
        "description": "For large-scale manufacturing enterprises",
        "monthly_price_cents": 99900,  # $999/month
        "annual_price_cents": 999000,  # $9,990/year (~17% discount)
        "limits": {
            "max_users": None,  # Unlimited
            "max_plants": None,  # Unlimited
            "storage_limit_gb": None  # Unlimited
        },
        "features": [
            "Everything in Professional",
            "Unlimited users and plants",
            "Unlimited storage",
            "White-label branding",
            "SSO / SAML integration",
            "API access",
            "Dedicated account manager",
            "24/7 phone support",
            "Custom SLA"
        ],
        "stripe_monthly_price_id": "price_enterprise_monthly",
        "stripe_annual_price_id": "price_enterprise_annual"
    }
}


# ============================================================================
# ADD-ON PRICING
# ============================================================================

ADDON_PRICES: Dict[AddOnType, Dict[str, any]] = {
    AddOnType.EXTRA_USERS: {
        "name": "Additional User",
        "description": "Add extra users beyond your plan limit",
        "unit_price_cents": 500,  # $5 per user per month
        "stripe_price_id": "price_addon_extra_user",
        "available_for_tiers": [SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL]
    },
    AddOnType.EXTRA_PLANTS: {
        "name": "Additional Plant",
        "description": "Add extra manufacturing plants beyond your plan limit",
        "unit_price_cents": 2500,  # $25 per plant per month
        "stripe_price_id": "price_addon_extra_plant",
        "available_for_tiers": [SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL]
    },
    AddOnType.EXTRA_STORAGE_GB: {
        "name": "Additional Storage (1GB)",
        "description": "Add extra storage beyond your plan limit",
        "unit_price_cents": 50,  # $0.50 per GB per month
        "stripe_price_id": "price_addon_extra_storage",
        "available_for_tiers": [SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL]
    }
}


# ============================================================================
# VOLUME DISCOUNTS
# ============================================================================

# Applied when purchasing add-ons in bulk
VOLUME_DISCOUNTS: Dict[AddOnType, list[Tuple[int, float]]] = {
    AddOnType.EXTRA_USERS: [
        (10, 0.10),  # 10+ users: 10% discount
        (25, 0.15),  # 25+ users: 15% discount
        (50, 0.20),  # 50+ users: 20% discount
    ],
    AddOnType.EXTRA_PLANTS: [
        (5, 0.10),   # 5+ plants: 10% discount
        (10, 0.15),  # 10+ plants: 15% discount
    ],
    AddOnType.EXTRA_STORAGE_GB: [
        (100, 0.10),  # 100+ GB: 10% discount
        (500, 0.15),  # 500+ GB: 15% discount
        (1000, 0.20), # 1000+ GB: 20% discount
    ]
}


# ============================================================================
# TRIAL CONFIGURATION
# ============================================================================

TRIAL_DURATION_DAYS = 14
TRIAL_DEFAULT_TIER = SubscriptionTier.STARTER
TRIAL_WARNING_DAYS = 3  # Send warning email 3 days before expiry


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tier_limits(tier: SubscriptionTier) -> UsageLimits:
    """
    Get resource limits for a subscription tier

    Args:
        tier: Subscription tier

    Returns:
        UsageLimits object with tier limits
    """
    limits = PRICING_TIERS[tier]["limits"]
    return UsageLimits(
        max_users=limits["max_users"],
        max_plants=limits["max_plants"],
        storage_limit_gb=limits["storage_limit_gb"]
    )


def calculate_price(
    tier: SubscriptionTier,
    billing_cycle: BillingCycle
) -> int:
    """
    Calculate base subscription price in cents

    Args:
        tier: Subscription tier
        billing_cycle: Monthly or annual billing

    Returns:
        Price in cents
    """
    tier_config = PRICING_TIERS[tier]

    if billing_cycle == BillingCycle.MONTHLY:
        return tier_config["monthly_price_cents"]
    else:
        return tier_config["annual_price_cents"]


def get_addon_price(
    addon_type: AddOnType,
    quantity: int,
    apply_volume_discount: bool = True
) -> int:
    """
    Calculate add-on price with optional volume discounts

    Args:
        addon_type: Type of add-on
        quantity: Number of units
        apply_volume_discount: Whether to apply volume discounts

    Returns:
        Total price in cents
    """
    base_price = ADDON_PRICES[addon_type]["unit_price_cents"]
    total_price = base_price * quantity

    if not apply_volume_discount or addon_type not in VOLUME_DISCOUNTS:
        return total_price

    # Apply highest applicable volume discount
    discount_rate = 0.0
    for threshold, rate in sorted(VOLUME_DISCOUNTS[addon_type], reverse=True):
        if quantity >= threshold:
            discount_rate = rate
            break

    if discount_rate > 0:
        total_price = int(total_price * (1 - discount_rate))

    return total_price


def get_stripe_price_id(
    tier: SubscriptionTier,
    billing_cycle: BillingCycle
) -> str:
    """
    Get Stripe Price ID for a tier and billing cycle

    Args:
        tier: Subscription tier
        billing_cycle: Monthly or annual billing

    Returns:
        Stripe Price ID string
    """
    tier_config = PRICING_TIERS[tier]

    if billing_cycle == BillingCycle.MONTHLY:
        return tier_config["stripe_monthly_price_id"]
    else:
        return tier_config["stripe_annual_price_id"]


def get_addon_stripe_price_id(addon_type: AddOnType) -> str:
    """
    Get Stripe Price ID for an add-on

    Args:
        addon_type: Type of add-on

    Returns:
        Stripe Price ID string
    """
    return ADDON_PRICES[addon_type]["stripe_price_id"]


def is_addon_available_for_tier(
    addon_type: AddOnType,
    tier: SubscriptionTier
) -> bool:
    """
    Check if add-on is available for a subscription tier

    Args:
        addon_type: Type of add-on
        tier: Subscription tier

    Returns:
        True if add-on is available for tier
    """
    return tier in ADDON_PRICES[addon_type]["available_for_tiers"]


def get_tier_features(tier: SubscriptionTier) -> list[str]:
    """
    Get list of features for a subscription tier

    Args:
        tier: Subscription tier

    Returns:
        List of feature descriptions
    """
    return PRICING_TIERS[tier]["features"]


def calculate_total_subscription_cost(
    tier: SubscriptionTier,
    billing_cycle: BillingCycle,
    addons: Optional[Dict[AddOnType, int]] = None
) -> Dict[str, any]:
    """
    Calculate total subscription cost including add-ons

    Args:
        tier: Subscription tier
        billing_cycle: Monthly or annual billing
        addons: Dictionary of addon_type -> quantity

    Returns:
        Dictionary with cost breakdown
    """
    base_price = calculate_price(tier, billing_cycle)
    addon_costs = {}
    total_addon_cost = 0

    if addons:
        for addon_type, quantity in addons.items():
            if quantity > 0:
                cost = get_addon_price(addon_type, quantity)
                addon_costs[addon_type.value] = cost
                total_addon_cost += cost

    # For annual billing, add-ons are also charged annually
    if billing_cycle == BillingCycle.ANNUAL:
        total_addon_cost *= 12

    total_cost = base_price + total_addon_cost

    return {
        "base_price_cents": base_price,
        "addon_costs": addon_costs,
        "total_addon_cost_cents": total_addon_cost,
        "total_cost_cents": total_cost,
        "billing_cycle": billing_cycle.value,
        "tier": tier.value,
        "currency": "USD",
        "base_price_dollars": Decimal(base_price) / 100,
        "total_cost_dollars": Decimal(total_cost) / 100
    }
