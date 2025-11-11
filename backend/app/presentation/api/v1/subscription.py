"""
Subscription API Endpoints

Handles subscription management: view, upgrade, cancel, and usage tracking.
Enforces subscription limits and provides usage information.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.domain.entities.user import User
from app.application.services.subscription_service import SubscriptionService
from app.application.services.usage_tracking_service import UsageTrackingService
from app.infrastructure.adapters.stripe.stripe_client import StripeClient, StripeClientError
from app.domain.entities.subscription import SubscriptionTier, BillingCycle
from app.presentation.schemas.subscription import (
    SubscriptionResponse,
    UsageResponse,
    UpgradeSubscriptionRequest,
    CancelSubscriptionRequest,
    LimitCheckResponse,
    SubscriptionActionResponse,
    UsageLimitsResponse,
    CurrentUsageResponse,
    ResourceUsageDetail
)
from app.core.exceptions import (
    ResourceNotFoundException,
    BusinessRuleException,
    ValidationException
)

router = APIRouter(prefix="/subscription")
logger = logging.getLogger(__name__)


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    """Dependency injection for SubscriptionService"""
    return SubscriptionService(db)


def get_usage_service(db: Session = Depends(get_db)) -> UsageTrackingService:
    """Dependency injection for UsageTrackingService"""
    return UsageTrackingService(db)


def get_stripe_client() -> StripeClient:
    """Dependency injection for Stripe client"""
    return StripeClient()


@router.get("", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    usage_service: UsageTrackingService = Depends(get_usage_service)
):
    """
    Get current subscription details for user's organization.

    Returns complete subscription information including:
    - Tier and status
    - Trial information
    - Billing period
    - Resource limits
    - Current usage

    Args:
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service
        usage_service: Usage tracking service

    Returns:
        SubscriptionResponse with complete subscription details

    Raises:
        HTTPException 404: Subscription not found
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(f"Getting subscription for organization {organization_id}")

        # Get subscription
        subscription = subscription_service.get_subscription(organization_id)

        # Get total limits (including add-ons)
        total_limits = subscription_service.get_total_limits_with_addons(organization_id)

        # Get current usage
        current_usage = usage_service.get_current_usage(organization_id)

        # Calculate days until trial expiry
        days_until_expiry = None
        if subscription.status == "trial":
            days_until_expiry = subscription_service.get_days_until_trial_expiry(organization_id)

        return SubscriptionResponse(
            id=subscription.id,
            organization_id=subscription.organization_id,
            tier=subscription.tier,
            status=subscription.status,
            billing_cycle=subscription.billing_cycle,
            trial_starts_at=subscription.trial_starts_at,
            trial_ends_at=subscription.trial_ends_at,
            trial_converted=subscription.trial_converted,
            days_until_trial_expiry=days_until_expiry,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            billing_email=subscription.billing_email,
            stripe_customer_id=subscription.stripe_customer_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            limits=UsageLimitsResponse(
                max_users=total_limits.max_users,
                max_plants=total_limits.max_plants,
                storage_limit_gb=total_limits.storage_limit_gb
            ),
            current_usage=CurrentUsageResponse(
                current_users=current_usage.current_users,
                current_plants=current_usage.current_plants,
                storage_used_gb=current_usage.storage_used_gb,
                measured_at=current_usage.measured_at
            ) if current_usage else None,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            cancelled_at=subscription.cancelled_at
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription"
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    usage_service: UsageTrackingService = Depends(get_usage_service)
):
    """
    Get detailed usage information for current organization.

    Returns usage details with percentages and remaining capacity for:
    - Users
    - Plants
    - Storage

    Args:
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service
        usage_service: Usage tracking service

    Returns:
        UsageResponse with detailed usage information

    Raises:
        HTTPException 404: Subscription not found
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(f"Getting usage for organization {organization_id}")

        # Get total limits and current usage
        total_limits = subscription_service.get_total_limits_with_addons(organization_id)
        current_usage = usage_service.get_current_usage(organization_id)
        violations = usage_service.get_limit_violations(organization_id)

        # Calculate usage details for users
        users_detail = ResourceUsageDetail(
            current=current_usage.current_users if current_usage else 0,
            limit=total_limits.max_users,
            percentage=round(
                (current_usage.current_users / total_limits.max_users * 100), 1
            ) if total_limits.max_users and current_usage else None,
            available=total_limits.max_users - current_usage.current_users
            if total_limits.max_users and current_usage else None
        )

        # Calculate usage details for plants
        plants_detail = ResourceUsageDetail(
            current=current_usage.current_plants if current_usage else 0,
            limit=total_limits.max_plants,
            percentage=round(
                (current_usage.current_plants / total_limits.max_plants * 100), 1
            ) if total_limits.max_plants and current_usage else None,
            available=total_limits.max_plants - current_usage.current_plants
            if total_limits.max_plants and current_usage else None
        )

        # Calculate storage usage
        storage_used = float(current_usage.storage_used_gb) if current_usage else 0.0
        storage_detail = {
            "current_gb": round(storage_used, 2),
            "limit_gb": total_limits.storage_limit_gb,
            "percentage": round(
                (storage_used / total_limits.storage_limit_gb * 100), 1
            ) if total_limits.storage_limit_gb else None,
            "available_gb": round(
                total_limits.storage_limit_gb - storage_used, 2
            ) if total_limits.storage_limit_gb else None
        }

        # Get violation messages
        violation_messages = [v.get_message() for v in violations]

        return UsageResponse(
            users=users_detail,
            plants=plants_detail,
            storage=storage_detail,
            within_limits=len(violations) == 0,
            violations=violation_messages
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage"
        )


@router.post("/upgrade", response_model=SubscriptionActionResponse)
async def upgrade_subscription(
    request: UpgradeSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    usage_service: UsageTrackingService = Depends(get_usage_service),
    stripe_client: StripeClient = Depends(get_stripe_client)
):
    """
    Upgrade subscription to a higher tier.

    Business Rules:
    - Can only upgrade to higher tier
    - If in trial, converts to paid subscription
    - If already paid, updates Stripe subscription
    - Prorated billing for mid-cycle upgrades

    Args:
        request: Upgrade request with new tier
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service
        usage_service: Usage tracking service
        stripe_client: Stripe API client

    Returns:
        SubscriptionActionResponse with updated subscription

    Raises:
        HTTPException 400: Invalid upgrade or business rule violation
        HTTPException 404: Subscription not found
        HTTPException 500: Stripe API error
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(
            f"Upgrading subscription for organization {organization_id} to {request.new_tier}"
        )

        # Get current subscription
        subscription = subscription_service.get_subscription(organization_id)

        # Validate upgrade
        current_tier = SubscriptionTier(subscription.tier)
        new_tier = SubscriptionTier(request.new_tier.value)

        tier_order = {
            SubscriptionTier.STARTER: 1,
            SubscriptionTier.PROFESSIONAL: 2,
            SubscriptionTier.ENTERPRISE: 3
        }

        if tier_order.get(new_tier, 0) <= tier_order.get(current_tier, 0):
            raise BusinessRuleException(
                f"Cannot upgrade from {current_tier.value} to {request.new_tier}. "
                "Please use downgrade or contact support."
            )

        # If trial, use checkout flow instead
        if subscription.status == "trial":
            raise BusinessRuleException(
                "Please use the checkout endpoint to convert from trial to paid subscription"
            )

        # Update Stripe subscription if exists
        stripe_subscription_id = None
        if subscription.stripe_subscription_id:
            try:
                from app.config.pricing import get_stripe_price_id
                billing_cycle = BillingCycle(
                    request.billing_cycle.value
                ) if request.billing_cycle else BillingCycle(subscription.billing_cycle)

                price_id = get_stripe_price_id(new_tier, billing_cycle)

                stripe_subscription = stripe_client.update_subscription(
                    subscription_id=subscription.stripe_subscription_id,
                    price_id=price_id,
                    metadata={
                        "tier": new_tier.value,
                        "organization_id": str(organization_id)
                    }
                )
                stripe_subscription_id = stripe_subscription["id"]

                logger.info(
                    f"Updated Stripe subscription {stripe_subscription_id} "
                    f"for org {organization_id}"
                )

            except StripeClientError as e:
                logger.error(f"Failed to update Stripe subscription: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update subscription: {str(e)}"
                )

        # Update subscription in database
        updated_subscription = subscription_service.upgrade_subscription(
            organization_id=organization_id,
            new_tier=new_tier,
            stripe_subscription_id=stripe_subscription_id
        )

        # Get updated usage and limits
        total_limits = subscription_service.get_total_limits_with_addons(organization_id)
        current_usage = usage_service.get_current_usage(organization_id)

        return SubscriptionActionResponse(
            success=True,
            message=f"Successfully upgraded to {new_tier.value} tier",
            subscription=SubscriptionResponse(
                id=updated_subscription.id,
                organization_id=updated_subscription.organization_id,
                tier=updated_subscription.tier,
                status=updated_subscription.status,
                billing_cycle=updated_subscription.billing_cycle,
                trial_starts_at=updated_subscription.trial_starts_at,
                trial_ends_at=updated_subscription.trial_ends_at,
                trial_converted=updated_subscription.trial_converted,
                days_until_trial_expiry=None,
                current_period_start=updated_subscription.current_period_start,
                current_period_end=updated_subscription.current_period_end,
                billing_email=updated_subscription.billing_email,
                stripe_customer_id=updated_subscription.stripe_customer_id,
                stripe_subscription_id=updated_subscription.stripe_subscription_id,
                limits=UsageLimitsResponse(
                    max_users=total_limits.max_users,
                    max_plants=total_limits.max_plants,
                    storage_limit_gb=total_limits.storage_limit_gb
                ),
                current_usage=CurrentUsageResponse(
                    current_users=current_usage.current_users,
                    current_plants=current_usage.current_plants,
                    storage_used_gb=current_usage.storage_used_gb,
                    measured_at=current_usage.measured_at
                ) if current_usage else None,
                created_at=updated_subscription.created_at,
                updated_at=updated_subscription.updated_at,
                cancelled_at=updated_subscription.cancelled_at
            )
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error upgrading subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade subscription"
        )


@router.post("/cancel", response_model=SubscriptionActionResponse)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    usage_service: UsageTrackingService = Depends(get_usage_service),
    stripe_client: StripeClient = Depends(get_stripe_client)
):
    """
    Cancel subscription.

    Business Rules:
    - Can cancel at period end (default) or immediately
    - Immediate cancellation stops access immediately
    - Period end cancellation maintains access until end of billing period
    - Cancels Stripe subscription if exists

    Args:
        request: Cancel request with immediate flag
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service
        usage_service: Usage tracking service
        stripe_client: Stripe API client

    Returns:
        SubscriptionActionResponse with updated subscription

    Raises:
        HTTPException 400: Invalid cancellation or business rule violation
        HTTPException 404: Subscription not found
        HTTPException 500: Stripe API error
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(
            f"Cancelling subscription for organization {organization_id}, "
            f"immediate={request.immediate}"
        )

        # Get current subscription
        subscription = subscription_service.get_subscription(organization_id)

        # Cancel Stripe subscription if exists
        if subscription.stripe_subscription_id:
            try:
                if request.immediate:
                    stripe_client.cancel_subscription_immediately(
                        subscription.stripe_subscription_id
                    )
                    logger.info(
                        f"Immediately cancelled Stripe subscription "
                        f"{subscription.stripe_subscription_id}"
                    )
                else:
                    stripe_client.cancel_subscription_at_period_end(
                        subscription.stripe_subscription_id
                    )
                    logger.info(
                        f"Scheduled cancellation for Stripe subscription "
                        f"{subscription.stripe_subscription_id} at period end"
                    )

            except StripeClientError as e:
                logger.error(f"Failed to cancel Stripe subscription: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to cancel subscription: {str(e)}"
                )

        # Cancel subscription in database
        cancelled_subscription = subscription_service.cancel_subscription(
            organization_id=organization_id,
            immediate=request.immediate
        )

        # Get updated limits and usage
        total_limits = subscription_service.get_total_limits_with_addons(organization_id)
        current_usage = usage_service.get_current_usage(organization_id)

        message = (
            "Subscription cancelled immediately"
            if request.immediate
            else f"Subscription will cancel at period end ({cancelled_subscription.current_period_end})"
        )

        return SubscriptionActionResponse(
            success=True,
            message=message,
            subscription=SubscriptionResponse(
                id=cancelled_subscription.id,
                organization_id=cancelled_subscription.organization_id,
                tier=cancelled_subscription.tier,
                status=cancelled_subscription.status,
                billing_cycle=cancelled_subscription.billing_cycle,
                trial_starts_at=cancelled_subscription.trial_starts_at,
                trial_ends_at=cancelled_subscription.trial_ends_at,
                trial_converted=cancelled_subscription.trial_converted,
                days_until_trial_expiry=None,
                current_period_start=cancelled_subscription.current_period_start,
                current_period_end=cancelled_subscription.current_period_end,
                billing_email=cancelled_subscription.billing_email,
                stripe_customer_id=cancelled_subscription.stripe_customer_id,
                stripe_subscription_id=cancelled_subscription.stripe_subscription_id,
                limits=UsageLimitsResponse(
                    max_users=total_limits.max_users,
                    max_plants=total_limits.max_plants,
                    storage_limit_gb=total_limits.storage_limit_gb
                ),
                current_usage=CurrentUsageResponse(
                    current_users=current_usage.current_users,
                    current_plants=current_usage.current_plants,
                    storage_used_gb=current_usage.storage_used_gb,
                    measured_at=current_usage.measured_at
                ) if current_usage else None,
                created_at=cancelled_subscription.created_at,
                updated_at=cancelled_subscription.updated_at,
                cancelled_at=cancelled_subscription.cancelled_at
            )
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error cancelling subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.get("/limits/check", response_model=LimitCheckResponse)
async def check_limit(
    action: str = Query(..., description="Action to check: add_user, add_plant, upload_file"),
    size_mb: Optional[float] = Query(None, description="File size in MB (for upload_file action)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    usage_service: UsageTrackingService = Depends(get_usage_service)
):
    """
    Check if an action is allowed based on subscription limits.

    Supported actions:
    - add_user: Check if another user can be added
    - add_plant: Check if another plant can be added
    - upload_file: Check if file can be uploaded (requires size_mb parameter)

    Args:
        action: Action to check
        size_mb: File size in MB (required for upload_file action)
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service
        usage_service: Usage tracking service

    Returns:
        LimitCheckResponse indicating if action is allowed

    Raises:
        HTTPException 400: Invalid action or missing parameters
        HTTPException 404: Subscription not found
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(f"Checking limit for organization {organization_id}, action={action}")

        # Get total limits and current usage
        total_limits = subscription_service.get_total_limits_with_addons(organization_id)
        current_usage = usage_service.get_current_usage(organization_id)

        allowed = False
        reason = None
        current_value = None
        limit_value = None

        if action == "add_user":
            current_value = current_usage.current_users if current_usage else 0
            limit_value = total_limits.max_users

            if total_limits.max_users is None:
                allowed = True  # Unlimited
            else:
                allowed = current_value < total_limits.max_users
                if not allowed:
                    reason = f"User limit reached ({current_value}/{total_limits.max_users})"

        elif action == "add_plant":
            current_value = current_usage.current_plants if current_usage else 0
            limit_value = total_limits.max_plants

            if total_limits.max_plants is None:
                allowed = True  # Unlimited
            else:
                allowed = current_value < total_limits.max_plants
                if not allowed:
                    reason = f"Plant limit reached ({current_value}/{total_limits.max_plants})"

        elif action == "upload_file":
            if size_mb is None:
                raise ValidationException("size_mb parameter required for upload_file action")

            storage_used_gb = float(current_usage.storage_used_gb) if current_usage else 0.0
            file_size_gb = size_mb / 1024
            new_total_gb = storage_used_gb + file_size_gb

            current_value = int(storage_used_gb)
            limit_value = total_limits.storage_limit_gb

            if total_limits.storage_limit_gb is None:
                allowed = True  # Unlimited
            else:
                allowed = new_total_gb <= total_limits.storage_limit_gb
                if not allowed:
                    reason = (
                        f"Storage limit would be exceeded "
                        f"({round(new_total_gb, 2)}GB / {total_limits.storage_limit_gb}GB)"
                    )

        else:
            raise ValidationException(
                f"Invalid action '{action}'. Supported: add_user, add_plant, upload_file"
            )

        return LimitCheckResponse(
            allowed=allowed,
            reason=reason,
            current_usage=current_value,
            limit=limit_value
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error checking limit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check limit"
        )
