"""
Unit tests for InviteTeamUseCase (TDD - RED phase)

Tests for team invitation functionality:
- Successful bulk invitations
- Custom role with role_description
- Duplicate email rejection (same org)
- 7-day expiry set correctly
- Onboarding status updated to 'completed'
- Onboarding completed timestamp set
- Invitation emails queued via PGMQ
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from app.application.use_cases.onboarding.invite_team_use_case import InviteTeamUseCase
from app.application.dtos.onboarding_dto import (
    InviteTeamRequestDTO,
    InviteTeamResponseDTO,
    TeamInvitation,
    TeamRole
)
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.exceptions.domain_exception import DomainValidationException


class TestInviteTeamUseCase:
    """Test suite for InviteTeamUseCase following TDD RED-GREEN-REFACTOR"""

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository for testing"""
        return Mock()

    @pytest.fixture
    def mock_invitation_repository(self):
        """Mock pending invitation repository for testing"""
        return Mock()

    @pytest.fixture
    def mock_pgmq_service(self):
        """Mock PGMQ service for email queueing"""
        return Mock()

    @pytest.fixture
    def invite_team_use_case(self, mock_user_repository, mock_invitation_repository, mock_pgmq_service):
        """Create InviteTeamUseCase instance with mocks"""
        return InviteTeamUseCase(
            user_repository=mock_user_repository,
            invitation_repository=mock_invitation_repository,
            pgmq_service=mock_pgmq_service
        )

    @pytest.fixture
    def user_with_plant(self):
        """Create user with plant created"""
        return User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            plant_id=789,
            onboarding_status="plant_created",
            is_active=True
        )

    def test_successful_bulk_invitations(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Successful bulk team invitations

        Given: User with plant created
        When: User invites multiple team members
        Then: All invitations are created and emails queued
        And: Onboarding status updated to 'completed'
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN),
                TeamInvitation(email="user2@example.com", role=TeamRole.OPERATOR)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        # Mock invitation creation - use side_effect to return different mocks for each call
        expiry = datetime.utcnow() + timedelta(days=7)

        mock_inv1 = Mock()
        mock_inv1.id = 1
        mock_inv1.email = "user1@example.com"
        mock_inv1.role = "admin"
        mock_inv1.role_description = None
        mock_inv1.expires_at = expiry

        mock_inv2 = Mock()
        mock_inv2.id = 2
        mock_inv2.email = "user2@example.com"
        mock_inv2.role = "operator"
        mock_inv2.role_description = None
        mock_inv2.expires_at = expiry

        mock_invitation_repository.create.side_effect = [mock_inv1, mock_inv2]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = datetime.utcnow()
        mock_user_repository.update.return_value = user_with_plant

        # Act
        response = invite_team_use_case.execute(request, user_id=1)

        # Assert
        assert isinstance(response, InviteTeamResponseDTO)
        assert len(response.invitations_sent) == 2
        assert response.invitations_sent[0].email == "user1@example.com"
        assert response.invitations_sent[1].email == "user2@example.com"

        # Verify invitations created
        assert mock_invitation_repository.create.call_count == 2

        # Verify emails queued
        assert mock_pgmq_service.send_message.call_count == 2

        # Verify onboarding completed
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_status == "completed"

    def test_custom_role_with_role_description(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Custom role with role_description handled correctly

        Given: Invitation with custom role and description
        When: Invitation is created
        Then: Role_description is stored and returned
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(
                    email="user1@example.com",
                    role=TeamRole.CUSTOM,
                    role_description="Quality Control Manager"
                )
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        # Mock invitation creation with custom role - use list for side_effect
        mock_created_invitation = Mock()
        mock_created_invitation.id = 1
        mock_created_invitation.email = "user1@example.com"
        mock_created_invitation.role = "custom"
        mock_created_invitation.role_description = "Quality Control Manager"
        mock_created_invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        mock_invitation_repository.create.side_effect = [mock_created_invitation]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = datetime.utcnow()
        mock_user_repository.update.return_value = user_with_plant

        # Act
        response = invite_team_use_case.execute(request, user_id=1)

        # Assert
        assert response.invitations_sent[0].role == TeamRole.CUSTOM
        assert response.invitations_sent[0].role_description == "Quality Control Manager"

    def test_duplicate_email_in_organization_raises_exception(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Duplicate email in same organization raises DomainValidationException

        Given: Email already invited in organization
        When: User attempts to invite same email
        Then: DomainValidationException is raised
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="existing@example.com", role=TeamRole.ADMIN)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant

        # Mock existing invitation with proper attributes
        existing_invitation = Mock()
        existing_invitation.id = 999
        existing_invitation.email = "existing@example.com"
        existing_invitation.organization_id = 456
        mock_invitation_repository.get_by_email_and_organization.return_value = existing_invitation

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            invite_team_use_case.execute(request, user_id=1)

        # Error message: "Email existing@example.com has already been invited to this organization"
        assert "has already been invited" in str(exc_info.value).lower()

    def test_seven_day_expiry_set_correctly(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: 7-day expiry set correctly for invitations

        Given: Team invitation created
        When: Invitation is stored
        Then: expires_at is set to 7 days from now
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        now = datetime.utcnow()
        expiry = now + timedelta(days=7)

        # Mock invitation with 7-day expiry - use list for side_effect
        mock_created_invitation = Mock()
        mock_created_invitation.id = 1
        mock_created_invitation.email = "user1@example.com"
        mock_created_invitation.role = "admin"
        mock_created_invitation.role_description = None
        mock_created_invitation.expires_at = expiry
        mock_invitation_repository.create.side_effect = [mock_created_invitation]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = now
        mock_user_repository.update.return_value = user_with_plant

        # Act
        response = invite_team_use_case.execute(request, user_id=1)

        # Assert
        sent_invitation = response.invitations_sent[0]
        time_diff = (sent_invitation.expires_at - now).days
        assert time_diff == 7

    def test_onboarding_status_updated_to_completed(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Onboarding status updated to 'completed'

        Given: User invites team successfully
        When: Invitations are sent
        Then: User.onboarding_status is updated to 'completed'
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        # Mock invitation - use list for side_effect with proper attributes
        mock_inv = Mock()
        mock_inv.id = 1
        mock_inv.email = "user1@example.com"
        mock_inv.role = "admin"
        mock_inv.role_description = None
        mock_inv.expires_at = datetime.utcnow() + timedelta(days=7)
        mock_invitation_repository.create.side_effect = [mock_inv]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = datetime.utcnow()
        mock_user_repository.update.return_value = user_with_plant

        # Act
        invite_team_use_case.execute(request, user_id=1)

        # Assert
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_status == "completed"

    def test_onboarding_completed_at_timestamp_set(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Onboarding completed_at timestamp set

        Given: User completes onboarding by inviting team
        When: Invitations are sent
        Then: User.onboarding_completed_at is set to current time
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        # Mock invitation - use list for side_effect with proper attributes
        mock_inv = Mock()
        mock_inv.id = 1
        mock_inv.email = "user1@example.com"
        mock_inv.role = "admin"
        mock_inv.role_description = None
        mock_inv.expires_at = datetime.utcnow() + timedelta(days=7)
        mock_invitation_repository.create.side_effect = [mock_inv]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = datetime.utcnow()
        mock_user_repository.update.return_value = user_with_plant

        # Act - capture time around execute() call
        before_time = datetime.utcnow()
        invite_team_use_case.execute(request, user_id=1)
        after_time = datetime.utcnow()

        # Assert
        update_call = mock_user_repository.update.call_args[0][0]
        assert update_call.onboarding_completed_at is not None
        assert before_time <= update_call.onboarding_completed_at <= after_time

    def test_invitation_emails_queued_via_pgmq(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Invitation emails queued via PGMQ

        Given: Team invitations created
        When: Invitations are processed
        Then: Email messages are queued via PGMQ service
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN),
                TeamInvitation(email="user2@example.com", role=TeamRole.OPERATOR)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        # Mock 2 invitations - use side_effect with 2 mocks
        expiry = datetime.utcnow() + timedelta(days=7)

        mock_inv1 = Mock()
        mock_inv1.id = 1
        mock_inv1.email = "user1@example.com"
        mock_inv1.role = "admin"
        mock_inv1.role_description = None
        mock_inv1.expires_at = expiry

        mock_inv2 = Mock()
        mock_inv2.id = 2
        mock_inv2.email = "user2@example.com"
        mock_inv2.role = "operator"
        mock_inv2.role_description = None
        mock_inv2.expires_at = expiry

        mock_invitation_repository.create.side_effect = [mock_inv1, mock_inv2]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = datetime.utcnow()
        mock_user_repository.update.return_value = user_with_plant

        # Act
        invite_team_use_case.execute(request, user_id=1)

        # Assert
        assert mock_pgmq_service.send_message.call_count == 2

    def test_user_without_plant_raises_exception(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service
    ):
        """
        Test: User without plant cannot invite team

        Given: User with onboarding_status='org_setup' (no plant)
        When: User attempts to invite team
        Then: DomainValidationException is raised
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN)
            ]
        )

        user_without_plant = User(
            id=1,
            email=Email("test@example.com"),
            username=Username("test"),
            hashed_password="hashed_password_123",
            organization_id=456,
            plant_id=None,
            onboarding_status="org_setup",
            is_active=True
        )
        mock_user_repository.get_by_id.return_value = user_without_plant

        # Act & Assert
        with pytest.raises(DomainValidationException) as exc_info:
            invite_team_use_case.execute(request, user_id=1)

        assert "plant" in str(exc_info.value).lower()

    def test_invitation_token_generated_32_bytes_hex(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Invitation token generated as 32 bytes hex

        Given: Team invitation created
        When: Invitation is stored
        Then: Token is 64 character hex string (32 bytes)
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        # Mock invitation with 64-char token - use list to allow multiple calls
        mock_created_invitation = Mock()
        mock_created_invitation.id = 1
        mock_created_invitation.email = "user1@example.com"
        mock_created_invitation.role = "admin"
        mock_created_invitation.role_description = None
        mock_created_invitation.token = "a" * 64  # 32 bytes = 64 hex characters
        mock_created_invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        mock_invitation_repository.create.side_effect = [mock_created_invitation]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = datetime.utcnow()
        mock_user_repository.update.return_value = user_with_plant

        # Act
        invite_team_use_case.execute(request, user_id=1)

        # Assert
        create_call = mock_invitation_repository.create.call_args[0][0]
        assert len(create_call.token) == 64

    def test_response_dto_contains_all_sent_invitations(
        self, invite_team_use_case, mock_user_repository, mock_invitation_repository,
        mock_pgmq_service, user_with_plant
    ):
        """
        Test: Response DTO contains all sent invitations with expiry

        Given: Multiple invitations sent
        When: Response is returned
        Then: Response contains all invitations with email, role, expires_at
        """
        # Arrange
        request = InviteTeamRequestDTO(
            invitations=[
                TeamInvitation(email="user1@example.com", role=TeamRole.ADMIN),
                TeamInvitation(email="user2@example.com", role=TeamRole.OPERATOR)
            ]
        )

        mock_user_repository.get_by_id.return_value = user_with_plant
        mock_invitation_repository.get_by_email_and_organization.return_value = None

        expiry = datetime.utcnow() + timedelta(days=7)
        # Mock multiple invitations with proper attributes
        mock_inv1 = Mock()
        mock_inv1.id = 1
        mock_inv1.email = "user1@example.com"
        mock_inv1.role = "admin"
        mock_inv1.role_description = None
        mock_inv1.expires_at = expiry

        mock_inv2 = Mock()
        mock_inv2.id = 2
        mock_inv2.email = "user2@example.com"
        mock_inv2.role = "operator"
        mock_inv2.role_description = None
        mock_inv2.expires_at = expiry

        mock_invitation_repository.create.side_effect = [mock_inv1, mock_inv2]

        user_with_plant._onboarding_status = 'completed'
        user_with_plant._onboarding_completed_at = datetime.utcnow()
        mock_user_repository.update.return_value = user_with_plant

        # Act
        response = invite_team_use_case.execute(request, user_id=1)

        # Assert
        assert isinstance(response, InviteTeamResponseDTO)
        assert len(response.invitations_sent) == 2
        for sent_inv in response.invitations_sent:
            assert hasattr(sent_inv, 'email')
            assert hasattr(sent_inv, 'role')
            assert hasattr(sent_inv, 'expires_at')
