"""
SQLAlchemy model for Production Log - TimescaleDB hypertable for time-series production data.

This table is converted to a TimescaleDB hypertable for efficient time-series queries.
"""

from sqlalchemy import Column, BigInteger, Integer, Numeric, Text, DateTime, ForeignKey, CheckConstraint, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ProductionLog(Base):
    """
    Production Log model - TimescaleDB hypertable for time-series production data.

    Tracks real-time production output, scrap, and rework for work orders.
    Uses BIGSERIAL for high-volume time-series data.
    Partitioned by timestamp with 1-day chunks for optimal query performance.
    """
    __tablename__ = "production_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # BIGSERIAL for high-volume data
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    plant_id = Column(Integer, ForeignKey('plants.id', ondelete='CASCADE'), nullable=False)
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False)
    operation_id = Column(Integer, ForeignKey('work_order_operation.id'), nullable=True)
    machine_id = Column(Integer, ForeignKey('machine.id'), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)  # Not PK for SQLite compatibility
    quantity_produced = Column(Numeric(15, 3), nullable=False)
    quantity_scrapped = Column(Numeric(15, 3), default=0, nullable=False)
    quantity_reworked = Column(Numeric(15, 3), default=0, nullable=False)
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    shift_id = Column(Integer, ForeignKey('shift.id'), nullable=True)
    notes = Column(Text, nullable=True)
    custom_metadata = Column(JSON, nullable=True)  # JSON works with both PostgreSQL and SQLite

    # Relationships
    organization = relationship("Organization")
    plant = relationship("Plant")
    work_order = relationship("WorkOrder")
    operation = relationship("WorkOrderOperation")
    machine = relationship("Machine")
    operator = relationship("UserModel")  # Changed from "User" to match actual class name
    shift = relationship("Shift")

    __table_args__ = (
        CheckConstraint('quantity_produced >= 0 AND quantity_scrapped >= 0 AND quantity_reworked >= 0',
                        name='check_quantities'),
        Index('idx_prod_log_org_time', 'organization_id', 'timestamp'),
        Index('idx_prod_log_plant_time', 'plant_id', 'timestamp'),
        Index('idx_prod_log_wo', 'work_order_id'),
        Index('idx_prod_log_machine_time', 'machine_id', 'timestamp',
              postgresql_where=(machine_id.isnot(None))),
        Index('idx_prod_log_operator_time', 'operator_id', 'timestamp',
              postgresql_where=(operator_id.isnot(None))),
    )

    def __repr__(self):
        return f"<ProductionLog(wo={self.work_order_id}, qty={self.quantity_produced}, time='{self.timestamp}')>"
