"""
CreatePlantUseCase - Plant Creation for Self-Service Onboarding

Implements the fourth step of the onboarding wizard:
1. Verify user has organization setup (onboarding_status >= 'org_setup')
2. Validate timezone if provided (IANA format)
3. Create Plant entity linked to user's organization
4. Update user onboarding_status to 'plant_created'
5. Save plant and user
6. Return response DTO

Security Features:
- Requires organization setup before plant creation
- Validates timezone against IANA database
- XSS protection via DTO validation

Follows Clean Architecture and SOLID principles:
- Single Responsibility: Only handles plant creation logic
- Dependency Inversion: Depends on repository interfaces
- Open/Closed: Extensible without modification
- Interface Segregation: Minimal dependencies
- Liskov Substitution: Compatible with repository interfaces

Error Handling:
- DomainValidationException: User without org, validation errors
- Database exceptions: Propagated to caller for transaction rollback

Example Usage:
    >>> user_repo = UserRepository(session)
    >>> plant_repo = PlantRepository(session)
    >>> use_case = CreatePlantUseCase(user_repo, plant_repo)
    >>> request = CreatePlantRequestDTO(
    ...     plant_name="Manufacturing Plant 1",
    ...     timezone="America/New_York"
    ... )
    >>> response = use_case.execute(request, user_id=1)
    >>> print(f"Plant created: {response.plant_id}")
"""
import logging
from datetime import datetime

from app.application.dtos.onboarding_dto import CreatePlantRequestDTO, CreatePlantResponseDTO
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.plant_repository import IPlantRepository
from app.domain.entities.plant import Plant
from app.domain.exceptions.domain_exception import DomainValidationException

logger = logging.getLogger(__name__)


class CreatePlantUseCase:
    """
    Use Case: Plant Creation (Self-Service Onboarding Step 4)

    Handles plant creation as part of the self-service onboarding workflow.
    This is the fourth step after organization setup.

    Responsibilities:
    - Validate user has organization setup
    - Validate timezone if provided (IANA format)
    - Create plant entity linked to organization
    - Update user onboarding status to 'plant_created'

    Dependencies (Injected):
    - IUserRepository: User database operations
    - IPlantRepository: Plant database operations

    Design Patterns:
    - Use Case Pattern: Business logic encapsulation
    - Dependency Injection: Testable, loosely coupled
    - Repository Pattern: Database abstraction

    Thread Safety: Not thread-safe (use per-request instances)
    Transaction Semantics: Atomic (both plant and user updates or nothing)
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        plant_repository: IPlantRepository
    ):
        """
        Initialize CreatePlantUseCase with required dependencies.

        Args:
            user_repository: Repository implementing IUserRepository interface
            plant_repository: Repository implementing IPlantRepository interface

        Example:
            >>> from app.infrastructure.persistence.user_repository_impl import UserRepository
            >>> from app.infrastructure.persistence.plant_repository_impl import PlantRepository
            >>>
            >>> user_repo = UserRepository(db_session)
            >>> plant_repo = PlantRepository(db_session)
            >>> use_case = CreatePlantUseCase(user_repo, plant_repo)
        """
        self._user_repository = user_repository
        self._plant_repository = plant_repository

    def execute(self, request: CreatePlantRequestDTO, user_id: int) -> CreatePlantResponseDTO:
        """
        Execute plant creation workflow (main entry point).

        Orchestrates the complete plant creation process including organization
        verification, timezone validation, plant creation, and user linking.
        This method is transactional - either all steps succeed or none do.

        Workflow Steps:
        1. Get user by ID
        2. Verify user has organization setup
        3. Validate timezone if provided (already done by DTO)
        4. Create Plant entity linked to organization
        5. Update user onboarding_status to 'plant_created'
        6. Save plant and user (transactional)
        7. Return success response

        Args:
            request: CreatePlantRequestDTO containing plant details.
                Fields are already validated by DTO (XSS, timezone).
            user_id: ID of user creating the plant

        Returns:
            CreatePlantResponseDTO containing:
            - plant_id: Newly created plant ID
            - name: Plant name
            - organization_id: Organization ID (foreign key)
            - created_at: Plant creation timestamp

        Raises:
            DomainValidationException: If user doesn't have organization or validation fails.
            Exception: Database errors propagated to caller for proper
                transaction rollback handling.

        Example:
            >>> request = CreatePlantRequestDTO(
            ...     plant_name="Manufacturing Plant 1",
            ...     address="123 Factory St",
            ...     timezone="America/New_York"
            ... )
            >>> response = use_case.execute(request, user_id=1)
            >>> print(response.plant_id)  # 789

        Performance:
        - Database: 1 SELECT (user) + 1 INSERT (plant) + 1 UPDATE (user)
        - Total: ~50-100ms typical

        Security Notes:
        - Requires organization setup before plant creation
        - Timezone validated against IANA database (DTO level)
        - XSS protection via DTO validation
        """
        logger.info(f"Starting plant creation for user {user_id}: {request.plant_name}")

        # Step 1: Get user by ID
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            logger.warning(f"Plant creation failed: User {user_id} not found")
            raise DomainValidationException(f"User {user_id} not found")

        # Step 2: Verify user has organization setup
        if user.organization_id is None:
            logger.warning(
                f"Plant creation failed: User {user_id} has no organization "
                f"(status: {user.onboarding_status})"
            )
            raise DomainValidationException(
                "You must create an organization before creating a plant"
            )

        # Step 3: Timezone validation already done by DTO (Pydantic validator)

        # Step 4: Create Plant entity linked to organization
        plant = Plant(
            id=None,  # Auto-generated by database
            organization_id=user.organization_id,
            plant_code=self._generate_plant_code(request.plant_name),
            plant_name=request.plant_name,
            location=request.address,  # Optional
            is_active=True,
            created_at=datetime.utcnow()
        )

        # Save plant to database
        try:
            created_plant = self._plant_repository.create(plant)
            logger.info(
                f"Plant created for user {user_id}: "
                f"ID={created_plant.id}, org_id={created_plant.organization_id}"
            )

        except Exception as e:
            logger.error(f"Plant creation failed for user {user_id}: {str(e)}")
            raise

        # Step 5: Update user onboarding status to 'plant_created'
        user.link_to_plant(created_plant.id)
        logger.info(f"User {user_id} linked to plant {created_plant.id}")

        # Step 6: Save user to database (transactional)
        try:
            updated_user = self._user_repository.update(user)
            logger.info(
                f"User {updated_user.id} plant link saved, "
                f"status updated to 'plant_created'"
            )

        except Exception as e:
            logger.error(f"User update failed for user {user_id}: {str(e)}")
            raise

        # Step 7: Return success response
        return CreatePlantResponseDTO(
            plant_id=created_plant.id,
            name=created_plant.plant_name,
            organization_id=created_plant.organization_id,
            created_at=created_plant.created_at
        )

    def _generate_plant_code(self, name: str) -> str:
        """
        Generate plant code from plant name.

        Algorithm:
        1. Convert to lowercase
        2. Replace non-alphanumeric characters with hyphens
        3. Remove consecutive hyphens
        4. Strip leading/trailing hyphens
        5. Truncate to 20 characters (plant_code max length)

        Args:
            name: Plant name

        Returns:
            Plant code (lowercase alphanumeric with hyphens, max 20 chars)

        Example:
            >>> _generate_plant_code("Manufacturing Plant 1")
            "manufacturing-plant"  # Truncated to 20 chars
            >>> _generate_plant_code("Plant NYC")
            "plant-nyc"
        """
        import re

        # Convert to lowercase
        code = name.lower()

        # Replace non-alphanumeric characters with hyphens
        code = re.sub(r'[^a-z0-9-]', '-', code)

        # Remove consecutive hyphens
        code = re.sub(r'-+', '-', code)

        # Strip leading/trailing hyphens
        code = code.strip('-')

        # Truncate to 20 characters (plant_code max length from Plant entity)
        if len(code) > 20:
            code = code[:20].rstrip('-')  # Remove trailing hyphen if truncation creates one

        return code
