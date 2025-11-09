from datetime import datetime
from typing import Optional
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username


class User:
    """Domain Entity: User

    Represents a user in the domain model.
    Contains business logic and domain rules.
    """

    def __init__(
        self,
        id: Optional[int],
        email: Email,
        username: Username,
        hashed_password: str,
        organization_id: Optional[int] = None,
        plant_id: Optional[int] = None,
        is_active: bool = True,
        is_superuser: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = id
        self._email = email
        self._username = username
        self._hashed_password = hashed_password
        self._organization_id = organization_id
        self._plant_id = plant_id
        self._is_active = is_active
        self._is_superuser = is_superuser
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def email(self) -> Email:
        return self._email

    @property
    def username(self) -> Username:
        return self._username

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def is_superuser(self) -> bool:
        return self._is_superuser

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._updated_at

    @property
    def organization_id(self) -> Optional[int]:
        return self._organization_id

    @property
    def plant_id(self) -> Optional[int]:
        return self._plant_id

    def activate(self) -> None:
        """Business logic: Activate user account"""
        self._is_active = True
        self._update_timestamp()

    def deactivate(self) -> None:
        """Business logic: Deactivate user account"""
        self._is_active = False
        self._update_timestamp()

    def change_email(self, new_email: Email) -> None:
        """Business logic: Change user email"""
        self._email = new_email
        self._update_timestamp()

    def change_password(self, new_hashed_password: str) -> None:
        """Business logic: Change user password"""
        self._hashed_password = new_hashed_password
        self._update_timestamp()

    def _update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self._updated_at = datetime.utcnow()
