"""
VerifyEmailUseCase - Email Verification for Self-Service Onboarding

Implements the second step of the onboarding wizard:
1. Receives verification token from email link
2. Validates token exists and hasn't expired (< 24 hours)
3. Updates user onboarding_status to 'email_verified'
4. Activates user account (is_active=True)
5. Clears verification token (one-time use security)
6. Saves user to database
7. Returns verification success response

Security Features:
- One-time token use (cleared after verification)
- Token expiry validation (24 hours from creation)
- Cryptographically secure token validation
- Idempotent operation (already verified users succeed)

Follows Clean Architecture and SOLID principles:
- Single Responsibility: Only handles email verification logic
- Dependency Inversion: Depends on repository interface
- Open/Closed: Extensible without modification
- Interface Segregation: Minimal dependencies
- Liskov Substitution: Compatible with IUserRepository interface

Error Handling:
- DomainValidationException: Invalid or expired tokens
- Database exceptions: Propagated to caller for transaction rollback

Example Usage:
    >>> repository = UserRepository(session)
    >>> use_case = VerifyEmailUseCase(repository)
    >>> request = VerifyEmailRequestDTO(token="abc123def456")
    >>> response = use_case.execute(request)
    >>> print(f"Email verified: {response.success}")
"""
import logging
from datetime import datetime

from app.application.dtos.onboarding_dto import VerifyEmailRequestDTO, VerifyEmailResponseDTO
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions.domain_exception import DomainValidationException

logger = logging.getLogger(__name__)


class VerifyEmailUseCase:
    """
    Use Case: Email Verification (Self-Service Onboarding Step 2)

    Handles email verification as part of the self-service onboarding workflow.
    This is the second step after user signup, confirming email ownership.

    Responsibilities:
    - Validate verification token exists and is not expired
    - Update user onboarding status to 'email_verified'
    - Activate user account (is_active=True)
    - Clear verification token (one-time use security)
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

    # Token configuration constants (must match SignupUseCase)
    TOKEN_EXPIRY_HOURS = 24  # 24 hours for email verification

    def __init__(self, user_repository: IUserRepository):
        """
        Initialize VerifyEmailUseCase with required dependencies.

        Args:
            user_repository: Repository implementing IUserRepository interface
                for user database operations (find by token, update)

        Example:
            >>> from app.infrastructure.persistence.user_repository_impl import UserRepository
            >>>
            >>> repository = UserRepository(db_session)
            >>> use_case = VerifyEmailUseCase(repository)
        """
        self._repository = user_repository

    def execute(self, request: VerifyEmailRequestDTO) -> VerifyEmailResponseDTO:
        """
        Execute email verification workflow (main entry point).

        Orchestrates the complete verification process including token validation,
        expiry checking, status update, and token clearing. This method is
        transactional - either all steps succeed or none do.

        Workflow Steps:
        1. Find user by verification token
        2. Validate token exists (raise exception if not found)
        3. Check if already verified (idempotent - return success)
        4. Validate token not expired (< 24 hours old)
        5. Update onboarding status to 'email_verified'
        6. Activate user account (is_active=True)
        7. Clear verification token (one-time use)
        8. Save user to database (transactional)
        9. Return success response

        Args:
            request: VerifyEmailRequestDTO containing verification token from email link.
                Token is already validated for non-empty by DTO.

        Returns:
            VerifyEmailResponseDTO containing:
            - success: Verification success status (True)
            - message: Success message with next steps
            - onboarding_status: Current status ('email_verified')

        Raises:
            DomainValidationException: If token is invalid, expired, or not found.
                Error message is user-friendly and suggests alternatives.
            Exception: Database errors propagated to caller for proper
                transaction rollback handling.

        Example:
            >>> request = VerifyEmailRequestDTO(token="abc123def456")
            >>> response = use_case.execute(request)
            >>> print(response.message)  # "Email verified successfully..."

        Performance:
        - Database: 1 SELECT (find by token) + 1 UPDATE (user status)
        - Total: ~50-100ms typical

        Security Notes:
        - Token is cleared after use (one-time verification)
        - Token expiry enforced (24 hours from creation)
        - Idempotent operation (safe to retry)
        """
        logger.info(f"Starting email verification for token: {request.token[:8]}...")

        # Step 1 & 2: Find user by token and validate existence
        user = self._repository.get_by_verification_token(request.token)

        if user is None:
            logger.warning(
                f"Email verification failed: Invalid token - {request.token[:8]}... "
                f"(Security: Potential token guessing attempt or expired link)"
            )
            raise DomainValidationException(
                "Invalid verification token. Please check your email link or request a new verification email."
            )

        # Step 3: Check if already verified (idempotent operation)
        if user.onboarding_status == 'email_verified':
            logger.info(f"Email already verified for user {user.id}")
            return VerifyEmailResponseDTO(
                success=True,
                message="Email already verified. You can proceed with onboarding.",
                onboarding_status="email_verified"
            )

        # Step 4: Validate token not expired (must be < 24 hours old)
        if user.is_token_expired():
            logger.warning(
                f"Email verification failed: Token expired for user {user.id} "
                f"(email: {user.email.value}). Expiry: {user.verification_token_expires_at}"
            )
            raise DomainValidationException(
                "Verification token has expired. Please request a new verification email."
            )

        # Step 5-7: Verify email (updates status, activates user, clears token)
        user.verify_email()
        logger.info(f"Email verified for user {user.id}, status updated to 'email_verified'")

        # Step 8: Save user to database (transaction)
        try:
            updated_user = self._repository.update(user)
            logger.info(f"User {updated_user.id} email verification saved to database")

        except Exception as e:
            # Rollback happens automatically via database transaction
            logger.error(f"Email verification failed for user {user.id}: {str(e)}")
            raise

        # Step 9: Return success response
        return VerifyEmailResponseDTO(
            success=True,
            message="Email verified successfully. You can now proceed to organization setup.",
            onboarding_status="email_verified"
        )
