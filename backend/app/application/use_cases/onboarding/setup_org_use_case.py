"""
SetupOrgUseCase - Organization Setup for Self-Service Onboarding

Implements the third step of the onboarding wizard:
1. Verify user is email_verified or phone_verified
2. Generate URL-safe slug from organization_name
3. Ensure slug uniqueness (append -2, -3 if duplicate)
4. Create Organization entity
5. Link user to organization
6. Update user onboarding_status to 'org_setup'
7. Save organization and user
8. Return response DTO

Security Features:
- Requires user verification (email or phone)
- Generates unique slugs for subdomain isolation
- XSS protection via DTO validation

Follows Clean Architecture and SOLID principles:
- Single Responsibility: Only handles organization setup logic
- Dependency Inversion: Depends on repository interfaces
- Open/Closed: Extensible without modification
- Interface Segregation: Minimal dependencies
- Liskov Substitution: Compatible with repository interfaces

Error Handling:
- DomainValidationException: Unverified users, validation errors
- Database exceptions: Propagated to caller for transaction rollback

Example Usage:
    >>> user_repo = UserRepository(session)
    >>> org_repo = OrganizationRepository(session)
    >>> use_case = SetupOrgUseCase(user_repo, org_repo)
    >>> request = SetupOrgRequestDTO(organization_name="Acme Corp")
    >>> response = use_case.execute(request, user_id=1)
    >>> print(f"Organization created: {response.organization_id}")
"""
import logging
import re
from datetime import datetime

from app.application.dtos.onboarding_dto import SetupOrgRequestDTO, SetupOrgResponseDTO
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.organization_repository import IOrganizationRepository
from app.domain.entities.organization import Organization
from app.domain.exceptions.domain_exception import DomainValidationException

logger = logging.getLogger(__name__)


class SetupOrgUseCase:
    """
    Use Case: Organization Setup (Self-Service Onboarding Step 3)

    Handles organization creation as part of the self-service onboarding workflow.
    This is the third step after email/phone verification.

    Responsibilities:
    - Validate user is verified (email_verified or phone_verified)
    - Generate unique URL-safe slug from organization name
    - Create organization entity
    - Link user to organization
    - Update user onboarding status to 'org_setup'

    Dependencies (Injected):
    - IUserRepository: User database operations
    - IOrganizationRepository: Organization database operations

    Design Patterns:
    - Use Case Pattern: Business logic encapsulation
    - Dependency Injection: Testable, loosely coupled
    - Repository Pattern: Database abstraction

    Thread Safety: Not thread-safe (use per-request instances)
    Transaction Semantics: Atomic (both user and org updates or nothing)
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        organization_repository: IOrganizationRepository
    ):
        """
        Initialize SetupOrgUseCase with required dependencies.

        Args:
            user_repository: Repository implementing IUserRepository interface
            organization_repository: Repository implementing IOrganizationRepository interface

        Example:
            >>> from app.infrastructure.persistence.user_repository_impl import UserRepository
            >>> from app.infrastructure.persistence.organization_repository_impl import OrganizationRepository
            >>>
            >>> user_repo = UserRepository(db_session)
            >>> org_repo = OrganizationRepository(db_session)
            >>> use_case = SetupOrgUseCase(user_repo, org_repo)
        """
        self._user_repository = user_repository
        self._org_repository = organization_repository

    def execute(self, request: SetupOrgRequestDTO, user_id: int) -> SetupOrgResponseDTO:
        """
        Execute organization setup workflow (main entry point).

        Orchestrates the complete organization setup process including verification
        checking, slug generation, uniqueness validation, organization creation,
        and user linking. This method is transactional - either all steps succeed
        or none do.

        Workflow Steps:
        1. Get user by ID
        2. Verify user is email_verified or phone_verified
        3. Generate slug from organization_name
        4. Ensure slug uniqueness (append -2, -3 if needed)
        5. Create Organization entity
        6. Link user to organization
        7. Update user onboarding_status to 'org_setup'
        8. Save organization and user (transactional)
        9. Return success response

        Args:
            request: SetupOrgRequestDTO containing organization_name.
                Name is already validated for XSS by DTO.
            user_id: ID of user creating the organization

        Returns:
            SetupOrgResponseDTO containing:
            - organization_id: Newly created organization ID
            - name: Organization name
            - slug: Auto-generated unique slug
            - created_at: Organization creation timestamp

        Raises:
            DomainValidationException: If user is not verified or validation fails.
            Exception: Database errors propagated to caller for proper
                transaction rollback handling.

        Example:
            >>> request = SetupOrgRequestDTO(organization_name="Acme Corp")
            >>> response = use_case.execute(request, user_id=1)
            >>> print(response.slug)  # "acme-corp"

        Performance:
        - Database: 1 SELECT (user) + N SELECT (slug check) + 1 INSERT (org) + 1 UPDATE (user)
        - Total: ~100-200ms typical

        Security Notes:
        - Requires user verification (email or phone)
        - Generates unique slugs for subdomain isolation
        - XSS protection via DTO validation
        """
        logger.info(f"Starting organization setup for user {user_id}: {request.organization_name}")

        # Step 1: Get user by ID
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            logger.warning(f"Organization setup failed: User {user_id} not found")
            raise DomainValidationException(f"User {user_id} not found")

        # Step 2: Verify user is email_verified or phone_verified
        if user.onboarding_status not in ['email_verified', 'phone_verified']:
            logger.warning(
                f"Organization setup failed: User {user_id} not verified "
                f"(status: {user.onboarding_status})"
            )
            raise DomainValidationException(
                "You must verify your email or phone before creating an organization"
            )

        # Step 3 & 4: Generate unique slug from organization_name
        slug = self._generate_unique_slug(request.organization_name)
        logger.info(f"Generated unique slug for user {user_id}: {slug}")

        # Step 5: Create Organization entity
        organization = Organization(
            id=None,  # Auto-generated by database
            org_code=slug,
            org_name=request.organization_name,
            subdomain=slug,
            is_active=True,
            created_at=datetime.utcnow()
        )

        # Save organization to database
        try:
            created_org = self._org_repository.create(organization)
            logger.info(
                f"Organization created for user {user_id}: "
                f"ID={created_org.id}, slug={created_org.subdomain}"
            )

        except Exception as e:
            logger.error(f"Organization creation failed for user {user_id}: {str(e)}")
            raise

        # Step 6 & 7: Link user to organization and update onboarding status
        user.link_to_organization(created_org.id)
        logger.info(f"User {user_id} linked to organization {created_org.id}")

        # Step 8: Save user to database (transactional)
        try:
            updated_user = self._user_repository.update(user)
            logger.info(
                f"User {updated_user.id} organization link saved, "
                f"status updated to 'org_setup'"
            )

        except Exception as e:
            logger.error(f"User update failed for user {user_id}: {str(e)}")
            raise

        # Step 9: Return success response
        return SetupOrgResponseDTO(
            organization_id=created_org.id,
            name=created_org.org_name,
            slug=created_org.subdomain,
            created_at=created_org.created_at
        )

    def _generate_slug(self, name: str) -> str:
        """
        Generate URL-safe slug from organization name.

        Algorithm:
        1. Convert to lowercase
        2. Replace non-alphanumeric characters with hyphens
        3. Remove consecutive hyphens
        4. Strip leading/trailing hyphens
        5. Truncate to 20 characters (org_code max length)

        Args:
            name: Organization name

        Returns:
            URL-safe slug (lowercase alphanumeric with hyphens, max 20 chars)

        Example:
            >>> _generate_slug("Acme Corp.")
            "acme-corp"
            >>> _generate_slug("Acme   Manufacturing!")
            "acme-manufacturing"
            >>> _generate_slug("Acme Manufacturing Corporation International")
            "acme-manufacturing-c"  # Truncated to 20 chars
        """
        # Convert to lowercase
        slug = name.lower()

        # Replace non-alphanumeric characters with hyphens
        slug = re.sub(r'[^a-z0-9-]', '-', slug)

        # Remove consecutive hyphens
        slug = re.sub(r'-+', '-', slug)

        # Strip leading/trailing hyphens
        slug = slug.strip('-')

        # Truncate to 20 characters (org_code max length from Organization entity)
        if len(slug) > 20:
            slug = slug[:20].rstrip('-')  # Remove trailing hyphen if truncation creates one

        return slug

    def _generate_unique_slug(self, name: str) -> str:
        """
        Generate unique slug by appending -2, -3, etc. if duplicates exist.

        Ensures the slug stays within 20 character limit by truncating base
        if needed to make room for the counter suffix.

        Args:
            name: Organization name

        Returns:
            Unique slug (max 20 characters)

        Example:
            >>> _generate_unique_slug("Acme Corp")
            "acme-corp"  # If available
            >>> _generate_unique_slug("Acme Corp")
            "acme-corp-2"  # If "acme-corp" already exists
            >>> _generate_unique_slug("Very Long Organization Name")
            "very-long-organizat"  # If available (truncated to 20 chars)
            >>> _generate_unique_slug("Very Long Organization Name")
            "very-long-organ-2"  # If taken (truncated to make room for -2)
        """
        base_slug = self._generate_slug(name)
        slug = base_slug
        counter = 2

        # Check for duplicates and append counter if needed
        while self._org_repository.get_by_slug(slug) is not None:
            # Calculate space needed for suffix (e.g., "-2" = 2 chars, "-10" = 3 chars)
            suffix = f"-{counter}"
            max_base_length = 20 - len(suffix)

            # Truncate base slug to make room for suffix
            truncated_base = base_slug[:max_base_length].rstrip('-')
            slug = f"{truncated_base}{suffix}"

            counter += 1
            logger.debug(f"Slug {base_slug} taken, trying {slug}")

        return slug
