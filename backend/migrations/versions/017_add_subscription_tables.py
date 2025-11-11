"""Add comprehensive subscription system for B2B SaaS

Revision ID: 017_add_subscription_tables
Revises: 007_inventory_alerts
Create Date: 2025-11-11 10:00:00.000000

Creates a complete subscription management system for Unison Manufacturing ERP:

Tables:
- subscriptions: Core subscription data with Stripe integration
- subscription_usage: Track current resource usage vs limits
- invoices: Billing history and payment tracking
- subscription_add_ons: Additional purchased capacity (users, plants, storage)

Also updates organizations table with onboarding tracking fields.

Triggers:
- Auto-update updated_at timestamps on subscriptions and invoices
- Auto-create trial subscription on new organization creation

Business Rules:
- 3-tier pricing: Starter, Professional, Enterprise
- Trial period management with conversion tracking
- Usage limits enforcement (NULL = unlimited for Enterprise)
- Stripe webhook integration for payment events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '017_add_subscription_tables'
down_revision = '007_inventory_alerts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create subscription system infrastructure.

    Creates tables for subscription management, billing, usage tracking,
    and add-ons. Also creates triggers for automation.
    """
    conn = op.get_bind()

    # ========================================================================
    # 1. Create subscriptions table
    # ========================================================================
    print("Creating subscriptions table...")

    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('tier', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('billing_cycle', sa.String(20), nullable=True),

        # Trial management
        sa.Column('trial_starts_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_converted', sa.Boolean(), server_default='false', nullable=False),

        # Stripe integration
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),

        # Billing
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_email', sa.String(255), nullable=True),

        # Limits (NULL = unlimited for Enterprise)
        sa.Column('max_users', sa.Integer(), nullable=True),
        sa.Column('max_plants', sa.Integer(), nullable=True),
        sa.Column('storage_limit_gb', sa.Integer(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', name='uq_subscriptions_organization_id'),
        sa.UniqueConstraint('stripe_customer_id', name='uq_subscriptions_stripe_customer_id'),
        sa.UniqueConstraint('stripe_subscription_id', name='uq_subscriptions_stripe_subscription_id'),
        sa.CheckConstraint(
            "tier IN ('starter', 'professional', 'enterprise')",
            name='ck_subscriptions_tier'
        ),
        sa.CheckConstraint(
            "status IN ('trial', 'active', 'cancelled', 'past_due', 'suspended')",
            name='ck_subscriptions_status'
        ),
        sa.CheckConstraint(
            "billing_cycle IN ('monthly', 'annual') OR billing_cycle IS NULL",
            name='ck_subscriptions_billing_cycle'
        ),
    )

    # Create indexes for performance
    op.create_index('idx_subscriptions_org_id', 'subscriptions', ['organization_id'])
    op.create_index('idx_subscriptions_stripe_customer', 'subscriptions', ['stripe_customer_id'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('idx_subscriptions_trial_ends', 'subscriptions', ['trial_ends_at'])
    op.create_index('idx_subscriptions_tier', 'subscriptions', ['tier'])

    # Add foreign key
    op.create_foreign_key(
        'fk_subscriptions_organization',
        'subscriptions', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )

    print("  ✓ subscriptions table created")

    # ========================================================================
    # 2. Create subscription_usage table
    # ========================================================================
    print("Creating subscription_usage table...")

    op.create_table(
        'subscription_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Current usage
        sa.Column('current_users', sa.Integer(), server_default='0', nullable=False),
        sa.Column('current_plants', sa.Integer(), server_default='0', nullable=False),
        sa.Column('storage_used_gb', sa.Numeric(10, 2), server_default='0.00', nullable=False),

        # Measured timestamp
        sa.Column('measured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    op.create_index('idx_subscription_usage_org_id', 'subscription_usage', ['organization_id'])
    op.create_index('idx_subscription_usage_measured_at', 'subscription_usage', ['measured_at'])

    # Add foreign key
    op.create_foreign_key(
        'fk_subscription_usage_organization',
        'subscription_usage', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )

    print("  ✓ subscription_usage table created")

    # ========================================================================
    # 3. Create invoices table
    # ========================================================================
    print("Creating invoices table...")

    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),

        # Stripe
        sa.Column('stripe_invoice_id', sa.String(255), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True),

        # Invoice details
        sa.Column('invoice_number', sa.String(100), nullable=True),
        sa.Column('amount_due', sa.Integer(), nullable=False),  # in cents
        sa.Column('amount_paid', sa.Integer(), server_default='0', nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=False),

        # Status
        sa.Column('status', sa.String(50), nullable=False),

        # Dates
        sa.Column('invoice_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),

        # PDF
        sa.Column('invoice_pdf_url', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_invoice_id', name='uq_invoices_stripe_invoice_id'),
        sa.UniqueConstraint('invoice_number', name='uq_invoices_invoice_number'),
        sa.CheckConstraint(
            "status IN ('draft', 'open', 'paid', 'void', 'uncollectible')",
            name='ck_invoices_status'
        ),
    )

    # Create indexes
    op.create_index('idx_invoices_org_id', 'invoices', ['organization_id'])
    op.create_index('idx_invoices_subscription_id', 'invoices', ['subscription_id'])
    op.create_index('idx_invoices_stripe_id', 'invoices', ['stripe_invoice_id'])
    op.create_index('idx_invoices_status', 'invoices', ['status'])
    op.create_index('idx_invoices_due_date', 'invoices', ['due_date'])
    op.create_index('idx_invoices_invoice_date', 'invoices', ['invoice_date'])

    # Add foreign keys
    op.create_foreign_key(
        'fk_invoices_organization',
        'invoices', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_invoices_subscription',
        'invoices', 'subscriptions',
        ['subscription_id'], ['id'],
        ondelete='CASCADE'
    )

    print("  ✓ invoices table created")

    # ========================================================================
    # 4. Create subscription_add_ons table
    # ========================================================================
    print("Creating subscription_add_ons table...")

    op.create_table(
        'subscription_add_ons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=False),

        # Add-on type
        sa.Column('add_on_type', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Integer(), nullable=False),  # in cents

        # Stripe
        sa.Column('stripe_price_id', sa.String(255), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "add_on_type IN ('extra_users', 'extra_plants', 'extra_storage_gb')",
            name='ck_add_ons_type'
        ),
    )

    # Create indexes
    op.create_index('idx_add_ons_subscription_id', 'subscription_add_ons', ['subscription_id'])
    op.create_index('idx_add_ons_type', 'subscription_add_ons', ['add_on_type'])
    op.create_index('idx_add_ons_active', 'subscription_add_ons', ['subscription_id', 'removed_at'])

    # Add foreign key
    op.create_foreign_key(
        'fk_add_ons_subscription',
        'subscription_add_ons', 'subscriptions',
        ['subscription_id'], ['id'],
        ondelete='CASCADE'
    )

    print("  ✓ subscription_add_ons table created")

    # ========================================================================
    # 5. Update organizations table with onboarding fields
    # ========================================================================
    print("Adding onboarding fields to organizations table...")

    op.add_column('organizations', sa.Column('onboarding_completed', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('organizations', sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True))

    # Create index for onboarding queries
    op.create_index('idx_organizations_onboarding', 'organizations', ['onboarding_completed'])

    print("  ✓ onboarding fields added to organizations")

    # ========================================================================
    # 6. Create trigger function for updated_at timestamps
    # ========================================================================
    print("Creating timestamp trigger function...")

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION update_subscription_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    print("  ✓ Timestamp trigger function created")

    # ========================================================================
    # 7. Create triggers for updated_at on subscriptions and invoices
    # ========================================================================
    print("Creating updated_at triggers...")

    conn.execute(text("""
        CREATE TRIGGER trg_subscriptions_updated_at
        BEFORE UPDATE ON subscriptions
        FOR EACH ROW
        EXECUTE FUNCTION update_subscription_updated_at();
    """))

    conn.execute(text("""
        CREATE TRIGGER trg_invoices_updated_at
        BEFORE UPDATE ON invoices
        FOR EACH ROW
        EXECUTE FUNCTION update_subscription_updated_at();
    """))

    print("  ✓ Updated_at triggers created")

    # ========================================================================
    # 8. Create function to initialize trial subscription on org creation
    # ========================================================================
    print("Creating default trial subscription function...")

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION create_default_trial_subscription()
        RETURNS TRIGGER AS $$
        DECLARE
            v_trial_days INTEGER := 14;  -- 14-day trial
            v_trial_start TIMESTAMP WITH TIME ZONE := NOW();
            v_trial_end TIMESTAMP WITH TIME ZONE := NOW() + INTERVAL '14 days';
        BEGIN
            -- Create trial subscription for new organization
            INSERT INTO subscriptions (
                organization_id,
                tier,
                status,
                billing_cycle,
                trial_starts_at,
                trial_ends_at,
                trial_converted,
                max_users,
                max_plants,
                storage_limit_gb,
                created_at
            ) VALUES (
                NEW.id,
                'starter',                    -- Default to starter tier
                'trial',                      -- Trial status
                NULL,                         -- No billing cycle during trial
                v_trial_start,
                v_trial_end,
                FALSE,                        -- Not yet converted
                3,                           -- Starter: 3 users
                1,                           -- Starter: 1 plant
                10,                          -- Starter: 10GB storage
                NOW()
            );

            -- Create initial usage tracking record
            INSERT INTO subscription_usage (
                organization_id,
                current_users,
                current_plants,
                storage_used_gb,
                measured_at
            ) VALUES (
                NEW.id,
                0,                           -- No users yet
                0,                           -- No plants yet
                0.00,                        -- No storage used yet
                NOW()
            );

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    print("  ✓ Default trial subscription function created")

    # ========================================================================
    # 9. Create trigger on organizations to auto-create trial subscription
    # ========================================================================
    print("Creating organization subscription trigger...")

    conn.execute(text("""
        CREATE TRIGGER trg_create_trial_subscription
        AFTER INSERT ON organizations
        FOR EACH ROW
        EXECUTE FUNCTION create_default_trial_subscription();
    """))

    print("  ✓ Organization subscription trigger created")

    # ========================================================================
    # 10. Enable RLS on subscription tables
    # ========================================================================
    print("Enabling Row-Level Security on subscription tables...")

    # Enable RLS on all subscription tables
    conn.execute(text("ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE subscription_usage ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("ALTER TABLE subscription_add_ons ENABLE ROW LEVEL SECURITY;"))

    # Create RLS policies for organization isolation
    conn.execute(text("""
        CREATE POLICY subscriptions_organization_isolation ON subscriptions
        FOR ALL
        USING (
            organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER
        );
    """))

    conn.execute(text("""
        CREATE POLICY subscription_usage_organization_isolation ON subscription_usage
        FOR ALL
        USING (
            organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER
        );
    """))

    conn.execute(text("""
        CREATE POLICY invoices_organization_isolation ON invoices
        FOR ALL
        USING (
            organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER
        );
    """))

    conn.execute(text("""
        CREATE POLICY subscription_add_ons_organization_isolation ON subscription_add_ons
        FOR ALL
        USING (
            subscription_id IN (
                SELECT id FROM subscriptions
                WHERE organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER
            )
        );
    """))

    print("  ✓ RLS policies created")

    print("\n✅ Subscription system created successfully!")
    print("   Tables created:")
    print("     - subscriptions (with Stripe integration)")
    print("     - subscription_usage (resource tracking)")
    print("     - invoices (billing history)")
    print("     - subscription_add_ons (extra capacity)")
    print("   ")
    print("   Organizations table updated:")
    print("     - onboarding_completed")
    print("     - onboarding_completed_at")
    print("   ")
    print("   Triggers created:")
    print("     - Auto-update updated_at on subscriptions/invoices")
    print("     - Auto-create 14-day trial on organization creation")
    print("   ")
    print("   Row-Level Security:")
    print("     - All subscription tables isolated by organization_id")


def downgrade() -> None:
    """Remove subscription system infrastructure"""
    conn = op.get_bind()

    print("Removing subscription system infrastructure...")

    # ========================================================================
    # 1. Drop RLS policies
    # ========================================================================
    print("Dropping RLS policies...")

    try:
        conn.execute(text("DROP POLICY IF EXISTS subscription_add_ons_organization_isolation ON subscription_add_ons;"))
        conn.execute(text("DROP POLICY IF EXISTS invoices_organization_isolation ON invoices;"))
        conn.execute(text("DROP POLICY IF EXISTS subscription_usage_organization_isolation ON subscription_usage;"))
        conn.execute(text("DROP POLICY IF EXISTS subscriptions_organization_isolation ON subscriptions;"))
        print("  ✓ RLS policies dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop RLS policies: {e}")

    # ========================================================================
    # 2. Drop triggers
    # ========================================================================
    print("Dropping triggers...")

    try:
        conn.execute(text("DROP TRIGGER IF EXISTS trg_create_trial_subscription ON organizations;"))
        conn.execute(text("DROP TRIGGER IF EXISTS trg_invoices_updated_at ON invoices;"))
        conn.execute(text("DROP TRIGGER IF EXISTS trg_subscriptions_updated_at ON subscriptions;"))
        print("  ✓ Triggers dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop triggers: {e}")

    # ========================================================================
    # 3. Drop trigger functions
    # ========================================================================
    print("Dropping trigger functions...")

    try:
        conn.execute(text("DROP FUNCTION IF EXISTS create_default_trial_subscription();"))
        conn.execute(text("DROP FUNCTION IF EXISTS update_subscription_updated_at();"))
        print("  ✓ Trigger functions dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop trigger functions: {e}")

    # ========================================================================
    # 4. Drop tables (in reverse order of dependencies)
    # ========================================================================
    print("Dropping subscription tables...")

    try:
        op.drop_table('subscription_add_ons')
        print("  ✓ subscription_add_ons table dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop subscription_add_ons: {e}")

    try:
        op.drop_table('invoices')
        print("  ✓ invoices table dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop invoices: {e}")

    try:
        op.drop_table('subscription_usage')
        print("  ✓ subscription_usage table dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop subscription_usage: {e}")

    try:
        op.drop_table('subscriptions')
        print("  ✓ subscriptions table dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop subscriptions: {e}")

    # ========================================================================
    # 5. Remove onboarding fields from organizations table
    # ========================================================================
    print("Removing onboarding fields from organizations table...")

    try:
        op.drop_index('idx_organizations_onboarding', table_name='organizations')
        op.drop_column('organizations', 'onboarding_completed_at')
        op.drop_column('organizations', 'onboarding_completed')
        print("  ✓ Onboarding fields removed from organizations")
    except Exception as e:
        print(f"  ✗ Failed to remove onboarding fields: {e}")

    print("\n✅ Subscription system infrastructure removed")
