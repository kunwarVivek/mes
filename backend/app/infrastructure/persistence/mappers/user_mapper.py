from app.domain.entities.user import User as UserEntity
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.infrastructure.persistence.models import UserModel


class UserMapper:
    """Mapper: Domain Entity <-> Database Model

    Responsible for converting between domain entities and database models.
    Maintains separation between domain and infrastructure layers.
    """

    @staticmethod
    def to_entity(model: UserModel) -> UserEntity:
        """Convert database model to domain entity"""
        return UserEntity(
            id=model.id,
            email=Email(model.email),
            username=Username(model.username),
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            is_superuser=model.is_superuser,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    @staticmethod
    def to_model(entity: UserEntity) -> UserModel:
        """Convert domain entity to database model"""
        return UserModel(
            id=entity.id,
            email=entity.email.value,
            username=entity.username.value,
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            is_superuser=entity.is_superuser,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
