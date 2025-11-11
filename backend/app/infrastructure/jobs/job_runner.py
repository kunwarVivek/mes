"""
Job Runner - Execute scheduled jobs from pg_cron

This module provides job execution functions that can be called by pg_cron.
Each job function handles its own database session and error logging.

Usage:
    pg_cron schedules jobs that call HTTP endpoints:
    - POST /api/v1/jobs/track-usage (runs every 6 hours)
    - POST /api/v1/jobs/check-trial-expirations (runs daily)
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.infrastructure.persistence.database import SessionLocal
from app.application.use_cases.billing.track_usage_use_case import TrackUsageUseCase
from app.application.use_cases.billing.handle_trial_expiration_use_case import (
    HandleTrialExpirationUseCase,
)
from app.models.subscription import SubscriptionModel
from app.domain.entities.subscription import SubscriptionStatus

logger = logging.getLogger(__name__)


class JobResult:
    """Job execution result"""

    def __init__(
        self,
        success: bool,
        message: str,
        processed_count: int = 0,
        error_count: int = 0,
        details: Dict[str, Any] = None,
    ):
        self.success = success
        self.message = message
        self.processed_count = processed_count
        self.error_count = error_count
        self.details = details or {}
        self.executed_at = datetime.now(timezone.utc)


def track_usage_job() -> JobResult:
    """
    Track usage for all active organizations

    Runs every 6 hours via pg_cron.
    Calculates current resource usage (users, plants, storage) for each
    organization and updates the subscription_usage table.

    Returns:
        JobResult with processed count and any errors
    """
    db = SessionLocal()
    try:
        logger.info("Starting usage tracking job")

        # Get all organizations with active or trial subscriptions
        subscriptions = (
            db.query(SubscriptionModel)
            .filter(
                SubscriptionModel.status.in_(
                    [SubscriptionStatus.TRIAL.value, SubscriptionStatus.ACTIVE.value]
                )
            )
            .all()
        )

        processed = 0
        errors = 0
        error_details = []

        for subscription in subscriptions:
            try:
                use_case = TrackUsageUseCase(db)
                use_case.execute(organization_id=subscription.organization_id)
                processed += 1
                logger.debug(
                    f"Tracked usage for organization {subscription.organization_id}"
                )
            except Exception as e:
                errors += 1
                error_msg = f"Org {subscription.organization_id}: {str(e)}"
                error_details.append(error_msg)
                logger.error(f"Failed to track usage for org {subscription.organization_id}: {e}")

        db.commit()

        result = JobResult(
            success=errors == 0,
            message=f"Tracked usage for {processed} organizations ({errors} errors)",
            processed_count=processed,
            error_count=errors,
            details={"errors": error_details} if error_details else {},
        )

        logger.info(
            f"Usage tracking job completed: {processed} processed, {errors} errors"
        )
        return result

    except Exception as e:
        logger.error(f"Usage tracking job failed: {e}", exc_info=True)
        db.rollback()
        return JobResult(
            success=False, message=f"Job failed: {str(e)}", error_count=1
        )
    finally:
        db.close()


def check_trial_expirations_job() -> JobResult:
    """
    Check for expired trials and handle them

    Runs daily via pg_cron.
    Finds all trials that have ended and suspends them if not converted.
    Can trigger email notifications (if configured).

    Returns:
        JobResult with processed count and any errors
    """
    db = SessionLocal()
    try:
        logger.info("Starting trial expiration check job")

        # Get all trial subscriptions that have ended
        now = datetime.now(timezone.utc)
        expired_trials = (
            db.query(SubscriptionModel)
            .filter(
                and_(
                    SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                    SubscriptionModel.trial_ends_at < now,
                    SubscriptionModel.trial_converted == False,
                )
            )
            .all()
        )

        processed = 0
        errors = 0
        error_details = []

        for subscription in expired_trials:
            try:
                use_case = HandleTrialExpirationUseCase(db)
                use_case.execute(organization_id=subscription.organization_id)
                processed += 1
                logger.info(
                    f"Handled trial expiration for organization {subscription.organization_id}"
                )
            except Exception as e:
                errors += 1
                error_msg = f"Org {subscription.organization_id}: {str(e)}"
                error_details.append(error_msg)
                logger.error(
                    f"Failed to handle trial expiration for org {subscription.organization_id}: {e}"
                )

        db.commit()

        result = JobResult(
            success=errors == 0,
            message=f"Handled {processed} expired trials ({errors} errors)",
            processed_count=processed,
            error_count=errors,
            details={"errors": error_details} if error_details else {},
        )

        logger.info(
            f"Trial expiration job completed: {processed} processed, {errors} errors"
        )
        return result

    except Exception as e:
        logger.error(f"Trial expiration job failed: {e}", exc_info=True)
        db.rollback()
        return JobResult(
            success=False, message=f"Job failed: {str(e)}", error_count=1
        )
    finally:
        db.close()


def get_job_stats(db: Session) -> Dict[str, Any]:
    """
    Get statistics about scheduled jobs

    Args:
        db: Database session

    Returns:
        Dictionary with job statistics
    """
    try:
        # Count subscriptions by status
        trial_count = (
            db.query(func.count(SubscriptionModel.id))
            .filter(SubscriptionModel.status == SubscriptionStatus.TRIAL.value)
            .scalar()
        )

        active_count = (
            db.query(func.count(SubscriptionModel.id))
            .filter(SubscriptionModel.status == SubscriptionStatus.ACTIVE.value)
            .scalar()
        )

        # Count expired trials (not converted)
        now = datetime.now(timezone.utc)
        expired_trial_count = (
            db.query(func.count(SubscriptionModel.id))
            .filter(
                and_(
                    SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                    SubscriptionModel.trial_ends_at < now,
                    SubscriptionModel.trial_converted == False,
                )
            )
            .scalar()
        )

        return {
            "trial_subscriptions": trial_count,
            "active_subscriptions": active_count,
            "expired_trials_pending": expired_trial_count,
            "total_to_track": trial_count + active_count,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get job stats: {e}")
        return {"error": str(e)}
