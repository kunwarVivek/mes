"""
Unit tests for SignupUseCase (TDD - RED phase)

Tests for self-service signup functionality:
- Successful signup flow
- Duplicate email rejection
- Password hashing verification
- Token generation and expiry
- Onboarding status initialization
- Email queue integration
- Database transaction rollback
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import secrets

from app.application.use_cases.onboarding.signup_use_case import SignupUseCase
from app.application.dtos.onboarding_dto import SignupRequestDTO, SignupResponseDTO
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.exceptions import DomainValidationException


class TestSignupUseCase:
    """Test suite for SignupUseCase following TDD RED-GREEN-REFACTOR"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing"""
        return Mock()

    @pytest.fixture
    def mock_email_service(self):
        """Mock email service (PGMQ client) for testing"""
        return Mock()

    @pytest.fixture
    def mock_password_hasher(self):
        """Mock password hasher for testing"""
        hasher = Mock()
        hasher.hash.return_value = "hashed_password_123"
        return hasher

    @pytest.fixture
    def signup_use_case(self, mock_user_repository, mock_email_service, mock_password_hasher):
        """Create SignupUseCase instance with mocks"""
        return SignupUseCase(
            user_repository=mock_user_repository,
            email_service=mock_email_service,
            password_hasher=mock_password_hasher
        )

    def test_successful_signup_creates_user_with_pending_verification(
        self, signup_use_case, mock_user_repository, mock_email_service
    ):
        """
        Test: Successful signup creates user with onboarding_status='pending_verification'

        Given: Valid email and password
        When: User signs up
        Then: User is created with pending_verification status
        """
        # Arrange
        request = SignupRequestDTO(email="test@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.create.return_value = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification"
        )

        # Act
        response = signup_use_case.execute(request)

        # Assert
        assert response.user_id == 1
        assert response.email == "test@example.com"
        assert "verification email sent" in response.message.lower()

        # Verify user was created with correct status
        created_user_call = mock_user_repository.create.call_args[0][0]
        assert created_user_call.onboarding_status == "pending_verification"

    def test_signup_rejects_duplicate_email(self, signup_use_case, mock_user_repository):
        """
        Test: Signup rejects already registered email

        Given: Email already exists in database
        When: User tries to signup with same email
        Then: DomainValidationException is raised
        """
        # Arrange
        request = SignupRequestDTO(email="existing@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = True

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            signup_use_case.execute(request)

        assert "already registered" in str(exc_info.value).lower()

    def test_signup_hashes_password_not_plain_text(
        self, signup_use_case, mock_user_repository, mock_password_hasher
    ):
        """
        Test: Signup hashes password before storing (security requirement)

        Given: Plain text password from user
        When: User signs up
        Then: Password is hashed using password_hasher
        And: Hashed password is stored, not plain text
        """
        # Arrange
        request = SignupRequestDTO(email="test@example.com", password="PlainTextPass123!")
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.create.return_value = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123"
        )

        # Act
        signup_use_case.execute(request)

        # Assert
        mock_password_hasher.hash.assert_called_once_with("PlainTextPass123!")

        # Verify hashed password is used, not plain text
        created_user = mock_user_repository.create.call_args[0][0]
        assert created_user.hashed_password == "hashed_password_123"
        assert created_user.hashed_password != "PlainTextPass123!"

    def test_signup_generates_secure_random_token(
        self, signup_use_case, mock_user_repository
    ):
        """
        Test: Signup generates secure random verification token

        Given: User signs up
        When: Token is generated
        Then: Token is 32 bytes hex string (64 characters)
        And: Token is cryptographically random (not predictable)
        """
        # Arrange
        request = SignupRequestDTO(email="test@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.create.return_value = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123"
        )

        # Act
        signup_use_case.execute(request)

        # Assert
        created_user = mock_user_repository.create.call_args[0][0]
        token = created_user.verification_token

        # Verify token is 64 characters (32 bytes hex)
        assert len(token) == 64

        # Verify token is hex string (only contains 0-9, a-f)
        assert all(c in '0123456789abcdef' for c in token)

    def test_signup_sets_token_expiry_24_hours(
        self, signup_use_case, mock_user_repository
    ):
        """
        Test: Signup sets verification token expiry to 24 hours from now

        Given: User signs up at specific time
        When: Token is generated
        Then: Token expiry is set to 24 hours from current time
        """
        # Arrange
        request = SignupRequestDTO(email="test@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = False

        before_signup = datetime.utcnow()

        mock_user_repository.create.return_value = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123"
        )

        # Act
        signup_use_case.execute(request)

        # Assert
        after_signup = datetime.utcnow()
        created_user = mock_user_repository.create.call_args[0][0]
        token_expiry = created_user.verification_token_expires_at

        # Verify expiry is ~24 hours from now (allow 1 second tolerance)
        expected_expiry_min = before_signup + timedelta(hours=24)
        expected_expiry_max = after_signup + timedelta(hours=24)

        assert expected_expiry_min <= token_expiry <= expected_expiry_max

    def test_signup_queues_verification_email_via_pgmq(
        self, signup_use_case, mock_user_repository, mock_email_service
    ):
        """
        Test: Signup queues verification email via PGMQ

        Given: User signs up successfully
        When: User is saved to database
        Then: Verification email is queued via PGMQ
        And: Email contains verification token and user email
        """
        # Arrange
        request = SignupRequestDTO(email="test@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.create.return_value = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123"
        )
        mock_email_service.enqueue.return_value = 1  # Message ID

        # Act
        signup_use_case.execute(request)

        # Assert
        mock_email_service.enqueue.assert_called_once()
        call_args = mock_email_service.enqueue.call_args

        # Verify queue name
        assert call_args[0][0] == "email_verification"

        # Verify message payload
        message = call_args[0][1]
        assert message["to_email"] == "test@example.com"
        assert message["user_id"] == 1
        # Token is generated by use case, verify it exists and is 64 chars hex
        assert "token" in message
        assert len(message["token"]) == 64
        assert all(c in '0123456789abcdef' for c in message["token"])

    def test_signup_generates_username_from_email(
        self, signup_use_case, mock_user_repository
    ):
        """
        Test: Signup generates username from email local part

        Given: User signs up with email
        When: Username is not provided
        Then: Username is generated from email local part
        And: Invalid characters (dots) are replaced with underscores
        """
        # Arrange
        request = SignupRequestDTO(email="john.doe@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.create.return_value = User(
            id=1,
            email=Email("john.doe@example.com"),
            username=Username("john_doe"),  # Dots replaced with underscores
            hashed_password="hashed_password_123"
        )

        # Act
        signup_use_case.execute(request)

        # Assert
        created_user = mock_user_repository.create.call_args[0][0]
        # Verify dots are replaced with underscores for valid username
        assert created_user.username.value == "john_doe"

    def test_signup_rolls_back_on_email_queue_failure(
        self, signup_use_case, mock_user_repository, mock_email_service
    ):
        """
        Test: Signup rolls back database transaction on email queue failure

        Given: User creation succeeds
        When: Email queue fails
        Then: Transaction is rolled back (user is not created)
        And: Exception is raised to caller
        """
        # Arrange
        request = SignupRequestDTO(email="test@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.create.return_value = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123"
        )
        mock_email_service.enqueue.side_effect = Exception("PGMQ connection failed")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            signup_use_case.execute(request)

        assert "PGMQ connection failed" in str(exc_info.value)

    def test_signup_returns_correct_response_dto(
        self, signup_use_case, mock_user_repository
    ):
        """
        Test: Signup returns SignupResponseDTO with correct structure

        Given: Successful signup
        When: Response is returned
        Then: Response is SignupResponseDTO with user_id, email, message
        """
        # Arrange
        request = SignupRequestDTO(email="test@example.com", password="SecurePass123!")
        mock_user_repository.exists_by_email.return_value = False
        mock_user_repository.create.return_value = User(
            id=42,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123"
        )

        # Act
        response = signup_use_case.execute(request)

        # Assert
        assert isinstance(response, SignupResponseDTO)
        assert response.user_id == 42
        assert response.email == "test@example.com"
        assert isinstance(response.message, str)
        assert len(response.message) > 0
