from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class UserModel(Base):
    """Database Model for User

    Represents the user table in the database.
    Separated from domain entity to maintain clean architecture.

    Multi-tenancy: Users belong to an organization and optionally a plant.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    organization_id = Column(Integer, nullable=True, index=True)  # FK to organizations
    plant_id = Column(Integer, nullable=True, index=True)  # FK to plants (optional)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
