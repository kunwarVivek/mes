from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username


class IUserRepository(ABC):
    """Repository Interface (Abstract)

    Defines the contract for user data access.
    Following the Dependency Inversion Principle (SOLID).
    """

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user"""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email"""
        pass

    @abstractmethod
    def get_by_username(self, username: Username) -> Optional[User]:
        """Get user by username"""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update existing user"""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete user by ID"""
        pass

    @abstractmethod
    def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email"""
        pass

    @abstractmethod
    def exists_by_username(self, username: Username) -> bool:
        """Check if user exists by username"""
        pass
