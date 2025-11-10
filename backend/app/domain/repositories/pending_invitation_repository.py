from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.pending_invitation import PendingInvitation


class IPendingInvitationRepository(ABC):
    """Repository Interface for PendingInvitation Entity

    Defines the contract for pending invitation data access.
    Following the Dependency Inversion Principle (SOLID).
    """

    @abstractmethod
    def create(self, invitation: PendingInvitation) -> PendingInvitation:
        """Create a new pending invitation"""
        pass

    @abstractmethod
    def get_by_id(self, invitation_id: int) -> Optional[PendingInvitation]:
        """Get invitation by ID"""
        pass

    @abstractmethod
    def get_by_token(self, token: str) -> Optional[PendingInvitation]:
        """Get invitation by token"""
        pass

    @abstractmethod
    def get_by_email_and_organization(self, email: str, organization_id: int) -> Optional[PendingInvitation]:
        """Get invitation by email and organization (check for duplicates)"""
        pass

    @abstractmethod
    def get_by_organization(self, organization_id: int) -> List[PendingInvitation]:
        """Get all invitations for an organization"""
        pass

    @abstractmethod
    def update(self, invitation: PendingInvitation) -> PendingInvitation:
        """Update existing invitation"""
        pass

    @abstractmethod
    def delete(self, invitation_id: int) -> bool:
        """Delete invitation by ID"""
        pass
