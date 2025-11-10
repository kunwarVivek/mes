from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.plant import Plant


class IPlantRepository(ABC):
    """Repository Interface for Plant Entity

    Defines the contract for plant data access.
    Following the Dependency Inversion Principle (SOLID).
    """

    @abstractmethod
    def create(self, plant: Plant) -> Plant:
        """Create a new plant"""
        pass

    @abstractmethod
    def get_by_id(self, plant_id: int) -> Optional[Plant]:
        """Get plant by ID"""
        pass

    @abstractmethod
    def get_by_organization(self, organization_id: int) -> List[Plant]:
        """Get all plants for an organization"""
        pass

    @abstractmethod
    def update(self, plant: Plant) -> Plant:
        """Update existing plant"""
        pass

    @abstractmethod
    def delete(self, plant_id: int) -> bool:
        """Delete plant by ID"""
        pass
