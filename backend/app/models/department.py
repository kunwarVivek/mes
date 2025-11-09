"""
SQLAlchemy model for Department - Organizational unit within plant
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Department(Base):
    """
    Department model - Functional unit within plant

    Departments organize users and workflows (Production, Quality, Maintenance, etc.)
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=False, index=True)
    dept_code = Column(String(20), nullable=False)  # Unique within plant
    dept_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    plant = relationship("Plant", back_populates="departments")

    __table_args__ = (
        UniqueConstraint('plant_id', 'dept_code', name='uq_dept_code_per_plant'),
        Index('idx_dept_plant', 'plant_id'),
        Index('idx_dept_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Department(code='{self.dept_code}', name='{self.dept_name}', plant_id={self.plant_id})>"
