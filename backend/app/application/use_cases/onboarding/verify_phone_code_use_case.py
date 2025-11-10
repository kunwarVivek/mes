"""
VerifyPhoneCodeUseCase - Phone Code Verification for Self-Service Onboarding

Implements the second step of phone verification:
1. Receives phone number and verification code from user
2. Validates code matches stored code (exact match, case-sensitive)
3. Validates code hasn't expired (< 15 minutes)
4. Updates user onboarding_status to 'phone_verified'
5. Activates user account (is_active=True)
6. Clears verification code (one-time use security)
7. Saves user to database
8. Returns verification success response

Security Features:
- One-time code use (cleared after verification)
- Code expiry validation (15 minutes from creation)
- Exact code matching (no fuzzy matching for security)
- Idempotent operation (already verified users succeed)

Follows Clean Architecture and SOLID principles:
- Single Responsibility: Only handles phone code verification logic
- Dependency Inversion: Depends on repository interface
- Open/Closed: Extensible without modification
- Interface Segregation: Minimal dependencies
- Liskov Substitution: Compatible with IUserRepository interface

Error Handling:
- DomainValidationException: Invalid or expired codes, phone not found
- Database exceptions: Propagated to caller for transaction rollback

Example Usage:
    >>> repository = UserRepository(session)
    >>> use_case = VerifyPhoneCodeUseCase(repository)
    >>> request = PhoneVerifyCodeRequestDTO(phone_number="+12025551234", code="123456")
    >>> response = use_case.execute(request)
    >>> print(f"Phone verified: {response.success}")
"""
import logging
from datetime import datetime

from app.application.dtos.onboarding_dto import PhoneVerifyCodeRequestDTO, PhoneVerifyResponseDTO
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions.domain_exception import DomainValidationException

logger = logging.getLogger(__name__)


class VerifyPhoneCodeUseCase:
    """
    Use Case: Phone Code Verification (Self-Service Onboarding - Phone Verification Step 2)

    Handles phone code verification as an alternative to email verification
    in the self-service onboarding workflow. This is the second step after
    requesting SMS code, confirming phone number ownership.

    Responsibilities:
    - Validate phone number exists in database
    - Validate verification code matches stored code
    - Validate code not expired (< 15 minutes)
    - Update user onboarding status to 'phone_verified'
    - Activate user account (is_active=True)
    - Clear verification code (one-time use security)
    - Handle idempotent verification (already verified users)

    Dependencies (Injected):
    - IUserRepository: Database operations for user persistence

    Design Patterns:
    - Use Case Pattern: Business logic encapsulation
    - Dependency Injection: Testable, loosely coupled
    - Repository Pattern: Database abstraction

    Thread Safety: Not thread-safe (use per-request instances)
    Transaction Semantics: Atomic (user update or nothing)
    """

    # Code configuration constants (must match RequestPhoneSMSUseCase)
    CODE_EXPIRY_MINUTES = 15  # 15 minutes for phone verification

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize VerifyPhoneCodeUseCase with required dependencies.

        Args:
            user_repository: Repository implementing IUserRepository interface
                for user database operations (find by phone, update)

        Example:
            >>> from app.infrastructure.persistence.user_repository_impl import UserRepository
            >>>
            >>> repository = UserRepository(db_session)
            >>> use_case = VerifyPhoneCodeUseCase(repository)
        """
        self._repository = user_repository

    def execute(self, request: PhoneVerifyCodeRequestDTO) -> PhoneVerifyResponseDTO:
        """
        Execute phone code verification workflow (main entry point).

        Orchestrates the complete verification process including phone lookup,
        code validation, expiry checking, status update, and code clearing.
        This method is transactional - either all steps succeed or none do.

        Workflow Steps:
        1. Find user by phone number
        2. Validate phone number exists (raise exception if not found)
        3. Check if already verified (idempotent - return success)
        4. Validate code exists (raise exception if None)
        5. Validate code matches (exact match, case-sensitive)
        6. Validate code not expired (< 15 minutes old)
        7. Update onboarding status to 'phone_verified'
        8. Activate user account (is_active=True)
        9. Clear verification code (one-time use)
        10. Save user to database (transactional)
        11. Return success response

        Args:
            request: PhoneVerifyCodeRequestDTO containing phone_number and code.
                Both fields are already validated by DTO.

        Returns:
            PhoneVerifyResponseDTO containing:
            - success: Verification success status (True)
            - message: Success message with next steps
            - onboarding_status: Current status ('phone_verified')

        Raises:
            DomainValidationException: If phone not found, code invalid/expired,
                or no code set. Error message is user-friendly and suggests alternatives.
            Exception: Database errors propagated to caller for proper
                transaction rollback handling.

        Example:
            >>> request = PhoneVerifyCodeRequestDTO(
            ...     phone_number="+12025551234",
            ...     code="123456"
            ... )
            >>> response = use_case.execute(request)
            >>> print(response.message)  # "Phone verified successfully..."

        Performance:
        - Database: 1 SELECT (find by phone) + 1 UPDATE (user status)
        - Total: ~50-100ms typical

        Security Notes:
        - Code is cleared after use (one-time verification)
        - Code expiry enforced (15 minutes from creation)
        - Exact code matching (no fuzzy matching)
        - Idempotent operation (safe to retry)
        """
        logger.info(f"Starting phone verification for phone: {request.phone_number}")

        # Step 1 & 2: Find user by phone number and validate existence
        user = self._repository.get_by_phone_number(request.phone_number)

        if user is None:
            logger.warning(
                f"Phone verification failed: Phone number not found - {request.phone_number} "
                f"(Security: Potential phone number guessing attempt)"
            )
            raise DomainValidationException(
                "Phone number not found. Please ensure you have requested a verification code first."
            )

        # Step 3: Check if already verified (idempotent operation)
        if user.onboarding_status == 'phone_verified':
            logger.info(f"Phone already verified for user {user.id}")
            return PhoneVerifyResponseDTO(
                success=True,
                message="Phone already verified. You can proceed with onboarding.",
                onboarding_status="phone_verified"
            )

        # Step 4: Validate code exists
        if user.phone_verification_code is None:
            logger.warning(
                f"Phone verification failed: No verification code set for user {user.id} "
                f"(phone: {request.phone_number})"
            )
            raise DomainValidationException(
                "No verification code found. Please request a new verification code."
            )

        # Step 5: Validate code matches (exact match, case-sensitive)
        if user.phone_verification_code != request.code:
            logger.warning(
                f"Phone verification failed: Invalid code for user {user.id} "
                f"(phone: {request.phone_number}). Expected: {user.phone_verification_code[:3]}***, "
                f"Got: {request.code[:3]}***"
            )
            raise DomainValidationException(
                "Invalid verification code. Please check the code and try again."
            )

        # Step 6: Validate code not expired (must be < 15 minutes old)
        if user.is_phone_code_expired():
            logger.warning(
                f"Phone verification failed: Code expired for user {user.id} "
                f"(phone: {request.phone_number}). Expiry: {user.phone_code_expires_at}"
            )
            raise DomainValidationException(
                "Verification code has expired. Please request a new verification code."
            )

        # Step 7-9: Verify phone (updates status, activates user, clears code)
        user.verify_phone()
        logger.info(f"Phone verified for user {user.id}, status updated to 'phone_verified'")

        # Step 10: Save user to database (transaction)
        try:
            updated_user = self._repository.update(user)
            logger.info(f"User {updated_user.id} phone verification saved to database")

        except Exception as e:
            # Rollback happens automatically via database transaction
            logger.error(f"Phone verification failed for user {user.id}: {str(e)}")
            raise

        # Step 11: Return success response
        return PhoneVerifyResponseDTO(
            success=True,
            message="Phone verified successfully. You can now proceed to organization setup.",
            onboarding_status="phone_verified"
        )
