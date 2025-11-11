"""
SQLAlchemy model for Organization - Multi-tenant foundation
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Organization(Base):
    """
    Organization model - Top-level multi-tenant boundary

    This is the primary tenant isolation level for Row-Level Security.
    All tenant data is scoped to organization_id.
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True)
    org_code = Column(String(20), unique=True, nullable=False, index=True)
    org_name = Column(String(200), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=True)  # For white-label access
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plants = relationship("Plant", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("SubscriptionModel", back_populates="organization", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_org_code', 'org_code'),
        Index('idx_org_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Organization(code='{self.org_code}', name='{self.org_name}', active={self.is_active})>"
