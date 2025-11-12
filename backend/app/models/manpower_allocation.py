"""Manpower Allocation model for tracking worker assignments to work orders."""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class ManpowerAllocation(Base):
    """Manpower allocation model for assigning workers to work orders and operations."""

    __tablename__ = "manpower_allocation"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_id = Column(Integer, ForeignKey("work_order_operations.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(100), nullable=True)  # operator, supervisor, technician, quality_inspector
    allocated_hours = Column(Numeric(10, 2), nullable=True)  # Planned hours
    actual_hours = Column(Numeric(10, 2), nullable=True)  # Actual hours worked
    hourly_rate = Column(Numeric(10, 2), nullable=True)  # Hourly labor rate
    allocated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    allocated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)  # When worker was released from assignment
    notes = Column(Text, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="manpower_allocations")
    work_order = relationship("WorkOrder", back_populates="manpower_allocations")
    operation = relationship("WorkOrderOperation", back_populates="manpower_allocations")
    worker = relationship("User", foreign_keys=[user_id], back_populates="work_assignments")
    allocator = relationship("User", foreign_keys=[allocated_by])

    def __repr__(self):
        return f"<ManpowerAllocation(id={self.id}, work_order_id={self.work_order_id}, user_id={self.user_id})>"

    @property
    def is_active(self) -> bool:
        """Check if allocation is currently active (not released)."""
        return self.released_at is None

    @property
    def total_labor_cost(self) -> float:
        """Calculate total labor cost (actual_hours * hourly_rate)."""
        if self.actual_hours and self.hourly_rate:
            return float(self.actual_hours) * float(self.hourly_rate)
        return 0.0

    @property
    def variance_hours(self) -> float:
        """Calculate variance between allocated and actual hours."""
        if self.allocated_hours and self.actual_hours:
            return float(self.actual_hours) - float(self.allocated_hours)
        return 0.0

    def release(self):
        """Mark this allocation as released."""
        if not self.released_at:
            self.released_at = func.now()
