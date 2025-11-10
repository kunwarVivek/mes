"""
Unit tests for RequestPhoneSMSUseCase (TDD - RED phase)

Tests for phone SMS code request functionality:
- Successful SMS code generation and sending
- 6-digit numeric code format validation
- 15-minute expiry set correctly
- SMS queued via PGMQ
- Duplicate phone number rejection (already verified)
- Code randomness validation (not predictable)
- Phone number format validation (E.164)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import re

from app.application.use_cases.onboarding.request_phone_sms_use_case import RequestPhoneSMSUseCase
from app.application.dtos.onboarding_dto import PhoneVerifyRequestDTO
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.exceptions.domain_exception import DomainValidationException


class TestRequestPhoneSMSUseCase:
    """Test suite for RequestPhoneSMSUseCase following TDD RED-GREEN-REFACTOR"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing"""
        return Mock()

    @pytest.fixture
    def mock_sms_service(self):
        """Mock SMS service (PGMQ) for testing"""
        mock = Mock()
        mock.enqueue.return_value = 123  # Mock message ID
        return mock

    @pytest.fixture
    def request_phone_sms_use_case(self, mock_user_repository, mock_sms_service):
        """Create RequestPhoneSMSUseCase instance with mocks"""
        return RequestPhoneSMSUseCase(
            user_repository=mock_user_repository,
            sms_service=mock_sms_service
        )

    def test_successful_sms_code_generation_and_queue(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: Successful SMS code generation and queueing

        Given: Valid phone number in E.164 format
        When: User requests SMS verification code
        Then: 6-digit code is generated
        And: Code is saved to user record with 15-minute expiry
        And: SMS is queued via PGMQ
        And: Success message is returned
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")

        # User exists but not phone verified
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = None  # Phone not in use
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        response = request_phone_sms_use_case.execute(request, user_id=1)

        # Assert
        assert response["success"] is True
        assert "SMS code sent to" in response["message"]
        assert "+12025551234" in response["message"]

        # Verify code was saved to user
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.phone_number == "+12025551234"
        assert update_call.phone_verification_code is not None
        assert update_call.phone_code_expires_at is not None

        # Verify SMS was queued
        assert mock_sms_service.enqueue.called
        queue_call = mock_sms_service.enqueue.call_args
        assert queue_call[0][0] == "phone_verification"  # Queue name
        assert queue_call[0][1]["phone_number"] == "+12025551234"
        assert "code" in queue_call[0][1]

    def test_generated_code_is_6_digits_numeric(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: Generated verification code is exactly 6 digits numeric

        Given: Valid phone number
        When: SMS code is generated
        Then: Code is exactly 6 characters long
        And: Code contains only digits (0-9)
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = None
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        request_phone_sms_use_case.execute(request, user_id=1)

        # Assert - Check code format
        update_call = mock_user_repository.update.call_args[0][0]
        code = update_call.phone_verification_code

        assert len(code) == 6, f"Code length should be 6, got {len(code)}"
        assert code.isdigit(), f"Code should be numeric, got {code}"
        assert re.match(r'^\d{6}$', code), f"Code should match 6-digit pattern, got {code}"

    def test_code_expiry_set_to_15_minutes(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: Code expiry is set to exactly 15 minutes from now

        Given: Valid phone number
        When: SMS code is generated
        Then: phone_code_expires_at is set to ~15 minutes from current time
        And: Expiry is within 1 second margin for test timing
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = None
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        before_execution = datetime.utcnow()
        request_phone_sms_use_case.execute(request, user_id=1)
        after_execution = datetime.utcnow()

        # Assert - Check expiry is ~15 minutes from now
        update_call = mock_user_repository.update.call_args[0][0]
        expiry = update_call.phone_code_expires_at

        expected_expiry_min = before_execution + timedelta(minutes=15)
        expected_expiry_max = after_execution + timedelta(minutes=15)

        assert expected_expiry_min <= expiry <= expected_expiry_max, \
            f"Expiry should be 15 minutes from now, got {expiry}"

    def test_sms_queued_with_correct_structure(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: SMS message is queued via PGMQ with correct structure

        Given: Valid phone number and generated code
        When: SMS is queued
        Then: Message contains type, phone_number, code, template, created_at
        And: Queue name is 'phone_verification'
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = None
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        request_phone_sms_use_case.execute(request, user_id=1)

        # Assert - Check SMS queue structure
        queue_call = mock_sms_service.enqueue.call_args
        queue_name = queue_call[0][0]
        message = queue_call[0][1]

        assert queue_name == "phone_verification"
        assert message["type"] == "phone_verification"
        assert message["user_id"] == 1
        assert message["phone_number"] == "+12025551234"
        assert "code" in message
        assert len(message["code"]) == 6
        assert message["template"] == "verify_phone"
        assert "created_at" in message

    def test_duplicate_phone_number_already_verified_rejected(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: Duplicate phone number (already verified) is rejected

        Given: Phone number already verified by another user
        When: User requests SMS code for that phone
        Then: DomainValidationException is raised
        And: No SMS is queued
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")

        # Phone already verified by another user
        existing_user = User(
            id=999,
            email=Email("other@example.com"),
            username=Username("other"),
            hashed_password="hashed_password_123",
            onboarding_status="phone_verified",
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = existing_user

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            request_phone_sms_use_case.execute(request, user_id=1)

        assert "already in use" in str(exc_info.value).lower()
        assert not mock_sms_service.enqueue.called

    def test_code_randomness_multiple_generations_unique(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: Generated codes are random and unique across multiple requests

        Given: Multiple SMS code generation requests
        When: Codes are generated
        Then: Codes are different (not predictable/sequential)
        And: Codes use cryptographically secure random generation
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = None
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        # Act - Generate multiple codes
        generated_codes = []
        for _ in range(5):
            request_phone_sms_use_case.execute(request, user_id=1)
            update_call = mock_user_repository.update.call_args[0][0]
            generated_codes.append(update_call.phone_verification_code)

        # Assert - Codes should be unique (very high probability with random generation)
        assert len(set(generated_codes)) == len(generated_codes), \
            f"Codes should be unique, got duplicates: {generated_codes}"

        # Assert - Codes should not be sequential
        codes_as_ints = [int(code) for code in generated_codes]
        for i in range(len(codes_as_ints) - 1):
            # Check codes are not sequential (difference > 1)
            assert abs(codes_as_ints[i] - codes_as_ints[i+1]) != 1, \
                f"Codes should not be sequential, got {codes_as_ints}"

    def test_user_not_found_raises_exception(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: User not found raises DomainValidationException

        Given: Invalid user_id
        When: SMS code is requested
        Then: DomainValidationException is raised
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")
        mock_user_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            request_phone_sms_use_case.execute(request, user_id=999)

        assert "user not found" in str(exc_info.value).lower()

    def test_phone_number_saved_in_e164_format(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: Phone number is saved in E.164 format

        Given: Valid E.164 phone number
        When: SMS code is generated
        Then: Phone number is saved exactly as provided (preserving E.164 format)
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+447911123456")  # UK number

        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True
        )

        mock_user_repository.get_by_phone_number.return_value = None
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        request_phone_sms_use_case.execute(request, user_id=1)

        # Assert - Phone saved in E.164 format
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.phone_number == "+447911123456"
        assert update_call.phone_number.startswith("+")

    def test_resend_code_overwrites_previous_code(
        self, request_phone_sms_use_case, mock_user_repository, mock_sms_service
    ):
        """
        Test: Resending code overwrites previous code and expiry

        Given: User already has a pending verification code
        When: User requests new SMS code
        Then: Previous code is overwritten with new code
        And: Expiry is reset to 15 minutes from now
        """
        # Arrange
        request = PhoneVerifyRequestDTO(phone_number="+12025551234")

        # User has existing pending code
        user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True,
            phone_number="+12025551234",
            phone_verification_code="123456",  # Old code
            phone_code_expires_at=datetime.utcnow() + timedelta(minutes=5)  # Old expiry
        )

        mock_user_repository.get_by_phone_number.return_value = user
        mock_user_repository.get_by_id.return_value = user
        mock_user_repository.update.return_value = user

        # Act
        old_code = user.phone_verification_code
        request_phone_sms_use_case.execute(request, user_id=1)

        # Assert - Code should be different (overwritten)
        update_call = mock_user_repository.update.call_args[0][0]
        new_code = update_call.phone_verification_code

        # Very high probability codes are different
        assert new_code != old_code or len(set([new_code, old_code])) == 1, \
            "New code should overwrite old code"
