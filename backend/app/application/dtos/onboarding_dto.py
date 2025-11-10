"""
Data Transfer Objects (DTOs) for Self-Service Onboarding API.

Pydantic v2 schemas for request/response validation in the onboarding flow:
- User signup and email verification
- Organization setup
- Plant creation
- Team invitation
- Onboarding progress tracking
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python < 3.9 fallback


class TeamRole(str, Enum):
    """Valid team member roles for invitations."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    CUSTOM = "custom"  # For custom role definitions


class SignupRequestDTO(BaseModel):
    """DTO for user signup request.

    Validates email format and password strength requirements.
    """
    email: EmailStr = Field(
        description="User email address (must be valid format)",
        examples=["user@example.com"]
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password (min 8 chars, must contain uppercase, lowercase, digit, special char)",
        examples=["SecurePass123!"]
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    )


class SignupResponseDTO(BaseModel):
    """DTO for user signup response.

    Returns user ID and confirmation message after successful signup.
    """
    user_id: int = Field(
        description="Newly created user ID",
        examples=[123]
    )
    email: str = Field(
        description="Registered email address",
        examples=["user@example.com"]
    )
    message: str = Field(
        description="Confirmation message with next steps",
        examples=["Verification email sent"]
    )
    onboarding_status: str = Field(
        description="Current onboarding status",
        examples=["pending_verification"]
    )

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM model conversion
        json_schema_extra={
            "example": {
                "user_id": 123,
                "email": "user@example.com",
                "message": "Verification email sent to user@example.com",
                "onboarding_status": "pending_verification"
            }
        }
    )


class VerifyEmailRequestDTO(BaseModel):
    """DTO for email verification request.

    Validates verification token from email link.
    """
    token: str = Field(
        min_length=1,
        description="Email verification token",
        examples=["abc123def456"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "abc123def456"
            }
        }
    )


class VerifyEmailResponseDTO(BaseModel):
    """DTO for email verification response.

    Returns verification status and next onboarding step.
    """
    success: bool = Field(
        description="Verification success status",
        examples=[True]
    )
    message: str = Field(
        description="Verification result message",
        examples=["Email verified successfully"]
    )
    onboarding_status: str = Field(
        description="Current onboarding status",
        examples=["email_verified"]
    )

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM model conversion
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Email verified successfully",
                "onboarding_status": "email_verified"
            }
        }
    )


class PhoneVerifyRequestDTO(BaseModel):
    """DTO for phone number verification request.

    Alternative to email verification for users preferring SMS.
    """
    phone_number: str = Field(
        pattern=r'^\+[1-9]\d{1,14}$',
        description="Phone number in E.164 format (e.g., +12025551234)",
        examples=["+12025551234"]
    )

    @field_validator('phone_number')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """Validate phone number is in E.164 format."""
        if not v.startswith('+'):
            raise ValueError('Phone number must start with + (E.164 format)')
        if len(v) < 8 or len(v) > 16:
            raise ValueError('Phone number must be 8-16 characters including +')
        if not v[1:].isdigit():
            raise ValueError('Phone number must contain only digits after +')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone_number": "+12025551234"
            }
        }
    )


class PhoneVerifyCodeRequestDTO(BaseModel):
    """DTO for phone verification code submission.

    User submits code received via SMS.
    """
    phone_number: str = Field(
        pattern=r'^\+[1-9]\d{1,14}$',
        description="Phone number that received the code",
        examples=["+12025551234"]
    )
    code: str = Field(
        min_length=4,
        max_length=8,
        pattern=r'^\d+$',
        description="Numeric verification code from SMS",
        examples=["123456"]
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone_number": "+12025551234",
                "code": "123456"
            }
        }
    )


class PhoneVerifyResponseDTO(BaseModel):
    """DTO for phone verification response.

    Returns verification status and next onboarding step.
    """
    success: bool = Field(
        description="Verification success status",
        examples=[True]
    )
    message: str = Field(
        description="Verification result message",
        examples=["Phone verified successfully"]
    )
    onboarding_status: str = Field(
        description="Current onboarding status",
        examples=["phone_verified"]
    )

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM model conversion
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Phone verified successfully",
                "onboarding_status": "phone_verified"
            }
        }
    )


class SetupOrgRequestDTO(BaseModel):
    """DTO for organization setup request.

    Validates organization name and prepares for slug generation.
    """
    organization_name: str = Field(
        min_length=1,
        max_length=200,
        description="Organization name (will be used to generate slug)",
        examples=["Acme Corporation"]
    )

    @field_validator('organization_name')
    @classmethod
    def reject_html_tags(cls, v: str) -> str:
        """Reject organization names containing HTML tags (XSS protection)."""
        if '<' in v or '>' in v:
            raise ValueError('Organization name cannot contain HTML tags')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "organization_name": "Acme Corporation"
            }
        }
    )


class SetupOrgResponseDTO(BaseModel):
    """DTO for organization setup response.

    Returns organization details including auto-generated slug.
    """
    organization_id: int = Field(
        description="Newly created organization ID",
        examples=[456]
    )
    name: str = Field(
        description="Organization name",
        examples=["Acme Corporation"]
    )
    slug: str = Field(
        pattern=r'^[a-z0-9-]+$',
        description="Auto-generated organization slug (URL-safe, lowercase alphanumeric with hyphens)",
        examples=["acme-corporation"]
    )
    created_at: datetime = Field(
        description="Organization creation timestamp",
        examples=["2025-01-15T10:30:00Z"]
    )

    @field_validator('slug')
    @classmethod
    def validate_slug_format(cls, v: str) -> str:
        """Validate slug is URL-safe (matches subdomain validation pattern)."""
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('slug must be lowercase alphanumeric with hyphens only')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('slug cannot start or end with hyphen')
        if '--' in v:
            raise ValueError('slug cannot contain consecutive hyphens')
        return v

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM model conversion
        json_schema_extra={
            "example": {
                "organization_id": 456,
                "name": "Acme Corporation",
                "slug": "acme-corporation",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
    )


class CreatePlantRequestDTO(BaseModel):
    """DTO for plant creation request.

    Validates plant details with optional address and timezone.
    """
    plant_name: str = Field(
        min_length=1,
        max_length=200,
        description="Plant name",
        examples=["Manufacturing Plant 1"]
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Plant address (optional)",
        examples=["123 Factory St, City, State"]
    )
    timezone: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Plant timezone (optional, IANA format)",
        examples=["America/New_York"]
    )

    @field_validator('plant_name')
    @classmethod
    def reject_html_tags_in_name(cls, v: str) -> str:
        """Reject plant names containing HTML tags (XSS protection)."""
        if '<' in v or '>' in v:
            raise ValueError('Plant name cannot contain HTML tags')
        return v

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        """Validate timezone is valid IANA timezone."""
        if v is None:
            return v
        try:
            # Validate against IANA timezone database
            ZoneInfo(v)
        except Exception:
            # Provide helpful error message
            raise ValueError(
                f'Invalid timezone "{v}". Must be IANA format (e.g., "America/New_York"). '
                f'See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones'
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plant_name": "Manufacturing Plant 1",
                "address": "123 Factory St, City, State",
                "timezone": "America/New_York"
            }
        }
    )


class CreatePlantResponseDTO(BaseModel):
    """DTO for plant creation response.

    Returns plant details after successful creation.
    """
    plant_id: int = Field(
        description="Newly created plant ID",
        examples=[789]
    )
    name: str = Field(
        description="Plant name",
        examples=["Manufacturing Plant 1"]
    )
    organization_id: int = Field(
        description="Organization ID (foreign key)",
        examples=[456]
    )
    created_at: datetime = Field(
        description="Plant creation timestamp",
        examples=["2025-01-15T11:00:00Z"]
    )

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM model conversion
        json_schema_extra={
            "example": {
                "plant_id": 789,
                "name": "Manufacturing Plant 1",
                "organization_id": 456,
                "created_at": "2025-01-15T11:00:00Z"
            }
        }
    )


class TeamInvitation(BaseModel):
    """Individual team invitation details."""
    email: EmailStr = Field(
        description="Invitee email address",
        examples=["user@example.com"]
    )
    role: TeamRole = Field(
        description="Invitee role (admin, operator, viewer, or custom)",
        examples=[TeamRole.ADMIN]
    )
    role_description: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Custom role description (required if role=custom)",
        examples=["Quality Control Manager"]
    )

    @model_validator(mode='after')
    def validate_custom_role_description(self):
        """Validate role_description is provided when role is CUSTOM."""
        if self.role == TeamRole.CUSTOM:
            if not self.role_description:
                raise ValueError('role_description is required when role is "custom"')
            if self.role_description and len(self.role_description.strip()) == 0:
                raise ValueError('role_description cannot be empty')
        return self


class InviteTeamRequestDTO(BaseModel):
    """DTO for team invitation request.

    Validates list of team member invitations.
    """
    invitations: List[TeamInvitation] = Field(
        min_length=1,
        description="List of team member invitations (at least 1 required)",
        examples=[
            [
                {"email": "user1@example.com", "role": "admin"},
                {"email": "user2@example.com", "role": "operator"}
            ]
        ]
    )

    @field_validator('invitations')
    @classmethod
    def validate_unique_emails(cls, v: List[TeamInvitation]) -> List[TeamInvitation]:
        """Ensure no duplicate emails in invitation list."""
        emails = [inv.email for inv in v]
        if len(emails) != len(set(emails)):
            raise ValueError('Duplicate emails found in invitation list')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invitations": [
                    {"email": "user1@example.com", "role": "admin"},
                    {"email": "user2@example.com", "role": "operator"}
                ]
            }
        }
    )


class SentInvitation(BaseModel):
    """Individual sent invitation details with expiration."""
    email: str = Field(
        description="Invitee email address",
        examples=["user@example.com"]
    )
    role: TeamRole = Field(
        description="Invitee role",
        examples=[TeamRole.ADMIN]
    )
    role_description: Optional[str] = Field(
        default=None,
        description="Custom role description (if role=custom)",
        examples=["Quality Control Manager"]
    )
    expires_at: datetime = Field(
        description="Invitation expiration timestamp",
        examples=["2025-01-22T10:30:00Z"]
    )


class InviteTeamResponseDTO(BaseModel):
    """DTO for team invitation response.

    Returns list of sent invitations with expiration details.
    """
    invitations_sent: List[SentInvitation] = Field(
        description="List of successfully sent invitations",
        examples=[
            [
                {
                    "email": "user1@example.com",
                    "role": "admin",
                    "expires_at": "2025-01-22T10:30:00Z"
                }
            ]
        ]
    )

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM model conversion
        json_schema_extra={
            "example": {
                "invitations_sent": [
                    {
                        "email": "user1@example.com",
                        "role": "admin",
                        "expires_at": "2025-01-22T10:30:00Z"
                    },
                    {
                        "email": "user2@example.com",
                        "role": "operator",
                        "expires_at": "2025-01-22T10:30:00Z"
                    }
                ]
            }
        }
    )


class OnboardingProgressResponseDTO(BaseModel):
    """DTO for onboarding progress tracking.

    Returns current onboarding status and progress details.
    """
    current_status: str = Field(
        description="Current onboarding status",
        examples=["organization_setup", "plant_creation", "team_invitation", "complete"]
    )
    completed_steps: List[str] = Field(
        description="List of completed onboarding steps",
        examples=[["signup", "email_verification", "organization_setup"]]
    )
    next_step: str = Field(
        description="Description of next onboarding step",
        examples=["Create your first plant"]
    )

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM model conversion
        json_schema_extra={
            "example": {
                "current_status": "organization_setup",
                "completed_steps": ["signup", "email_verification"],
                "next_step": "Create your first plant"
            }
        }
    )
