#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix migration state and clean up database for fresh RLS migration
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database configuration
DB_CONFIG = {
    'dbname': 'unison_erp',
    'user': 'unison',
    'password': 'unison_dev_password',
    'host': 'localhost',
    'port': '5432'
}

def main():
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    print("Fixing migration state...")
    print("")

    # 1. Update alembic version to correct state (before RLS migration)
    print("1. Setting alembic version to 59a3603c568e (lanes migration)...")
    cur.execute("DELETE FROM alembic_version;")
    cur.execute("INSERT INTO alembic_version (version_num) VALUES ('59a3603c568e');")
    print("   Alembic version updated")
    print("")

    # 2. Check which tables exist
    print("2. Checking existing tables...")
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cur.fetchall()]
    print("   Found %d tables:" % len(tables))
    for table in tables:
        print("   - " + table)
    print("")

    # 3. Check for tables with organization_id column
    print("3. Checking tables with organization_id column...")
    tables_with_org_id = []
    for table in tables:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                AND column_name = 'organization_id'
            );
        """, (table,))
        has_org_id = cur.fetchone()[0]
        if has_org_id:
            tables_with_org_id.append(table)

    print("   Found %d tables with organization_id:" % len(tables_with_org_id))
    for table in tables_with_org_id:
        print("   - " + table)
    print("")

    # 4. Check for tables with plant_id column
    print("4. Checking tables with plant_id column...")
    tables_with_plant_id = []
    for table in tables:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                AND column_name = 'plant_id'
            );
        """, (table,))
        has_plant_id = cur.fetchone()[0]
        if has_plant_id:
            tables_with_plant_id.append(table)

    print("   Found %d tables with plant_id:" % len(tables_with_plant_id))
    for table in tables_with_plant_id:
        print("   - " + table)
    print("")

    # 5. Remove any partial RLS policies that might exist
    print("5. Removing any existing RLS policies...")
    cur.execute("""
        SELECT tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public';
    """)
    policies = cur.fetchall()

    if policies:
        print("   Found %d existing policies:" % len(policies))
        for table, policy in policies:
            print("   Dropping %s.%s..." % (table, policy))
            cur.execute("DROP POLICY IF EXISTS %s ON %s;" % (policy, table))
        print("   All existing policies removed")
        print("")
    else:
        print("   No existing policies found")
        print("")

    # 6. Disable RLS on all tables
    print("6. Disabling RLS on all tables...")
    for table in tables:
        cur.execute("ALTER TABLE %s DISABLE ROW LEVEL SECURITY;" % table)
    print("   RLS disabled on %d tables" % len(tables))
    print("")

    # 7. Remove organization_id and plant_id from users if they exist
    print("7. Checking users table for tenant fields...")
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'users'
        AND column_name IN ('organization_id', 'plant_id');
    """)
    user_tenant_cols = [row[0] for row in cur.fetchall()]

    if user_tenant_cols:
        print("   Found tenant columns in users table: " + str(user_tenant_cols))
        print("   Removing them...")

        # Drop indexes first
        cur.execute("DROP INDEX IF EXISTS idx_users_organization_id;")
        cur.execute("DROP INDEX IF EXISTS idx_users_plant_id;")

        # Drop foreign keys
        try:
            cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_organization_id;")
        except:
            pass
        try:
            cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_plant_id;")
        except:
            pass

        # Drop columns
        if 'organization_id' in user_tenant_cols:
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS organization_id;")
        if 'plant_id' in user_tenant_cols:
            cur.execute("ALTER TABLE users DROP COLUMN IF EXISTS plant_id;")

        print("   Tenant fields removed from users table")
        print("")
    else:
        print("   No tenant fields found in users table")
        print("")

    print("Migration state fixed successfully!")
    print("Database is now at migration 59a3603c568e (lanes)")
    print("Ready for new RLS migration")
    print("")
    print("Tables ready for RLS (%d with organization_id):" % len(tables_with_org_id))
    for table in sorted(tables_with_org_id):
        has_plant = " + plant_id" if table in tables_with_plant_id else ""
        print("  - " + table + has_plant)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
