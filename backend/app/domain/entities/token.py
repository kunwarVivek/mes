from datetime import datetime
from typing import Optional


class Token:
    """Domain Entity: Authentication Token

    Represents an access/refresh token pair in the domain.
    """

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_type: str = "bearer",
        expires_at: Optional[datetime] = None
    ):
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_type = token_type
        self._expires_at = expires_at

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def refresh_token(self) -> Optional[str]:
        return self._refresh_token

    @property
    def token_type(self) -> str:
        return self._token_type

    @property
    def expires_at(self) -> Optional[datetime]:
        return self._expires_at

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self._expires_at:
            return False
        return datetime.utcnow() > self._expires_at
