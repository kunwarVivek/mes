"""
Stripe Webhook Handler

Handles Stripe webhook events for subscription lifecycle management.
Verifies webhook signatures and processes subscription and invoice events.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging
import os
from datetime import datetime

from app.core.database import get_db
from app.application.services.subscription_service import SubscriptionService
from app.infrastructure.adapters.stripe.stripe_client import StripeClient, StripeClientError
from app.models.subscription import InvoiceModel, SubscriptionModel
from app.domain.entities.subscription import SubscriptionStatus, BillingCycle, SubscriptionTier
from app.presentation.schemas.subscription import WebhookEventResponse
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(prefix="/webhooks")
logger = logging.getLogger(__name__)


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    """Dependency injection for SubscriptionService"""
    return SubscriptionService(db)


def get_stripe_client() -> StripeClient:
    """Dependency injection for Stripe client"""
    return StripeClient()


@router.post("/stripe", response_model=WebhookEventResponse)
async def handle_stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    stripe_client: StripeClient = Depends(get_stripe_client)
):
    """
    Handle Stripe webhook events.

    Processes the following events:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    - checkout.session.completed

    Webhook signature verification ensures events are from Stripe.

    Args:
        request: FastAPI request with raw body
        stripe_signature: Stripe signature header
        db: Database session
        subscription_service: Subscription service
        stripe_client: Stripe API client

    Returns:
        WebhookEventResponse with processing result

    Raises:
        HTTPException 400: Invalid signature or payload
        HTTPException 500: Event processing error
    """
    try:
        # Read raw request body
        payload = await request.body()

        # Get webhook secret from environment
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured - webhook signature verification disabled")
            # In production, this should fail. For development, we can continue.
            import json
            event = json.loads(payload)
        else:
            # Verify webhook signature
            if not stripe_signature:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing stripe-signature header"
                )

            try:
                event = stripe_client.construct_webhook_event(
                    payload=payload,
                    signature=stripe_signature,
                    webhook_secret=webhook_secret
                )
            except StripeClientError as e:
                logger.error(f"Webhook signature verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid signature: {str(e)}"
                )

        # Extract event details
        event_id = event.get("id")
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})

        logger.info(f"Processing webhook event: {event_type} (id: {event_id})")

        # Route to appropriate handler
        processed = False
        message = None

        if event_type == "checkout.session.completed":
            processed, message = await _handle_checkout_completed(
                event_data, db, subscription_service
            )

        elif event_type == "customer.subscription.created":
            processed, message = await _handle_subscription_created(
                event_data, db, subscription_service
            )

        elif event_type == "customer.subscription.updated":
            processed, message = await _handle_subscription_updated(
                event_data, db, subscription_service
            )

        elif event_type == "customer.subscription.deleted":
            processed, message = await _handle_subscription_deleted(
                event_data, db, subscription_service
            )

        elif event_type == "invoice.payment_succeeded":
            processed, message = await _handle_invoice_paid(
                event_data, db, subscription_service
            )

        elif event_type == "invoice.payment_failed":
            processed, message = await _handle_invoice_failed(
                event_data, db, subscription_service
            )

        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            message = f"Event type {event_type} not handled"

        return WebhookEventResponse(
            received=True,
            event_id=event_id,
            event_type=event_type,
            processed=processed,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook event"
        )


# ============================================================================
# EVENT HANDLERS
# ============================================================================

async def _handle_checkout_completed(
    session_data: dict,
    db: Session,
    subscription_service: SubscriptionService
) -> tuple[bool, str]:
    """
    Handle checkout.session.completed event.

    Converts trial to paid subscription when checkout is completed.

    Args:
        session_data: Checkout session data from Stripe
        db: Database session
        subscription_service: Subscription service

    Returns:
        Tuple of (processed: bool, message: str)
    """
    try:
        # Extract metadata
        metadata = session_data.get("metadata", {})
        organization_id = int(metadata.get("organization_id"))
        tier = metadata.get("tier")
        billing_cycle = metadata.get("billing_cycle")

        stripe_customer_id = session_data.get("customer")
        stripe_subscription_id = session_data.get("subscription")

        logger.info(
            f"Processing checkout completion for org {organization_id}, "
            f"tier={tier}, cycle={billing_cycle}"
        )

        # Convert trial to paid
        subscription_service.convert_trial_to_paid(
            organization_id=organization_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            billing_cycle=BillingCycle(billing_cycle),
            tier=SubscriptionTier(tier) if tier else None
        )

        db.commit()

        logger.info(f"Successfully converted trial to paid for org {organization_id}")

        # TODO: Send confirmation email
        # await send_subscription_confirmation_email(organization_id)

        return True, f"Trial converted to paid subscription for organization {organization_id}"

    except Exception as e:
        logger.error(f"Error handling checkout completion: {e}")
        db.rollback()
        return False, f"Error: {str(e)}"


async def _handle_subscription_created(
    subscription_data: dict,
    db: Session,
    subscription_service: SubscriptionService
) -> tuple[bool, str]:
    """
    Handle customer.subscription.created event.

    Updates subscription with Stripe subscription details.

    Args:
        subscription_data: Subscription data from Stripe
        db: Database session
        subscription_service: Subscription service

    Returns:
        Tuple of (processed: bool, message: str)
    """
    try:
        metadata = subscription_data.get("metadata", {})
        organization_id = int(metadata.get("organization_id"))
        stripe_subscription_id = subscription_data.get("id")
        stripe_customer_id = subscription_data.get("customer")

        logger.info(f"Processing subscription creation for org {organization_id}")

        # Get subscription
        subscription = subscription_service.get_subscription(organization_id)

        # Update Stripe IDs if not already set
        if not subscription.stripe_subscription_id:
            subscription.stripe_subscription_id = stripe_subscription_id
        if not subscription.stripe_customer_id:
            subscription.stripe_customer_id = stripe_customer_id

        # Update billing period
        subscription.current_period_start = datetime.fromtimestamp(
            subscription_data.get("current_period_start")
        )
        subscription.current_period_end = datetime.fromtimestamp(
            subscription_data.get("current_period_end")
        )

        db.commit()

        logger.info(f"Updated subscription for org {organization_id}")

        return True, f"Subscription created for organization {organization_id}"

    except Exception as e:
        logger.error(f"Error handling subscription creation: {e}")
        db.rollback()
        return False, f"Error: {str(e)}"


async def _handle_subscription_updated(
    subscription_data: dict,
    db: Session,
    subscription_service: SubscriptionService
) -> tuple[bool, str]:
    """
    Handle customer.subscription.updated event.

    Updates subscription status and billing period.

    Args:
        subscription_data: Subscription data from Stripe
        db: Database session
        subscription_service: Subscription service

    Returns:
        Tuple of (processed: bool, message: str)
    """
    try:
        stripe_subscription_id = subscription_data.get("id")
        stripe_status = subscription_data.get("status")

        logger.info(f"Processing subscription update for {stripe_subscription_id}")

        # Find subscription by Stripe ID
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.stripe_subscription_id == stripe_subscription_id
        ).first()

        if not subscription:
            logger.warning(f"Subscription not found for Stripe ID {stripe_subscription_id}")
            return False, f"Subscription not found: {stripe_subscription_id}"

        # Map Stripe status to our status
        status_mapping = {
            "active": SubscriptionStatus.ACTIVE.value,
            "past_due": SubscriptionStatus.PAST_DUE.value,
            "canceled": SubscriptionStatus.CANCELLED.value,
            "unpaid": SubscriptionStatus.SUSPENDED.value
        }

        new_status = status_mapping.get(stripe_status, subscription.status)
        subscription.status = new_status

        # Update billing period
        subscription.current_period_start = datetime.fromtimestamp(
            subscription_data.get("current_period_start")
        )
        subscription.current_period_end = datetime.fromtimestamp(
            subscription_data.get("current_period_end")
        )

        # Check if cancellation scheduled
        cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
        if cancel_at_period_end:
            subscription.cancelled_at = subscription.current_period_end

        db.commit()

        logger.info(
            f"Updated subscription for org {subscription.organization_id}, "
            f"status={new_status}"
        )

        # TODO: Send notification email for status changes
        # if new_status == SubscriptionStatus.PAST_DUE.value:
        #     await send_payment_failed_email(subscription.organization_id)

        return True, f"Subscription updated for organization {subscription.organization_id}"

    except Exception as e:
        logger.error(f"Error handling subscription update: {e}")
        db.rollback()
        return False, f"Error: {str(e)}"


async def _handle_subscription_deleted(
    subscription_data: dict,
    db: Session,
    subscription_service: SubscriptionService
) -> tuple[bool, str]:
    """
    Handle customer.subscription.deleted event.

    Marks subscription as cancelled.

    Args:
        subscription_data: Subscription data from Stripe
        db: Database session
        subscription_service: Subscription service

    Returns:
        Tuple of (processed: bool, message: str)
    """
    try:
        stripe_subscription_id = subscription_data.get("id")

        logger.info(f"Processing subscription deletion for {stripe_subscription_id}")

        # Find subscription by Stripe ID
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.stripe_subscription_id == stripe_subscription_id
        ).first()

        if not subscription:
            logger.warning(f"Subscription not found for Stripe ID {stripe_subscription_id}")
            return False, f"Subscription not found: {stripe_subscription_id}"

        # Mark as cancelled
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.cancelled_at = datetime.utcnow()

        db.commit()

        logger.info(f"Cancelled subscription for org {subscription.organization_id}")

        # TODO: Send cancellation confirmation email
        # await send_cancellation_email(subscription.organization_id)

        return True, f"Subscription cancelled for organization {subscription.organization_id}"

    except Exception as e:
        logger.error(f"Error handling subscription deletion: {e}")
        db.rollback()
        return False, f"Error: {str(e)}"


async def _handle_invoice_paid(
    invoice_data: dict,
    db: Session,
    subscription_service: SubscriptionService
) -> tuple[bool, str]:
    """
    Handle invoice.payment_succeeded event.

    Creates or updates invoice record and reactivates subscription if needed.

    Args:
        invoice_data: Invoice data from Stripe
        db: Database session
        subscription_service: Subscription service

    Returns:
        Tuple of (processed: bool, message: str)
    """
    try:
        stripe_invoice_id = invoice_data.get("id")
        stripe_customer_id = invoice_data.get("customer")
        stripe_subscription_id = invoice_data.get("subscription")

        logger.info(f"Processing successful payment for invoice {stripe_invoice_id}")

        # Find subscription by Stripe customer ID
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.stripe_customer_id == stripe_customer_id
        ).first()

        if not subscription:
            logger.warning(f"Subscription not found for customer {stripe_customer_id}")
            return False, f"Subscription not found for customer {stripe_customer_id}"

        # Create or update invoice
        invoice = db.query(InvoiceModel).filter(
            InvoiceModel.stripe_invoice_id == stripe_invoice_id
        ).first()

        if not invoice:
            invoice = InvoiceModel(
                organization_id=subscription.organization_id,
                subscription_id=subscription.id,
                stripe_invoice_id=stripe_invoice_id,
                stripe_payment_intent_id=invoice_data.get("payment_intent"),
                invoice_number=invoice_data.get("number", f"INV-{stripe_invoice_id}"),
                amount_due=invoice_data.get("amount_due", 0),
                amount_paid=invoice_data.get("amount_paid", 0),
                currency=invoice_data.get("currency", "usd").upper(),
                status="paid",
                invoice_date=datetime.fromtimestamp(invoice_data.get("created")),
                due_date=datetime.fromtimestamp(invoice_data.get("due_date"))
                if invoice_data.get("due_date") else None,
                paid_at=datetime.utcnow(),
                invoice_pdf_url=invoice_data.get("invoice_pdf")
            )
            db.add(invoice)
        else:
            invoice.status = "paid"
            invoice.amount_paid = invoice_data.get("amount_paid", 0)
            invoice.paid_at = datetime.utcnow()
            invoice.invoice_pdf_url = invoice_data.get("invoice_pdf")

        # Reactivate subscription if it was suspended
        if subscription.status == SubscriptionStatus.SUSPENDED.value:
            subscription.status = SubscriptionStatus.ACTIVE.value
            logger.info(f"Reactivated subscription for org {subscription.organization_id}")

        db.commit()

        logger.info(
            f"Recorded successful payment for org {subscription.organization_id}, "
            f"invoice {stripe_invoice_id}"
        )

        # TODO: Send payment confirmation email
        # await send_payment_success_email(subscription.organization_id, invoice_id=invoice.id)

        return True, f"Invoice paid for organization {subscription.organization_id}"

    except Exception as e:
        logger.error(f"Error handling invoice payment: {e}")
        db.rollback()
        return False, f"Error: {str(e)}"


async def _handle_invoice_failed(
    invoice_data: dict,
    db: Session,
    subscription_service: SubscriptionService
) -> tuple[bool, str]:
    """
    Handle invoice.payment_failed event.

    Updates invoice status and suspends subscription if needed.

    Args:
        invoice_data: Invoice data from Stripe
        db: Database session
        subscription_service: Subscription service

    Returns:
        Tuple of (processed: bool, message: str)
    """
    try:
        stripe_invoice_id = invoice_data.get("id")
        stripe_customer_id = invoice_data.get("customer")
        attempt_count = invoice_data.get("attempt_count", 0)

        logger.warning(
            f"Processing failed payment for invoice {stripe_invoice_id}, "
            f"attempt {attempt_count}"
        )

        # Find subscription by Stripe customer ID
        subscription = db.query(SubscriptionModel).filter(
            SubscriptionModel.stripe_customer_id == stripe_customer_id
        ).first()

        if not subscription:
            logger.warning(f"Subscription not found for customer {stripe_customer_id}")
            return False, f"Subscription not found for customer {stripe_customer_id}"

        # Create or update invoice
        invoice = db.query(InvoiceModel).filter(
            InvoiceModel.stripe_invoice_id == stripe_invoice_id
        ).first()

        if not invoice:
            invoice = InvoiceModel(
                organization_id=subscription.organization_id,
                subscription_id=subscription.id,
                stripe_invoice_id=stripe_invoice_id,
                stripe_payment_intent_id=invoice_data.get("payment_intent"),
                invoice_number=invoice_data.get("number", f"INV-{stripe_invoice_id}"),
                amount_due=invoice_data.get("amount_due", 0),
                amount_paid=0,
                currency=invoice_data.get("currency", "usd").upper(),
                status="open",
                invoice_date=datetime.fromtimestamp(invoice_data.get("created")),
                due_date=datetime.fromtimestamp(invoice_data.get("due_date"))
                if invoice_data.get("due_date") else None,
                invoice_pdf_url=invoice_data.get("invoice_pdf")
            )
            db.add(invoice)
        else:
            invoice.status = "open"

        # Suspend subscription after multiple failed attempts (e.g., 3+)
        if attempt_count >= 3:
            subscription.status = SubscriptionStatus.SUSPENDED.value
            logger.warning(
                f"Suspended subscription for org {subscription.organization_id} "
                f"after {attempt_count} failed payment attempts"
            )
        else:
            subscription.status = SubscriptionStatus.PAST_DUE.value

        db.commit()

        logger.info(
            f"Recorded failed payment for org {subscription.organization_id}, "
            f"invoice {stripe_invoice_id}"
        )

        # TODO: Send payment failed notification email
        # await send_payment_failed_email(
        #     subscription.organization_id,
        #     invoice_id=invoice.id,
        #     attempt_count=attempt_count
        # )

        return True, f"Invoice payment failed for organization {subscription.organization_id}"

    except Exception as e:
        logger.error(f"Error handling invoice failure: {e}")
        db.rollback()
        return False, f"Error: {str(e)}"
