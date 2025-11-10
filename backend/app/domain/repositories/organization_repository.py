from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.organization import Organization


class IOrganizationRepository(ABC):
    """Repository Interface for Organization Entity

    Defines the contract for organization data access.
    Following the Dependency Inversion Principle (SOLID).
    """

    @abstractmethod
    def create(self, organization: Organization) -> Organization:
        """Create a new organization"""
        pass

    @abstractmethod
    def get_by_id(self, organization_id: int) -> Optional[Organization]:
        """Get organization by ID"""
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug (subdomain)"""
        pass

    @abstractmethod
    def update(self, organization: Organization) -> Organization:
        """Update existing organization"""
        pass

    @abstractmethod
    def delete(self, organization_id: int) -> bool:
        """Delete organization by ID"""
        pass
