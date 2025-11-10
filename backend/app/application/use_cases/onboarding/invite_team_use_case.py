"""
InviteTeamUseCase - Team Invitation for Self-Service Onboarding

Implements the fifth step of the onboarding wizard:
1. Verify user has plant created (onboarding_status >= 'plant_created')
2. For each invitation:
   - Validate email not already in organization
   - Generate invitation token (32 bytes hex)
   - Set 7-day expiry
   - Create PendingInvitation entity
   - Queue invitation email via PGMQ
3. Update user onboarding_status to 'completed'
4. Set user.onboarding_completed_at = now()
5. Save all pending invitations and user
6. Return response DTO with expiry times

Security Features:
- Requires plant creation before team invitation
- Prevents duplicate invitations in same organization
- Cryptographically secure tokens (32 bytes)
- 7-day expiry enforcement

Follows Clean Architecture and SOLID principles:
- Single Responsibility: Only handles team invitation logic
- Dependency Inversion: Depends on repository interfaces
- Open/Closed: Extensible without modification
- Interface Segregation: Minimal dependencies
- Liskov Substitution: Compatible with repository interfaces

Error Handling:
- DomainValidationException: User without plant, duplicate emails
- Database exceptions: Propagated to caller for transaction rollback

Example Usage:
    >>> user_repo = UserRepository(session)
    >>> invitation_repo = PendingInvitationRepository(session)
    >>> pgmq = PGMQService(session)
    >>> use_case = InviteTeamUseCase(user_repo, invitation_repo, pgmq)
    >>> request = InviteTeamRequestDTO(
    ...     invitations=[
    ...         TeamInvitation(email="user@example.com", role=TeamRole.ADMIN)
    ...     ]
    ... )
    >>> response = use_case.execute(request, user_id=1)
    >>> print(f"Invitations sent: {len(response.invitations_sent)}")
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import List

from app.application.dtos.onboarding_dto import (
    InviteTeamRequestDTO,
    InviteTeamResponseDTO,
    SentInvitation,
    TeamRole
)
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.pending_invitation_repository import IPendingInvitationRepository
from app.domain.entities.pending_invitation import PendingInvitation
from app.domain.exceptions.domain_exception import DomainValidationException

logger = logging.getLogger(__name__)


class InviteTeamUseCase:
    """
    Use Case: Team Invitation (Self-Service Onboarding Step 5)

    Handles team member invitations as part of the self-service onboarding workflow.
    This is the final step that completes onboarding.

    Responsibilities:
    - Validate user has plant created
    - Check for duplicate invitations in organization
    - Generate secure invitation tokens
    - Create pending invitation entities
    - Queue invitation emails via PGMQ
    - Mark onboarding as completed

    Dependencies (Injected):
    - IUserRepository: User database operations
    - IPendingInvitationRepository: Invitation database operations
    - PGMQ Service: Email queue operations

    Design Patterns:
    - Use Case Pattern: Business logic encapsulation
    - Dependency Injection: Testable, loosely coupled
    - Repository Pattern: Database abstraction

    Thread Safety: Not thread-safe (use per-request instances)
    Transaction Semantics: Atomic (all invitations and user update or nothing)
    """

    INVITATION_EXPIRY_DAYS = 7  # 7 days for team invitations

    def __init__(
        self,
        user_repository: IUserRepository,
        invitation_repository: IPendingInvitationRepository,
        pgmq_service
    ):
        """
        Initialize InviteTeamUseCase with required dependencies.

        Args:
            user_repository: Repository implementing IUserRepository interface
            invitation_repository: Repository implementing IPendingInvitationRepository interface
            pgmq_service: PGMQ service for email queue operations

        Example:
            >>> from app.infrastructure.persistence.user_repository_impl import UserRepository
            >>> from app.infrastructure.persistence.pending_invitation_repository_impl import PendingInvitationRepository
            >>> from app.infrastructure.messaging.pgmq_service import PGMQService
            >>>
            >>> user_repo = UserRepository(db_session)
            >>> invitation_repo = PendingInvitationRepository(db_session)
            >>> pgmq = PGMQService(db_session)
            >>> use_case = InviteTeamUseCase(user_repo, invitation_repo, pgmq)
        """
        self._user_repository = user_repository
        self._invitation_repository = invitation_repository
        self._pgmq_service = pgmq_service

    def execute(self, request: InviteTeamRequestDTO, user_id: int) -> InviteTeamResponseDTO:
        """
        Execute team invitation workflow (main entry point).

        Orchestrates the complete team invitation process including plant verification,
        duplicate checking, invitation creation, email queueing, and onboarding completion.
        This method is transactional - either all steps succeed or none do.

        Workflow Steps:
        1. Get user by ID
        2. Verify user has plant created
        3. For each invitation:
           a. Check for duplicate email in organization
           b. Generate secure token (32 bytes hex)
           c. Set 7-day expiry
           d. Create PendingInvitation entity
           e. Save invitation to database
           f. Queue invitation email via PGMQ
        4. Update user onboarding_status to 'completed'
        5. Set user.onboarding_completed_at = now()
        6. Save user (transactional)
        7. Return success response with expiry times

        Args:
            request: InviteTeamRequestDTO containing list of invitations.
                Fields are already validated by DTO (email format, unique emails, custom role).
            user_id: ID of user sending invitations

        Returns:
            InviteTeamResponseDTO containing:
            - invitations_sent: List of sent invitations with expiry times

        Raises:
            DomainValidationException: If user doesn't have plant, duplicate email, or validation fails.
            Exception: Database errors propagated to caller for proper
                transaction rollback handling.

        Example:
            >>> request = InviteTeamRequestDTO(
            ...     invitations=[
            ...         TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN),
            ...         TeamInvitation(email="user2@example.com", role=TeamRole.OPERATOR)
            ...     ]
            ... )
            >>> response = use_case.execute(request, user_id=1)
            >>> print(len(response.invitations_sent))  # 2

        Performance:
        - Database: 1 SELECT (user) + N SELECT (duplicate check) + N INSERT (invitations) + 1 UPDATE (user)
        - PGMQ: N messages queued
        - Total: ~200-500ms typical for 2-5 invitations

        Security Notes:
        - Requires plant creation before team invitation
        - Prevents duplicate invitations in same organization
        - Cryptographically secure tokens (32 bytes)
        - 7-day expiry enforcement
        """
        logger.info(
            f"Starting team invitation for user {user_id}: "
            f"{len(request.invitations)} invitations"
        )

        # Step 1: Get user by ID
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            logger.warning(f"Team invitation failed: User {user_id} not found")
            raise DomainValidationException(f"User {user_id} not found")

        # Step 2: Verify user has plant created
        if user.plant_id is None:
            logger.warning(
                f"Team invitation failed: User {user_id} has no plant "
                f"(status: {user.onboarding_status})"
            )
            raise DomainValidationException(
                "You must create a plant before inviting team members"
            )

        # Step 3: Process each invitation
        sent_invitations: List[SentInvitation] = []

        for invitation in request.invitations:
            # Step 3a: Check for duplicate email in organization
            existing = self._invitation_repository.get_by_email_and_organization(
                invitation.email,
                user.organization_id
            )

            if existing is not None:
                logger.warning(
                    f"Team invitation failed: Email {invitation.email} "
                    f"already invited in organization {user.organization_id}"
                )
                raise DomainValidationException(
                    f"Email {invitation.email} has already been invited to this organization"
                )

            # Step 3b: Generate secure token (32 bytes = 64 hex characters)
            token = secrets.token_hex(32)

            # Step 3c: Set 7-day expiry
            expires_at = datetime.utcnow() + timedelta(days=self.INVITATION_EXPIRY_DAYS)

            # Step 3d: Create PendingInvitation entity
            pending_invitation = PendingInvitation(
                id=None,  # Auto-generated by database
                organization_id=user.organization_id,
                email=invitation.email,
                role=invitation.role.value,
                role_description=invitation.role_description,
                token=token,
                expires_at=expires_at,
                created_at=datetime.utcnow(),
                invited_by_user_id=user_id
            )

            # Step 3e: Save invitation to database
            try:
                created_invitation = self._invitation_repository.create(pending_invitation)
                logger.info(
                    f"Invitation created: ID={created_invitation.id}, "
                    f"email={created_invitation.email}, org_id={user.organization_id}"
                )

            except Exception as e:
                logger.error(
                    f"Invitation creation failed for {invitation.email}: {str(e)}"
                )
                raise

            # Step 3f: Queue invitation email via PGMQ
            try:
                email_message = {
                    "to": invitation.email,
                    "template": "team_invitation",
                    "data": {
                        "inviter_email": user.email.value,
                        "role": invitation.role.value,
                        "role_description": invitation.role_description,
                        "token": token,
                        "expires_at": expires_at.isoformat()
                    }
                }

                self._pgmq_service.send_message("email_queue", email_message)
                logger.info(f"Invitation email queued for {invitation.email}")

            except Exception as e:
                logger.error(
                    f"Email queue failed for {invitation.email}: {str(e)}"
                )
                raise

            # Add to response list
            sent_invitations.append(
                SentInvitation(
                    email=created_invitation.email,
                    role=TeamRole(created_invitation.role),
                    role_description=created_invitation.role_description,
                    expires_at=created_invitation.expires_at
                )
            )

        # Step 4 & 5: Mark onboarding as completed
        user.complete_onboarding()
        logger.info(f"User {user_id} onboarding marked as completed")

        # Step 6: Save user to database (transactional)
        try:
            updated_user = self._user_repository.update(user)
            logger.info(
                f"User {updated_user.id} onboarding completed at "
                f"{updated_user.onboarding_completed_at}"
            )

        except Exception as e:
            logger.error(f"User update failed for user {user_id}: {str(e)}")
            raise

        # Step 7: Return success response
        logger.info(
            f"Team invitation completed for user {user_id}: "
            f"{len(sent_invitations)} invitations sent"
        )

        return InviteTeamResponseDTO(invitations_sent=sent_invitations)
