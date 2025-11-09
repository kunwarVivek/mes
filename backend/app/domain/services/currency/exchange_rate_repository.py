"""
Exchange Rate Repository - Multi-Currency Costing Module.
Repository pattern for exchange rate persistence and retrieval.

Provides abstraction over database operations for exchange rates.
"""
from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.currency import ExchangeRate as ExchangeRateModel


class ExchangeRateRepository:
    """
    Repository for exchange rate persistence operations.

    Follows repository pattern to abstract database operations.
    Provides domain-friendly interface for exchange rate data access.
    """

    def __init__(self, db_session: Session):
        """
        Initialize repository with database session.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session

    def create(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        effective_date: datetime,
        created_by: str
    ) -> ExchangeRateModel:
        """
        Create new exchange rate record.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            rate: Exchange rate value
            effective_date: Date when rate becomes effective
            created_by: User who created the rate

        Returns:
            Created exchange rate model
        """
        exchange_rate = ExchangeRateModel(
            from_currency_code=from_currency,
            to_currency_code=to_currency,
            rate=rate,
            effective_date=effective_date,
            created_by=created_by
        )

        self.db.add(exchange_rate)
        self.db.commit()
        self.db.refresh(exchange_rate)

        return exchange_rate

    def find_latest_before_date(
        self,
        from_currency: str,
        to_currency: str,
        conversion_date: datetime
    ) -> Optional[ExchangeRateModel]:
        """
        Find latest exchange rate before or on conversion date.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            conversion_date: Date for rate lookup

        Returns:
            Exchange rate model or None if not found
        """
        return self.db.query(ExchangeRateModel).filter(
            ExchangeRateModel.from_currency_code == from_currency,
            ExchangeRateModel.to_currency_code == to_currency,
            ExchangeRateModel.effective_date <= conversion_date
        ).order_by(ExchangeRateModel.effective_date.desc()).first()

    def find_all_between_currencies(
        self,
        from_currency: str,
        to_currency: str,
        limit: Optional[int] = None
    ) -> List[ExchangeRateModel]:
        """
        Find all exchange rates between two currencies.

        Returns historical records ordered by effective date (most recent first).

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            limit: Maximum number of records to return (optional)

        Returns:
            List of exchange rate records
        """
        query = self.db.query(ExchangeRateModel).filter(
            ExchangeRateModel.from_currency_code == from_currency,
            ExchangeRateModel.to_currency_code == to_currency
        ).order_by(ExchangeRateModel.effective_date.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def find_by_id(self, rate_id: int) -> Optional[ExchangeRateModel]:
        """
        Find exchange rate by ID.

        Args:
            rate_id: Exchange rate ID

        Returns:
            Exchange rate model or None if not found
        """
        return self.db.query(ExchangeRateModel).filter(
            ExchangeRateModel.id == rate_id
        ).first()

    def find_all_for_date(
        self,
        conversion_date: datetime,
        from_currency: Optional[str] = None,
        to_currency: Optional[str] = None
    ) -> List[ExchangeRateModel]:
        """
        Find all exchange rates effective on or before specific date.

        Optionally filter by currency codes.

        Args:
            conversion_date: Date for rate lookup
            from_currency: Optional source currency filter
            to_currency: Optional target currency filter

        Returns:
            List of exchange rate records
        """
        query = self.db.query(ExchangeRateModel).filter(
            ExchangeRateModel.effective_date <= conversion_date
        )

        if from_currency:
            query = query.filter(ExchangeRateModel.from_currency_code == from_currency)

        if to_currency:
            query = query.filter(ExchangeRateModel.to_currency_code == to_currency)

        return query.order_by(ExchangeRateModel.effective_date.desc()).all()
