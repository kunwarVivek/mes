"""Setup scheduled jobs using pg_cron

Revision ID: 019_setup_scheduled_jobs
Revises: 018_add_admin_audit_logs
Create Date: 2025-11-11

This migration sets up automated scheduled jobs using pg_cron extension:
1. Usage tracking job (every 6 hours)
2. Trial expiration check (daily at 2 AM UTC)

Requirements:
- pg_cron extension must be installed and enabled
- pg_net extension must be installed (for http_post)
- INTERNAL_API_KEY must be set in environment

Jobs call internal API endpoints that execute use cases.
"""
from alembic import op
import sqlalchemy as sa
import os


# revision identifiers
revision = '019_setup_scheduled_jobs'
down_revision = '018_add_admin_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Set up pg_cron scheduled jobs

    Creates two scheduled jobs:
    1. track-usage: Runs every 6 hours, calculates resource usage
    2. check-trial-expirations: Runs daily at 2 AM UTC, handles expired trials
    """

    # Get API configuration from environment
    api_base_url = os.getenv('API_BASE_URL', 'http://backend:8000')
    internal_api_key = os.getenv('INTERNAL_API_KEY', 'change-me-in-production')

    # Ensure pg_cron extension is available
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_cron;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_net;")

    # Remove existing jobs if they exist (for idempotency)
    op.execute("""
    SELECT cron.unschedule('track-usage') WHERE EXISTS (
        SELECT 1 FROM cron.job WHERE jobname = 'track-usage'
    );
    """)

    op.execute("""
    SELECT cron.unschedule('check-trial-expirations') WHERE EXISTS (
        SELECT 1 FROM cron.job WHERE jobname = 'check-trial-expirations'
    );
    """)

    # Schedule usage tracking job (every 6 hours)
    # Cron: 0 */6 * * * = At minute 0 past every 6th hour
    op.execute(f"""
    SELECT cron.schedule(
        'track-usage',
        '0 */6 * * *',
        $$
        SELECT net.http_post(
            url := '{api_base_url}/api/v1/jobs/track-usage',
            headers := '{{"Content-Type": "application/json", "X-API-Key": "{internal_api_key}"}}'::jsonb
        );
        $$
    );
    """)

    # Schedule trial expiration check (daily at 2 AM UTC)
    # Cron: 0 2 * * * = At 02:00 AM every day
    op.execute(f"""
    SELECT cron.schedule(
        'check-trial-expirations',
        '0 2 * * *',
        $$
        SELECT net.http_post(
            url := '{api_base_url}/api/v1/jobs/check-trial-expirations',
            headers := '{{"Content-Type": "application/json", "X-API-Key": "{internal_api_key}"}}'::jsonb
        );
        $$
    );
    """)

    # Create job execution log table for monitoring
    op.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_job_logs (
        id SERIAL PRIMARY KEY,
        job_name VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'failure')),
        message TEXT,
        processed_count INTEGER DEFAULT 0,
        error_count INTEGER DEFAULT 0,
        details JSONB,
        executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        duration_ms INTEGER
    );

    CREATE INDEX idx_scheduled_job_logs_job_name ON scheduled_job_logs(job_name);
    CREATE INDEX idx_scheduled_job_logs_executed_at ON scheduled_job_logs(executed_at DESC);
    CREATE INDEX idx_scheduled_job_logs_status ON scheduled_job_logs(status);
    """)

    # Add comment documenting the jobs
    op.execute("""
    COMMENT ON TABLE scheduled_job_logs IS
    'Execution logs for pg_cron scheduled jobs. Tracks job runs, success/failure, and performance metrics.';
    """)


def downgrade() -> None:
    """
    Remove scheduled jobs and log table
    """

    # Unschedule jobs
    op.execute("""
    SELECT cron.unschedule('track-usage') WHERE EXISTS (
        SELECT 1 FROM cron.job WHERE jobname = 'track-usage'
    );
    """)

    op.execute("""
    SELECT cron.unschedule('check-trial-expirations') WHERE EXISTS (
        SELECT 1 FROM cron.job WHERE jobname = 'check-trial-expirations'
    );
    """)

    # Drop log table
    op.execute("DROP TABLE IF EXISTS scheduled_job_logs;")
