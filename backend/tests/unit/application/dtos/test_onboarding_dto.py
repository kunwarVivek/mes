"""
Unit tests for Onboarding DTOs.

Tests validation, transformations, and edge cases for self-service onboarding flow.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.application.dtos.onboarding_dto import (
    SignupRequestDTO,
    SignupResponseDTO,
    VerifyEmailRequestDTO,
    VerifyEmailResponseDTO,
    PhoneVerifyRequestDTO,
    PhoneVerifyCodeRequestDTO,
    PhoneVerifyResponseDTO,
    SetupOrgRequestDTO,
    SetupOrgResponseDTO,
    CreatePlantRequestDTO,
    CreatePlantResponseDTO,
    InviteTeamRequestDTO,
    InviteTeamResponseDTO,
    OnboardingProgressResponseDTO,
    TeamRole,
)


class TestSignupRequestDTO:
    """Test SignupRequestDTO validation"""

    def test_valid_signup_request(self):
        """Test valid signup request with proper email and password"""
        dto = SignupRequestDTO(
            email="test@example.com",
            password="SecurePass123!"
        )
        assert dto.email == "test@example.com"
        assert dto.password == "SecurePass123!"

    def test_invalid_email_format(self):
        """Test signup request with invalid email format"""
        with pytest.raises(ValidationError) as exc_info:
            SignupRequestDTO(
                email="invalid-email",
                password="SecurePass123!"
            )
        assert "email" in str(exc_info.value).lower()

    def test_password_too_short(self):
        """Test signup request with password less than 8 characters"""
        with pytest.raises(ValidationError) as exc_info:
            SignupRequestDTO(
                email="test@example.com",
                password="short"
            )
        assert "password" in str(exc_info.value).lower()

    def test_missing_required_fields(self):
        """Test signup request with missing required fields"""
        with pytest.raises(ValidationError):
            SignupRequestDTO(email="test@example.com")

    def test_empty_email(self):
        """Test signup request with empty email"""
        with pytest.raises(ValidationError):
            SignupRequestDTO(email="", password="SecurePass123!")


class TestSignupResponseDTO:
    """Test SignupResponseDTO structure"""

    def test_valid_signup_response(self):
        """Test valid signup response"""
        dto = SignupResponseDTO(
            user_id=123,
            email="test@example.com",
            message="Verification email sent"
        )
        assert dto.user_id == 123
        assert dto.email == "test@example.com"
        assert dto.message == "Verification email sent"


class TestVerifyEmailRequestDTO:
    """Test VerifyEmailRequestDTO validation"""

    def test_valid_verify_email_request(self):
        """Test valid email verification request"""
        dto = VerifyEmailRequestDTO(token="abc123token")
        assert dto.token == "abc123token"

    def test_missing_token(self):
        """Test verification request with missing token"""
        with pytest.raises(ValidationError):
            VerifyEmailRequestDTO()

    def test_empty_token(self):
        """Test verification request with empty token"""
        with pytest.raises(ValidationError):
            VerifyEmailRequestDTO(token="")


class TestVerifyEmailResponseDTO:
    """Test VerifyEmailResponseDTO structure"""

    def test_valid_verify_email_response(self):
        """Test valid email verification response"""
        dto = VerifyEmailResponseDTO(
            success=True,
            message="Email verified successfully",
            onboarding_status="email_verified"
        )
        assert dto.success is True
        assert dto.message == "Email verified successfully"
        assert dto.onboarding_status == "email_verified"


class TestSetupOrgRequestDTO:
    """Test SetupOrgRequestDTO validation"""

    def test_valid_setup_org_request(self):
        """Test valid organization setup request"""
        dto = SetupOrgRequestDTO(organization_name="Acme Corporation")
        assert dto.organization_name == "Acme Corporation"

    def test_missing_organization_name(self):
        """Test organization setup with missing name"""
        with pytest.raises(ValidationError):
            SetupOrgRequestDTO()

    def test_empty_organization_name(self):
        """Test organization setup with empty name"""
        with pytest.raises(ValidationError):
            SetupOrgRequestDTO(organization_name="")

    def test_organization_name_too_long(self):
        """Test organization setup with name exceeding max length"""
        with pytest.raises(ValidationError):
            SetupOrgRequestDTO(organization_name="A" * 201)


class TestSetupOrgResponseDTO:
    """Test SetupOrgResponseDTO structure"""

    def test_valid_setup_org_response(self):
        """Test valid organization setup response"""
        now = datetime.now()
        dto = SetupOrgResponseDTO(
            organization_id=456,
            name="Acme Corporation",
            slug="acme-corporation",
            created_at=now
        )
        assert dto.organization_id == 456
        assert dto.name == "Acme Corporation"
        assert dto.slug == "acme-corporation"
        assert dto.created_at == now


class TestCreatePlantRequestDTO:
    """Test CreatePlantRequestDTO validation"""

    def test_valid_create_plant_request(self):
        """Test valid plant creation request with all fields"""
        dto = CreatePlantRequestDTO(
            plant_name="Manufacturing Plant 1",
            address="123 Factory St, City, State",
            timezone="America/New_York"
        )
        assert dto.plant_name == "Manufacturing Plant 1"
        assert dto.address == "123 Factory St, City, State"
        assert dto.timezone == "America/New_York"

    def test_create_plant_without_optional_fields(self):
        """Test plant creation with only required fields"""
        dto = CreatePlantRequestDTO(plant_name="Plant 1")
        assert dto.plant_name == "Plant 1"
        assert dto.address is None
        assert dto.timezone is None

    def test_missing_plant_name(self):
        """Test plant creation with missing name"""
        with pytest.raises(ValidationError):
            CreatePlantRequestDTO()

    def test_empty_plant_name(self):
        """Test plant creation with empty name"""
        with pytest.raises(ValidationError):
            CreatePlantRequestDTO(plant_name="")


class TestCreatePlantResponseDTO:
    """Test CreatePlantResponseDTO structure"""

    def test_valid_create_plant_response(self):
        """Test valid plant creation response"""
        now = datetime.now()
        dto = CreatePlantResponseDTO(
            plant_id=789,
            name="Manufacturing Plant 1",
            organization_id=456,
            created_at=now
        )
        assert dto.plant_id == 789
        assert dto.name == "Manufacturing Plant 1"
        assert dto.organization_id == 456
        assert dto.created_at == now


class TestInviteTeamRequestDTO:
    """Test InviteTeamRequestDTO validation"""

    def test_valid_invite_team_request(self):
        """Test valid team invitation request"""
        dto = InviteTeamRequestDTO(
            invitations=[
                {"email": "user1@example.com", "role": "admin"},
                {"email": "user2@example.com", "role": "operator"}
            ]
        )
        assert len(dto.invitations) == 2
        assert dto.invitations[0].email == "user1@example.com"
        assert dto.invitations[0].role == "admin"

    def test_empty_invitations_list(self):
        """Test team invitation with empty list"""
        with pytest.raises(ValidationError):
            InviteTeamRequestDTO(invitations=[])

    def test_invalid_email_in_invitation(self):
        """Test team invitation with invalid email format"""
        with pytest.raises(ValidationError):
            InviteTeamRequestDTO(
                invitations=[{"email": "invalid-email", "role": "admin"}]
            )

    def test_missing_role_in_invitation(self):
        """Test team invitation with missing role"""
        with pytest.raises(ValidationError):
            InviteTeamRequestDTO(
                invitations=[{"email": "user@example.com"}]
            )


class TestInviteTeamResponseDTO:
    """Test InviteTeamResponseDTO structure"""

    def test_valid_invite_team_response(self):
        """Test valid team invitation response"""
        expires_at = datetime.now()
        dto = InviteTeamResponseDTO(
            invitations_sent=[
                {
                    "email": "user1@example.com",
                    "role": "admin",
                    "expires_at": expires_at
                }
            ]
        )
        assert len(dto.invitations_sent) == 1
        assert dto.invitations_sent[0].email == "user1@example.com"


class TestOnboardingProgressResponseDTO:
    """Test OnboardingProgressResponseDTO structure"""

    def test_valid_onboarding_progress_response(self):
        """Test valid onboarding progress response"""
        dto = OnboardingProgressResponseDTO(
            current_status="organization_setup",
            completed_steps=["signup", "email_verification"],
            next_step="Create your first plant"
        )
        assert dto.current_status == "organization_setup"
        assert len(dto.completed_steps) == 2
        assert dto.next_step == "Create your first plant"

    def test_empty_completed_steps(self):
        """Test onboarding progress with no completed steps"""
        dto = OnboardingProgressResponseDTO(
            current_status="signup",
            completed_steps=[],
            next_step="Verify your email"
        )
        assert len(dto.completed_steps) == 0


class TestPasswordSecurity:
    """Test password complexity validation (security)"""

    @pytest.mark.parametrize("password,should_fail", [
        ("12345678", True),  # No uppercase, lowercase, special char
        ("password", True),  # Too short
        ("Password", True),  # No digit, special char
        ("Password1", True),  # No special char
        ("password1!", True),  # No uppercase
        ("PASSWORD1!", True),  # No lowercase
        ("Password!", True),  # No digit
        ("Password1!", False),  # Valid - all requirements met
        ("SecurePass123!", False),  # Valid
    ])
    def test_password_strength_validation(self, password, should_fail):
        """Test password strength requirements"""
        if should_fail:
            with pytest.raises(ValidationError) as exc_info:
                SignupRequestDTO(email="test@example.com", password=password)
            assert "password" in str(exc_info.value).lower()
        else:
            dto = SignupRequestDTO(email="test@example.com", password=password)
            assert dto.password == password

    def test_password_exactly_8_chars(self):
        """Test password at minimum boundary"""
        dto = SignupRequestDTO(email="test@example.com", password="Pass123!")
        assert len(dto.password) == 8

    def test_password_max_length(self):
        """Test password at maximum boundary"""
        long_password = "A" * 127 + "1!"  # 128 chars total with uppercase, digit, special
        with pytest.raises(ValidationError):
            SignupRequestDTO(email="test@example.com", password=long_password + "X")


class TestRoleValidation:
    """Test team role enumeration (security)"""

    def test_valid_roles(self):
        """Test valid team roles"""
        valid_roles = [TeamRole.ADMIN, TeamRole.OPERATOR, TeamRole.VIEWER]
        for role in valid_roles:
            dto = InviteTeamRequestDTO(
                invitations=[{"email": "user@example.com", "role": role.value}]
            )
            assert dto.invitations[0].role == role

    def test_invalid_role_rejected(self):
        """Test invalid role is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            InviteTeamRequestDTO(
                invitations=[{"email": "user@example.com", "role": "hacker"}]
            )
        assert "role" in str(exc_info.value).lower()

    def test_sql_injection_in_role(self):
        """Test SQL injection attempt in role is rejected"""
        with pytest.raises(ValidationError):
            InviteTeamRequestDTO(
                invitations=[{"email": "user@example.com", "role": "admin'; DROP TABLE users;--"}]
            )


class TestSlugValidation:
    """Test slug format validation (security - SQL injection, XSS)"""

    def test_valid_slug_formats(self):
        """Test valid slug formats"""
        valid_slugs = [
            "acme-corporation",
            "test-org-123",
            "company",
            "a-b-c-d-e",
            "org-2025"
        ]
        for slug in valid_slugs:
            dto = SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug=slug,
                created_at=datetime.now()
            )
            assert dto.slug == slug

    def test_slug_with_uppercase_rejected(self):
        """Test slug with uppercase letters is rejected"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="Acme-Corporation",
                created_at=datetime.now()
            )

    def test_slug_with_spaces_rejected(self):
        """Test slug with spaces is rejected"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="acme corporation",
                created_at=datetime.now()
            )

    def test_slug_with_special_chars_rejected(self):
        """Test slug with special characters is rejected"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="acme_corporation!",
                created_at=datetime.now()
            )

    def test_slug_sql_injection_attempt(self):
        """Test slug rejects SQL injection"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="acme'; DROP TABLE organizations;--",
                created_at=datetime.now()
            )

    def test_slug_xss_attempt(self):
        """Test slug rejects XSS"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="<script>alert('XSS')</script>",
                created_at=datetime.now()
            )

    def test_slug_starts_with_hyphen(self):
        """Test slug cannot start with hyphen"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="-acme",
                created_at=datetime.now()
            )

    def test_slug_ends_with_hyphen(self):
        """Test slug cannot end with hyphen"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="acme-",
                created_at=datetime.now()
            )

    def test_slug_consecutive_hyphens(self):
        """Test slug cannot have consecutive hyphens"""
        with pytest.raises(ValidationError):
            SetupOrgResponseDTO(
                organization_id=1,
                name="Test",
                slug="acme--corp",
                created_at=datetime.now()
            )


class TestTimezoneValidation:
    """Test timezone IANA format validation (security - runtime errors)"""

    @pytest.mark.parametrize("timezone", [
        "America/New_York",
        "Europe/London",
        "Asia/Tokyo",
        "UTC",
        "America/Los_Angeles",
        "Australia/Sydney"
    ])
    def test_valid_iana_timezones(self, timezone):
        """Test valid IANA timezones"""
        dto = CreatePlantRequestDTO(plant_name="Plant 1", timezone=timezone)
        assert dto.timezone == timezone

    @pytest.mark.parametrize("invalid_tz", [
        "UTC+5",  # Offset format, not IANA
        "New York",  # Spaces, not IANA
        "America/Invalid_City",  # Invalid city
        "Pacific/Fake_Zone"  # Non-existent zone
    ])
    def test_invalid_timezone_formats(self, invalid_tz):
        """Test invalid timezone formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            CreatePlantRequestDTO(plant_name="Plant 1", timezone=invalid_tz)
        assert "timezone" in str(exc_info.value).lower()

    def test_none_timezone_allowed(self):
        """Test None timezone is allowed (optional field)"""
        dto = CreatePlantRequestDTO(plant_name="Plant 1", timezone=None)
        assert dto.timezone is None


class TestXSSProtection:
    """Test HTML tag rejection (XSS protection)"""

    def test_organization_name_rejects_script_tag(self):
        """Test org name rejects script tags"""
        with pytest.raises(ValidationError) as exc_info:
            SetupOrgRequestDTO(organization_name="<script>alert('XSS')</script>")
        assert "html" in str(exc_info.value).lower()

    def test_organization_name_rejects_img_tag(self):
        """Test org name rejects img tags"""
        with pytest.raises(ValidationError):
            SetupOrgRequestDTO(organization_name="Acme <img src=x onerror=alert(1)>")

    def test_organization_name_rejects_any_html(self):
        """Test org name rejects any HTML tags"""
        with pytest.raises(ValidationError):
            SetupOrgRequestDTO(organization_name="<div>Test</div>")

    def test_plant_name_rejects_script_tag(self):
        """Test plant name rejects script tags"""
        with pytest.raises(ValidationError):
            CreatePlantRequestDTO(plant_name="<script>alert('XSS')</script>")

    def test_plant_name_rejects_img_tag(self):
        """Test plant name rejects img tags"""
        with pytest.raises(ValidationError):
            CreatePlantRequestDTO(plant_name="Plant <img src=x onerror=alert(1)>")

    def test_organization_name_allows_special_chars(self):
        """Test org name allows non-HTML special characters"""
        valid_names = [
            "Société Française",
            "日本株式会社",
            "Company & Co.",
            "Acme (USA)",
            "Test @ 2025"
        ]
        for name in valid_names:
            dto = SetupOrgRequestDTO(organization_name=name)
            assert dto.organization_name == name


class TestDuplicateEmailValidation:
    """Test duplicate email detection"""

    def test_duplicate_emails_in_invitations(self):
        """Test team invitation rejects duplicate emails"""
        with pytest.raises(ValidationError) as exc_info:
            InviteTeamRequestDTO(
                invitations=[
                    {"email": "user@example.com", "role": "admin"},
                    {"email": "user@example.com", "role": "operator"}
                ]
            )
        assert "duplicate" in str(exc_info.value).lower()

    def test_unique_emails_pass_validation(self):
        """Test team invitation with unique emails passes"""
        dto = InviteTeamRequestDTO(
            invitations=[
                {"email": "user1@example.com", "role": "admin"},
                {"email": "user2@example.com", "role": "operator"},
                {"email": "user3@example.com", "role": "viewer"}
            ]
        )
        assert len(dto.invitations) == 3


class TestPhoneVerification:
    """Test phone number verification DTOs"""

    @pytest.mark.parametrize("phone_number", [
        "+12025551234",  # US number
        "+442071234567",  # UK number
        "+81312345678",  # Japan number
        "+61212345678",  # Australia number
        "+33123456789",  # France number
    ])
    def test_valid_phone_numbers(self, phone_number):
        """Test valid E.164 phone numbers"""
        dto = PhoneVerifyRequestDTO(phone_number=phone_number)
        assert dto.phone_number == phone_number

    @pytest.mark.parametrize("invalid_phone", [
        "2025551234",  # Missing + prefix
        "+1 202 555 1234",  # Spaces
        "+1-202-555-1234",  # Hyphens
        "+1(202)5551234",  # Parentheses
        "001-202-555-1234",  # Invalid prefix
        "+1",  # Too short
        "+123456789012345678",  # Too long (>16 chars)
        "+1abc2345678",  # Contains letters
    ])
    def test_invalid_phone_formats(self, invalid_phone):
        """Test invalid phone number formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            PhoneVerifyRequestDTO(phone_number=invalid_phone)
        assert "phone" in str(exc_info.value).lower()

    def test_phone_verification_code_valid(self):
        """Test valid phone verification code submission"""
        dto = PhoneVerifyCodeRequestDTO(
            phone_number="+12025551234",
            code="123456"
        )
        assert dto.phone_number == "+12025551234"
        assert dto.code == "123456"

    @pytest.mark.parametrize("invalid_code", [
        "abc",  # Letters
        "12",  # Too short (min 4)
        "123456789",  # Too long (max 8)
        "12 34",  # Spaces
        "12-34",  # Hyphen
    ])
    def test_invalid_verification_codes(self, invalid_code):
        """Test invalid verification codes are rejected"""
        with pytest.raises(ValidationError):
            PhoneVerifyCodeRequestDTO(
                phone_number="+12025551234",
                code=invalid_code
            )

    def test_phone_verify_response(self):
        """Test phone verification response structure"""
        dto = PhoneVerifyResponseDTO(
            success=True,
            message="Phone verified successfully",
            onboarding_status="phone_verified"
        )
        assert dto.success is True
        assert dto.message == "Phone verified successfully"
        assert dto.onboarding_status == "phone_verified"


class TestCustomRoles:
    """Test custom role functionality"""

    def test_custom_role_with_description(self):
        """Test custom role requires role_description"""
        dto = InviteTeamRequestDTO(
            invitations=[
                {
                    "email": "user@example.com",
                    "role": "custom",
                    "role_description": "Quality Control Manager"
                }
            ]
        )
        assert dto.invitations[0].role == TeamRole.CUSTOM
        assert dto.invitations[0].role_description == "Quality Control Manager"

    def test_custom_role_without_description_fails(self):
        """Test custom role without role_description is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            InviteTeamRequestDTO(
                invitations=[
                    {
                        "email": "user@example.com",
                        "role": "custom"
                    }
                ]
            )
        assert "role_description" in str(exc_info.value).lower()

    def test_custom_role_with_empty_description_fails(self):
        """Test custom role with empty role_description is rejected"""
        with pytest.raises(ValidationError):
            InviteTeamRequestDTO(
                invitations=[
                    {
                        "email": "user@example.com",
                        "role": "custom",
                        "role_description": "   "
                    }
                ]
            )

    def test_standard_roles_dont_require_description(self):
        """Test standard roles (admin/operator/viewer) don't require role_description"""
        for role in ["admin", "operator", "viewer"]:
            dto = InviteTeamRequestDTO(
                invitations=[
                    {
                        "email": "user@example.com",
                        "role": role
                    }
                ]
            )
            assert dto.invitations[0].role_description is None

    def test_custom_role_description_max_length(self):
        """Test custom role description respects max length"""
        long_description = "A" * 200
        dto = InviteTeamRequestDTO(
            invitations=[
                {
                    "email": "user@example.com",
                    "role": "custom",
                    "role_description": long_description
                }
            ]
        )
        assert dto.invitations[0].role_description == long_description

        with pytest.raises(ValidationError):
            InviteTeamRequestDTO(
                invitations=[
                    {
                        "email": "user@example.com",
                        "role": "custom",
                        "role_description": "A" * 201
                    }
                ]
            )

    def test_all_team_roles_enum_values(self):
        """Test all TeamRole enum values"""
        assert TeamRole.ADMIN.value == "admin"
        assert TeamRole.OPERATOR.value == "operator"
        assert TeamRole.VIEWER.value == "viewer"
        assert TeamRole.CUSTOM.value == "custom"
        assert len(TeamRole) == 4
