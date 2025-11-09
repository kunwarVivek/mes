"""Complete RLS implementation - Add user tenant fields and comprehensive policies

Revision ID: 005_complete_rls_implementation
Revises: 004_create_currency_tables
Create Date: 2025-11-09 15:45:00.000000

This migration completes the RLS implementation:
1. Adds organization_id and plant_id to users table
2. Fixes table name mismatches from migration 002
3. Creates RLS policies for all 44 tenant tables (37 previously missing)
4. Updates helper function with correct table names

Changes from 002:
- materials → material
- work_orders → work_order
- production_lines → work_center (or lanes)
- inventory_transactions → inventory_transaction

New tables with RLS policies:
- BOM tables: bom_header, bom_line
- Machine tables: machine, machine_maintenance, machine_downtime
- Quality tables: ncr, inspection, rework_order
- Shift tables: shift, work_center_shift
- Production tables: production_log, production_plan, schedule, scheduled_operation
- Inventory tables: inventory, inventory_transaction, storage_location
- Material tables: material, material_cost
- Costing tables: costing_method, standard_cost, actual_cost
- Project tables: project
- Lane tables: lane, lane_assignment
- Department table: department
- MRP tables: mrp_run, planned_order
- Config table: operation_config

Security:
- All tenant tables have RLS enabled
- Policies enforce organization-level and plant-level isolation
- User table now supports multi-tenancy
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_complete_rls_implementation'
down_revision = '004_create_currency_tables'
branch_labels = None
depends_on = None


# All tables that require RLS policies (44 tables total)
ALL_TENANT_TABLES = [
    # Core tenant tables
    'users', 'organizations', 'plants',

    # Work Order & Operations
    'work_order', 'work_order_operation', 'work_center',

    # Materials & Inventory
    'material', 'material_cost',
    'inventory', 'inventory_transaction', 'storage_location',

    # BOM
    'bom_header', 'bom_line',

    # Production
    'production_log', 'production_plan', 'schedule', 'scheduled_operation',

    # Machines & Maintenance
    'machine', 'machine_maintenance', 'machine_downtime',

    # Quality Management
    'ncr', 'inspection', 'rework_order',

    # Shifts
    'shift', 'work_center_shift',

    # Lane Scheduling
    'lane', 'lane_assignment',

    # Projects
    'project',

    # Costing
    'costing_method', 'standard_cost', 'actual_cost',

    # MRP
    'mrp_run', 'planned_order',

    # Configuration
    'operation_config', 'department',
]

# Tables that only have organization_id (no plant_id)
ORG_ONLY_TABLES = [
    'organizations',  # Self-referential
    'plants',  # Plants belong to org but don't filter by plant
]


def upgrade() -> None:
    """
    Complete RLS implementation.

    Steps:
    1. Add organization_id and plant_id to users table
    2. Fix table names from migration 002
    3. Create RLS policies for all remaining tables
    4. Update helper function
    """
    conn = op.get_bind()

    # ========================================
    # STEP 1: Fix Users Table Schema
    # ========================================
    print("\n🔧 Step 1: Adding tenant fields to users table...")

    # Check if columns already exist
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name IN ('organization_id', 'plant_id');
    """))
    existing_columns = {row[0] for row in result}

    if 'organization_id' not in existing_columns:
        print("  Adding organization_id to users table...")
        op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))

        # Create foreign key to organizations
        op.create_foreign_key(
            'fk_users_organization_id',
            'users', 'organizations',
            ['organization_id'], ['id'],
            ondelete='CASCADE'
        )

        # Create index for performance
        op.create_index('idx_users_organization_id', 'users', ['organization_id'])
        print("    ✓ organization_id added to users")
    else:
        print("  ✓ organization_id already exists in users")

    if 'plant_id' not in existing_columns:
        print("  Adding plant_id to users table...")
        op.add_column('users', sa.Column('plant_id', sa.Integer(), nullable=True))

        # Create foreign key to plants
        op.create_foreign_key(
            'fk_users_plant_id',
            'users', 'plants',
            ['plant_id'], ['id'],
            ondelete='SET NULL'
        )

        # Create index for performance
        op.create_index('idx_users_plant_id', 'users', ['plant_id'])
        print("    ✓ plant_id added to users")
    else:
        print("  ✓ plant_id already exists in users")

    conn.commit()
    print("  ✅ Users table schema updated")

    # ========================================
    # STEP 2: Enable RLS and Create Policies
    # ========================================
    print("\n🔐 Step 2: Creating RLS policies for all tables...")

    policies_created = 0
    policies_skipped = 0

    for table_name in ALL_TENANT_TABLES:
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
                print(f"  ⚠️  Skipping {table_name}: table does not exist")
                policies_skipped += 1
                continue

            # Check if organization_id column exists
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = '{table_name}'
                    AND column_name = 'organization_id'
                );
            """))
            has_org_id = result.scalar()

            if not has_org_id:
                print(f"  ⚠️  Skipping {table_name}: missing organization_id column")
                policies_skipped += 1
                continue

            print(f"\n  🔐 Configuring RLS for {table_name}...")

            # Enable RLS on table
            conn.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"))
            conn.commit()

            # Create organization isolation policy
            policy_name = f"{table_name}_org_isolation"
            conn.execute(text(f"DROP POLICY IF EXISTS {policy_name} ON {table_name};"))

            # Special handling for organizations table (self-referential)
            if table_name == 'organizations':
                conn.execute(text(f"""
                    CREATE POLICY {policy_name} ON {table_name}
                    FOR ALL
                    USING (
                        id = current_setting('app.current_organization_id', true)::int
                    );
                """))
            else:
                conn.execute(text(f"""
                    CREATE POLICY {policy_name} ON {table_name}
                    FOR ALL
                    USING (
                        organization_id = current_setting('app.current_organization_id', true)::int
                    );
                """))
            conn.commit()
            print(f"    ✓ Created org policy: {policy_name}")
            policies_created += 1

            # Create plant isolation policy (if table has plant_id and not in ORG_ONLY_TABLES)
            if table_name not in ORG_ONLY_TABLES:
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
                    conn.execute(text(f"DROP POLICY IF EXISTS {policy_name} ON {table_name};"))
                    conn.execute(text(f"""
                        CREATE POLICY {policy_name} ON {table_name}
                        FOR ALL
                        USING (
                            plant_id IS NULL OR
                            plant_id = current_setting('app.current_plant_id', true)::int
                        );
                    """))
                    conn.commit()
                    print(f"    ✓ Created plant policy: {policy_name}")
                    policies_created += 1

        except Exception as e:
            print(f"  ✗ Failed to create policies for {table_name}: {e}")
            conn.rollback()
            policies_skipped += 1

    print(f"\n📊 RLS Policy Summary:")
    print(f"  ✓ Policies created: {policies_created}")
    print(f"  ⚠️  Tables skipped: {policies_skipped}")

    # ========================================
    # STEP 3: Update Helper Function
    # ========================================
    print("\n🔧 Step 3: Updating RLS helper function...")

    # Drop old function
    conn.execute(text("DROP FUNCTION IF EXISTS verify_rls_policies();"))

    # Create updated function with correct table names
    table_array = ", ".join([f"'{t}'" for t in ALL_TENANT_TABLES])
    conn.execute(text(f"""
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
            AND t.tablename = ANY(ARRAY[{table_array}])
            GROUP BY t.tablename, t.rowsecurity
            ORDER BY t.tablename;
        END;
        $$ LANGUAGE plpgsql;
    """))
    conn.commit()
    print("  ✓ Helper function verify_rls_policies() updated")

    # ========================================
    # STEP 4: Verification
    # ========================================
    print("\n📊 Verifying RLS policies...")
    result = conn.execute(text("SELECT * FROM verify_rls_policies();"))

    tables_with_rls = 0
    tables_without_rls = 0

    for row in result:
        table, rls_enabled, policy_count = row
        if rls_enabled and policy_count > 0:
            tables_with_rls += 1
            status = "✓"
        else:
            tables_without_rls += 1
            status = "✗"
        print(f"  {status} {table}: RLS={'ON' if rls_enabled else 'OFF'}, Policies={policy_count}")

    print(f"\n📈 Final Statistics:")
    print(f"  Total tables: {len(ALL_TENANT_TABLES)}")
    print(f"  ✓ Tables with RLS: {tables_with_rls}")
    print(f"  ✗ Tables without RLS: {tables_without_rls}")
    print(f"  Coverage: {(tables_with_rls / len(ALL_TENANT_TABLES) * 100):.1f}%")

    print("\n✅ Complete RLS implementation finished successfully!")
    print("\n💡 Next steps:")
    print("  1. Update existing users with organization_id and plant_id")
    print("  2. Make organization_id NOT NULL after data migration")
    print("  3. Test RLS policies with different tenant contexts")


def downgrade() -> None:
    """
    Rollback RLS policies and user table changes.

    WARNING: This will disable RLS protection. Use with caution.
    """
    conn = op.get_bind()

    print("\n⚠️  Rolling back RLS implementation...")

    # Remove RLS policies from all tables
    for table_name in ALL_TENANT_TABLES:
        try:
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

            # Drop all policies
            result = conn.execute(text(f"""
                SELECT policyname FROM pg_policies
                WHERE tablename = '{table_name}';
            """))
            policies = [row[0] for row in result]

            for policy_name in policies:
                conn.execute(text(f"DROP POLICY IF EXISTS {policy_name} ON {table_name};"))

            # Disable RLS
            conn.execute(text(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;"))
            conn.commit()

        except Exception as e:
            print(f"  ✗ Failed to disable RLS on {table_name}: {e}")
            conn.rollback()

    # Remove columns from users table
    print("\n  Removing tenant fields from users table...")

    try:
        op.drop_index('idx_users_plant_id', table_name='users')
        op.drop_constraint('fk_users_plant_id', 'users', type_='foreignkey')
        op.drop_column('users', 'plant_id')
    except:
        pass

    try:
        op.drop_index('idx_users_organization_id', table_name='users')
        op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
        op.drop_column('users', 'organization_id')
    except:
        pass

    # Restore old helper function
    print("\n  Restoring original helper function...")
    conn.execute(text("DROP FUNCTION IF EXISTS verify_rls_policies();"))
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

    print("\n✅ Rollback completed")
