"""
Use Case: Create Checkout Session

Handles creation of Stripe checkout sessions for subscription signup.
Follows clean architecture principles with dependency injection.
"""
from typing import Dict, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
import logging

from app.domain.entities.subscription import (
    SubscriptionTier,
    BillingCycle,
    SubscriptionStatus
)
from app.application.services.subscription_service import SubscriptionService
from app.infrastructure.adapters.stripe.stripe_client import StripeClient
from app.core.exceptions import (
    BusinessRuleException,
    ValidationException
)


logger = logging.getLogger(__name__)


@dataclass
class CreateCheckoutSessionDTO:
    """Data Transfer Object for checkout session creation"""
    organization_id: int
    tier: SubscriptionTier
    billing_cycle: BillingCycle
    customer_email: str
    success_url: str
    cancel_url: str


class CreateCheckoutSessionUseCase:
    """
    Use Case: Create Stripe Checkout Session

    Orchestrates:
    1. Validate subscription eligibility
    2. Create/retrieve Stripe customer
    3. Create checkout session
    4. Return session URL for redirect

    Single Responsibility: Handle checkout session creation logic
    """

    def __init__(
        self,
        db: Session,
        stripe_client: StripeClient
    ):
        """
        Initialize use case with dependencies

        Args:
            db: Database session
            stripe_client: Stripe API client
        """
        self.db = db
        self.stripe_client = stripe_client
        self.subscription_service = SubscriptionService(db)

    def execute(self, dto: CreateCheckoutSessionDTO) -> Dict[str, Any]:
        """
        Execute checkout session creation

        Args:
            dto: Checkout session data

        Returns:
            Dictionary with checkout session details:
            {
                "checkout_session_id": "cs_...",
                "checkout_url": "https://checkout.stripe.com/...",
                "organization_id": 123,
                "tier": "professional",
                "billing_cycle": "monthly"
            }

        Raises:
            ValidationException: If input data is invalid
            BusinessRuleException: If subscription rules prevent checkout
        """
        logger.info(
            f"Creating checkout session for organization {dto.organization_id}, "
            f"tier={dto.tier.value}, cycle={dto.billing_cycle.value}"
        )

        # Step 1: Validate organization can create checkout session
        self._validate_checkout_eligibility(dto.organization_id)

        # Step 2: Get or create Stripe customer
        subscription = self.subscription_service.get_subscription(dto.organization_id)
        customer_id = subscription.stripe_customer_id

        if not customer_id:
            # Create new Stripe customer
            customer = self.stripe_client.create_customer(
                email=dto.customer_email,
                organization_id=dto.organization_id,
                metadata={
                    "organization_id": str(dto.organization_id),
                    "tier": dto.tier.value
                }
            )
            customer_id = customer["id"]
            logger.info(f"Created Stripe customer {customer_id} for organization {dto.organization_id}")

        # Step 3: Create checkout session
        session = self.stripe_client.create_checkout_session(
            organization_id=dto.organization_id,
            tier=dto.tier,
            billing_cycle=dto.billing_cycle,
            customer_email=dto.customer_email,
            success_url=dto.success_url,
            cancel_url=dto.cancel_url,
            customer_id=customer_id
        )

        logger.info(
            f"Created checkout session {session['id']} for organization {dto.organization_id}"
        )

        return {
            "checkout_session_id": session["id"],
            "checkout_url": session["url"],
            "organization_id": dto.organization_id,
            "tier": dto.tier.value,
            "billing_cycle": dto.billing_cycle.value,
            "customer_id": customer_id
        }

    def _validate_checkout_eligibility(self, organization_id: int) -> None:
        """
        Validate organization can create checkout session

        Args:
            organization_id: Organization ID

        Raises:
            BusinessRuleException: If organization is not eligible
        """
        try:
            subscription = self.subscription_service.get_subscription(organization_id)
        except Exception as e:
            raise BusinessRuleException(
                f"No subscription found for organization {organization_id}"
            )

        # Only trial or cancelled subscriptions can create checkout sessions
        if subscription.status not in [
            SubscriptionStatus.TRIAL.value,
            SubscriptionStatus.CANCELLED.value
        ]:
            raise BusinessRuleException(
                f"Cannot create checkout session for subscription with status: {subscription.status}. "
                "Please manage your existing subscription through the billing portal."
            )

        # If trial is already converted, prevent checkout
        if subscription.trial_converted and subscription.status == SubscriptionStatus.TRIAL.value:
            raise BusinessRuleException(
                "Trial has already been converted to paid subscription"
            )
