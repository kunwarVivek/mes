"""Complete RLS implementation for all tenant tables

Revision ID: ef6ec56e007e
Revises: 59a3603c568e
Create Date: 2025-11-09 15:52:51.224020

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'ef6ec56e007e'
down_revision = '59a3603c568e'
branch_labels = None
depends_on = None


# Tables that currently have organization_id (discovered from database)
TENANT_TABLES_WITH_ORG_ID = [
    'bom_header',
    'cost_layer',
    'downtime_event',
    'inspection_log',
    'inspection_plan',
    'inventory',
    'inventory_transaction',
    'machine',
    'material',
    'material_category',
    'material_costing',
    'ncr',
    'operation_scheduling_config',
    'plants',
    'pm_schedule',
    'pm_work_order',
    'production_logs',
    'projects',
    'rework_config',
    'shift',
    'shift_handover',
    'shift_performance',
    'storage_location',
    'work_center',
    'work_order',
    'work_order_operation',
]

# Tables that only have organization_id (no plant_id)
ORG_ONLY_TABLES = [
    'material_category',
    'plants',
]

# Global tables - organizations doesn't have organization_id, needs special handling
ORGANIZATIONS_TABLE = 'organizations'


def upgrade() -> None:
    conn = op.get_bind()

    print("\n" + "="*80)
    print("RLS Implementation - Complete Multi-Tenant Security")
    print("="*80 + "\n")

    # =========================================================================
    # STEP 1: Add tenant fields to users table
    # =========================================================================
    print("Step 1: Adding tenant fields to users table...")

    # Add organization_id column
    print("  Adding organization_id to users table...")
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_users_organization_id',
        'users',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_users_organization_id', 'users', ['organization_id'])
    print("    organization_id added to users")

    # Add plant_id column
    print("  Adding plant_id to users table...")
    op.add_column('users', sa.Column('plant_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_users_plant_id',
        'users',
        'plants',
        ['plant_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_users_plant_id', 'users', ['plant_id'])
    print("    plant_id added to users")
    print("  Users table schema updated\n")

    # =========================================================================
    # STEP 2: Enable RLS and create policies for all tenant tables
    # =========================================================================
    print("Step 2: Creating RLS policies for all tables...")
    print("  Total tables to configure: %d\n" % (len(TENANT_TABLES_WITH_ORG_ID) + 2))

    policies_created = 0

    # Handle organizations table (special case - self-referential)
    print("  Configuring RLS for organizations...")
    conn.execute(text("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("DROP POLICY IF EXISTS organizations_org_isolation ON organizations;"))
    conn.execute(text("""
        CREATE POLICY organizations_org_isolation ON organizations
        FOR ALL
        USING (
            id = current_setting('app.current_organization_id', true)::int
        );
    """))
    print("    Created self-referential org policy: organizations_org_isolation")
    policies_created += 1

    # Handle users table
    print("  Configuring RLS for users...")
    conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY;"))
    conn.execute(text("DROP POLICY IF EXISTS users_org_isolation ON users;"))
    conn.execute(text("DROP POLICY IF EXISTS users_plant_isolation ON users;"))

    conn.execute(text("""
        CREATE POLICY users_org_isolation ON users
        FOR ALL
        USING (
            organization_id = current_setting('app.current_organization_id', true)::int
        );
    """))
    print("    Created org policy: users_org_isolation")
    policies_created += 1

    conn.execute(text("""
        CREATE POLICY users_plant_isolation ON users
        FOR ALL
        USING (
            plant_id IS NULL OR
            plant_id = current_setting('app.current_plant_id', true)::int
        );
    """))
    print("    Created plant policy: users_plant_isolation")
    policies_created += 1

    # Handle all other tenant tables
    for table_name in TENANT_TABLES_WITH_ORG_ID:
        print("  Configuring RLS for %s..." % table_name)

        # Enable RLS on the table
        conn.execute(text("ALTER TABLE %s ENABLE ROW LEVEL SECURITY;" % table_name))

        # Drop existing policies if they exist (for idempotency)
        conn.execute(text("DROP POLICY IF EXISTS %s_org_isolation ON %s;" % (table_name, table_name)))
        conn.execute(text("DROP POLICY IF EXISTS %s_plant_isolation ON %s;" % (table_name, table_name)))

        # Create organization isolation policy
        conn.execute(text("""
            CREATE POLICY %s_org_isolation ON %s
            FOR ALL
            USING (
                organization_id = current_setting('app.current_organization_id', true)::int
            );
        """ % (table_name, table_name)))
        print("    Created org policy: %s_org_isolation" % table_name)
        policies_created += 1

        # Create plant isolation policy (if table has plant_id)
        if table_name not in ORG_ONLY_TABLES:
            # Check if table has plant_id column
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = '%s'
                    AND column_name = 'plant_id'
                );
            """ % table_name))
            has_plant_id = result.scalar()

            if has_plant_id:
                conn.execute(text("""
                    CREATE POLICY %s_plant_isolation ON %s
                    FOR ALL
                    USING (
                        plant_id IS NULL OR
                        plant_id = current_setting('app.current_plant_id', true)::int
                    );
                """ % (table_name, table_name)))
                print("    Created plant policy: %s_plant_isolation" % table_name)
                policies_created += 1

    print("\nRLS Policy Summary:")
    print("  Policies created: %d\n" % policies_created)

    # =========================================================================
    # STEP 3: Update RLS helper function
    # =========================================================================
    print("Step 3: Updating RLS helper function...")

    # Build the table list dynamically
    all_tables = ['users', 'organizations'] + TENANT_TABLES_WITH_ORG_ID
    table_list = "'" + "', '".join(all_tables) + "'"

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION verify_rls_policies()
        RETURNS TABLE(table_name TEXT, rls_enabled BOOLEAN, policy_count INTEGER)
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                t.tablename::TEXT,
                t.rowsecurity::BOOLEAN,
                COUNT(p.policyname)::INTEGER as policy_count
            FROM pg_tables t
            LEFT JOIN pg_policies p ON t.tablename = p.tablename
            WHERE t.schemaname = 'public'
            AND t.tablename IN (%s)
            GROUP BY t.tablename, t.rowsecurity
            ORDER BY t.tablename;
        END;
        $$;
    """ % table_list))
    print("  Helper function verify_rls_policies() updated\n")

    # =========================================================================
    # STEP 4: Verify RLS policies
    # =========================================================================
    print("Verifying RLS policies...")
    result = conn.execute(text("SELECT * FROM verify_rls_policies();"))
    verification_data = result.fetchall()

    tables_with_rls = 0
    tables_without_rls = 0

    for row in verification_data:
        table_name, rls_enabled, policy_count = row
        if rls_enabled and policy_count > 0:
            print("  %s: RLS=ON, Policies=%d" % (table_name, policy_count))
            tables_with_rls += 1
        else:
            print("  %s: RLS=%s, Policies=%d" % (table_name, 'ON' if rls_enabled else 'OFF', policy_count))
            tables_without_rls += 1

    total_tables = len(verification_data)
    coverage_percentage = (tables_with_rls / total_tables * 100) if total_tables > 0 else 0

    print("\nFinal Statistics:")
    print("  Total tables: %d" % total_tables)
    print("  Tables with RLS: %d" % tables_with_rls)
    print("  Tables without RLS: %d" % tables_without_rls)
    print("  Coverage: %.1f%%\n" % coverage_percentage)

    if tables_without_rls == 0:
        print("Complete RLS implementation finished successfully!")
    else:
        print("RLS implementation completed with warnings - some tables lack policies")

    print("\n" + "="*80 + "\n")


def downgrade() -> None:
    conn = op.get_bind()

    print("\n" + "="*80)
    print("Rolling back RLS implementation...")
    print("="*80 + "\n")

    # Step 1: Remove RLS policies from all tables
    print("Step 1: Removing RLS policies...")

    # Handle organizations
    conn.execute(text("DROP POLICY IF EXISTS organizations_org_isolation ON organizations;"))
    conn.execute(text("ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;"))

    # Handle users
    conn.execute(text("DROP POLICY IF EXISTS users_org_isolation ON users;"))
    conn.execute(text("DROP POLICY IF EXISTS users_plant_isolation ON users;"))
    conn.execute(text("ALTER TABLE users DISABLE ROW LEVEL SECURITY;"))

    # Handle all other tenant tables
    for table_name in TENANT_TABLES_WITH_ORG_ID:
        conn.execute(text("DROP POLICY IF EXISTS %s_org_isolation ON %s;" % (table_name, table_name)))
        conn.execute(text("DROP POLICY IF EXISTS %s_plant_isolation ON %s;" % (table_name, table_name)))
        conn.execute(text("ALTER TABLE %s DISABLE ROW LEVEL SECURITY;" % table_name))

    print("  All RLS policies removed\n")

    # Step 2: Remove tenant fields from users table
    print("Step 2: Removing tenant fields from users table...")
    op.drop_index('idx_users_plant_id', 'users')
    op.drop_constraint('fk_users_plant_id', 'users', type_='foreignkey')
    op.drop_column('users', 'plant_id')

    op.drop_index('idx_users_organization_id', 'users')
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    op.drop_column('users', 'organization_id')
    print("  Tenant fields removed from users table\n")

    print("Rollback completed successfully!")
    print("="*80 + "\n")
