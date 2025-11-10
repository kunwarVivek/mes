"""
SignupUseCase - Self-Service User Signup

Implements the first step of the onboarding wizard:
1. Validates email not already registered
2. Hashes password using bcrypt (never stores plain text)
3. Generates cryptographically secure verification token (32 bytes hex)
4. Sets token expiry (24 hours from creation)
5. Creates user with onboarding_status='pending_verification'
6. Saves user to database (transactional)
7. Queues verification email via PGMQ
8. Returns SignupResponseDTO with user details

Security Features:
- Password hashing via bcrypt (cost factor 12)
- Cryptographically secure token generation (secrets.token_hex)
- Transactional database operations (rollback on failure)
- Email validation via Pydantic EmailStr
- Password complexity requirements enforced in DTO

Follows Clean Architecture and SOLID principles:
- Single Responsibility: Only handles signup logic
- Dependency Inversion: Depends on repository/service interfaces
- Open/Closed: Extensible without modification
- Interface Segregation: Minimal dependencies
- Liskov Substitution: Compatible with IUserRepository interface

Error Handling:
- DomainValidationException: Business logic violations (duplicate email)
- Database exceptions: Propagated to caller for transaction rollback
- PGMQ exceptions: Propagated to ensure atomic signup (user + email queue)

Example Usage:
    >>> repository = UserRepository(session)
    >>> pgmq_client = PGMQClient(...)
    >>> use_case = SignupUseCase(repository, pgmq_client)
    >>> request = SignupRequestDTO(email="user@example.com", password="SecurePass123!")
    >>> response = use_case.execute(request)
    >>> print(f"User {response.user_id} created, verification email sent")
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext

from app.application.dtos.onboarding_dto import SignupRequestDTO, SignupResponseDTO
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions import DomainValidationException

logger = logging.getLogger(__name__)


class PasswordHasher:
    """
    Password hashing utility using bcrypt.

    Provides secure password hashing and verification using bcrypt algorithm
    with configurable cost factor (default 12 rounds).

    Security Properties:
    - Adaptive hashing (computationally expensive to crack)
    - Automatic salt generation (unique per password)
    - Constant-time comparison (prevents timing attacks)

    Thread Safety: Safe for concurrent use (passlib is thread-safe)
    """

    def __init__(self):
        """Initialize password hasher with bcrypt scheme"""
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, plain_password: str) -> str:
        """
        Hash a plain text password using bcrypt.

        Args:
            plain_password: Plain text password to hash

        Returns:
            Bcrypt hash string (60 characters, includes salt)

        Example:
            >>> hasher = PasswordHasher()
            >>> hashed = hasher.hash("MySecurePass123!")
            >>> print(len(hashed))  # 60
        """
        return self._pwd_context.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash (constant-time comparison).

        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hash to compare against

        Returns:
            True if password matches hash, False otherwise

        Example:
            >>> hasher = PasswordHasher()
            >>> hashed = hasher.hash("MyPass123!")
            >>> hasher.verify("MyPass123!", hashed)  # True
            >>> hasher.verify("WrongPass", hashed)  # False
        """
        return self._pwd_context.verify(plain_password, hashed_password)


class SignupUseCase:
    """
    Use Case: User Signup (Self-Service Onboarding Step 1)

    Handles new user registration with email verification as part of the
    self-service onboarding workflow. This is the entry point for new users
    signing up for the platform.

    Responsibilities:
    - Validate email uniqueness (prevent duplicate registrations)
    - Secure password hashing (never store plain text passwords)
    - Generate cryptographically secure verification tokens
    - Create user entity with pending verification status
    - Queue verification email for asynchronous delivery
    - Return signup confirmation to client

    Dependencies (Injected):
    - IUserRepository: Database operations for user persistence
    - Email Service (PGMQ): Message queue for email delivery
    - PasswordHasher: Bcrypt password hashing (optional, uses default)

    Design Patterns:
    - Use Case Pattern: Business logic encapsulation
    - Dependency Injection: Testable, loosely coupled
    - Repository Pattern: Database abstraction
    - Value Objects: Email and Username domain primitives

    Thread Safety: Not thread-safe (use per-request instances)
    Transaction Semantics: Atomic (user creation + email queue or nothing)
    """

    # Token configuration constants
    TOKEN_LENGTH_BYTES = 32  # 32 bytes = 64 hex characters
    TOKEN_EXPIRY_HOURS = 24  # 24 hours for email verification

    def __init__(
        self,
        user_repository: IUserRepository,
        email_service,  # PGMQClient or EmailService interface
        password_hasher: Optional[PasswordHasher] = None
    ):
        """
        Initialize SignupUseCase with required dependencies.

        Args:
            user_repository: Repository implementing IUserRepository interface
                for user database operations (create, exists checks)
            email_service: Message queue service (PGMQClient) implementing
                enqueue(queue_name, message) method for email delivery
            password_hasher: Optional password hasher (creates default bcrypt
                hasher if None). Useful for testing with mock hashers.

        Example:
            >>> from app.infrastructure.persistence.user_repository_impl import UserRepository
            >>> from app.infrastructure.messaging.pgmq_client import PGMQClient
            >>>
            >>> repository = UserRepository(db_session)
            >>> pgmq = PGMQClient(host="localhost", database="unison")
            >>> use_case = SignupUseCase(repository, pgmq)
        """
        self._repository = user_repository
        self._email_service = email_service
        self._password_hasher = password_hasher or PasswordHasher()

    def execute(self, request: SignupRequestDTO) -> SignupResponseDTO:
        """
        Execute user signup workflow (main entry point).

        Orchestrates the complete signup process including validation, password
        hashing, token generation, user creation, and email queueing. This method
        is transactional - either all steps succeed or none do.

        Workflow Steps:
        1. Validate email uniqueness (check repository)
        2. Hash password using bcrypt (never store plain text)
        3. Generate secure verification token (32 bytes hex)
        4. Set token expiry (24 hours from now)
        5. Create username from email local part (sanitize dots)
        6. Create User entity with pending_verification status
        7. Persist user to database (transactional)
        8. Queue verification email via PGMQ (atomic with user creation)
        9. Return success response to client

        Args:
            request: SignupRequestDTO containing validated email and password.
                Email is already validated by Pydantic EmailStr.
                Password is already validated for complexity by DTO validator.

        Returns:
            SignupResponseDTO containing:
            - user_id: Newly created user's database ID
            - email: Registered email address (for confirmation)
            - message: Success message with next steps
            - onboarding_status: Current status (pending_verification)

        Raises:
            DomainValidationException: If email already registered in database.
                Error message is user-friendly and suggests alternatives.
            Exception: Database or PGMQ errors propagated to caller for
                proper transaction rollback handling.

        Example:
            >>> request = SignupRequestDTO(
            ...     email="newuser@example.com",
            ...     password="SecurePass123!"
            ... )
            >>> response = use_case.execute(request)
            >>> print(f"User {response.user_id} created")
            >>> print(response.message)  # "Verification email sent to..."

        Performance:
        - Database: 1 SELECT (exists check) + 1 INSERT (user creation)
        - PGMQ: 1 INSERT (email queue)
        - Password hashing: ~250ms (bcrypt cost factor 12)
        - Total: ~300-400ms typical

        Security Notes:
        - Password is hashed before database insert (never stored plain text)
        - Token is cryptographically secure (secrets module)
        - Email validation prevents injection attacks (Pydantic)
        - Transaction rollback on email queue failure ensures consistency
        """
        logger.info(f"Starting signup for email: {request.email}")

        # Step 1: Check if email already exists
        email_vo = Email(request.email)
        if self._repository.exists_by_email(email_vo):
            logger.warning(f"Signup failed: Email already registered - {request.email}")
            raise DomainValidationException(
                f"Email {request.email} is already registered. Please login or use password reset."
            )

        # Step 2: Hash password (security requirement - never store plain text)
        hashed_password = self._password_hasher.hash(request.password)
        logger.debug("Password hashed successfully")

        # Step 3: Generate secure random verification token (32 bytes = 64 hex chars)
        # Using secrets module for cryptographically secure random generation
        verification_token = secrets.token_hex(self.TOKEN_LENGTH_BYTES)
        logger.debug(f"Generated verification token: {verification_token[:8]}...")

        # Step 4: Set token expiry (24 hours from now)
        token_expiry = datetime.utcnow() + timedelta(hours=self.TOKEN_EXPIRY_HOURS)
        logger.debug(f"Token expiry set to: {token_expiry}")

        # Step 5: Generate username from email local part
        # Sanitize username: replace dots and invalid chars with underscores
        # to comply with Username value object validation rules
        username_str = self._generate_username_from_email(request.email)
        username_vo = Username(username_str)

        # Step 6: Create user entity with onboarding_status='pending_verification'
        user = User(
            id=None,  # Database will assign ID
            email=email_vo,
            username=username_vo,
            hashed_password=hashed_password,
            organization_id=None,  # Set later during org setup
            plant_id=None,  # Set later during plant creation
            is_active=False,  # Inactive until email verified
            is_superuser=False,
            onboarding_status='pending_verification',
            verification_token=verification_token,
            verification_token_expires_at=token_expiry,
            onboarding_completed_at=None
        )

        # Step 7: Save user to database (transaction begins)
        try:
            created_user = self._repository.create(user)
            logger.info(f"User created with ID: {created_user.id}")

            # Step 8: Queue verification email via PGMQ
            self._queue_verification_email(
                user_id=created_user.id,
                email=request.email,
                token=verification_token
            )
            logger.info(f"Verification email queued for user {created_user.id}")

        except Exception as e:
            # Rollback happens automatically via database transaction
            logger.error(f"Signup failed for {request.email}: {str(e)}")
            raise

        # Step 9: Return success response
        return SignupResponseDTO(
            user_id=created_user.id,
            email=request.email,
            message=f"Verification email sent to {request.email}. Please check your inbox and verify within 24 hours.",
            onboarding_status="pending_verification"
        )

    def _generate_username_from_email(self, email: str) -> str:
        """
        Generate valid username from email local part.

        Sanitizes email local part to create a valid username that complies
        with Username value object validation rules (alphanumeric, hyphens,
        underscores only).

        Args:
            email: Email address (e.g., "john.doe@example.com")

        Returns:
            Sanitized username (e.g., "john_doe")

        Example:
            >>> use_case._generate_username_from_email("john.doe@example.com")
            'john_doe'
            >>> use_case._generate_username_from_email("user-123@test.com")
            'user-123'
        """
        local_part = email.split('@')[0]
        # Replace dots with underscores (dots not allowed in Username)
        sanitized = local_part.replace('.', '_')
        logger.debug(f"Generated username '{sanitized}' from email '{email}'")
        return sanitized

    def _queue_verification_email(self, user_id: int, email: str, token: str) -> None:
        """
        Queue verification email via PGMQ for asynchronous delivery.

        Enqueues a message to the 'email_verification' queue containing user
        details and verification token. A background worker will process this
        message and send the actual email.

        Message Structure:
        - type: Message type identifier for worker routing
        - user_id: User ID for tracking and logging
        - to_email: Recipient email address
        - token: Verification token (64 hex characters)
        - template: Email template name for rendering
        - created_at: ISO timestamp for message age tracking

        Args:
            user_id: Database ID of newly created user
            email: User's email address for delivery
            token: Email verification token (32 bytes hex)

        Returns:
            None (message ID logged but not returned)

        Raises:
            Exception: If PGMQ enqueue operation fails. Caller should
                handle this by rolling back the user creation transaction
                to maintain consistency.

        Queue Behavior:
        - Queue: 'email_verification'
        - Visibility timeout: 30 seconds (configurable in PGMQ)
        - Retry count: 3 attempts (configured in PGMQ client)
        - DLQ: Failed messages moved to 'email_verification_dlq'

        Example:
            >>> use_case._queue_verification_email(
            ...     user_id=123,
            ...     email="user@example.com",
            ...     token="abc123def456..."
            ... )
            # Message queued with ID 456 (logged)
        """
        message = {
            "type": "email_verification",
            "user_id": user_id,
            "to_email": email,
            "token": token,
            "template": "verify_email",
            "created_at": datetime.utcnow().isoformat()
        }

        # Enqueue message to 'email_verification' queue
        # Worker will pick this up and send the email asynchronously
        msg_id = self._email_service.enqueue("email_verification", message)
        logger.debug(f"Queued email verification message {msg_id} for user {user_id}")
