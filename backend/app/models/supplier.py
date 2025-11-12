"""Supplier model for material procurement."""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Supplier(Base):
    """Supplier model for tracking material suppliers and vendors."""

    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    is_active = Column(Boolean, nullable=False, default=True, server_default='true')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="suppliers")
    materials = relationship("MaterialSupplier", back_populates="supplier")
    ncr_reports = relationship("NCRReport", back_populates="supplier", foreign_keys="NCRReport.supplier_id")

    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='ck_suppliers_rating'),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<Supplier(id={self.id}, code='{self.supplier_code}', name='{self.name}')>"
