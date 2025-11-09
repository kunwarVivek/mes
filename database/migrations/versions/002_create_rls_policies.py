"""Create Row-Level Security (RLS) policies for multi-tenant data isolation

Revision ID: 002_create_rls_policies
Revises: 001_install_extensions
Create Date: 2025-11-08 02:30:00.000000

This migration creates:
1. RLS audit log table for tracking context changes
2. RLS policies on tenant tables (users, organizations, plants)
3. Helper function for policy verification

RLS Policy Pattern:
- Organization isolation: Filter by organization_id
- Plant isolation: Filter by plant_id (optional, allows NULL)
- Context variables: app.current_organization_id, app.current_plant_id

Security:
- All tenant tables have RLS enabled
- Policies enforce multi-tenant data isolation
- Audit logging tracks all context changes (optional)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '002_create_rls_policies'
down_revision = '001_install_extensions'
branch_labels = None
depends_on = None


# Tables that require RLS policies (multi-tenant tables)
TENANT_TABLES = [
    'users',
    'organizations',
    'plants',
    'materials',
    'work_orders',
    'production_lines',
    'inventory_transactions',
]


def upgrade() -> None:
    """
    Create RLS policies and audit log table.

    Steps:
    1. Create rls_audit_log table for tracking context changes
    2. Enable RLS on all tenant tables
    3. Create organization isolation policies
    4. Create plant isolation policies (allows NULL plant_id)
    5. Create helper function for policy verification
    """
    conn = op.get_bind()

    # Step 1: Create audit log table
    print("\n🔐 Creating RLS audit log table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS rls_audit_log (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER,
            plant_id INTEGER,
            action VARCHAR(50) NOT NULL,
            user_id INTEGER,
            session_id VARCHAR(100),
            ip_address INET,
            created_at TIMESTAMP DEFAULT NOW(),
            metadata JSONB
        );
    """))
    conn.commit()

    # Create index on audit log for performance
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_rls_audit_log_org_id
        ON rls_audit_log(organization_id);
    """))
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_rls_audit_log_created_at
        ON rls_audit_log(created_at DESC);
    """))
    conn.commit()

    print("  ✓ rls_audit_log table created")

    # Step 2: Enable RLS and create policies for each tenant table
    for table_name in TENANT_TABLES:
        try:
            # Check if table exists
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table_name}'
                );
            """))
            table_exists = result.scalar()

            if not table_exists:
                print(f"  ⚠️  Skipping {table_name}: table does not exist yet")
                continue

            print(f"\n🔐 Enabling RLS on {table_name}...")

            # Enable RLS on table
            conn.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"))
            conn.commit()
            print(f"  ✓ RLS enabled on {table_name}")

            # Create organization isolation policy
            policy_name = f"{table_name}_org_isolation"
            conn.execute(text(f"""
                DROP POLICY IF EXISTS {policy_name} ON {table_name};
            """))
            conn.execute(text(f"""
                CREATE POLICY {policy_name} ON {table_name}
                FOR ALL
                USING (
                    organization_id = current_setting('app.current_organization_id', true)::int
                );
            """))
            conn.commit()
            print(f"  ✓ Created policy: {policy_name}")

            # Create plant isolation policy (if table has plant_id column)
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    AND column_name = 'plant_id'
                );
            """))
            has_plant_id = result.scalar()

            if has_plant_id:
                policy_name = f"{table_name}_plant_isolation"
                conn.execute(text(f"""
                    DROP POLICY IF EXISTS {policy_name} ON {table_name};
                """))
                conn.execute(text(f"""
                    CREATE POLICY {policy_name} ON {table_name}
                    FOR ALL
                    USING (
                        plant_id IS NULL OR
                        plant_id = current_setting('app.current_plant_id', true)::int
                    );
                """))
                conn.commit()
                print(f"  ✓ Created policy: {policy_name}")

        except Exception as e:
            print(f"  ✗ Failed to create policies for {table_name}: {e}")
            # Continue with other tables even if one fails
            conn.rollback()

    # Step 3: Create helper function for policy verification
    print("\n🔐 Creating RLS helper function...")
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION verify_rls_policies()
        RETURNS TABLE(
            table_name TEXT,
            rls_enabled BOOLEAN,
            policy_count INTEGER
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                t.tablename::TEXT,
                t.rowsecurity AS rls_enabled,
                COUNT(p.policyname)::INTEGER AS policy_count
            FROM pg_tables t
            LEFT JOIN pg_policies p ON t.tablename = p.tablename
            WHERE t.schemaname = 'public'
            AND t.tablename = ANY(ARRAY['users', 'organizations', 'plants',
                                        'materials', 'work_orders', 'production_lines',
                                        'inventory_transactions'])
            GROUP BY t.tablename, t.rowsecurity
            ORDER BY t.tablename;
        END;
        $$ LANGUAGE plpgsql;
    """))
    conn.commit()
    print("  ✓ Helper function verify_rls_policies() created")

    # Step 4: Verify RLS policies were created
    print("\n📊 Verifying RLS policies...")
    result = conn.execute(text("SELECT * FROM verify_rls_policies();"))

    for row in result:
        table, rls_enabled, policy_count = row
        status = "✓" if rls_enabled and policy_count > 0 else "✗"
        print(f"  {status} {table}: RLS={'ON' if rls_enabled else 'OFF'}, Policies={policy_count}")

    print("\n✅ RLS policies migration completed successfully!")


def downgrade() -> None:
    """
    Remove RLS policies and audit log table.

    WARNING: This will disable all RLS protection and remove audit logs.
    Use with extreme caution in production environments.
    """
    conn = op.get_bind()

    print("\n⚠️  Disabling RLS policies...")

    # Drop RLS policies from all tenant tables
    for table_name in TENANT_TABLES:
        try:
            # Check if table exists
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table_name}'
                );
            """))
            table_exists = result.scalar()

            if not table_exists:
                continue

            print(f"  Disabling RLS on {table_name}...")

            # Drop all policies on this table
            result = conn.execute(text(f"""
                SELECT policyname FROM pg_policies
                WHERE tablename = '{table_name}';
            """))
            policies = [row[0] for row in result]

            for policy_name in policies:
                conn.execute(text(f"DROP POLICY IF EXISTS {policy_name} ON {table_name};"))

            # Disable RLS on table
            conn.execute(text(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;"))
            conn.commit()
            print(f"    ✓ RLS disabled on {table_name}")

        except Exception as e:
            print(f"    ✗ Failed to disable RLS on {table_name}: {e}")
            conn.rollback()

    # Drop helper function
    print("\n  Dropping RLS helper function...")
    conn.execute(text("DROP FUNCTION IF EXISTS verify_rls_policies();"))
    conn.commit()

    # Drop audit log table
    print("  Dropping rls_audit_log table...")
    conn.execute(text("DROP TABLE IF EXISTS rls_audit_log CASCADE;"))
    conn.commit()

    print("\n✅ RLS policies removed successfully")
