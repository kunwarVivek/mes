"""Add admin audit logs for platform admin actions

Revision ID: 018_add_admin_audit_logs
Revises: 017_add_subscription_tables
Create Date: 2025-11-11 12:00:00.000000

Creates audit logging infrastructure for platform admin operations:

Tables:
- admin_audit_logs: Complete audit trail of all admin actions

Business Rules:
- Immutable audit records (no updates/deletes after creation)
- Retained indefinitely for compliance and security
- Indexed for fast querying by admin, organization, action type
- JSON details field for flexible context storage

All platform admin actions are logged including:
- Organization management (activate/deactivate)
- Subscription changes (trial extension, suspension, reactivation)
- User impersonation
- Data access and exports
- Configuration changes
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '018_add_admin_audit_logs'
down_revision = '017_add_subscription_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create admin audit logs table for tracking platform admin actions.

    All admin operations are logged for:
    - Security auditing
    - Compliance requirements (SOC2, GDPR)
    - Debugging and troubleshooting
    - Accountability and transparency
    """
    conn = op.get_bind()

    # ========================================================================
    # 1. Create admin_audit_logs table
    # ========================================================================

    conn.execute(text("""
        CREATE TABLE admin_audit_logs (
            id SERIAL PRIMARY KEY,

            -- Admin performing action
            admin_user_id INTEGER NOT NULL,

            -- Action details
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50) NOT NULL,  -- organization, subscription, user, etc.
            target_id INTEGER,  -- ID of affected resource (nullable)

            -- Additional context (JSON for flexibility)
            details JSONB,

            -- Timestamp (immutable)
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );

        COMMENT ON TABLE admin_audit_logs IS
            'Audit log for all platform admin actions. Immutable records for compliance.';

        COMMENT ON COLUMN admin_audit_logs.admin_user_id IS
            'User ID of platform admin performing action';

        COMMENT ON COLUMN admin_audit_logs.action IS
            'Action performed (e.g., suspend_subscription, extend_trial, impersonate_user)';

        COMMENT ON COLUMN admin_audit_logs.target_type IS
            'Type of resource affected (organization, subscription, user, platform)';

        COMMENT ON COLUMN admin_audit_logs.target_id IS
            'ID of affected resource (NULL for platform-wide actions)';

        COMMENT ON COLUMN admin_audit_logs.details IS
            'JSON context including reason, changes, previous values, etc.';

        COMMENT ON COLUMN admin_audit_logs.created_at IS
            'Timestamp of action (immutable, for audit trail)';
    """))

    # ========================================================================
    # 2. Create indexes for efficient querying
    # ========================================================================

    conn.execute(text("""
        -- Index for querying by admin user
        CREATE INDEX idx_audit_admin_user
            ON admin_audit_logs(admin_user_id);

        -- Index for querying by action type
        CREATE INDEX idx_audit_action
            ON admin_audit_logs(action);

        -- Composite index for querying by target
        CREATE INDEX idx_audit_target
            ON admin_audit_logs(target_type, target_id);

        -- Index for time-based queries
        CREATE INDEX idx_audit_created
            ON admin_audit_logs(created_at DESC);

        -- Composite index for user activity queries
        CREATE INDEX idx_audit_admin_action
            ON admin_audit_logs(admin_user_id, action);

        -- GIN index for JSON field querying
        CREATE INDEX idx_audit_details_gin
            ON admin_audit_logs USING GIN (details);
    """))

    # ========================================================================
    # 3. Add comments for documentation
    # ========================================================================

    conn.execute(text("""
        COMMENT ON INDEX idx_audit_admin_user IS
            'Fast lookup of all actions by specific admin user';

        COMMENT ON INDEX idx_audit_action IS
            'Fast filtering by action type (e.g., all subscription suspensions)';

        COMMENT ON INDEX idx_audit_target IS
            'Fast lookup of all actions on specific resource';

        COMMENT ON INDEX idx_audit_created IS
            'Fast time-based queries and pagination';

        COMMENT ON INDEX idx_audit_admin_action IS
            'Optimized for user activity reports';

        COMMENT ON INDEX idx_audit_details_gin IS
            'Fast JSON field searches (e.g., find all actions with specific reason)';
    """))

    # ========================================================================
    # 4. Create view for enriched audit logs (with admin email)
    # ========================================================================

    conn.execute(text("""
        CREATE OR REPLACE VIEW admin_audit_logs_enriched AS
        SELECT
            aal.id,
            aal.admin_user_id,
            u.email AS admin_email,
            u.username AS admin_username,
            aal.action,
            aal.target_type,
            aal.target_id,
            aal.details,
            aal.created_at
        FROM admin_audit_logs aal
        LEFT JOIN users u ON aal.admin_user_id = u.id
        ORDER BY aal.created_at DESC;

        COMMENT ON VIEW admin_audit_logs_enriched IS
            'Audit logs with admin user details (email, username) for reporting';
    """))

    print("✅ Admin audit logs table created successfully")
    print("✅ Indexes created for efficient querying")
    print("✅ Enriched view created for reporting")


def downgrade() -> None:
    """
    Remove admin audit logs infrastructure.

    WARNING: This will permanently delete all audit logs.
    Only use in development/testing environments.
    """
    conn = op.get_bind()

    # Drop view first
    conn.execute(text("DROP VIEW IF EXISTS admin_audit_logs_enriched;"))

    # Drop table (indexes are automatically dropped)
    conn.execute(text("DROP TABLE IF EXISTS admin_audit_logs CASCADE;"))

    print("⚠️  Admin audit logs table dropped")
