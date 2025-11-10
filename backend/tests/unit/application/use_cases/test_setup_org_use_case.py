"""
Unit tests for SetupOrgUseCase (TDD - RED phase)

Tests for organization setup functionality:
- Successful organization creation
- Slug generation from organization name
- Slug uniqueness handling (append -2, -3 if duplicate)
- User verification requirement (email_verified or phone_verified)
- Organization linked to user
- Onboarding status updated to 'org_setup'
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from app.application.use_cases.onboarding.setup_org_use_case import SetupOrgUseCase
from app.application.dtos.onboarding_dto import SetupOrgRequestDTO, SetupOrgResponseDTO
from app.domain.entities.user import User
from app.domain.entities.organization import Organization
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.exceptions.domain_exception import DomainValidationException


class TestSetupOrgUseCase:
    """Test suite for SetupOrgUseCase following TDD RED-GREEN-REFACTOR"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing"""
        return Mock()

    @pytest.fixture
    def mock_org_repository(self):
        """Mock organization repository for testing"""
        return Mock()

    @pytest.fixture
    def setup_org_use_case(self, mock_user_repository, mock_org_repository):
        """Create SetupOrgUseCase instance with mocks"""
        return SetupOrgUseCase(
            user_repository=mock_user_repository,
            organization_repository=mock_org_repository
        )

    @pytest.fixture
    def verified_user(self):
        """Create a verified user for testing"""
        return User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="email_verified",
            is_active=True
        )

    def test_successful_organization_creation(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Successful organization creation

        Given: Verified user with valid organization name
        When: User creates organization
        Then: Organization is created with correct details
        And: User is linked to organization
        And: Onboarding status updated to 'org_setup'
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Corporation")

        mock_user_repository.get_by_id.return_value = verified_user

        # Mock organization creation
        created_org = Organization(
            id=456,
            org_code="acme-corporation",
            org_name="Acme Corporation",
            subdomain="acme-corporation",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org
        mock_org_repository.get_by_slug.return_value = None  # No duplicate

        mock_user_repository.update.return_value = verified_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        assert isinstance(response, SetupOrgResponseDTO)
        assert response.organization_id == 456
        assert response.name == "Acme Corporation"
        assert response.slug == "acme-corporation"

        # Verify organization was created
        mock_org_repository.create.assert_called_once()

        # Verify user was updated with organization link
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.organization_id == 456
        assert update_call.onboarding_status == "org_setup"

    def test_slug_generation_converts_spaces_to_hyphens(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Slug generation converts spaces to hyphens

        Given: Organization name with spaces
        When: Organization is created
        Then: Slug is lowercase with hyphens instead of spaces
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Manufacturing Corp")

        mock_user_repository.get_by_id.return_value = verified_user
        mock_org_repository.get_by_slug.return_value = None

        created_org = Organization(
            id=456,
            org_code="acme-mfg-corp",
            org_name="Acme Manufacturing Corp",
            subdomain="acme-mfg-corp",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        assert response.slug == "acme-mfg-corp"

    def test_slug_generation_removes_special_characters(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Slug generation removes non-alphanumeric characters

        Given: Organization name with special characters
        When: Organization is created
        Then: Slug contains only lowercase alphanumeric and hyphens
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Corp. & Co.!")

        mock_user_repository.get_by_id.return_value = verified_user
        mock_org_repository.get_by_slug.return_value = None

        created_org = Organization(
            id=456,
            org_code="acme-corp-co",
            org_name="Acme Corp. & Co.!",
            subdomain="acme-corp-co",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        assert response.slug == "acme-corp-co"
        assert response.slug.replace('-', '').isalnum()

    def test_slug_uniqueness_appends_number_if_duplicate(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Slug uniqueness appends -2 if duplicate exists

        Given: Organization name that generates duplicate slug
        When: Organization is created
        Then: Slug has -2 appended to ensure uniqueness
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Corporation")

        mock_user_repository.get_by_id.return_value = verified_user

        # First call returns existing org, second returns None (unique)
        mock_org_repository.get_by_slug.side_effect = [
            Organization(id=999, org_code="acme-corporation", org_name="Existing Acme",
                        subdomain="acme-corporation", is_active=True, created_at=datetime.utcnow()),
            None  # acme-corporation-2 is available
        ]

        created_org = Organization(
            id=456,
            org_code="acme-corporation-2",
            org_name="Acme Corporation",
            subdomain="acme-corporation-2",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        assert response.slug == "acme-corporation-2"
        assert mock_org_repository.get_by_slug.call_count == 2

    def test_unverified_user_raises_domain_validation_exception(
        self, setup_org_use_case, mock_user_repository, mock_org_repository
    ):
        """
        Test: Unverified user cannot create organization

        Given: User with onboarding_status='pending_verification'
        When: User attempts to create organization
        Then: DomainValidationException is raised
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Corporation")

        unverified_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="pending_verification",
            is_active=False
        )
        mock_user_repository.get_by_id.return_value = unverified_user

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            setup_org_use_case.execute(request, user_id=1)

        assert "verify" in str(exc_info.value).lower()

    def test_phone_verified_user_can_create_organization(
        self, setup_org_use_case, mock_user_repository, mock_org_repository
    ):
        """
        Test: Phone verified user can create organization

        Given: User with onboarding_status='phone_verified'
        When: User creates organization
        Then: Organization is created successfully
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Corporation")

        phone_verified_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            onboarding_status="phone_verified",
            is_active=True
        )
        mock_user_repository.get_by_id.return_value = phone_verified_user
        mock_org_repository.get_by_slug.return_value = None

        created_org = Organization(
            id=456,
            org_code="acme-corporation",
            org_name="Acme Corporation",
            subdomain="acme-corporation",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        assert response.organization_id == 456
        assert response.name == "Acme Corporation"

    def test_organization_linked_to_user(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Organization is linked to user via user.organization_id

        Given: Verified user creates organization
        When: Organization is created
        Then: User.organization_id is set to created organization ID
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Corporation")

        mock_user_repository.get_by_id.return_value = verified_user
        mock_org_repository.get_by_slug.return_value = None

        created_org = Organization(
            id=456,
            org_code="acme-corporation",
            org_name="Acme Corporation",
            subdomain="acme-corporation",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        setup_org_use_case.execute(request, user_id=1)

        # Assert
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.organization_id == 456

    def test_onboarding_status_updated_to_org_setup(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Onboarding status updated to 'org_setup' after organization creation

        Given: Verified user creates organization
        When: Organization is created successfully
        Then: User.onboarding_status is updated to 'org_setup'
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme Corporation")

        mock_user_repository.get_by_id.return_value = verified_user
        mock_org_repository.get_by_slug.return_value = None

        created_org = Organization(
            id=456,
            org_code="acme-corporation",
            org_name="Acme Corporation",
            subdomain="acme-corporation",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_status == "org_setup"

    def test_slug_removes_consecutive_hyphens(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Slug generation removes consecutive hyphens

        Given: Organization name that generates consecutive hyphens
        When: Organization is created
        Then: Consecutive hyphens are replaced with single hyphen
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="Acme   Corp")

        mock_user_repository.get_by_id.return_value = verified_user
        mock_org_repository.get_by_slug.return_value = None

        created_org = Organization(
            id=456,
            org_code="acme-corp",
            org_name="Acme   Corp",
            subdomain="acme-corp",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        assert response.slug == "acme-corp"
        assert "--" not in response.slug

    def test_slug_strips_leading_trailing_hyphens(
        self, setup_org_use_case, mock_user_repository, mock_org_repository, verified_user
    ):
        """
        Test: Slug generation strips leading and trailing hyphens

        Given: Organization name that generates leading/trailing hyphens
        When: Organization is created
        Then: Leading and trailing hyphens are removed
        """
        # Arrange
        request = SetupOrgRequestDTO(organization_name="!Acme Corp!")

        mock_user_repository.get_by_id.return_value = verified_user
        mock_org_repository.get_by_slug.return_value = None

        created_org = Organization(
            id=456,
            org_code="acme-corp",
            org_name="!Acme Corp!",
            subdomain="acme-corp",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_org_repository.create.return_value = created_org

        updated_user = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.update.return_value = updated_user

        # Act
        response = setup_org_use_case.execute(request, user_id=1)

        # Assert
        assert not response.slug.startswith('-')
        assert not response.slug.endswith('-')
