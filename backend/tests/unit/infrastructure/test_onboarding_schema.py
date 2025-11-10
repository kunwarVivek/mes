"""
Unit tests for onboarding database schema.
Tests verify presence of onboarding_status, verification_token, and pending_invitations table.
"""
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.core.database import engine


class TestUsersTableOnboardingFields:
    """Test users table has onboarding-related columns"""

    def test_users_table_has_onboarding_status_column(self):
        """Test that users table has onboarding_status column with ENUM type"""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('users')}

        assert 'onboarding_status' in columns, "users table missing onboarding_status column"

        # Verify it's NOT NULL with default
        col = columns['onboarding_status']
        assert col['nullable'] is False, "onboarding_status should be NOT NULL"
        assert col['default'] is not None, "onboarding_status should have default value"

    def test_users_table_has_verification_token_column(self):
        """Test that users table has verification_token column"""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('users')}

        assert 'verification_token' in columns, "users table missing verification_token column"

        # Verify it's nullable (not all users need verification)
        col = columns['verification_token']
        assert col['nullable'] is True, "verification_token should be nullable"

    def test_users_table_has_verification_token_expires_at_column(self):
        """Test that users table has verification_token_expires_at column"""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('users')}

        assert 'verification_token_expires_at' in columns, "users table missing verification_token_expires_at column"

        col = columns['verification_token_expires_at']
        assert col['nullable'] is True, "verification_token_expires_at should be nullable"

    def test_users_table_has_onboarding_completed_at_column(self):
        """Test that users table has onboarding_completed_at column"""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('users')}

        assert 'onboarding_completed_at' in columns, "users table missing onboarding_completed_at column"

        col = columns['onboarding_completed_at']
        assert col['nullable'] is True, "onboarding_completed_at should be nullable"

    def test_users_table_has_onboarding_status_index(self):
        """Test that users table has index on onboarding_status"""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('users')

        index_names = [idx['name'] for idx in indexes]
        assert 'idx_users_onboarding_status' in index_names, "Missing index on onboarding_status"


class TestPendingInvitationsTable:
    """Test pending_invitations table exists with correct structure"""

    def test_pending_invitations_table_exists(self):
        """Test that pending_invitations table exists"""
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert 'pending_invitations' in tables, "pending_invitations table does not exist"

    def test_pending_invitations_has_required_columns(self):
        """Test that pending_invitations table has all required columns"""
        inspector = inspect(engine)
        columns = {col['name']: col for col in inspector.get_columns('pending_invitations')}

        required_columns = [
            'id',
            'inviter_id',
            'organization_id',
            'plant_id',
            'email',
            'role',
            'token',
            'status',
            'expires_at',
            'created_at',
            'accepted_at'
        ]

        for col_name in required_columns:
            assert col_name in columns, f"pending_invitations missing column: {col_name}"

    def test_pending_invitations_has_foreign_keys(self):
        """Test that pending_invitations has correct foreign key constraints"""
        inspector = inspect(engine)
        foreign_keys = inspector.get_foreign_keys('pending_invitations')

        # Should have FKs to users, organizations, and plants
        fk_columns = [fk['constrained_columns'][0] for fk in foreign_keys]

        assert 'inviter_id' in fk_columns, "Missing FK for inviter_id"
        assert 'organization_id' in fk_columns, "Missing FK for organization_id"
        assert 'plant_id' in fk_columns, "Missing FK for plant_id"

    def test_pending_invitations_has_indexes(self):
        """Test that pending_invitations has performance indexes"""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('pending_invitations')

        index_names = [idx['name'] for idx in indexes]

        assert 'idx_pending_invitations_email' in index_names, "Missing index on email"
        assert 'idx_pending_invitations_token' in index_names, "Missing index on token"
        assert 'idx_pending_invitations_status' in index_names, "Missing index on status"

    def test_pending_invitations_token_is_unique(self):
        """Test that token column has unique constraint"""
        inspector = inspect(engine)
        unique_constraints = inspector.get_unique_constraints('pending_invitations')
        indexes = inspector.get_indexes('pending_invitations')

        # Token uniqueness can be enforced via unique constraint or unique index
        unique_columns = []
        for constraint in unique_constraints:
            unique_columns.extend(constraint['column_names'])

        for index in indexes:
            if index.get('unique'):
                unique_columns.extend(index['column_names'])

        assert 'token' in unique_columns, "token column should have unique constraint"


class TestOnboardingSchemaIntegration:
    """Integration tests to verify schema works end-to-end"""

    def test_can_insert_user_with_onboarding_status(self):
        """Test that we can insert a user with onboarding_status"""
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            # Insert test user with onboarding status
            result = db.execute(text("""
                INSERT INTO users (email, username, hashed_password, onboarding_status, is_active, is_superuser)
                VALUES (:email, :username, :password, :status, :active, :superuser)
                RETURNING id, onboarding_status
            """), {
                'email': f'test_onboarding_{pytest.__version__}@example.com',
                'username': f'test_user_{pytest.__version__}',
                'password': 'hashed_password_here',
                'status': 'pending_verification',
                'active': True,
                'superuser': False
            })

            row = result.fetchone()
            assert row is not None, "Failed to insert user"
            assert row[1] == 'pending_verification', "onboarding_status not set correctly"

            # Cleanup
            db.execute(text("DELETE FROM users WHERE id = :id"), {'id': row[0]})
            db.commit()
        finally:
            db.close()

    def test_can_insert_pending_invitation(self):
        """Test that we can insert a pending invitation"""
        from app.core.database import SessionLocal
        from datetime import datetime, timedelta

        db = SessionLocal()
        try:
            # Get a test organization and user
            org_result = db.execute(text("SELECT id FROM organizations LIMIT 1"))
            org_row = org_result.fetchone()

            if org_row is None:
                pytest.skip("No organizations in database for test")

            user_result = db.execute(text("SELECT id FROM users LIMIT 1"))
            user_row = user_result.fetchone()

            if user_row is None:
                pytest.skip("No users in database for test")

            org_id = org_row[0]
            user_id = user_row[0]

            # Insert test invitation
            expires_at = datetime.utcnow() + timedelta(days=7)
            result = db.execute(text("""
                INSERT INTO pending_invitations
                (inviter_id, organization_id, email, role, token, status, expires_at)
                VALUES (:inviter_id, :org_id, :email, :role, :token, :status, :expires_at)
                RETURNING id, email, status
            """), {
                'inviter_id': user_id,
                'org_id': org_id,
                'email': f'test_invite_{pytest.__version__}@example.com',
                'role': 'operator',
                'token': f'test_token_{pytest.__version__}',
                'status': 'email_queued',
                'expires_at': expires_at
            })

            row = result.fetchone()
            assert row is not None, "Failed to insert pending invitation"
            assert row[2] == 'email_queued', "status not set correctly"

            # Cleanup
            db.execute(text("DELETE FROM pending_invitations WHERE id = :id"), {'id': row[0]})
            db.commit()
        finally:
            db.close()
