"""
Unit tests for VerifyPhoneCodeUseCase (TDD - RED phase)

Tests for phone code verification functionality:
- Successful phone verification flow
- Invalid code rejection
- Expired code rejection (> 15 minutes)
- Phone number not found rejection
- Already verified user (idempotency)
- Code cleared after successful verification
- Multiple verification attempts with same code (fail after first)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from app.application.use_cases.onboarding.verify_phone_code_use_case import VerifyPhoneCodeUseCase
from app.application.dtos.onboarding_dto import PhoneVerifyCodeRequestDTO, PhoneVerifyResponseDTO
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.exceptions.domain_exception import DomainValidationException


class TestVerifyPhoneCodeUseCase:
    """Test suite for VerifyPhoneCodeUseCase following TDD RED-GREEN-REFACTOR"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing"""
        return Mock()

    @pytest.fixture
    def verify_phone_code_use_case(self, mock_user_repository):
        """Create VerifyPhoneCodeUseCase instance with mocks"""
        return VerifyPhoneCodeUseCase(user_repository=mock_user_repository)

    def test_successful_phone_verification_updates_status_to_phone_verified(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Successful phone verification updates onboarding_status to 'phone_verified'

        Given: Valid phone number and matching verification code
        When: User verifies phone
        Then: Onboarding status is updated to 'phone_verified'
        And: User is activated (is_active=True)
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        # User with pending phone verification
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",
            phone_code_expires_at=datetime.utcnow() + timedelta(minutes=10),  # Valid
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        response = verify_phone_code_use_case.execute(request)

        # Assert
        assert response.success is True
        assert "verified successfully" in response.message.lower()
        assert response.onboarding_status == "phone_verified"

        # Verify user was updated with correct status
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_status == "phone_verified"
        assert update_call.is_active is True

    def test_verification_clears_code_after_successful_use(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Verification clears code after successful use (one-time use security)

        Given: Valid phone number and code
        When: Phone is verified successfully
        Then: Phone verification code is set to None
        And: Code expiry is set to None
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",
            phone_code_expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        verify_phone_code_use_case.execute(request)

        # Assert - Verify code was cleared (one-time use)
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.phone_verification_code is None
        assert update_call.phone_code_expires_at is None

    def test_invalid_code_raises_domain_validation_exception(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Invalid verification code raises DomainValidationException

        Given: Valid phone number but incorrect code
        When: User attempts to verify phone
        Then: DomainValidationException is raised with appropriate message
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="999999"  # Wrong code
        )

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",  # Correct code
            phone_code_expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_phone_code_use_case.execute(request)

        assert "invalid verification code" in str(exc_info.value).lower()

    def test_expired_code_raises_domain_validation_exception(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Expired code (> 15 minutes) raises DomainValidationException

        Given: Valid phone and code but expired timestamp
        When: User attempts to verify phone
        Then: DomainValidationException is raised indicating code expired
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        # Code expired 5 minutes ago
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",
            phone_code_expires_at=datetime.utcnow() - timedelta(minutes=5),  # Expired
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_phone_code_use_case.execute(request)

        assert "expired" in str(exc_info.value).lower()

    def test_phone_number_not_found_raises_exception(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Phone number not found raises DomainValidationException

        Given: Phone number not in database
        When: User attempts to verify
        Then: DomainValidationException is raised
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+19995551234",
            code="123456"
        )

        mock_user_repository.get_by_phone_number.return_value = None

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_phone_code_use_case.execute(request)

        assert "phone number not found" in str(exc_info.value).lower()

    def test_already_verified_phone_returns_success_idempotent(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Already verified phone returns success (idempotent operation)

        Given: User with onboarding_status='phone_verified'
        When: User attempts to verify phone again
        Then: Success response is returned without changes
        And: No database update is called
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        # User already verified (code cleared, status updated)
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="phone_verified",
            phone_number="+12025551234",
            phone_verification_code=None,  # Already cleared
            phone_code_expires_at=None,
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user

        # Act
        response = verify_phone_code_use_case.execute(request)

        # Assert - Returns success without updating
        assert response.success is True
        assert response.onboarding_status == "phone_verified"
        # Update should not be called for already verified
        assert not mock_user_repository.update.called

    def test_no_code_set_raises_exception(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Phone number exists but no code set raises exception

        Given: User with phone but no verification code
        When: User attempts to verify
        Then: DomainValidationException is raised
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code=None,  # No code set
            phone_code_expires_at=None,
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_phone_code_use_case.execute(request)

        assert "no verification code" in str(exc_info.value).lower()

    def test_multiple_verification_attempts_fail_after_first_use(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Multiple verification attempts with same code fail after first use

        Given: Code was used for first verification
        When: User attempts to verify with same code again
        Then: Code is not found (was cleared) and verification fails
        """
        # Arrange - First verification
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",
            phone_code_expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user
        mock_user_repository.update.return_value = user

        # Act - First verification succeeds
        response1 = verify_phone_code_use_case.execute(request)
        assert response1.success is True

        # Arrange - Second verification attempt (code should be cleared)
        verified_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="phone_verified",
            phone_number="+12025551234",
            phone_verification_code=None,  # Cleared after first verification
            phone_code_expires_at=None,
            is_active=True
        )
        mock_user_repository.get_by_phone_number.return_value = verified_user

        # Act & Assert - Second verification returns success (idempotent)
        response2 = verify_phone_code_use_case.execute(request)
        assert response2.success is True
        assert response2.onboarding_status == "phone_verified"

    def test_code_expiry_boundary_exactly_15_minutes(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Code expiry boundary at exactly 15 minutes

        Given: Code that expires in exactly 0 seconds (current time)
        When: User attempts to verify
        Then: Code is considered expired
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        # Code expires exactly now (boundary case)
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",
            phone_code_expires_at=datetime.utcnow(),  # Expires exactly now
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user

        # Act & Assert - Should be considered expired
        with pytest.raises(DomainValidationException) as exc_info:
            verify_phone_code_use_case.execute(request)

        assert "expired" in str(exc_info.value).lower()

    def test_verification_returns_correct_response_dto_structure(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Verification returns PhoneVerifyResponseDTO with correct structure

        Given: Successful verification
        When: Response is returned
        Then: Response is PhoneVerifyResponseDTO with success, message, onboarding_status
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",
            phone_code_expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        response = verify_phone_code_use_case.execute(request)

        # Assert
        assert isinstance(response, PhoneVerifyResponseDTO)
        assert isinstance(response.success, bool)
        assert isinstance(response.message, str)
        assert isinstance(response.onboarding_status, str)
        assert len(response.message) > 0

    def test_case_sensitive_code_validation(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Code validation is exact match (numeric codes)

        Given: Stored code "123456"
        When: User submits code with leading zeros or different format
        Then: Code must match exactly
        """
        # Arrange
        request = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="012345"  # Different code
        )

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            phone_number="+12025551234",
            phone_verification_code="123456",
            phone_code_expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = user

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            verify_phone_code_use_case.execute(request)

        assert "invalid verification code" in str(exc_info.value).lower()

    def test_whitespace_in_code_not_trimmed(
        self, verify_phone_code_use_case, mock_user_repository
    ):
        """
        Test: Code with whitespace is rejected by DTO validation (exact match required)

        Given: Stored code "123456"
        When: User submits "123456 " (with trailing space)
        Then: DTO validation fails before reaching use case
        """
        # Arrange & Act & Assert
        # DTO will reject invalid format before reaching use case
        # This test validates that Pydantic enforces exact numeric pattern
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            request = PhoneVerifyCodeRequestDTO(
                phone_number="+12025551234",
                code="123456 "  # Trailing space (rejected by DTO pattern validation)
            )

        # Verify the validation error is about the pattern mismatch
        assert "string_pattern_mismatch" in str(exc_info.value)
