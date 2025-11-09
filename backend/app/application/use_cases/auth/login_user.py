from passlib.context import CryptContext
from app.domain.entities.user import User
from app.domain.entities.token import Token
from app.domain.value_objects.email import Email
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions import EntityNotFoundException, DomainValidationException
from app.infrastructure.security.jwt_handler import JWTHandler
from datetime import datetime, timedelta


class LoginUserUseCase:
    """Use Case: User Login

    Single Responsibility: Authenticate user and generate tokens.
    """

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._jwt_handler = JWTHandler()

    def execute(self, email: str, password: str) -> Token:
        """Execute user login"""
        email_vo = Email(email)

        # Get user
        user = self._repository.get_by_email(email_vo)
        if not user:
            raise EntityNotFoundException("Invalid credentials")

        # Verify password
        if not self._verify_password(password, user.hashed_password):
            raise DomainValidationException("Invalid credentials")

        # Check if user is active
        if not user.is_active:
            raise DomainValidationException("User account is inactive")

        # Generate tokens with tenant context for RLS enforcement
        token_data = {
            "sub": str(user.id),
            "email": user.email.value,
            "username": user.username.value,
            "is_superuser": user.is_superuser,
            "organization_id": user.organization_id,
            "plant_id": user.plant_id
        }

        access_token = self._jwt_handler.create_access_token(token_data)
        refresh_token = self._jwt_handler.create_refresh_token(token_data)

        expires_at = datetime.utcnow() + timedelta(
            minutes=self._jwt_handler.access_token_expire_minutes
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            organization_id=user.organization_id,
            plant_id=user.plant_id
        )

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self._pwd_context.verify(plain_password, hashed_password)
