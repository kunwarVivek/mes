"""
Currency Service - Multi-Currency Costing Module.
Domain Layer Service for currency conversion and exchange rate management.

Supports real-time and historical exchange rates with configurable rounding rules.
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.currency import Currency as CurrencyModel, ExchangeRate as ExchangeRateModel
from app.domain.services.currency.models import CurrencyRoundingRule


class CurrencyService:
    """
    Domain service for currency conversion and exchange rate management.

    Responsibilities:
    - Currency conversion with historical rates
    - Exchange rate management (create, retrieve)
    - Rounding rules per currency
    - Inverse and cross-rate conversions
    - Audit trail for exchange rate changes
    """

    def __init__(self, db_session: Session):
        """
        Initialize CurrencyService with database session.

        Args:
            db_session: SQLAlchemy session for database operations
        """
        self.db = db_session

    def _get_currency(self, currency_code: str) -> CurrencyModel:
        """
        Retrieve currency by code.

        Args:
            currency_code: ISO currency code (USD, EUR, etc.)

        Returns:
            Currency model

        Raises:
            ValueError: If currency not found
        """
        currency = self.db.query(CurrencyModel).filter(
            CurrencyModel.code == currency_code
        ).first()

        if not currency:
            raise ValueError(f"Invalid currency code: {currency_code}")

        return currency

    def _get_rounding_rule(self, currency_code: str) -> CurrencyRoundingRule:
        """
        Get rounding rule for currency.

        Args:
            currency_code: ISO currency code

        Returns:
            Rounding rule for the currency
        """
        currency = self._get_currency(currency_code)
        return CurrencyRoundingRule(
            currency_code=currency.code,
            decimal_places=currency.decimal_places
        )

    def _get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        conversion_date: datetime
    ) -> Optional[ExchangeRateModel]:
        """
        Retrieve latest exchange rate before or on conversion date.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            conversion_date: Date for rate lookup

        Returns:
            Exchange rate model or None if not found
        """
        exchange_rate = self.db.query(ExchangeRateModel).filter(
            ExchangeRateModel.from_currency_code == from_currency,
            ExchangeRateModel.to_currency_code == to_currency,
            ExchangeRateModel.effective_date <= conversion_date
        ).order_by(ExchangeRateModel.effective_date.desc()).first()

        return exchange_rate

    def _get_inverse_rate(
        self,
        from_currency: str,
        to_currency: str,
        conversion_date: datetime
    ) -> Optional[Decimal]:
        """
        Get inverse exchange rate (reciprocal).

        If USD->EUR rate exists, calculate EUR->USD as 1/rate.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            conversion_date: Date for rate lookup

        Returns:
            Inverse rate or None if not found
        """
        # Look for inverse rate (to->from)
        inverse_rate_record = self._get_exchange_rate(to_currency, from_currency, conversion_date)

        if inverse_rate_record:
            # Return reciprocal
            return Decimal("1.0") / inverse_rate_record.rate

        return None

    def _get_cross_rate(
        self,
        from_currency: str,
        to_currency: str,
        conversion_date: datetime,
        base_currency: str = "USD"
    ) -> Optional[Decimal]:
        """
        Calculate cross-rate through base currency.

        Example: EUR->GBP via USD = (EUR->USD) * (USD->GBP)

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            conversion_date: Date for rate lookup
            base_currency: Intermediate currency for cross-rate calculation

        Returns:
            Cross rate or None if cannot be calculated
        """
        # Get from_currency -> base_currency rate
        rate1_record = self._get_exchange_rate(from_currency, base_currency, conversion_date)
        if not rate1_record:
            # Try inverse
            rate1 = self._get_inverse_rate(from_currency, base_currency, conversion_date)
            if not rate1:
                return None
        else:
            rate1 = rate1_record.rate

        # Get base_currency -> to_currency rate
        rate2_record = self._get_exchange_rate(base_currency, to_currency, conversion_date)
        if not rate2_record:
            # Try inverse
            rate2 = self._get_inverse_rate(base_currency, to_currency, conversion_date)
            if not rate2:
                return None
        else:
            rate2 = rate2_record.rate

        # Calculate cross rate
        return rate1 * rate2

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        conversion_date: datetime,
        base_currency: Optional[str] = "USD"
    ) -> Decimal:
        """
        Convert amount from one currency to another.

        Supports direct rates, inverse rates, and cross-rates through base currency.
        Applies currency-specific rounding rules.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            conversion_date: Date for exchange rate lookup
            base_currency: Base currency for cross-rate calculation (default: USD)

        Returns:
            Converted amount rounded to target currency precision

        Raises:
            ValueError: If amount is negative, currencies invalid, or no rate found
        """
        # Validate amount
        if amount < 0:
            raise ValueError("Amount must be non-negative")

        # Validate currencies exist
        self._get_currency(from_currency)
        to_currency_obj = self._get_currency(to_currency)

        # Same currency - return original amount
        if from_currency == to_currency:
            return amount

        # Try to get direct exchange rate
        exchange_rate_record = self._get_exchange_rate(from_currency, to_currency, conversion_date)

        if exchange_rate_record:
            rate = exchange_rate_record.rate
        else:
            # Try inverse rate
            rate = self._get_inverse_rate(from_currency, to_currency, conversion_date)

            if not rate and base_currency:
                # Try cross-rate through base currency
                rate = self._get_cross_rate(from_currency, to_currency, conversion_date, base_currency)

            if not rate:
                raise ValueError(
                    f"No exchange rate found for {from_currency} to {to_currency} "
                    f"on or before {conversion_date}"
                )

        # Convert amount
        converted_amount = amount * rate

        # Apply rounding rule for target currency
        rounding_rule = self._get_rounding_rule(to_currency)
        return rounding_rule.round_amount(converted_amount)

    def create_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        effective_date: datetime,
        created_by: str
    ) -> ExchangeRateModel:
        """
        Create new exchange rate record.

        Creates historical record for audit trail.
        Does not update or delete existing rates.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            rate: Exchange rate value
            effective_date: Date when rate becomes effective
            created_by: User who created the rate

        Returns:
            Created exchange rate model

        Raises:
            ValueError: If rate is invalid or currencies don't exist
        """
        # Validate rate
        if rate <= 0:
            raise ValueError("Exchange rate must be positive")

        # Validate currencies exist
        self._get_currency(from_currency)
        self._get_currency(to_currency)

        if from_currency == to_currency:
            raise ValueError("Cannot create exchange rate for same currency")

        # Create exchange rate record
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

    def get_exchange_rate_history(
        self,
        from_currency: str,
        to_currency: str,
        limit: Optional[int] = None
    ) -> List[ExchangeRateModel]:
        """
        Retrieve exchange rate history (audit trail).

        Returns all historical rates ordered by effective date (most recent first).

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
