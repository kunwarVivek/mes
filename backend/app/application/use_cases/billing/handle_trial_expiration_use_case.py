"""
Use Case: Handle Trial Expiration

Manages trial expiration logic, including suspension of expired trials
and notification triggers. Typically called by a scheduled job.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.subscription import SubscriptionModel
from app.domain.entities.subscription import SubscriptionStatus
from app.application.services.subscription_service import SubscriptionService
from app.config.pricing import TRIAL_WARNING_DAYS


logger = logging.getLogger(__name__)


class HandleTrialExpirationUseCase:
    """
    Use Case: Handle Trial Expirations

    Responsibilities:
    1. Find trials expiring soon (warning notifications)
    2. Find expired trials (suspension)
    3. Update subscription status
    4. Trigger notification emails

    Single Responsibility: Manage trial lifecycle
    """

    def __init__(self, db: Session):
        """
        Initialize use case

        Args:
            db: Database session
        """
        self.db = db
        self.subscription_service = SubscriptionService(db)

    def execute(self) -> Dict[str, Any]:
        """
        Execute trial expiration handling

        Returns:
            Dictionary with summary:
            {
                "expired_count": 5,
                "expired_org_ids": [123, 456, ...],
                "warning_count": 12,
                "warning_org_ids": [789, ...],
                "timestamp": "2023-11-11T12:00:00Z"
            }
        """
        logger.info("Running trial expiration handler")

        # Step 1: Handle expired trials
        expired_result = self._handle_expired_trials()

        # Step 2: Handle trials expiring soon (warnings)
        warning_result = self._handle_expiring_soon_trials()

        result = {
            "expired_count": len(expired_result),
            "expired_org_ids": expired_result,
            "warning_count": len(warning_result),
            "warning_org_ids": warning_result,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(
            f"Trial expiration handler completed: "
            f"{result['expired_count']} expired, {result['warning_count']} warnings"
        )

        return result

    def _handle_expired_trials(self) -> List[int]:
        """
        Find and suspend expired trials

        Returns:
            List of organization IDs with expired trials
        """
        now = datetime.utcnow()

        # Find expired trials that are still active
        expired_trials = self.db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                SubscriptionModel.trial_ends_at <= now,
                SubscriptionModel.trial_converted == False
            )
        ).all()

        suspended_org_ids = []

        for subscription in expired_trials:
            try:
                # Suspend expired trial
                self.subscription_service.suspend_subscription(
                    subscription.organization_id
                )
                suspended_org_ids.append(subscription.organization_id)

                logger.info(
                    f"Suspended expired trial for organization {subscription.organization_id}"
                )

                # TODO: Trigger notification email
                # self._send_trial_expired_email(subscription)

            except Exception as e:
                logger.error(
                    f"Failed to suspend trial for organization {subscription.organization_id}: {e}"
                )

        return suspended_org_ids

    def _handle_expiring_soon_trials(self) -> List[int]:
        """
        Find trials expiring soon and trigger warning notifications

        Returns:
            List of organization IDs with trials expiring soon
        """
        now = datetime.utcnow()
        warning_threshold = now + timedelta(days=TRIAL_WARNING_DAYS)

        # Find trials expiring within warning period
        expiring_soon = self.db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                SubscriptionModel.trial_ends_at > now,
                SubscriptionModel.trial_ends_at <= warning_threshold,
                SubscriptionModel.trial_converted == False
            )
        ).all()

        warning_org_ids = []

        for subscription in expiring_soon:
            days_remaining = (subscription.trial_ends_at - now).days

            logger.info(
                f"Trial expiring soon for organization {subscription.organization_id}: "
                f"{days_remaining} days remaining"
            )

            warning_org_ids.append(subscription.organization_id)

            # TODO: Trigger warning notification email
            # self._send_trial_expiring_email(subscription, days_remaining)

        return warning_org_ids

    def _send_trial_expired_email(self, subscription: SubscriptionModel) -> None:
        """
        Send trial expired notification email

        Args:
            subscription: Expired subscription

        TODO: Implement email sending via email service
        """
        logger.info(f"TODO: Send trial expired email for org {subscription.organization_id}")
        # email_service.send_trial_expired_email(
        #     to=subscription.billing_email,
        #     organization_id=subscription.organization_id,
        #     trial_ended=subscription.trial_ends_at
        # )

    def _send_trial_expiring_email(
        self,
        subscription: SubscriptionModel,
        days_remaining: int
    ) -> None:
        """
        Send trial expiring soon notification email

        Args:
            subscription: Subscription with trial expiring soon
            days_remaining: Days until trial expiration

        TODO: Implement email sending via email service
        """
        logger.info(
            f"TODO: Send trial expiring email for org {subscription.organization_id}, "
            f"days remaining: {days_remaining}"
        )
        # email_service.send_trial_expiring_email(
        #     to=subscription.billing_email,
        #     organization_id=subscription.organization_id,
        #     days_remaining=days_remaining,
        #     trial_ends=subscription.trial_ends_at
        # )

    def get_trials_requiring_action(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get trials that require action (expired or expiring soon)

        Returns:
            Dictionary with expired and expiring_soon lists
        """
        now = datetime.utcnow()
        warning_threshold = now + timedelta(days=TRIAL_WARNING_DAYS)

        # Expired trials
        expired = self.db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                SubscriptionModel.trial_ends_at <= now,
                SubscriptionModel.trial_converted == False
            )
        ).all()

        # Expiring soon
        expiring_soon = self.db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                SubscriptionModel.trial_ends_at > now,
                SubscriptionModel.trial_ends_at <= warning_threshold,
                SubscriptionModel.trial_converted == False
            )
        ).all()

        return {
            "expired": [
                {
                    "organization_id": s.organization_id,
                    "trial_ends_at": s.trial_ends_at.isoformat(),
                    "days_overdue": (now - s.trial_ends_at).days
                }
                for s in expired
            ],
            "expiring_soon": [
                {
                    "organization_id": s.organization_id,
                    "trial_ends_at": s.trial_ends_at.isoformat(),
                    "days_remaining": (s.trial_ends_at - now).days
                }
                for s in expiring_soon
            ]
        }
