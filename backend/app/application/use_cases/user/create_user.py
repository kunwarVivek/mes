from passlib.context import CryptContext
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.repositories.user_repository import IUserRepository
from app.domain.exceptions import DuplicateEntityException
from app.application.dtos.user_dto import CreateUserDTO


class CreateUserUseCase:
    """Use Case: Create User

    Single Responsibility: Handle user creation logic
    Open/Closed: Can extend without modifying existing code
    """

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def execute(self, dto: CreateUserDTO) -> User:
        """Execute the create user use case"""
        email = Email(dto.email)
        username = Username(dto.username)

        if self._repository.exists_by_email(email):
            raise DuplicateEntityException("Email already registered")

        if self._repository.exists_by_username(username):
            raise DuplicateEntityException("Username already taken")

        hashed_password = self._pwd_context.hash(dto.password)

        user = User(
            id=None,
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_active=dto.is_active,
            is_superuser=dto.is_superuser
        )

        return self._repository.create(user)
