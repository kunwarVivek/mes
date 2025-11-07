from typing import List
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions import EntityNotFoundException


class GetUserUseCase:
    """Use Case: Get User by ID

    Single Responsibility: Handle retrieving a single user
    """

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository

    def execute(self, user_id: int) -> User:
        """Execute the get user use case"""
        user = self._repository.get_by_id(user_id)

        if not user:
            raise EntityNotFoundException(f"User with ID {user_id} not found")

        return user


class GetAllUsersUseCase:
    """Use Case: Get All Users

    Single Responsibility: Handle retrieving all users with pagination
    """

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository

    def execute(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Execute the get all users use case"""
        return self._repository.get_all(skip=skip, limit=limit)
