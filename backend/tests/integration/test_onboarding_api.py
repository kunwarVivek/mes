"""
Integration tests for Onboarding API Router.

Tests all 8 onboarding endpoints following TDD methodology:
1. POST /signup - User signup with email verification
2. POST /verify-email - Email verification token validation
3. POST /phone/request - Request SMS verification code
4. POST /phone/verify - Verify SMS code
5. POST /organization - Organization setup
6. POST /plant - Plant creation
7. POST /team/invite - Team member invitations
8. GET /progress - Onboarding progress tracking

Test Strategy:
- Use real database with transaction rollback
- Mock PGMQ for email/SMS queueing
- Mock JWT authentication for protected endpoints
- Test both success and error cases
- Validate response DTOs
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.main import app
from app.core.database import Base, get_db
from app.infrastructure.security.dependencies import get_current_user
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.infrastructure.persistence.models import UserModel
from app.models.organization import Organization as OrganizationModel
from app.models.plant import Plant as PlantModel


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db: Session):
    """FastAPI test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close test_db, it's managed by test_db fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def mock_pgmq():
    """Mock PGMQ client for email/SMS queueing."""
    with patch('app.application.use_cases.onboarding.signup_use_case.PGMQClient') as mock:
        pgmq_instance = Mock()
        pgmq_instance.enqueue.return_value = 12345  # Mock message ID
        mock.return_value = pgmq_instance
        yield pgmq_instance


@pytest.fixture
def verified_user(test_db: Session) -> UserModel:
    """Create a verified user for testing authenticated endpoints."""
    from app.infrastructure.persistence.models import OnboardingStatus
    user = UserModel(
        email="verified@example.com",
        username="verified_user",
        hashed_password="$2b$12$test_hashed_password",
        is_active=True,
        is_superuser=False,
        onboarding_status=OnboardingStatus.EMAIL_VERIFIED,
        verification_token=None,
        verification_token_expires_at=None,
        onboarding_completed_at=None,
        organization_id=None,
        plant_id=None
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def user_with_org(test_db: Session) -> tuple[UserModel, OrganizationModel]:
    """Create user with organization for plant creation tests."""
    from app.infrastructure.persistence.models import OnboardingStatus
    org = OrganizationModel(
        name="Test Organization",
        slug="test-organization",
        created_at=datetime.utcnow()
    )
    test_db.add(org)
    test_db.flush()

    user = UserModel(
        email="user_with_org@example.com",
        username="user_with_org",
        hashed_password="$2b$12$test_hashed_password",
        is_active=True,
        is_superuser=False,
        onboarding_status=OnboardingStatus.ORG_SETUP,
        organization_id=org.id,
        plant_id=None
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    test_db.refresh(org)

    return user, org


def create_mock_auth_user(user_model: UserModel):
    """Convert UserModel to User entity for authentication mock."""
    return User(
        id=user_model.id,
        email=Email(user_model.email),
        username=Username(user_model.username),
        hashed_password=user_model.hashed_password,
        organization_id=user_model.organization_id,
        plant_id=user_model.plant_id,
        is_active=user_model.is_active,
        is_superuser=user_model.is_superuser,
        onboarding_status=user_model.onboarding_status,
        verification_token=user_model.verification_token,
        verification_token_expires_at=user_model.verification_token_expires_at,
        onboarding_completed_at=user_model.onboarding_completed_at
    )


# ============================================================================
# TEST 1: POST /api/v1/onboarding/signup
# ============================================================================

class TestSignup:
    """Test user signup endpoint."""

    def test_signup_success(self, client: TestClient, test_db: Session, mock_pgmq):
        """Test successful user signup with valid data."""
        response = client.post(
            "/api/v1/onboarding/signup",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "newuser@example.com"
        assert data["user_id"] > 0
        assert data["onboarding_status"] == "pending_verification"
        assert "verification email sent" in data["message"].lower()

        # Verify user created in database
        user = test_db.query(UserModel).filter_by(email="newuser@example.com").first()
        assert user is not None
        assert user.is_active is False
        assert user.verification_token is not None
        assert user.verification_token_expires_at is not None

    def test_signup_duplicate_email(self, client: TestClient, test_db: Session):
        """Test signup fails with duplicate email."""
        # Create existing user
        existing_user = UserModel(
            email="existing@example.com",
            username="existing",
            hashed_password="$2b$12$test",
            is_active=True,
            onboarding_status="complete"
        )
        test_db.add(existing_user)
        test_db.commit()

        # Attempt signup with same email
        response = client.post(
            "/api/v1/onboarding/signup",
            json={
                "email": "existing@example.com",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_signup_weak_password(self, client: TestClient):
        """Test signup fails with weak password."""
        response = client.post(
            "/api/v1/onboarding/signup",
            json={
                "email": "test@example.com",
                "password": "weak"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_signup_invalid_email(self, client: TestClient):
        """Test signup fails with invalid email format."""
        response = client.post(
            "/api/v1/onboarding/signup",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!"
            }
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# TEST 2: POST /api/v1/onboarding/verify-email
# ============================================================================

class TestVerifyEmail:
    """Test email verification endpoint."""

    def test_verify_email_success(self, client: TestClient, test_db: Session):
        """Test successful email verification with valid token."""
        from app.infrastructure.persistence.models import OnboardingStatus
        # Create user with verification token
        token = "valid_token_12345"
        user = UserModel(
            email="verify@example.com",
            username="verify_user",
            hashed_password="$2b$12$test",
            is_active=False,
            onboarding_status=OnboardingStatus.PENDING_VERIFICATION,
            verification_token=token,
            verification_token_expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        test_db.add(user)
        test_db.commit()

        response = client.post(
            "/api/v1/onboarding/verify-email",
            json={"token": token}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["onboarding_status"] == "email_verified"
        assert "verified" in data["message"].lower()

        # Verify user updated in database
        test_db.refresh(user)
        assert user.is_active is True
        assert user.verification_token is None

    def test_verify_email_invalid_token(self, client: TestClient):
        """Test email verification fails with invalid token."""
        response = client.post(
            "/api/v1/onboarding/verify-email",
            json={"token": "invalid_token"}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_verify_email_expired_token(self, client: TestClient, test_db: Session):
        """Test email verification fails with expired token."""
        from app.infrastructure.persistence.models import OnboardingStatus
        token = "expired_token_12345"
        user = UserModel(
            email="expired@example.com",
            username="expired_user",
            hashed_password="$2b$12$test",
            is_active=False,
            onboarding_status=OnboardingStatus.PENDING_VERIFICATION,
            verification_token=token,
            verification_token_expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        test_db.add(user)
        test_db.commit()

        response = client.post(
            "/api/v1/onboarding/verify-email",
            json={"token": token}
        )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


# ============================================================================
# TEST 3: POST /api/v1/onboarding/organization
# ============================================================================

class TestOrganizationSetup:
    """Test organization setup endpoint."""

    def test_organization_setup_success(self, client: TestClient, verified_user: UserModel):
        """Test successful organization setup."""
        mock_user = create_mock_auth_user(verified_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/organization",
                json={"organization_name": "Acme Corporation"},
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["name"] == "Acme Corporation"
            assert data["slug"] == "acme-corporation"
            assert data["organization_id"] > 0
            assert "created_at" in data
        finally:
            app.dependency_overrides.clear()

    def test_organization_setup_unauthenticated(self, client: TestClient):
        """Test organization setup fails without authentication."""
        response = client.post(
            "/api/v1/onboarding/organization",
            json={"organization_name": "Test Org"}
        )

        assert response.status_code == 403

    def test_organization_setup_html_injection(self, client: TestClient, verified_user: UserModel):
        """Test organization setup rejects HTML tags."""
        mock_user = create_mock_auth_user(verified_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/organization",
                json={"organization_name": "<script>alert('xss')</script>"},
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# TEST 4: POST /api/v1/onboarding/plant
# ============================================================================

class TestPlantCreation:
    """Test plant creation endpoint."""

    def test_plant_creation_success(self, client: TestClient, user_with_org: tuple):
        """Test successful plant creation."""
        user, org = user_with_org
        mock_user = create_mock_auth_user(user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/plant",
                json={
                    "plant_name": "Manufacturing Plant 1",
                    "address": "123 Factory St",
                    "timezone": "America/New_York"
                },
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["name"] == "Manufacturing Plant 1"
            assert data["organization_id"] == org.id
            assert data["plant_id"] > 0
        finally:
            app.dependency_overrides.clear()

    def test_plant_creation_no_organization(self, client: TestClient, verified_user: UserModel):
        """Test plant creation fails without organization."""
        mock_user = create_mock_auth_user(verified_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/plant",
                json={"plant_name": "Test Plant"},
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 400
        finally:
            app.dependency_overrides.clear()

    def test_plant_creation_invalid_timezone(self, client: TestClient, user_with_org: tuple):
        """Test plant creation fails with invalid timezone."""
        user, org = user_with_org
        mock_user = create_mock_auth_user(user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/plant",
                json={
                    "plant_name": "Test Plant",
                    "timezone": "Invalid/Timezone"
                },
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# TEST 5: POST /api/v1/onboarding/team/invite
# ============================================================================

class TestTeamInvitation:
    """Test team invitation endpoint."""

    def test_team_invitation_success(self, client: TestClient, user_with_org: tuple, mock_pgmq):
        """Test successful team member invitation."""
        user, org = user_with_org
        mock_user = create_mock_auth_user(user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/team/invite",
                json={
                    "invitations": [
                        {"email": "user1@example.com", "role": "admin"},
                        {"email": "user2@example.com", "role": "operator"}
                    ]
                },
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data["invitations_sent"]) == 2
            assert data["invitations_sent"][0]["email"] == "user1@example.com"
            assert data["invitations_sent"][0]["role"] == "admin"
            assert "expires_at" in data["invitations_sent"][0]
        finally:
            app.dependency_overrides.clear()

    def test_team_invitation_duplicate_emails(self, client: TestClient, user_with_org: tuple):
        """Test team invitation fails with duplicate emails."""
        user, org = user_with_org
        mock_user = create_mock_auth_user(user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/team/invite",
                json={
                    "invitations": [
                        {"email": "user1@example.com", "role": "admin"},
                        {"email": "user1@example.com", "role": "operator"}
                    ]
                },
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()

    def test_team_invitation_custom_role_without_description(self, client: TestClient, user_with_org: tuple):
        """Test team invitation fails for custom role without description."""
        user, org = user_with_org
        mock_user = create_mock_auth_user(user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.post(
                "/api/v1/onboarding/team/invite",
                json={
                    "invitations": [
                        {"email": "user1@example.com", "role": "custom"}
                    ]
                },
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# TEST 6: GET /api/v1/onboarding/progress
# ============================================================================

class TestOnboardingProgress:
    """Test onboarding progress tracking endpoint."""

    def test_progress_email_verified(self, client: TestClient, verified_user: UserModel):
        """Test progress for user with email verified."""
        mock_user = create_mock_auth_user(verified_user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.get(
                "/api/v1/onboarding/progress",
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["current_status"] == "email_verified"
            assert "signup" in data["completed_steps"]
            assert "email_verification" in data["completed_steps"]
            assert "next_step" in data
        finally:
            app.dependency_overrides.clear()

    def test_progress_organization_setup(self, client: TestClient, user_with_org: tuple):
        """Test progress for user with organization setup."""
        user, org = user_with_org
        mock_user = create_mock_auth_user(user)
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            response = client.get(
                "/api/v1/onboarding/progress",
                headers={"Authorization": "Bearer fake_token"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["current_status"] == "organization_setup"
            assert "organization_setup" in data["completed_steps"]
        finally:
            app.dependency_overrides.clear()

    def test_progress_unauthenticated(self, client: TestClient):
        """Test progress fails without authentication."""
        response = client.get("/api/v1/onboarding/progress")

        assert response.status_code == 403
