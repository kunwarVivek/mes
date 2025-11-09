"""
SQLAlchemy model for Plant - Manufacturing site within organization
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Plant(Base):
    """
    Plant model - Manufacturing site and sub-tenant boundary

    Each plant belongs to an organization and has independent operations.
    RLS can filter by both organization_id AND plant_id.
    """
    __tablename__ = "plants"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    plant_code = Column(String(20), nullable=False)  # Unique within org
    plant_name = Column(String(200), nullable=False)
    location = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="plants")
    departments = relationship("Department", back_populates="plant", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="plant", cascade="all, delete-orphan")
    lanes = relationship("Lane", back_populates="plant", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_code', name='uq_plant_code_per_org'),
        Index('idx_plant_org', 'organization_id'),
        Index('idx_plant_active', 'is_active'),
        Index('idx_plant_org_code', 'organization_id', 'plant_code'),
    )

    def __repr__(self):
        return f"<Plant(code='{self.plant_code}', name='{self.plant_name}', org_id={self.organization_id})>"
