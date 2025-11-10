from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class OnboardingStatus(str, enum.Enum):
    """Onboarding workflow status tracking"""
    PENDING_VERIFICATION = "pending_verification"
    EMAIL_VERIFIED = "email_verified"
    ORG_SETUP = "org_setup"
    PLANT_CREATED = "plant_created"
    INVITES_SENT = "invites_sent"
    COMPLETED = "completed"


class UserModel(Base):
    """Database Model for User

    Represents the user table in the database.
    Separated from domain entity to maintain clean architecture.

    Multi-tenancy: Users belong to an organization and optionally a plant.
    Onboarding: Tracks self-service onboarding progress through workflow stages.
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

    # Onboarding fields
    onboarding_status = Column(
        Enum(OnboardingStatus, name='onboarding_status_enum'),
        nullable=False,
        server_default='pending_verification',
        index=True
    )
    verification_token = Column(Text, nullable=True)
    verification_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PendingInvitationModel(Base):
    """Database Model for Pending Team Invitations

    Tracks team invitations sent during onboarding workflow.
    Invitations expire after 7 days and can be in various states.
    """
    __tablename__ = "pending_invitations"

    id = Column(Integer, primary_key=True, index=True)
    inviter_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    token = Column(Text, nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, server_default='email_queued', index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
