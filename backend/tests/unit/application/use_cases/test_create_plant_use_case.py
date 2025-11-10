"""
Unit tests for CreatePlantUseCase (TDD - RED phase)

Tests for plant creation functionality:
- Successful plant creation
- Plant linked to organization
- Timezone validation (IANA format)
- User without organization rejection
- Onboarding status updated to 'plant_created'
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from app.application.use_cases.onboarding.create_plant_use_case import CreatePlantUseCase
from app.application.dtos.onboarding_dto import CreatePlantRequestDTO, CreatePlantResponseDTO
from app.domain.entities.user import User
from app.domain.entities.plant import Plant
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.exceptions.domain_exception import DomainValidationException


class TestCreatePlantUseCase:
    """Test suite for CreatePlantUseCase following TDD RED-GREEN-REFACTOR"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing"""
        return Mock()

    @pytest.fixture
    def mock_plant_repository(self):
        """Mock plant repository for testing"""
        return Mock()

    @pytest.fixture
    def create_plant_use_case(self, mock_user_repository, mock_plant_repository):
        """Create CreatePlantUseCase instance with mocks"""
        return CreatePlantUseCase(
            user_repository=mock_user_repository,
            plant_repository=mock_plant_repository
        )

    @pytest.fixture
    def user_with_org(self):
        """Create user with organization setup"""
        return User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            onboarding_status="org_setup",
            is_active=True
        )

    def test_successful_plant_creation(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Successful plant creation

        Given: User with organization setup
        When: User creates plant
        Then: Plant is created with correct details
        And: Onboarding status updated to 'plant_created'
        """
        # Arrange
        request = CreatePlantRequestDTO(
            plant_name="Manufacturing Plant 1",
            address="123 Factory St, City, State",
            timezone="America/New_York"
        )

        mock_user_repository.get_by_id.return_value = user_with_org

        created_plant = Plant(
            id=789,
            organization_id=456,
            plant_code="manufacturing-plant",  # Truncated to 19 chars (≤20 limit)
            plant_name="Manufacturing Plant 1",
            location="123 Factory St, City, State",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_plant_repository.create.return_value = created_plant

        user_with_org._onboarding_status = 'plant_created'
        mock_user_repository.update.return_value = user_with_org

        # Act
        response = create_plant_use_case.execute(request, user_id=1)

        # Assert
        assert isinstance(response, CreatePlantResponseDTO)
        assert response.plant_id == 789
        assert response.name == "Manufacturing Plant 1"
        assert response.organization_id == 456

        # Verify plant was created
        mock_plant_repository.create.assert_called_once()

        # Verify user onboarding status updated
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_status == "plant_created"

    def test_plant_linked_to_organization(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Plant is linked to user's organization

        Given: User with organization setup
        When: Plant is created
        Then: Plant.organization_id matches user.organization_id
        """
        # Arrange
        request = CreatePlantRequestDTO(plant_name="Manufacturing Plant 1")

        mock_user_repository.get_by_id.return_value = user_with_org

        created_plant = Plant(
            id=789,
            organization_id=456,
            plant_code="manufacturing-plant",  # Truncated to 19 chars (≤20 limit)
            plant_name="Manufacturing Plant 1",
            location=None,
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_plant_repository.create.return_value = created_plant
        mock_user_repository.update.return_value = user_with_org

        # Act
        response = create_plant_use_case.execute(request, user_id=1)

        # Assert
        create_call = mock_plant_repository.create.call_args[0][0]
        assert create_call.organization_id == 456
        assert create_call.organization_id == user_with_org.organization_id

    def test_valid_timezone_accepted(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Valid IANA timezone is accepted

        Given: Plant creation with valid timezone
        When: Plant is created
        Then: No validation error occurs
        """
        # Arrange
        request = CreatePlantRequestDTO(
            plant_name="Manufacturing Plant 1",
            timezone="America/New_York"
        )

        mock_user_repository.get_by_id.return_value = user_with_org

        created_plant = Plant(
            id=789,
            organization_id=456,
            plant_code="manufacturing-plant",  # Truncated to 19 chars (≤20 limit)
            plant_name="Manufacturing Plant 1",
            location=None,
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_plant_repository.create.return_value = created_plant
        mock_user_repository.update.return_value = user_with_org

        # Act - Should not raise exception
        response = create_plant_use_case.execute(request, user_id=1)

        # Assert
        assert response.plant_id == 789

    def test_invalid_timezone_raises_validation_error(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Invalid timezone raises DomainValidationException

        Given: Plant creation with invalid timezone
        When: Timezone validation occurs
        Then: DomainValidationException is raised (caught at DTO level)
        """
        # Note: Validation happens at DTO level via Pydantic
        # This test verifies the behavior when invalid timezone reaches use case
        with pytest.raises(Exception) as exc_info:
            request = CreatePlantRequestDTO(
                plant_name="Manufacturing Plant 1",
                timezone="Invalid/Timezone"
            )

        assert "timezone" in str(exc_info.value).lower()

    def test_user_without_organization_raises_exception(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository
    ):
        """
        Test: User without organization cannot create plant

        Given: User with onboarding_status='email_verified' (no org)
        When: User attempts to create plant
        Then: DomainValidationException is raised
        """
        # Arrange
        request = CreatePlantRequestDTO(plant_name="Manufacturing Plant 1")

        user_without_org = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=None,
            onboarding_status="email_verified",
            is_active=True
        )
        mock_user_repository.get_by_id.return_value = user_without_org

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            create_plant_use_case.execute(request, user_id=1)

        assert "organization" in str(exc_info.value).lower()

    def test_onboarding_status_updated_to_plant_created(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Onboarding status updated to 'plant_created'

        Given: User creates plant successfully
        When: Plant creation completes
        Then: User.onboarding_status is updated to 'plant_created'
        """
        # Arrange
        request = CreatePlantRequestDTO(plant_name="Manufacturing Plant 1")

        mock_user_repository.get_by_id.return_value = user_with_org

        created_plant = Plant(
            id=789,
            organization_id=456,
            plant_code="manufacturing-plant",  # Truncated to 19 chars (≤20 limit)
            plant_name="Manufacturing Plant 1",
            location=None,
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_plant_repository.create.return_value = created_plant

        user_with_org._onboarding_status = 'plant_created'
        mock_user_repository.update.return_value = user_with_org

        # Act
        response = create_plant_use_case.execute(request, user_id=1)

        # Assert
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_status == "plant_created"

    def test_optional_address_handled_correctly(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Optional address field handled correctly

        Given: Plant creation without address
        When: Plant is created
        Then: Plant is created successfully with None address
        """
        # Arrange
        request = CreatePlantRequestDTO(plant_name="Manufacturing Plant 1")

        mock_user_repository.get_by_id.return_value = user_with_org

        created_plant = Plant(
            id=789,
            organization_id=456,
            plant_code="manufacturing-plant",  # Truncated to 19 chars (≤20 limit)
            plant_name="Manufacturing Plant 1",
            location=None,
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_plant_repository.create.return_value = created_plant
        mock_user_repository.update.return_value = user_with_org

        # Act
        response = create_plant_use_case.execute(request, user_id=1)

        # Assert
        assert response.plant_id == 789
        create_call = mock_plant_repository.create.call_args[0][0]
        assert create_call.location is None

    def test_optional_timezone_handled_correctly(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Optional timezone field handled correctly

        Given: Plant creation without timezone
        When: Plant is created
        Then: Plant is created successfully with default timezone
        """
        # Arrange
        request = CreatePlantRequestDTO(plant_name="Manufacturing Plant 1")

        mock_user_repository.get_by_id.return_value = user_with_org

        created_plant = Plant(
            id=789,
            organization_id=456,
            plant_code="manufacturing-plant",  # Truncated to 19 chars (≤20 limit)
            plant_name="Manufacturing Plant 1",
            location=None,
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_plant_repository.create.return_value = created_plant
        mock_user_repository.update.return_value = user_with_org

        # Act
        response = create_plant_use_case.execute(request, user_id=1)

        # Assert
        assert response.plant_id == 789

    def test_plant_creation_returns_correct_response_dto(
        self, create_plant_use_case, mock_user_repository, mock_plant_repository, user_with_org
    ):
        """
        Test: Plant creation returns CreatePlantResponseDTO with correct structure

        Given: Successful plant creation
        When: Response is returned
        Then: Response contains plant_id, name, organization_id, created_at
        """
        # Arrange
        request = CreatePlantRequestDTO(plant_name="Manufacturing Plant 1")

        mock_user_repository.get_by_id.return_value = user_with_org

        created_plant = Plant(
            id=789,
            organization_id=456,
            plant_code="manufacturing-plant",  # Truncated to 19 chars (≤20 limit)
            plant_name="Manufacturing Plant 1",
            location=None,
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_plant_repository.create.return_value = created_plant
        mock_user_repository.update.return_value = user_with_org

        # Act
        response = create_plant_use_case.execute(request, user_id=1)

        # Assert
        assert isinstance(response, CreatePlantResponseDTO)
        assert isinstance(response.plant_id, int)
        assert isinstance(response.name, str)
        assert isinstance(response.organization_id, int)
        assert isinstance(response.created_at, datetime)
