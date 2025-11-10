"""
Onboarding API Router - Self-service user onboarding flow.

Provides 6 endpoints for the onboarding wizard:
1. POST /signup - User signup with email verification
2. POST /verify-email - Email verification token validation
3. POST /organization - Organization setup (requires auth)
4. POST /plant - Plant creation (requires auth + org)
5. POST /team/invite - Team member invitations (requires auth + org)
6. GET /progress - Onboarding progress tracking (requires auth)

All authenticated endpoints use JWT tokens and enforce RLS via get_current_user.
"""
import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user
from app.domain.entities.user import User
from app.domain.exceptions import DomainValidationException

# Import DTOs
from app.application.dtos.onboarding_dto import (
    SignupRequestDTO,
    SignupResponseDTO,
    VerifyEmailRequestDTO,
    VerifyEmailResponseDTO,
    SetupOrgRequestDTO,
    SetupOrgResponseDTO,
    CreatePlantRequestDTO,
    CreatePlantResponseDTO,
    InviteTeamRequestDTO,
    InviteTeamResponseDTO,
    OnboardingProgressResponseDTO,
)

# Import use cases
from app.application.use_cases.onboarding.signup_use_case import SignupUseCase
from app.application.use_cases.onboarding.verify_email_use_case import VerifyEmailUseCase
from app.application.use_cases.onboarding.setup_org_use_case import SetupOrgUseCase
from app.application.use_cases.onboarding.create_plant_use_case import CreatePlantUseCase
from app.application.use_cases.onboarding.invite_team_use_case import InviteTeamUseCase

# Import repositories
from app.infrastructure.persistence.user_repository_impl import UserRepository
from app.infrastructure.repositories.organization_repository import OrganizationRepository
from app.infrastructure.repositories.plant_repository import PlantRepository

# Note: PendingInvitationRepository concrete implementation needs to be created
# For now, import the interface and create a stub
from app.domain.repositories.pending_invitation_repository import IPendingInvitationRepository
from app.domain.entities.pending_invitation import PendingInvitation
from typing import List, Optional


class PendingInvitationRepository(IPendingInvitationRepository):
    """Stub implementation of PendingInvitationRepository for onboarding API."""

    def __init__(self, db: Session):
        self._db = db

    def create(self, invitation: PendingInvitation) -> PendingInvitation:
        from app.infrastructure.persistence.models import PendingInvitationModel
        db_invitation = PendingInvitationModel(
            inviter_id=invitation.inviter_id,
            organization_id=invitation.organization_id,
            plant_id=invitation.plant_id,
            email=invitation.email,
            role=invitation.role,
            token=invitation.token,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at
        )
        self._db.add(db_invitation)
        self._db.flush()
        invitation.id = db_invitation.id
        return invitation

    def get_by_id(self, invitation_id: int) -> Optional[PendingInvitation]:
        pass

    def get_by_token(self, token: str) -> Optional[PendingInvitation]:
        pass

    def get_by_email_and_organization(self, email: str, organization_id: int) -> Optional[PendingInvitation]:
        pass

    def get_by_organization(self, organization_id: int) -> List[PendingInvitation]:
        pass

    def update(self, invitation: PendingInvitation) -> PendingInvitation:
        pass

    def delete(self, invitation_id: int) -> bool:
        pass

# Import messaging
from app.infrastructure.messaging.pgmq_client import PGMQClient
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Dependency Injection Helpers
# ============================================================================

def get_pgmq_client() -> PGMQClient:
    """Create PGMQ client for email/SMS queueing."""
    return PGMQClient(
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )


# ============================================================================
# 1. POST /signup - User Signup (Public)
# ============================================================================

@router.post("/signup", response_model=SignupResponseDTO, status_code=status.HTTP_200_OK)
def signup(
    request: SignupRequestDTO,
    db: Session = Depends(get_db)
):
    """
    User signup with email verification.

    Creates a new user account and sends email verification link.
    This is a public endpoint (no authentication required).

    Workflow:
    1. Validate email not already registered
    2. Hash password securely (bcrypt)
    3. Generate verification token (32 bytes hex)
    4. Set token expiry (24 hours)
    5. Create user with status='pending_verification'
    6. Queue verification email via PGMQ

    Args:
        request: SignupRequestDTO with email and password
        db: Database session (injected)

    Returns:
        SignupResponseDTO with user_id, email, message, onboarding_status

    Raises:
        HTTPException 400: Email already registered
        HTTPException 422: Validation error (weak password, invalid email)
    """
    logger.info(f"Signup request for email: {request.email}")

    try:
        # Create dependencies
        user_repository = UserRepository(db)
        pgmq_client = get_pgmq_client()

        # Create and execute use case
        use_case = SignupUseCase(user_repository, pgmq_client)
        response = use_case.execute(request)

        logger.info(f"Signup successful for user_id: {response.user_id}")
        return response

    except DomainValidationException as e:
        logger.warning(f"Signup validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed due to internal error"
        )


# ============================================================================
# 2. POST /verify-email - Email Verification (Public)
# ============================================================================

@router.post("/verify-email", response_model=VerifyEmailResponseDTO, status_code=status.HTTP_200_OK)
def verify_email(
    request: VerifyEmailRequestDTO,
    db: Session = Depends(get_db)
):
    """
    Verify email with token from verification email.

    Validates verification token and activates user account.
    This is a public endpoint (no authentication required).

    Workflow:
    1. Find user by verification token
    2. Check token not expired (24 hour TTL)
    3. Activate user account (is_active=True)
    4. Clear verification token
    5. Update onboarding_status to 'email_verified'

    Args:
        request: VerifyEmailRequestDTO with token
        db: Database session (injected)

    Returns:
        VerifyEmailResponseDTO with success, message, onboarding_status

    Raises:
        HTTPException 400: Invalid or expired token
    """
    logger.info(f"Email verification request for token: {request.token[:8]}...")

    try:
        # Create dependencies
        user_repository = UserRepository(db)

        # Create and execute use case
        use_case = VerifyEmailUseCase(user_repository)
        response = use_case.execute(request)

        logger.info(f"Email verification successful")
        return response

    except DomainValidationException as e:
        logger.warning(f"Email verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Email verification failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed due to internal error"
        )


# ============================================================================
# 3. POST /organization - Organization Setup (Authenticated)
# ============================================================================

@router.post("/organization", response_model=SetupOrgResponseDTO, status_code=status.HTTP_200_OK)
def setup_organization(
    request: SetupOrgRequestDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create organization for authenticated user.

    Sets up organization and associates user with it.
    Requires JWT authentication.

    Workflow:
    1. Generate URL-safe slug from organization name
    2. Check slug uniqueness
    3. Create organization entity
    4. Associate user with organization
    5. Update onboarding_status to 'org_setup'

    Args:
        request: SetupOrgRequestDTO with organization_name
        current_user: Authenticated user (from JWT)
        db: Database session (injected)

    Returns:
        SetupOrgResponseDTO with organization_id, name, slug, created_at

    Raises:
        HTTPException 400: Organization name already taken, user already has org
        HTTPException 401: Invalid/expired JWT token
    """
    logger.info(f"Organization setup for user_id: {current_user.id}")

    try:
        # Create dependencies
        user_repository = UserRepository(db)
        org_repository = OrganizationRepository(db)

        # Create and execute use case
        use_case = SetupOrgUseCase(user_repository, org_repository)
        response = use_case.execute(request, current_user.id)

        logger.info(f"Organization {response.organization_id} created for user {current_user.id}")
        return response

    except DomainValidationException as e:
        logger.warning(f"Organization setup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Organization setup failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Organization setup failed due to internal error"
        )


# ============================================================================
# 4. POST /plant - Plant Creation (Authenticated + Org Required)
# ============================================================================

@router.post("/plant", response_model=CreatePlantResponseDTO, status_code=status.HTTP_200_OK)
def create_plant(
    request: CreatePlantRequestDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create plant for user's organization.

    Creates plant and associates user with it.
    Requires JWT authentication and existing organization.

    Workflow:
    1. Verify user has organization
    2. Create plant entity with optional address and timezone
    3. Associate user with plant
    4. Update onboarding_status to 'plant_created'

    Args:
        request: CreatePlantRequestDTO with plant_name, address?, timezone?
        current_user: Authenticated user (from JWT)
        db: Database session (injected)

    Returns:
        CreatePlantResponseDTO with plant_id, name, organization_id, created_at

    Raises:
        HTTPException 400: User has no organization, invalid timezone
        HTTPException 401: Invalid/expired JWT token
    """
    logger.info(f"Plant creation for user_id: {current_user.id}")

    try:
        # Create dependencies
        user_repository = UserRepository(db)
        plant_repository = PlantRepository(db)

        # Create and execute use case
        use_case = CreatePlantUseCase(user_repository, plant_repository)
        response = use_case.execute(request, current_user.id)

        logger.info(f"Plant {response.plant_id} created for user {current_user.id}")
        return response

    except DomainValidationException as e:
        logger.warning(f"Plant creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Plant creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Plant creation failed due to internal error"
        )


# ============================================================================
# 5. POST /team/invite - Team Invitations (Authenticated + Org Required)
# ============================================================================

@router.post("/team/invite", response_model=InviteTeamResponseDTO, status_code=status.HTTP_200_OK)
def invite_team(
    request: InviteTeamRequestDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send team member invitations.

    Creates pending invitations and queues invitation emails.
    Requires JWT authentication and existing organization.

    Workflow:
    1. Verify user has organization
    2. Validate no duplicate emails in list
    3. Generate invitation tokens (32 bytes hex each)
    4. Set expiry (7 days from creation)
    5. Create pending invitation records
    6. Queue invitation emails via PGMQ
    7. Update onboarding_status to 'invites_sent'

    Args:
        request: InviteTeamRequestDTO with invitations list
        current_user: Authenticated user (from JWT)
        db: Database session (injected)

    Returns:
        InviteTeamResponseDTO with invitations_sent list

    Raises:
        HTTPException 400: User has no organization, duplicate emails
        HTTPException 401: Invalid/expired JWT token
    """
    logger.info(f"Team invitations from user_id: {current_user.id}")

    try:
        # Create dependencies
        user_repository = UserRepository(db)
        invitation_repository = PendingInvitationRepository(db)
        pgmq_client = get_pgmq_client()

        # Create and execute use case
        use_case = InviteTeamUseCase(user_repository, invitation_repository, pgmq_client)
        response = use_case.execute(request, current_user.id)

        logger.info(f"Sent {len(response.invitations_sent)} invitations from user {current_user.id}")
        return response

    except DomainValidationException as e:
        logger.warning(f"Team invitation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Team invitation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Team invitation failed due to internal error"
        )


# ============================================================================
# 6. GET /progress - Onboarding Progress (Authenticated)
# ============================================================================

@router.get("/progress", response_model=OnboardingProgressResponseDTO, status_code=status.HTTP_200_OK)
def get_onboarding_progress(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's onboarding progress.

    Returns current onboarding status, completed steps, and next step.
    Requires JWT authentication.

    Workflow:
    1. Read current_user.onboarding_status
    2. Map status to completed steps
    3. Determine next step based on status

    Args:
        current_user: Authenticated user (from JWT)

    Returns:
        OnboardingProgressResponseDTO with current_status, completed_steps, next_step

    Raises:
        HTTPException 401: Invalid/expired JWT token
    """
    logger.info(f"Progress check for user_id: {current_user.id}")

    try:
        # Map onboarding status to completed steps and next step
        status_mapping = {
            "pending_verification": {
                "completed_steps": ["signup"],
                "next_step": "Verify your email address"
            },
            "email_verified": {
                "completed_steps": ["signup", "email_verification"],
                "next_step": "Set up your organization"
            },
            "org_setup": {
                "completed_steps": ["signup", "email_verification", "organization_setup"],
                "next_step": "Create your first plant"
            },
            "plant_created": {
                "completed_steps": ["signup", "email_verification", "organization_setup", "plant_creation"],
                "next_step": "Invite team members"
            },
            "invites_sent": {
                "completed_steps": ["signup", "email_verification", "organization_setup", "plant_creation", "team_invitation"],
                "next_step": "Start using the platform"
            },
            "completed": {
                "completed_steps": ["signup", "email_verification", "organization_setup", "plant_creation", "team_invitation"],
                "next_step": "Onboarding complete"
            }
        }

        progress_data = status_mapping.get(current_user.onboarding_status, {
            "completed_steps": [],
            "next_step": "Unknown status"
        })

        response = OnboardingProgressResponseDTO(
            current_status=current_user.onboarding_status,
            completed_steps=progress_data["completed_steps"],
            next_step=progress_data["next_step"]
        )

        logger.info(f"Progress for user {current_user.id}: {current_user.onboarding_status}")
        return response

    except Exception as e:
        logger.error(f"Progress check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Progress check failed due to internal error"
        )
