"""
Billing API Endpoints

Handles Stripe checkout sessions, customer portal access, and invoice management.
Requires active subscription check before creating checkout sessions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.domain.entities.user import User
from app.application.services.subscription_service import SubscriptionService
from app.infrastructure.adapters.stripe.stripe_client import StripeClient, StripeClientError
from app.models.subscription import InvoiceModel, SubscriptionModel
from app.domain.entities.subscription import SubscriptionStatus
from app.presentation.schemas.subscription import (
    CreateCheckoutRequest,
    CreatePortalRequest,
    CheckoutSessionResponse,
    PortalSessionResponse,
    InvoiceResponse,
    InvoiceListResponse
)
from app.core.exceptions import (
    ResourceNotFoundException,
    BusinessRuleException,
    ValidationException
)

router = APIRouter(prefix="/billing")
logger = logging.getLogger(__name__)


def get_stripe_client() -> StripeClient:
    """Dependency injection for Stripe client"""
    return StripeClient()


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    """Dependency injection for SubscriptionService"""
    return SubscriptionService(db)


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    stripe_client: StripeClient = Depends(get_stripe_client)
):
    """
    Create Stripe checkout session for subscription purchase.

    Business Rules:
    - User must belong to an organization
    - Can upgrade/convert trial subscription
    - Cannot create checkout if already have active paid subscription for same/higher tier
    - Checkout session expires in 30 minutes

    Args:
        request: Checkout request with tier and billing cycle
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service
        stripe_client: Stripe API client

    Returns:
        CheckoutSessionResponse with checkout URL

    Raises:
        HTTPException 400: Invalid request or business rule violation
        HTTPException 404: Organization or subscription not found
        HTTPException 500: Stripe API error
    """
    try:
        # Get organization ID from user
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(
            f"Creating checkout session for organization {organization_id}, "
            f"tier={request.tier}, cycle={request.billing_cycle}"
        )

        # Get current subscription
        try:
            subscription = subscription_service.get_subscription(organization_id)

            # Check if already have active paid subscription
            if subscription.status == SubscriptionStatus.ACTIVE.value:
                # Allow upgrade, but not same tier or downgrade via checkout
                from app.domain.entities.subscription import SubscriptionTier
                current_tier = SubscriptionTier(subscription.tier)
                new_tier = SubscriptionTier(request.tier.value)

                tier_order = {
                    SubscriptionTier.STARTER: 1,
                    SubscriptionTier.PROFESSIONAL: 2,
                    SubscriptionTier.ENTERPRISE: 3
                }

                if tier_order.get(new_tier, 0) <= tier_order.get(current_tier, 0):
                    raise BusinessRuleException(
                        "Cannot create checkout for same or lower tier. Use upgrade endpoint or contact support."
                    )

        except ResourceNotFoundException:
            # No subscription exists - this should not happen as trial is created on signup
            raise ResourceNotFoundException("organization", organization_id)

        # Get or create Stripe customer
        stripe_customer_id = subscription.stripe_customer_id

        if not stripe_customer_id:
            # Create new Stripe customer
            try:
                customer = stripe_client.create_customer(
                    email=current_user.email.value,
                    organization_id=organization_id,
                    name=f"Organization {organization_id}",
                    metadata={
                        "organization_id": str(organization_id),
                        "user_id": str(current_user.id)
                    }
                )
                stripe_customer_id = customer["id"]

                # Update subscription with customer ID
                subscription.stripe_customer_id = stripe_customer_id
                db.commit()

                logger.info(f"Created Stripe customer {stripe_customer_id} for org {organization_id}")

            except StripeClientError as e:
                logger.error(f"Failed to create Stripe customer: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create customer: {str(e)}"
                )

        # Set default URLs if not provided
        from app.domain.entities.subscription import SubscriptionTier, BillingCycle
        tier = SubscriptionTier(request.tier.value)
        billing_cycle = BillingCycle(request.billing_cycle.value)

        success_url = request.success_url or "https://app.example.com/billing/success"
        cancel_url = request.cancel_url or "https://app.example.com/pricing"

        # Create checkout session
        try:
            session = stripe_client.create_checkout_session(
                organization_id=organization_id,
                tier=tier,
                billing_cycle=billing_cycle,
                customer_email=current_user.email.value,
                success_url=success_url,
                cancel_url=cancel_url,
                customer_id=stripe_customer_id
            )

            logger.info(
                f"Created checkout session {session['id']} for org {organization_id}"
            )

            return CheckoutSessionResponse(
                checkout_url=session["url"],
                session_id=session["id"],
                expires_at=session["expires_at"]
            )

        except StripeClientError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create checkout session: {str(e)}"
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
        logger.error(f"Unexpected error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    request: CreatePortalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    stripe_client: StripeClient = Depends(get_stripe_client)
):
    """
    Create Stripe Customer Portal session.

    Allows customers to:
    - Update payment methods
    - View invoices
    - Manage subscription (upgrade/downgrade/cancel)
    - Update billing information

    Args:
        request: Portal request with return URL
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service
        stripe_client: Stripe API client

    Returns:
        PortalSessionResponse with portal URL

    Raises:
        HTTPException 400: Invalid request
        HTTPException 404: Subscription not found or no Stripe customer
        HTTPException 500: Stripe API error
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(f"Creating portal session for organization {organization_id}")

        # Get subscription
        subscription = subscription_service.get_subscription(organization_id)

        # Verify Stripe customer exists
        if not subscription.stripe_customer_id:
            raise BusinessRuleException(
                "No payment information found. Please subscribe to a plan first."
            )

        # Set default return URL
        return_url = request.return_url or "https://app.example.com/billing"

        # Create portal session
        try:
            session = stripe_client.create_portal_session(
                customer_id=subscription.stripe_customer_id,
                return_url=return_url
            )

            logger.info(
                f"Created portal session for customer {subscription.stripe_customer_id}"
            )

            return PortalSessionResponse(
                portal_url=session["url"]
            )

        except StripeClientError as e:
            logger.error(f"Failed to create portal session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create portal session: {str(e)}"
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
        logger.error(f"Unexpected error creating portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    limit: int = Query(10, ge=1, le=100, description="Number of invoices to return"),
    offset: int = Query(0, ge=0, description="Number of invoices to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """
    List invoices for current organization.

    Returns paginated list of invoices sorted by invoice date (newest first).

    Args:
        limit: Maximum number of invoices to return (1-100)
        offset: Number of invoices to skip (for pagination)
        current_user: Authenticated user
        db: Database session
        subscription_service: Subscription service

    Returns:
        InvoiceListResponse with paginated invoices

    Raises:
        HTTPException 400: Invalid pagination parameters
        HTTPException 404: Subscription not found
    """
    try:
        organization_id = current_user.organization_id
        if not organization_id:
            raise ValidationException("User must belong to an organization")

        logger.info(f"Listing invoices for organization {organization_id}")

        # Get subscription to verify access
        subscription = subscription_service.get_subscription(organization_id)

        # Query invoices
        query = db.query(InvoiceModel).filter(
            InvoiceModel.organization_id == organization_id
        ).order_by(InvoiceModel.invoice_date.desc())

        # Get total count
        total_count = query.count()

        # Apply pagination
        invoices = query.offset(offset).limit(limit).all()

        # Convert to response DTOs
        invoice_responses = []
        for invoice in invoices:
            invoice_responses.append(InvoiceResponse(
                id=invoice.id,
                invoice_number=invoice.invoice_number,
                stripe_invoice_id=invoice.stripe_invoice_id,
                amount_due=invoice.amount_due / 100,  # Convert cents to dollars
                amount_paid=invoice.amount_paid / 100,
                currency=invoice.currency,
                status=invoice.status,
                invoice_date=invoice.invoice_date,
                due_date=invoice.due_date,
                paid_at=invoice.paid_at,
                invoice_pdf_url=invoice.invoice_pdf_url
            ))

        has_more = (offset + limit) < total_count

        logger.info(
            f"Retrieved {len(invoice_responses)} invoices for org {organization_id} "
            f"(total: {total_count}, has_more: {has_more})"
        )

        return InvoiceListResponse(
            invoices=invoice_responses,
            total_count=total_count,
            has_more=has_more
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
        logger.error(f"Unexpected error listing invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list invoices"
        )
