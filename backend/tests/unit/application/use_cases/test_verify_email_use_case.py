"""
Unit tests for VerifyEmailUseCase (TDD - RED phase)

Tests for email verification functionality:
- Successful email verification flow
- Invalid token rejection
- Expired token rejection (> 24h)
- Token not found rejection
- Already verified user (idempotency)
- Token cleared after successful verification
- Onboarding status updated correctly
- Multiple verification attempts with same token (should fail after first use)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from app.application.use_cases.onboarding.verify_email_use_case import VerifyEmailUseCase
from app.application.dtos.onboarding_dto import VerifyEmailRequestDTO, VerifyEmailResponseDTO
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.exceptions.domain_exception import DomainValidationException


class TestVerifyEmailUseCase:
    """Test suite for VerifyEmailUseCase following TDD RED-GREEN-REFACTOR"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing"""
        return Mock()

    @pytest.fixture
    def verify_email_use_case(self, mock_user_repository):
        """Create VerifyEmailUseCase instance with mocks"""
        return VerifyEmailUseCase(user_repository=mock_user_repository)

    def test_successful_email_verification_updates_status_to_email_verified(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Successful email verification updates onboarding_status to 'email_verified'

        Given: Valid verification token
        When: User verifies email
        Then: Onboarding status is updated to 'email_verified'
        And: User is activated (is_active=True)
        """
        # Arrange
        request = VerifyEmailRequestDTO(token="abc123def456")

        # Create user with pending verification
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification",
            verification_token="abc123def456",
            verification_token_expires_at=datetime.utcnow() + timedelta(hours=12),  # Valid token
            is_active=False
        )

        mock_user_repository.get_by_verification_token.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        response = verify_email_use_case.execute(request)

        # Assert
        assert response.success is True
        assert "verified successfully" in response.message.lower()
        assert response.onboarding_status == "email_verified"

        # Verify user was updated with correct status
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_status == "email_verified"
        assert update_call.is_active is True

    def test_verification_clears_token_after_successful_use(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Verification clears token after successful use (one-time use security)

        Given: Valid verification token
        When: Email is verified successfully
        Then: Verification token is set to None
        And: Token expiry is set to None
        """
        # Arrange
        request = VerifyEmailRequestDTO(token="abc123def456")

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification",
            verification_token="abc123def456",
            verification_token_expires_at=datetime.utcnow() + timedelta(hours=12),
            is_active=False
        )

        mock_user_repository.get_by_verification_token.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        verify_email_use_case.execute(request)

        # Assert - Verify token was cleared (one-time use)
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.verification_token is None
        assert update_call.verification_token_expires_at is None

    def test_invalid_token_raises_domain_validation_exception(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Invalid token raises DomainValidationException

        Given: Non-existent verification token
        When: User attempts to verify email
        Then: DomainValidationException is raised with appropriate message
        """
        # Arrange
        request = VerifyEmailRequestDTO(token="invalid_token_123")
        mock_user_repository.get_by_verification_token.return_value = None

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_email_use_case.execute(request)

        assert "invalid verification token" in str(exc_info.value).lower()

    def test_expired_token_raises_domain_validation_exception(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Expired token (> 24 hours) raises DomainValidationException

        Given: Verification token that expired 2 hours ago
        When: User attempts to verify email
        Then: DomainValidationException is raised indicating token expired
        """
        # Arrange
        request = VerifyEmailRequestDTO(token="expired_token_123")

        # Token expired 2 hours ago
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification",
            verification_token="expired_token_123",
            verification_token_expires_at=datetime.utcnow() - timedelta(hours=2),  # Expired
            is_active=False
        )

        mock_user_repository.get_by_verification_token.return_value = user

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_email_use_case.execute(request)

        assert "expired" in str(exc_info.value).lower()

    def test_already_verified_user_returns_success_idempotent(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Already verified user returns success (idempotent operation)

        Given: User with onboarding_status='email_verified'
        When: User attempts to verify email again
        Then: Success response is returned without changes
        And: No database update is called
        """
        # Arrange
        request = VerifyEmailRequestDTO(token="already_used_token")

        # User already verified (token cleared, status updated)
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            verification_token=None,  # Already cleared
            verification_token_expires_at=None,
            is_active=True
        )

        mock_user_repository.get_by_verification_token.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        response = verify_email_use_case.execute(request)

        # Assert - Returns success without updating
        assert response.success is True
        assert response.onboarding_status == "email_verified"

    def test_none_token_user_raises_domain_validation_exception(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Token that returns None user raises DomainValidationException

        Given: Token that doesn't match any user
        When: User attempts to verify email
        Then: DomainValidationException is raised
        """
        # Arrange - Token exists but no user found
        request = VerifyEmailRequestDTO(token="nonexistent_token_123")
        mock_user_repository.get_by_verification_token.return_value = None

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_email_use_case.execute(request)

        assert "invalid verification token" in str(exc_info.value).lower()

    def test_multiple_verification_attempts_fail_after_first_use(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Multiple verification attempts with same token fail after first use

        Given: Token was used for first verification
        When: User attempts to verify with same token again
        Then: Token is not found (was cleared) and verification fails
        """
        # Arrange - First verification
        request = VerifyEmailRequestDTO(token="one_time_token_123")

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification",
            verification_token="one_time_token_123",
            verification_token_expires_at=datetime.utcnow() + timedelta(hours=12),
            is_active=False
        )

        mock_user_repository.get_by_verification_token.return_value = user
        mock_user_repository.update.return_value = user

        # Act - First verification succeeds
        response1 = verify_email_use_case.execute(request)
        assert response1.success is True

        # Arrange - Second verification attempt (token should be cleared)
        mock_user_repository.get_by_verification_token.return_value = None

        # Act & Assert - Second verification fails
        with pytest.raises(DomainValidationException) as exc_info:
            verify_email_use_case.execute(request)

        assert "invalid verification token" in str(exc_info.value).lower()

    def test_token_expiry_boundary_exactly_24_hours(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Token expiry boundary at exactly 24 hours

        Given: Token that expires in exactly 0 seconds (current time)
        When: User attempts to verify email
        Then: Token is considered expired
        """
        # Arrange
        request = VerifyEmailRequestDTO(token="boundary_token_123")

        # Token expires exactly now (boundary case)
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification",
            verification_token="boundary_token_123",
            verification_token_expires_at=datetime.utcnow(),  # Expires exactly now
            is_active=False
        )

        mock_user_repository.get_by_verification_token.return_value = user

        # Act & Assert - Should be considered expired
        with pytest.raises(DomainValidationException) as exc_info:
            verify_email_use_case.execute(request)

        assert "expired" in str(exc_info.value).lower()

    def test_verification_returns_correct_response_dto_structure(
        self, verify_email_use_case, mock_user_repository
    ):
        """
        Test: Verification returns VerifyEmailResponseDTO with correct structure

        Given: Successful verification
        When: Response is returned
        Then: Response is VerifyEmailResponseDTO with success, message, onboarding_status
        """
        # Arrange
        request = VerifyEmailRequestDTO(token="abc123def456")

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification",
            verification_token="abc123def456",
            verification_token_expires_at=datetime.utcnow() + timedelta(hours=12),
            is_active=False
        )

        mock_user_repository.get_by_verification_token.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        response = verify_email_use_case.execute(request)

        # Assert
        assert isinstance(response, VerifyEmailResponseDTO)
        assert isinstance(response.success, bool)
        assert isinstance(response.message, str)
        assert isinstance(response.onboarding_status, str)
        assert len(response.message) > 0
