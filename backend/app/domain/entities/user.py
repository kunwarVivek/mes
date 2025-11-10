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
        updated_at: Optional[datetime] = None,
        onboarding_status: str = 'pending_verification',
        verification_token: Optional[str] = None,
        verification_token_expires_at: Optional[datetime] = None,
        onboarding_completed_at: Optional[datetime] = None,
        phone_number: Optional[str] = None,
        phone_verification_code: Optional[str] = None,
        phone_code_expires_at: Optional[datetime] = None
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
        self._onboarding_status = onboarding_status
        self._verification_token = verification_token
        self._verification_token_expires_at = verification_token_expires_at
        self._onboarding_completed_at = onboarding_completed_at
        self._phone_number = phone_number
        self._phone_verification_code = phone_verification_code
        self._phone_code_expires_at = phone_code_expires_at

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

    @property
    def onboarding_status(self) -> str:
        return self._onboarding_status

    @property
    def verification_token(self) -> Optional[str]:
        return self._verification_token

    @property
    def verification_token_expires_at(self) -> Optional[datetime]:
        return self._verification_token_expires_at

    @property
    def onboarding_completed_at(self) -> Optional[datetime]:
        return self._onboarding_completed_at

    @property
    def phone_number(self) -> Optional[str]:
        return self._phone_number

    @property
    def phone_verification_code(self) -> Optional[str]:
        return self._phone_verification_code

    @property
    def phone_code_expires_at(self) -> Optional[datetime]:
        return self._phone_code_expires_at

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

    def verify_email(self) -> None:
        """Business logic: Mark email as verified and activate user"""
        self._onboarding_status = 'email_verified'
        self._verification_token = None
        self._verification_token_expires_at = None
        self._is_active = True
        self._update_timestamp()

    def verify_phone(self) -> None:
        """Business logic: Mark phone as verified and activate user"""
        self._onboarding_status = 'phone_verified'
        self._phone_verification_code = None
        self._phone_code_expires_at = None
        self._is_active = True
        self._update_timestamp()

    def set_phone_verification_code(self, phone_number: str, code: str, expires_at: datetime) -> None:
        """Business logic: Set phone verification code for SMS verification"""
        self._phone_number = phone_number
        self._phone_verification_code = code
        self._phone_code_expires_at = expires_at
        self._update_timestamp()

    def is_token_expired(self) -> bool:
        """Check if verification token is expired"""
        if self._verification_token_expires_at is None:
            return True
        return datetime.utcnow() >= self._verification_token_expires_at

    def is_phone_code_expired(self) -> bool:
        """Check if phone verification code is expired"""
        if self._phone_code_expires_at is None:
            return True
        return datetime.utcnow() >= self._phone_code_expires_at

    def link_to_organization(self, organization_id: int) -> None:
        """Business logic: Link user to organization and update onboarding status"""
        self._organization_id = organization_id
        self._onboarding_status = 'org_setup'
        self._update_timestamp()

    def link_to_plant(self, plant_id: int) -> None:
        """Business logic: Link user to plant and update onboarding status"""
        self._plant_id = plant_id
        self._onboarding_status = 'plant_created'
        self._update_timestamp()

    def complete_onboarding(self) -> None:
        """Business logic: Mark onboarding as completed"""
        self._onboarding_status = 'completed'
        self._onboarding_completed_at = datetime.utcnow()
        self._update_timestamp()

    def _update_timestamp(self) -> None:
        """Update the last modified timestamp"""
        self._updated_at = datetime.utcnow()
