#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User Organization Data Migration Script

This script migrates existing users to the multi-tenant model by assigning
organization_id to all users that currently have NULL values.

IMPORTANT: Run this AFTER the RLS migration (ef6ec56e007e) has been applied.
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


def get_default_organization(conn):
    """Get or create default organization for migration"""
    cur = conn.cursor()

    # Check if default organization exists
    cur.execute("SELECT id, org_code FROM organizations ORDER BY id LIMIT 1;")
    result = cur.fetchone()

    if result:
        org_id, org_code = result
        print("Found existing organization: ID=%d, Code=%s" % (org_id, org_code))
        cur.close()
        return org_id
    else:
        print("No organizations found in database")
        print("Please create at least one organization before running this migration")
        cur.close()
        return None


def migrate_users(conn, default_org_id):
    """Migrate users without organization_id to default organization"""
    cur = conn.cursor()

    # Count users needing migration
    cur.execute("SELECT COUNT(*) FROM users WHERE organization_id IS NULL;")
    count = cur.fetchone()[0]

    if count == 0:
        print("No users require migration (all have organization_id)")
        cur.close()
        return True

    print("\nFound %d users without organization_id" % count)
    print("Assigning them to organization ID: %d" % default_org_id)

    # Get list of affected users
    cur.execute("""
        SELECT id, username, email
        FROM users
        WHERE organization_id IS NULL
        LIMIT 10;
    """)
    sample_users = cur.fetchall()

    print("\nSample users to be migrated:")
    for user_id, username, email in sample_users:
        print("  - User ID: %d, Username: %s, Email: %s" % (user_id, username, email))

    if count > 10:
        print("  ... and %d more users" % (count - 10))

    # Confirm migration
    print("\nThis will UPDATE %d user records" % count)
    response = input("Continue with migration? (yes/no): ")

    if response.lower() != 'yes':
        print("Migration cancelled")
        cur.close()
        return False

    # Perform migration
    print("\nMigrating users...")
    cur.execute("""
        UPDATE users
        SET organization_id = %s
        WHERE organization_id IS NULL;
    """, (default_org_id,))

    rows_updated = cur.rowcount
    print("Successfully updated %d users" % rows_updated)

    cur.close()
    return True


def verify_migration(conn):
    """Verify that all users now have organization_id"""
    cur = conn.cursor()

    # Count users with NULL organization_id
    cur.execute("SELECT COUNT(*) FROM users WHERE organization_id IS NULL;")
    null_count = cur.fetchone()[0]

    # Get organization distribution
    cur.execute("""
        SELECT organization_id, COUNT(*) as user_count
        FROM users
        WHERE organization_id IS NOT NULL
        GROUP BY organization_id
        ORDER BY organization_id;
    """)
    distribution = cur.fetchall()

    print("\nMigration Verification:")
    print("  Users with NULL organization_id: %d" % null_count)
    print("\nUser distribution by organization:")
    for org_id, user_count in distribution:
        print("  Organization ID %d: %d users" % (org_id, user_count))

    success = null_count == 0

    if success:
        print("\nVERIFICATION PASSED: All users have organization_id")
    else:
        print("\nVERIFICATION FAILED: Some users still have NULL organization_id")

    cur.close()
    return success


def make_organization_id_required(conn):
    """Make organization_id NOT NULL after successful migration"""
    cur = conn.cursor()

    print("\nOptional: Make organization_id column NOT NULL")
    print("This prevents future users from being created without an organization")
    response = input("Apply NOT NULL constraint? (yes/no): ")

    if response.lower() != 'yes':
        print("Skipping NOT NULL constraint")
        cur.close()
        return True

    print("Applying NOT NULL constraint to users.organization_id...")
    cur.execute("ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;")
    print("Constraint applied successfully")

    cur.close()
    return True


def main():
    """Run user organization migration"""
    print("="*80)
    print("USER ORGANIZATION DATA MIGRATION")
    print("="*80)
    print("\nThis script migrates existing users to the multi-tenant model")
    print("by assigning organization_id to users with NULL values.\n")

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        # Step 1: Get default organization
        print("Step 1: Identifying default organization...")
        default_org_id = get_default_organization(conn)

        if not default_org_id:
            print("\nERROR: No organizations available for migration")
            print("Create an organization first, then re-run this script")
            return

        # Step 2: Migrate users
        print("\nStep 2: Migrating users to organization...")
        if not migrate_users(conn, default_org_id):
            print("\nMigration cancelled by user")
            return

        # Step 3: Verify migration
        print("\nStep 3: Verifying migration...")
        if not verify_migration(conn):
            print("\nWARNING: Migration verification failed")
            return

        # Step 4: Optional - make organization_id required
        print("\nStep 4: Applying constraints...")
        make_organization_id_required(conn)

        print("\n" + "="*80)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nNext steps:")
        print("  1. Verify application authentication includes organization_id")
        print("  2. Test RLS policies with actual user sessions")
        print("  3. Update JWT tokens to include org_id claim")
        print("  4. Deploy to staging for integration testing")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
