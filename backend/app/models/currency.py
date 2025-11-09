"""
SQLAlchemy models for Currency and Exchange Rate domain.
Multi-Currency Costing Module - Database Models

Supports multi-currency costing with exchange rate management and audit trail.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from decimal import Decimal


class Currency(Base):
    """
    Currency entity - defines supported currencies.

    Stores currency metadata including code, name, symbol, and rounding rules.
    Decimal places determine precision for amounts in this currency.
    """
    __tablename__ = "currency"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # ISO 4217 code (USD, EUR, etc.)
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)
    decimal_places = Column(Integer, nullable=False, default=2)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    exchange_rates_from = relationship(
        "ExchangeRate",
        foreign_keys="ExchangeRate.from_currency_code",
        backref="from_currency"
    )
    exchange_rates_to = relationship(
        "ExchangeRate",
        foreign_keys="ExchangeRate.to_currency_code",
        backref="to_currency"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint('decimal_places >= 0', name='chk_decimal_places_non_negative'),
        CheckConstraint('decimal_places <= 6', name='chk_decimal_places_max'),
        Index('idx_currency_code', 'code'),
    )

    def __repr__(self):
        return f"<Currency(code='{self.code}', name='{self.name}', decimals={self.decimal_places})>"


class ExchangeRate(Base):
    """
    Exchange Rate entity - stores historical exchange rates between currencies.

    Supports time-based exchange rate lookups for historical costing.
    Each record represents rate at a specific effective date.
    Maintains audit trail of who created each rate.
    """
    __tablename__ = "exchange_rate"

    id = Column(Integer, primary_key=True, index=True)
    from_currency_code = Column(String(3), ForeignKey('currency.code', ondelete='CASCADE'), nullable=False, index=True)
    to_currency_code = Column(String(3), ForeignKey('currency.code', ondelete='CASCADE'), nullable=False, index=True)
    rate = Column(Numeric(18, 8), nullable=False)  # High precision for exchange rates
    effective_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('rate > 0', name='chk_rate_positive'),
        CheckConstraint(
            'from_currency_code != to_currency_code',
            name='chk_different_currencies'
        ),
        Index('idx_exchange_rate_currencies', 'from_currency_code', 'to_currency_code'),
        Index('idx_exchange_rate_effective_date', 'effective_date'),
        Index('idx_exchange_rate_lookup', 'from_currency_code', 'to_currency_code', 'effective_date'),
    )

    def __repr__(self):
        return f"<ExchangeRate({self.from_currency_code}->{self.to_currency_code}, rate={self.rate}, date={self.effective_date})>"
