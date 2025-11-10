"""
Inventory Alert Model

Tracks inventory alerts (low stock, out of stock, restocked) with PostgreSQL LISTEN/NOTIFY support.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, BigInteger, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class InventoryAlert(Base):
    """
    Inventory Alert entity.

    Stores alert history for inventory conditions (low stock, out of stock, restocked).
    Integrated with PostgreSQL LISTEN/NOTIFY for real-time WebSocket notifications.

    Alert Types:
    - LOW_STOCK: Quantity below reorder point
    - OUT_OF_STOCK: Quantity is zero
    - RESTOCKED: Quantity crossed back above reorder point

    Severity Levels:
    - INFO: Quantity between 75-100% of reorder point
    - WARNING: Quantity between 50-75% of reorder point
    - CRITICAL: Quantity below 50% of reorder point or out of stock
    """

    __tablename__ = "inventory_alerts"

    id = Column(BigInteger, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey("plant.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("material.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_location_id = Column(Integer, nullable=True)

    # Alert details
    alert_type = Column(String(50), nullable=False)  # LOW_STOCK, OUT_OF_STOCK, RESTOCKED
    severity = Column(String(20), nullable=False)  # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)

    # Inventory state at time of alert
    quantity_on_hand = Column(Numeric(15, 4), nullable=False)
    reorder_point = Column(Numeric(15, 4), nullable=True)
    max_stock_level = Column(Numeric(15, 4), nullable=True)

    # Acknowledgement
    is_acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_by_user_id = Column(Integer, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default="now()", nullable=False, index=True)

    # Relationships
    organization = relationship("Organization")
    plant = relationship("Plant")
    material = relationship("Material")

    def __repr__(self):
        return f"<InventoryAlert(id={self.id}, type={self.alert_type}, material_id={self.material_id}, severity={self.severity})>"

    def to_dict(self) -> dict:
        """Convert alert to dictionary for API responses."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "plant_id": self.plant_id,
            "material_id": self.material_id,
            "storage_location_id": self.storage_location_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "quantity_on_hand": float(self.quantity_on_hand) if self.quantity_on_hand else 0.0,
            "reorder_point": float(self.reorder_point) if self.reorder_point else None,
            "max_stock_level": float(self.max_stock_level) if self.max_stock_level else None,
            "is_acknowledged": self.is_acknowledged,
            "acknowledged_by_user_id": self.acknowledged_by_user_id,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
