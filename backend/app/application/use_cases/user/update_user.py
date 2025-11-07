from passlib.context import CryptContext
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions import EntityNotFoundException, DuplicateEntityException
from app.application.dtos.user_dto import UpdateUserDTO


class UpdateUserUseCase:
    """Use Case: Update User

    Single Responsibility: Handle user update logic
    """

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def execute(self, user_id: int, dto: UpdateUserDTO) -> User:
        """Execute the update user use case"""
        user = self._repository.get_by_id(user_id)

        if not user:
            raise EntityNotFoundException(f"User with ID {user_id} not found")

        if dto.email:
            new_email = Email(dto.email)
            if new_email != user.email and self._repository.exists_by_email(new_email):
                raise DuplicateEntityException("Email already registered")
            user.change_email(new_email)

        if dto.username:
            new_username = Username(dto.username)
            if new_username != user.username and self._repository.exists_by_username(new_username):
                raise DuplicateEntityException("Username already taken")

        if dto.password:
            hashed_password = self._pwd_context.hash(dto.password)
            user.change_password(hashed_password)

        if dto.is_active is not None:
            if dto.is_active:
                user.activate()
            else:
                user.deactivate()

        return self._repository.update(user)
