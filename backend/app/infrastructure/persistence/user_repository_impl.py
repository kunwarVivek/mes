from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.user import User as UserEntity
from app.domain.value_objects.email import Email
from app.domain.value_objects.username import Username
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.persistence.models import UserModel
from app.infrastructure.persistence.mappers.user_mapper import UserMapper


class UserRepository(IUserRepository):
    """Concrete Repository Implementation

    Implements the repository interface defined in the domain layer.
    Handles the mapping between domain entities and database models.
    """

    def __init__(self, db: Session):
        self._db = db
        self._mapper = UserMapper()

    def create(self, user: UserEntity) -> UserEntity:
        """Create a new user in the database"""
        db_user = self._mapper.to_model(user)
        self._db.add(db_user)
        self._db.commit()
        self._db.refresh(db_user)
        return self._mapper.to_entity(db_user)

    def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        """Get user by ID"""
        db_user = self._db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._mapper.to_entity(db_user) if db_user else None

    def get_by_email(self, email: Email) -> Optional[UserEntity]:
        """Get user by email"""
        db_user = self._db.query(UserModel).filter(
            UserModel.email == email.value
        ).first()
        return self._mapper.to_entity(db_user) if db_user else None

    def get_by_username(self, username: Username) -> Optional[UserEntity]:
        """Get user by username"""
        db_user = self._db.query(UserModel).filter(
            UserModel.username == username.value
        ).first()
        return self._mapper.to_entity(db_user) if db_user else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[UserEntity]:
        """Get all users with pagination"""
        db_users = self._db.query(UserModel).offset(skip).limit(limit).all()
        return [self._mapper.to_entity(db_user) for db_user in db_users]

    def update(self, user: UserEntity) -> UserEntity:
        """Update existing user"""
        db_user = self._db.query(UserModel).filter(UserModel.id == user.id).first()
        if db_user:
            db_user.email = user.email.value
            db_user.username = user.username.value
            db_user.hashed_password = user.hashed_password
            db_user.is_active = user.is_active
            db_user.is_superuser = user.is_superuser
            db_user.updated_at = user.updated_at

            self._db.commit()
            self._db.refresh(db_user)
            return self._mapper.to_entity(db_user)
        return user

    def delete(self, user_id: int) -> bool:
        """Delete user by ID"""
        db_user = self._db.query(UserModel).filter(UserModel.id == user_id).first()
        if db_user:
            self._db.delete(db_user)
            self._db.commit()
            return True
        return False

    def exists_by_email(self, email: Email) -> bool:
        """Check if user exists by email"""
        return self._db.query(UserModel).filter(
            UserModel.email == email.value
        ).first() is not None

    def exists_by_username(self, username: Username) -> bool:
        """Check if user exists by username"""
        return self._db.query(UserModel).filter(
            UserModel.username == username.value
        ).first() is not None
