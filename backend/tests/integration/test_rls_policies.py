"""
Integration tests for RLS (Row-Level Security) policies.

Tests the actual database RLS policies with real database connections.
Requires migration 002_create_rls_policies to be run.
"""
import pytest
from sqlalchemy import text, create_engine, Table, MetaData, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.infrastructure.database.rls import set_rls_context, get_current_org_id, get_current_plant_id


@pytest.fixture(scope="module")
def db_engine():
    """Create a database engine for testing."""
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a clean database session for each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def setup_test_tables(db_engine):
    """
    Create test tables with RLS policies for integration testing.

    Creates a minimal test_users table to verify RLS behavior.
    """
    with db_engine.connect() as conn:
        # Create test table with organization_id and plant_id
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_rls_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                organization_id INTEGER NOT NULL,
                plant_id INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        conn.commit()

        # Enable RLS on test table
        conn.execute(text("ALTER TABLE test_rls_users ENABLE ROW LEVEL SECURITY;"))
        conn.commit()

        # Create organization isolation policy
        conn.execute(text("""
            CREATE POLICY IF NOT EXISTS test_rls_users_org_isolation
            ON test_rls_users
            USING (organization_id = current_setting('app.current_organization_id')::int);
        """))
        conn.commit()

        # Create plant isolation policy (optional plant_id)
        conn.execute(text("""
            CREATE POLICY IF NOT EXISTS test_rls_users_plant_isolation
            ON test_rls_users
            USING (plant_id IS NULL OR plant_id = current_setting('app.current_plant_id')::int);
        """))
        conn.commit()

        # Insert test data
        conn.execute(text("""
            INSERT INTO test_rls_users (username, organization_id, plant_id)
            VALUES
                ('org1_plant10_user', 1, 10),
                ('org1_plant20_user', 1, 20),
                ('org1_no_plant_user', 1, NULL),
                ('org2_plant10_user', 2, 10),
                ('org2_plant30_user', 2, 30),
                ('org3_user', 3, NULL);
        """))
        conn.commit()

    yield

    # Cleanup after all tests
    with db_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS test_rls_users CASCADE;"))
        conn.commit()


class TestRLSPoliciesIntegration:
    """Integration tests for RLS policies with real database."""

    @pytest.mark.skipif(
        True,
        reason="Requires running migration: alembic upgrade head (002_create_rls_policies)"
    )
    def test_migration_script_exists(self):
        """Test that the RLS migration script exists."""
        import os
        migration_file = "/Users/vivek/jet/unison/database/migrations/versions/002_create_rls_policies.py"
        assert os.path.exists(migration_file), "RLS migration script not found"

    @pytest.mark.skipif(
        True,
        reason="Requires running migration: alembic upgrade head (002_create_rls_policies)"
    )
    def test_rls_audit_log_table_exists(self, db_session):
        """Test that rls_audit_log table exists after migration."""
        result = db_session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'rls_audit_log'
            );
        """))
        exists = result.scalar()
        assert exists is True, "rls_audit_log table should exist after migration"

    def test_set_and_get_rls_context(self, db_session, setup_test_tables):
        """Test setting and retrieving RLS context variables."""
        # Set RLS context
        set_rls_context(db_session, organization_id=1, plant_id=10)

        # Verify context was set
        org_id = get_current_org_id(db_session)
        plant_id = get_current_plant_id(db_session)

        assert org_id == 1, f"Expected org_id=1, got {org_id}"
        assert plant_id == 10, f"Expected plant_id=10, got {plant_id}"

    def test_rls_filters_by_organization(self, db_session, setup_test_tables):
        """Test that RLS policies filter data by organization_id."""
        # Set context to organization 1
        set_rls_context(db_session, organization_id=1, plant_id=10)

        # Query all users (should only see org 1 users)
        result = db_session.execute(text("SELECT username FROM test_rls_users ORDER BY username;"))
        usernames = [row[0] for row in result]

        # Should only see users from organization 1
        assert 'org1_plant10_user' in usernames
        assert 'org1_plant20_user' in usernames
        assert 'org1_no_plant_user' in usernames

        # Should NOT see users from other organizations
        assert 'org2_plant10_user' not in usernames
        assert 'org2_plant30_user' not in usernames
        assert 'org3_user' not in usernames

    def test_rls_filters_by_plant(self, db_session, setup_test_tables):
        """Test that RLS policies filter data by plant_id."""
        # Set context to organization 1, plant 10
        set_rls_context(db_session, organization_id=1, plant_id=10)

        # Query all users
        result = db_session.execute(text("SELECT username FROM test_rls_users ORDER BY username;"))
        usernames = [row[0] for row in result]

        # Should see plant 10 user and NULL plant user
        assert 'org1_plant10_user' in usernames
        assert 'org1_no_plant_user' in usernames

        # Should NOT see plant 20 user (different plant in same org)
        assert 'org1_plant20_user' not in usernames

    def test_rls_cross_tenant_isolation(self, db_session, setup_test_tables):
        """Test that RLS prevents cross-tenant data access."""
        # Set context to organization 2, plant 10
        set_rls_context(db_session, organization_id=2, plant_id=10)

        # Query all users
        result = db_session.execute(text("SELECT username FROM test_rls_users ORDER BY username;"))
        usernames = [row[0] for row in result]

        # Should only see organization 2 users
        assert 'org2_plant10_user' in usernames

        # Should NOT see organization 1 users, even with same plant_id=10
        assert 'org1_plant10_user' not in usernames
        assert 'org1_plant20_user' not in usernames
        assert 'org1_no_plant_user' not in usernames

    def test_rls_context_switch(self, db_session, setup_test_tables):
        """Test switching RLS context within same session."""
        # Start with organization 1
        set_rls_context(db_session, organization_id=1, plant_id=10)
        result = db_session.execute(text("SELECT COUNT(*) FROM test_rls_users;"))
        count_org1 = result.scalar()

        # Switch to organization 2
        set_rls_context(db_session, organization_id=2, plant_id=30)
        result = db_session.execute(text("SELECT COUNT(*) FROM test_rls_users;"))
        count_org2 = result.scalar()

        # Counts should be different
        assert count_org1 != count_org2, "Different organizations should see different data"
        assert count_org1 >= 2, "Org 1 should have at least 2 users"
        assert count_org2 >= 1, "Org 2 should have at least 1 user"

    def test_rls_without_context_fails(self, db_session, setup_test_tables):
        """Test that querying without RLS context raises an error."""
        # Don't set any RLS context, just try to query
        # PostgreSQL should raise an error about missing configuration parameter

        with pytest.raises(Exception) as exc_info:
            result = db_session.execute(text("SELECT * FROM test_rls_users;"))
            result.fetchall()

        # Should fail due to missing context
        error_msg = str(exc_info.value).lower()
        assert "unrecognized configuration parameter" in error_msg or \
               "current_setting" in error_msg or \
               "app.current_organization_id" in error_msg

    def test_rls_null_plant_accessible_from_all_plants(self, db_session, setup_test_tables):
        """Test that records with plant_id=NULL are visible to all plants in same org."""
        # Set context to org 1, plant 10
        set_rls_context(db_session, organization_id=1, plant_id=10)
        result = db_session.execute(text("SELECT username FROM test_rls_users WHERE plant_id IS NULL;"))
        users_plant10 = [row[0] for row in result]

        # Switch to org 1, plant 20
        set_rls_context(db_session, organization_id=1, plant_id=20)
        result = db_session.execute(text("SELECT username FROM test_rls_users WHERE plant_id IS NULL;"))
        users_plant20 = [row[0] for row in result]

        # Both should see the NULL plant user
        assert 'org1_no_plant_user' in users_plant10
        assert 'org1_no_plant_user' in users_plant20

    @pytest.mark.skipif(
        not settings.RLS_AUDIT_LOG_ENABLED,
        reason="RLS audit logging is disabled in settings"
    )
    def test_rls_audit_log_records_context_changes(self, db_session, setup_test_tables):
        """Test that RLS context changes are logged when audit is enabled."""
        # Set RLS context
        set_rls_context(db_session, organization_id=1, plant_id=10)

        # Check audit log
        result = db_session.execute(text("""
            SELECT organization_id, plant_id, action
            FROM rls_audit_log
            WHERE organization_id = 1 AND plant_id = 10
            ORDER BY created_at DESC
            LIMIT 1;
        """))

        log_entry = result.fetchone()
        assert log_entry is not None, "Audit log should have an entry"
        assert log_entry[0] == 1  # organization_id
        assert log_entry[1] == 10  # plant_id
        assert log_entry[2] == 'SET_CONTEXT'  # action
