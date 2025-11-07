from app.domain.entities.token import Token
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions import DomainValidationException
from app.infrastructure.security.jwt_handler import JWTHandler
from datetime import datetime, timedelta


class RefreshTokenUseCase:
    """Use Case: Refresh Access Token

    Single Responsibility: Generate new access token from refresh token.
    """

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository
        self._jwt_handler = JWTHandler()

    def execute(self, refresh_token: str) -> Token:
        """Execute token refresh"""
        try:
            # Decode refresh token
            payload = self._jwt_handler.decode_token(refresh_token)

            # Verify token type
            if payload.get("type") != "refresh":
                raise DomainValidationException("Invalid token type")

            # Get user
            user_id = int(payload.get("sub"))
            user = self._repository.get_by_id(user_id)

            if not user or not user.is_active:
                raise DomainValidationException("User not found or inactive")

            # Generate new tokens
            token_data = {
                "sub": str(user.id),
                "email": user.email.value,
                "username": user.username.value,
                "is_superuser": user.is_superuser
            }

            access_token = self._jwt_handler.create_access_token(token_data)
            new_refresh_token = self._jwt_handler.create_refresh_token(token_data)

            expires_at = datetime.utcnow() + timedelta(
                minutes=self._jwt_handler.access_token_expire_minutes
            )

            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_at=expires_at
            )

        except ValueError as e:
            raise DomainValidationException(str(e))
