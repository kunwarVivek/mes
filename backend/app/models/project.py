"""
SQLAlchemy model for Project - Multi-project manufacturing.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, ForeignKey, Enum as SQLEnum, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.domain.entities.project import ProjectStatus


class Project(Base):
    """
    Project model - Multi-project manufacturing.

    Represents discrete manufacturing projects with BOM linkage,
    timeline tracking, and multi-tenant isolation.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=False, index=True)
    project_code = Column(String(50), nullable=False)
    project_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    bom_id = Column(Integer, ForeignKey('bom_header.id'), nullable=True, index=True)
    planned_start_date = Column(Date, nullable=True)
    planned_end_date = Column(Date, nullable=True)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    status = Column(SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING, index=True)
    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    plant = relationship("Plant", back_populates="projects")
    bom = relationship("BOMHeader", back_populates="projects")

    __table_args__ = (
        UniqueConstraint('plant_id', 'project_code', name='uq_project_code_per_plant'),
        CheckConstraint('planned_end_date >= planned_start_date', name='check_dates'),
        Index('idx_project_org', 'organization_id'),
        Index('idx_project_plant', 'plant_id'),
        Index('idx_project_status', 'status'),
        Index('idx_project_bom', 'bom_id'),
    )

    def __repr__(self):
        return f"<Project(code='{self.project_code}', name='{self.project_name}', status='{self.status}')>"
