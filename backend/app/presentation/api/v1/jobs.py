"""
Jobs API - Endpoints for scheduled jobs

These endpoints are called by pg_cron to execute scheduled tasks.
Access is restricted to internal calls only (no external access).

Security: Use internal API key or IP whitelist in production.
"""
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.infrastructure.persistence.database import get_db
from app.infrastructure.jobs.job_runner import (
    track_usage_job,
    check_trial_expirations_job,
    get_job_stats,
    JobResult,
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def verify_internal_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verify internal API key for job endpoints

    In production, set INTERNAL_API_KEY environment variable.
    For development, this check is optional.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: If API key is invalid
    """
    internal_api_key = getattr(settings, "INTERNAL_API_KEY", None)

    # If no internal API key is configured, allow access (dev mode)
    if not internal_api_key:
        logger.warning(
            "INTERNAL_API_KEY not configured - allowing job access (development mode)"
        )
        return True

    # Verify API key
    if x_api_key != internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )

    return True


class JobResultResponse:
    """Response model for job execution"""

    def __init__(self, result: JobResult):
        self.success = result.success
        self.message = result.message
        self.processed_count = result.processed_count
        self.error_count = result.error_count
        self.details = result.details
        self.executed_at = result.executed_at.isoformat()


@router.post("/track-usage")
async def run_usage_tracking_job(
    authorized: bool = Depends(verify_internal_api_key),
):
    """
    Execute usage tracking job

    Tracks resource usage (users, plants, storage) for all active organizations.
    Called by pg_cron every 6 hours.

    **Cron Schedule**: `0 */6 * * *` (every 6 hours)

    **pg_cron Command**:
    ```sql
    SELECT cron.schedule(
        'track-usage',
        '0 */6 * * *',
        $$
        SELECT net.http_post(
            url := 'http://backend:8000/api/v1/jobs/track-usage',
            headers := '{"Content-Type": "application/json", "X-API-Key": "your-internal-api-key"}'
        );
        $$
    );
    ```

    Returns:
        JobResultResponse with execution summary
    """
    logger.info("Usage tracking job triggered via API")

    result = track_usage_job()

    return {
        "success": result.success,
        "message": result.message,
        "processed_count": result.processed_count,
        "error_count": result.error_count,
        "details": result.details,
        "executed_at": result.executed_at.isoformat(),
    }


@router.post("/check-trial-expirations")
async def run_trial_expiration_job(
    authorized: bool = Depends(verify_internal_api_key),
):
    """
    Execute trial expiration check job

    Finds expired trials and suspends access if not converted to paid.
    Called by pg_cron daily at 2 AM UTC.

    **Cron Schedule**: `0 2 * * *` (daily at 2 AM UTC)

    **pg_cron Command**:
    ```sql
    SELECT cron.schedule(
        'check-trial-expirations',
        '0 2 * * *',
        $$
        SELECT net.http_post(
            url := 'http://backend:8000/api/v1/jobs/check-trial-expirations',
            headers := '{"Content-Type": "application/json", "X-API-Key": "your-internal-api-key"}'
        );
        $$
    );
    ```

    Returns:
        JobResultResponse with execution summary
    """
    logger.info("Trial expiration check job triggered via API")

    result = check_trial_expirations_job()

    return {
        "success": result.success,
        "message": result.message,
        "processed_count": result.processed_count,
        "error_count": result.error_count,
        "details": result.details,
        "executed_at": result.executed_at.isoformat(),
    }


@router.get("/stats")
async def get_job_statistics(
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_internal_api_key),
):
    """
    Get job execution statistics

    Returns counts of subscriptions and pending operations.
    Useful for monitoring job health.

    Returns:
        Dictionary with subscription counts and pending operations
    """
    stats = get_job_stats(db)
    return stats


@router.post("/trigger-all")
async def trigger_all_jobs(
    authorized: bool = Depends(verify_internal_api_key),
):
    """
    Manually trigger all scheduled jobs

    Useful for testing or manual execution.
    Runs usage tracking and trial expiration jobs sequentially.

    Returns:
        Dictionary with results from both jobs
    """
    logger.info("Manually triggering all jobs")

    usage_result = track_usage_job()
    trial_result = check_trial_expiration_job()

    return {
        "usage_tracking": {
            "success": usage_result.success,
            "message": usage_result.message,
            "processed_count": usage_result.processed_count,
            "error_count": usage_result.error_count,
        },
        "trial_expiration": {
            "success": trial_result.success,
            "message": trial_result.message,
            "processed_count": trial_result.processed_count,
            "error_count": trial_result.error_count,
        },
        "executed_at": datetime.now().isoformat(),
    }
