"""Material Transaction model for inventory costing (FIFO/LIFO/Weighted Average)."""
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class MaterialTransaction(Base):
    """Material transaction model for tracking all inventory movements and costing.

    This is a TimescaleDB hypertable partitioned by transaction_date for efficient
    time-series queries needed for FIFO/LIFO costing calculations.
    """

    __tablename__ = "material_transactions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)  # receipt, issue, adjustment, transfer_in, transfer_out
    quantity = Column(Numeric(15, 4), nullable=False)  # Can be negative for issues
    unit_cost = Column(Numeric(15, 4), nullable=True)  # Cost per unit at time of transaction
    total_cost = Column(Numeric(15, 2), nullable=True)  # quantity * unit_cost (denormalized for performance)
    reference_type = Column(String(50), nullable=True, index=True)  # work_order, purchase_order, adjustment, transfer
    reference_id = Column(Integer, nullable=True, index=True)
    batch_number = Column(String(100), nullable=True)
    lot_number = Column(String(100), nullable=True)
    storage_location_id = Column(Integer, ForeignKey("storage_locations.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    performed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="material_transactions")
    material = relationship("Material", back_populates="transactions")
    plant = relationship("Plant", back_populates="material_transactions")
    storage_location = relationship("StorageLocation", back_populates="material_transactions")
    user = relationship("User", foreign_keys=[performed_by])

    # Constraints
    __table_args__ = (
        CheckConstraint('quantity != 0', name='ck_material_transactions_qty'),
        CheckConstraint(
            "transaction_type IN ('receipt', 'issue', 'adjustment', 'transfer_in', 'transfer_out')",
            name='ck_material_transactions_type'
        ),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<MaterialTransaction(id={self.id}, type='{self.transaction_type}', qty={self.quantity}, date={self.transaction_date})>"

    @property
    def is_receipt(self) -> bool:
        """Check if this is a receipt transaction (increases inventory)."""
        return self.transaction_type in ('receipt', 'transfer_in')

    @property
    def is_issue(self) -> bool:
        """Check if this is an issue transaction (decreases inventory)."""
        return self.transaction_type in ('issue', 'transfer_out')

    def calculate_total_cost(self):
        """Calculate and set total_cost from quantity and unit_cost."""
        if self.quantity and self.unit_cost:
            self.total_cost = float(self.quantity) * float(self.unit_cost)
