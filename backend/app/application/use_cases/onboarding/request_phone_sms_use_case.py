"""
RequestPhoneSMSUseCase - Phone SMS Code Request for Self-Service Onboarding

Implements phone number verification as alternative to email verification:
1. Generates cryptographically secure 6-digit numeric code
2. Sets 15-minute expiry for code
3. Saves code to user record (phone_number, phone_verification_code, phone_code_expires_at)
4. Queues SMS via PGMQ for delivery
5. Returns success message

Security Features:
- Cryptographically secure random code generation (secrets module)
- One-time code use (cleared after verification)
- 15-minute expiry window (prevents replay attacks)
- Phone number uniqueness validation (prevents duplicate phone numbers)
- E.164 format enforcement (international standard)

Follows Clean Architecture and SOLID principles:
- Single Responsibility: Only handles SMS code request logic
- Dependency Inversion: Depends on repository/service interfaces
- Open/Closed: Extensible without modification
- Interface Segregation: Minimal dependencies
- Liskov Substitution: Compatible with IUserRepository interface

Error Handling:
- DomainValidationException: Business logic violations (duplicate phone, user not found)
- Database exceptions: Propagated to caller for transaction rollback
- PGMQ exceptions: Propagated to ensure atomic operation (user + SMS queue)

Example Usage:
    >>> repository = UserRepository(session)
    >>> pgmq_client = PGMQClient(...)
    >>> use_case = RequestPhoneSMSUseCase(repository, pgmq_client)
    >>> request = PhoneVerifyRequestDTO(phone_number="+12025551234")
    >>> response = use_case.execute(request, user_id=123)
    >>> print(response["message"])  # "SMS code sent to +12025551234"
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict

from app.application.dtos.onboarding_dto import PhoneVerifyRequestDTO
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions.domain_exception import DomainValidationException

logger = logging.getLogger(__name__)


class RequestPhoneSMSUseCase:
    """
    Use Case: Phone SMS Code Request (Self-Service Onboarding - Phone Verification Step 1)

    Handles phone verification code generation and SMS delivery as an alternative
    to email verification in the self-service onboarding workflow.

    Responsibilities:
    - Validate phone number not already in use
    - Generate cryptographically secure 6-digit numeric code
    - Set 15-minute expiry for code
    - Save code to user record
    - Queue SMS for asynchronous delivery via PGMQ
    - Return success confirmation

    Dependencies (Injected):
    - IUserRepository: Database operations for user persistence
    - SMS Service (PGMQ): Message queue for SMS delivery

    Design Patterns:
    - Use Case Pattern: Business logic encapsulation
    - Dependency Injection: Testable, loosely coupled
    - Repository Pattern: Database abstraction

    Thread Safety: Not thread-safe (use per-request instances)
    Transaction Semantics: Atomic (user update + SMS queue or nothing)
    """

    # Code configuration constants
    CODE_LENGTH = 6  # 6-digit numeric code
    CODE_EXPIRY_MINUTES = 15  # 15 minutes for phone verification

    def __init__(
        self,
        user_repository: IUserRepository,
        sms_service  # PGMQClient or SMSService interface
    ):
        """
        Initialize RequestPhoneSMSUseCase with required dependencies.

        Args:
            user_repository: Repository implementing IUserRepository interface
                for user database operations (get by phone, update)
            sms_service: Message queue service (PGMQClient) implementing
                enqueue(queue_name, message) method for SMS delivery

        Example:
            >>> from app.infrastructure.persistence.user_repository_impl import UserRepository
            >>> from app.infrastructure.messaging.pgmq_client import PGMQClient
            >>>
            >>> repository = UserRepository(db_session)
            >>> pgmq = PGMQClient(host="localhost", database="unison")
            >>> use_case = RequestPhoneSMSUseCase(repository, pgmq)
        """
        self._repository = user_repository
        self._sms_service = sms_service

    def execute(self, request: PhoneVerifyRequestDTO, user_id: int) -> Dict[str, any]:
        """
        Execute phone SMS code request workflow (main entry point).

        Orchestrates the complete SMS code generation process including phone
        validation, code generation, expiry setting, and SMS queueing. This method
        is transactional - either all steps succeed or none do.

        Workflow Steps:
        1. Validate user exists
        2. Check if phone number already in use by verified user
        3. Generate cryptographically secure 6-digit numeric code
        4. Set 15-minute expiry from current time
        5. Save code + phone + expiry to user record
        6. Queue SMS via PGMQ for delivery
        7. Return success message

        Args:
            request: PhoneVerifyRequestDTO containing phone_number in E.164 format.
                Phone number is already validated by DTO (E.164 format).
            user_id: ID of user requesting phone verification

        Returns:
            Dict containing:
            - success: Request success status (True)
            - message: Success message with phone number confirmation

        Raises:
            DomainValidationException: If user not found or phone already in use.
                Error message is user-friendly and suggests alternatives.
            Exception: Database or PGMQ errors propagated to caller for
                proper transaction rollback handling.

        Example:
            >>> request = PhoneVerifyRequestDTO(phone_number="+12025551234")
            >>> response = use_case.execute(request, user_id=123)
            >>> print(response["message"])  # "SMS code sent to +12025551234"

        Performance:
        - Database: 1 SELECT (phone check) + 1 SELECT (user get) + 1 UPDATE (save code)
        - PGMQ: 1 INSERT (SMS queue)
        - Code generation: ~1ms (cryptographically secure)
        - Total: ~50-100ms typical

        Security Notes:
        - Code is cryptographically secure (secrets module)
        - Phone uniqueness enforced (prevents duplicate verifications)
        - E.164 format validated (prevents malformed numbers)
        - 15-minute expiry enforced (prevents stale codes)
        """
        logger.info(f"Starting phone SMS code request for user {user_id}, phone: {request.phone_number}")

        # Step 1: Validate user exists
        user = self._repository.get_by_id(user_id)
        if user is None:
            logger.warning(f"Phone SMS request failed: User {user_id} not found")
            raise DomainValidationException(
                f"User not found. Please ensure you are logged in."
            )

        # Step 2: Check if phone number already in use by another verified user
        existing_user = self._repository.get_by_phone_number(request.phone_number)
        if existing_user is not None and existing_user.id != user_id:
            # Phone already verified by different user
            if existing_user.onboarding_status == 'phone_verified':
                logger.warning(
                    f"Phone SMS request failed: Phone {request.phone_number} already in use "
                    f"by user {existing_user.id}"
                )
                raise DomainValidationException(
                    f"Phone number {request.phone_number} is already in use. "
                    f"Please use a different phone number."
                )

        # Step 3: Generate cryptographically secure 6-digit numeric code
        # Using secrets module for cryptographic randomness (not predictable)
        code = self._generate_verification_code()
        logger.debug(f"Generated verification code for user {user_id}: {code[:3]}...")

        # Step 4: Set 15-minute expiry from current time
        code_expiry = datetime.utcnow() + timedelta(minutes=self.CODE_EXPIRY_MINUTES)
        logger.debug(f"Code expiry set to: {code_expiry}")

        # Step 5: Save code + phone + expiry to user record
        user.set_phone_verification_code(
            phone_number=request.phone_number,
            code=code,
            expires_at=code_expiry
        )

        try:
            updated_user = self._repository.update(user)
            logger.info(f"Phone verification code saved for user {updated_user.id}")

            # Step 6: Queue SMS via PGMQ for delivery
            self._queue_verification_sms(
                user_id=updated_user.id,
                phone_number=request.phone_number,
                code=code
            )
            logger.info(f"Verification SMS queued for user {updated_user.id}")

        except Exception as e:
            # Rollback happens automatically via database transaction
            logger.error(f"Phone SMS request failed for user {user_id}: {str(e)}")
            raise

        # Step 7: Return success message
        return {
            "success": True,
            "message": f"SMS code sent to {request.phone_number}. Code expires in {self.CODE_EXPIRY_MINUTES} minutes."
        }

    def _generate_verification_code(self) -> str:
        """
        Generate cryptographically secure 6-digit numeric verification code.

        Uses secrets module for cryptographic randomness to prevent code prediction
        attacks. Code is guaranteed to be exactly 6 digits (with leading zeros).

        Returns:
            6-digit numeric string (e.g., "012345", "987654")

        Example:
            >>> code = use_case._generate_verification_code()
            >>> print(len(code))  # 6
            >>> print(code.isdigit())  # True
        """
        # Generate random integer between 0 and 999999 (inclusive)
        # Format with leading zeros to ensure exactly 6 digits
        code_int = secrets.randbelow(1000000)
        code = f"{code_int:06d}"  # Format with leading zeros
        logger.debug(f"Generated 6-digit code: {code[:2]}****")
        return code

    def _queue_verification_sms(self, user_id: int, phone_number: str, code: str) -> None:
        """
        Queue verification SMS via PGMQ for asynchronous delivery.

        Enqueues a message to the 'phone_verification' queue containing user
        details and verification code. A background worker will process this
        message and send the actual SMS.

        Message Structure:
        - type: Message type identifier for worker routing
        - user_id: User ID for tracking and logging
        - phone_number: Recipient phone number (E.164 format)
        - code: 6-digit verification code
        - template: SMS template name for rendering
        - created_at: ISO timestamp for message age tracking

        Args:
            user_id: Database ID of user requesting verification
            phone_number: User's phone number for SMS delivery (E.164 format)
            code: 6-digit verification code

        Returns:
            None (message ID logged but not returned)

        Raises:
            Exception: If PGMQ enqueue operation fails. Caller should
                handle this by rolling back the user update transaction
                to maintain consistency.

        Queue Behavior:
        - Queue: 'phone_verification'
        - Visibility timeout: 30 seconds (configurable in PGMQ)
        - Retry count: 3 attempts (configured in PGMQ client)
        - DLQ: Failed messages moved to 'phone_verification_dlq'

        Example:
            >>> use_case._queue_verification_sms(
            ...     user_id=123,
            ...     phone_number="+12025551234",
            ...     code="123456"
            ... )
            # Message queued with ID 789 (logged)
        """
        message = {
            "type": "phone_verification",
            "user_id": user_id,
            "phone_number": phone_number,
            "code": code,
            "template": "verify_phone",
            "created_at": datetime.utcnow().isoformat()
        }

        # Enqueue message to 'phone_verification' queue
        # Worker will pick this up and send the SMS asynchronously
        msg_id = self._sms_service.enqueue("phone_verification", message)
        logger.debug(f"Queued phone verification message {msg_id} for user {user_id}")
