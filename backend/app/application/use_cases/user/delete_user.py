from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions import EntityNotFoundException


class DeleteUserUseCase:
    """Use Case: Delete User

    Single Responsibility: Handle user deletion logic
    """

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository

    def execute(self, user_id: int) -> bool:
        """Execute the delete user use case"""
        user = self._repository.get_by_id(user_id)

        if not user:
            raise EntityNotFoundException(f"User with ID {user_id} not found")

        return self._repository.delete(user_id)
