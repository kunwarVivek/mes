"""
Domain models for Currency Service.
Multi-Currency Costing Module - Domain Layer

Value objects and entities for currency operations.
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Currency:
    """
    Currency value object - immutable representation of a currency.

    Contains currency metadata for conversion and rounding operations.
    """
    code: str
    name: str
    symbol: str
    decimal_places: int

    def __post_init__(self):
        if self.decimal_places < 0 or self.decimal_places > 6:
            raise ValueError("Decimal places must be between 0 and 6")


@dataclass(frozen=True)
class ExchangeRate:
    """
    Exchange Rate value object - immutable exchange rate record.

    Represents conversion rate between two currencies at a specific time.
    """
    from_currency: str
    to_currency: str
    rate: Decimal
    effective_date: datetime
    created_by: str

    def __post_init__(self):
        if self.rate <= 0:
            raise ValueError("Exchange rate must be positive")
        if self.from_currency == self.to_currency:
            raise ValueError("From and to currencies must be different")


@dataclass(frozen=True)
class CurrencyRoundingRule:
    """
    Rounding rule for currency amounts.

    Defines how to round monetary values for specific currencies.
    """
    currency_code: str
    decimal_places: int

    def round_amount(self, amount: Decimal) -> Decimal:
        """
        Round amount according to currency rules.

        Args:
            amount: Amount to round

        Returns:
            Rounded amount
        """
        if self.decimal_places == 0:
            return amount.quantize(Decimal("1"))
        else:
            format_str = "0." + ("0" * self.decimal_places)
            return amount.quantize(Decimal(format_str))
