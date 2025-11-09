from datetime import datetime
from typing import Optional


class Token:
    """Domain Entity: Authentication Token

    Represents an access/refresh token pair with tenant context in the domain.
    """

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_type: str = "bearer",
        expires_at: Optional[datetime] = None,
        organization_id: Optional[int] = None,
        plant_id: Optional[int] = None
    ):
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_type = token_type
        self._expires_at = expires_at
        self._organization_id = organization_id
        self._plant_id = plant_id

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

    @property
    def organization_id(self) -> Optional[int]:
        return self._organization_id

    @property
    def plant_id(self) -> Optional[int]:
        return self._plant_id

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self._expires_at:
            return False
        return datetime.utcnow() > self._expires_at
