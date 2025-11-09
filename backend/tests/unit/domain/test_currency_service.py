"""
Unit tests for Currency Service - Multi-Currency Costing Module.

Tests currency conversion, exchange rate management, and rounding rules.
Following strict TDD: RED -> GREEN -> REFACTOR
"""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.services.currency.currency_service import CurrencyService
from app.domain.services.currency.models import Currency, ExchangeRate, CurrencyRoundingRule
from app.models.currency import Currency as CurrencyModel, ExchangeRate as ExchangeRateModel


@pytest.fixture
def db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session for testing"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_currencies(db_session):
    """Setup common currencies for testing"""
    currencies = [
        CurrencyModel(code="USD", name="US Dollar", symbol="$", decimal_places=2),
        CurrencyModel(code="EUR", name="Euro", symbol="€", decimal_places=2),
        CurrencyModel(code="GBP", name="British Pound", symbol="£", decimal_places=2),
        CurrencyModel(code="INR", name="Indian Rupee", symbol="₹", decimal_places=2),
        CurrencyModel(code="JPY", name="Japanese Yen", symbol="¥", decimal_places=0),
        CurrencyModel(code="CNY", name="Chinese Yuan", symbol="¥", decimal_places=2),
    ]
    db_session.add_all(currencies)
    db_session.commit()
    return {c.code: c for c in currencies}


class TestCurrencyConversionBasic:
    """Test basic currency conversion functionality"""

    def test_convert_same_currency(self, db_session, setup_currencies):
        """Test converting amount in same currency returns original amount"""
        service = CurrencyService(db_session)

        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="USD",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        assert result == Decimal("100.00")

    def test_convert_usd_to_eur(self, db_session, setup_currencies):
        """Test USD to EUR conversion with exchange rate"""
        # Setup exchange rate: 1 USD = 0.85 EUR
        exchange_rate = ExchangeRateModel(
            from_currency_code="USD",
            to_currency_code="EUR",
            rate=Decimal("0.85"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        )
        db_session.add(exchange_rate)
        db_session.commit()

        service = CurrencyService(db_session)
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="EUR",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # 100 USD * 0.85 = 85.00 EUR
        assert result == Decimal("85.00")

    def test_convert_usd_to_jpy_with_rounding(self, db_session, setup_currencies):
        """Test USD to JPY conversion with 0 decimal places (JPY rounding rule)"""
        # Setup exchange rate: 1 USD = 110.50 JPY
        exchange_rate = ExchangeRateModel(
            from_currency_code="USD",
            to_currency_code="JPY",
            rate=Decimal("110.50"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        )
        db_session.add(exchange_rate)
        db_session.commit()

        service = CurrencyService(db_session)
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="JPY",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # 100 USD * 110.50 = 11050 JPY (rounded to 0 decimals)
        assert result == Decimal("11050")

    def test_convert_no_exchange_rate_raises_error(self, db_session, setup_currencies):
        """Test conversion fails when no exchange rate exists"""
        service = CurrencyService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.convert(
                amount=Decimal("100.00"),
                from_currency="USD",
                to_currency="EUR",
                conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
            )

        assert "No exchange rate found" in str(exc_info.value)


class TestHistoricalExchangeRates:
    """Test historical exchange rate lookups"""

    def test_get_latest_exchange_rate_before_date(self, db_session, setup_currencies):
        """Test retrieval of latest exchange rate before conversion date"""
        # Setup multiple exchange rates
        rates = [
            ExchangeRateModel(
                from_currency_code="USD",
                to_currency_code="EUR",
                rate=Decimal("0.80"),
                effective_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
                created_by="system"
            ),
            ExchangeRateModel(
                from_currency_code="USD",
                to_currency_code="EUR",
                rate=Decimal("0.85"),
                effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                created_by="system"
            ),
            ExchangeRateModel(
                from_currency_code="USD",
                to_currency_code="EUR",
                rate=Decimal("0.90"),
                effective_date=datetime(2025, 11, 15, tzinfo=timezone.utc),
                created_by="system"
            ),
        ]
        db_session.add_all(rates)
        db_session.commit()

        service = CurrencyService(db_session)

        # Convert on Nov 8 - should use Nov 1 rate (0.85), not Nov 15 rate
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="EUR",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        assert result == Decimal("85.00")

    def test_get_exchange_rate_exact_date_match(self, db_session, setup_currencies):
        """Test exchange rate retrieval with exact date match"""
        exchange_rate = ExchangeRateModel(
            from_currency_code="GBP",
            to_currency_code="USD",
            rate=Decimal("1.25"),
            effective_date=datetime(2025, 11, 8, tzinfo=timezone.utc),
            created_by="system"
        )
        db_session.add(exchange_rate)
        db_session.commit()

        service = CurrencyService(db_session)
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="GBP",
            to_currency="USD",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # 100 GBP * 1.25 = 125.00 USD
        assert result == Decimal("125.00")


class TestRoundingRules:
    """Test currency-specific rounding rules"""

    def test_usd_rounding_2_decimals(self, db_session, setup_currencies):
        """Test USD rounds to 2 decimal places"""
        exchange_rate = ExchangeRateModel(
            from_currency_code="EUR",
            to_currency_code="USD",
            rate=Decimal("1.17647"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        )
        db_session.add(exchange_rate)
        db_session.commit()

        service = CurrencyService(db_session)
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="EUR",
            to_currency="USD",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # 100 EUR * 1.17647 = 117.647 -> rounds to 117.65 USD
        assert result == Decimal("117.65")

    def test_jpy_rounding_0_decimals(self, db_session, setup_currencies):
        """Test JPY rounds to 0 decimal places"""
        exchange_rate = ExchangeRateModel(
            from_currency_code="USD",
            to_currency_code="JPY",
            rate=Decimal("110.555"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        )
        db_session.add(exchange_rate)
        db_session.commit()

        service = CurrencyService(db_session)
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="JPY",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # 100 USD * 110.555 = 11055.5 -> rounds to 11056 JPY
        assert result == Decimal("11056")

    def test_inr_rounding_2_decimals(self, db_session, setup_currencies):
        """Test INR rounds to 2 decimal places"""
        exchange_rate = ExchangeRateModel(
            from_currency_code="USD",
            to_currency_code="INR",
            rate=Decimal("83.456"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        )
        db_session.add(exchange_rate)
        db_session.commit()

        service = CurrencyService(db_session)
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="INR",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # 100 USD * 83.456 = 8345.6 -> rounds to 8345.60 INR
        assert result == Decimal("8345.60")


class TestInverseConversion:
    """Test inverse currency conversion (using reciprocal rates)"""

    def test_inverse_conversion_eur_to_usd(self, db_session, setup_currencies):
        """Test inverse conversion when only USD->EUR rate exists"""
        # Only setup USD->EUR rate
        exchange_rate = ExchangeRateModel(
            from_currency_code="USD",
            to_currency_code="EUR",
            rate=Decimal("0.85"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        )
        db_session.add(exchange_rate)
        db_session.commit()

        service = CurrencyService(db_session)

        # Convert EUR to USD using inverse (1 / 0.85 = 1.176470588...)
        result = service.convert(
            amount=Decimal("85.00"),
            from_currency="EUR",
            to_currency="USD",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # 85 EUR * (1/0.85) = 100.00 USD
        assert result == Decimal("100.00")


class TestCrossRateConversion:
    """Test cross-rate conversion through base currency"""

    def test_cross_rate_eur_to_gbp_via_usd(self, db_session, setup_currencies):
        """Test EUR->GBP conversion through USD base currency"""
        # Setup rates: EUR->USD and USD->GBP
        rates = [
            ExchangeRateModel(
                from_currency_code="EUR",
                to_currency_code="USD",
                rate=Decimal("1.18"),
                effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                created_by="system"
            ),
            ExchangeRateModel(
                from_currency_code="USD",
                to_currency_code="GBP",
                rate=Decimal("0.80"),
                effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                created_by="system"
            ),
        ]
        db_session.add_all(rates)
        db_session.commit()

        service = CurrencyService(db_session)

        # Convert EUR->GBP via USD: 100 EUR * 1.18 = 118 USD * 0.80 = 94.40 GBP
        result = service.convert(
            amount=Decimal("100.00"),
            from_currency="EUR",
            to_currency="GBP",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc),
            base_currency="USD"
        )

        assert result == Decimal("94.40")


class TestExchangeRateManagement:
    """Test exchange rate CRUD operations"""

    def test_create_exchange_rate(self, db_session, setup_currencies):
        """Test creating new exchange rate record"""
        service = CurrencyService(db_session)

        exchange_rate = service.create_exchange_rate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.85"),
            effective_date=datetime(2025, 11, 8, tzinfo=timezone.utc),
            created_by="admin"
        )

        assert exchange_rate.from_currency_code == "USD"
        assert exchange_rate.to_currency_code == "EUR"
        assert exchange_rate.rate == Decimal("0.85")
        assert exchange_rate.created_by == "admin"

    def test_update_exchange_rate_creates_new_record(self, db_session, setup_currencies):
        """Test updating exchange rate creates new historical record"""
        service = CurrencyService(db_session)

        # Create initial rate
        service.create_exchange_rate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.85"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="admin"
        )

        # Update rate (creates new record)
        new_rate = service.create_exchange_rate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.90"),
            effective_date=datetime(2025, 11, 8, tzinfo=timezone.utc),
            created_by="admin"
        )

        # Verify both records exist
        all_rates = db_session.query(ExchangeRateModel).filter(
            ExchangeRateModel.from_currency_code == "USD",
            ExchangeRateModel.to_currency_code == "EUR"
        ).all()

        assert len(all_rates) == 2
        assert new_rate.rate == Decimal("0.90")

    def test_get_exchange_rate_audit_trail(self, db_session, setup_currencies):
        """Test retrieving audit trail of exchange rate changes"""
        # Setup multiple historical rates
        rates = [
            ExchangeRateModel(
                from_currency_code="USD",
                to_currency_code="EUR",
                rate=Decimal("0.80"),
                effective_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
                created_by="admin"
            ),
            ExchangeRateModel(
                from_currency_code="USD",
                to_currency_code="EUR",
                rate=Decimal("0.85"),
                effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
                created_by="admin"
            ),
            ExchangeRateModel(
                from_currency_code="USD",
                to_currency_code="EUR",
                rate=Decimal("0.90"),
                effective_date=datetime(2025, 11, 8, tzinfo=timezone.utc),
                created_by="admin"
            ),
        ]
        db_session.add_all(rates)
        db_session.commit()

        service = CurrencyService(db_session)
        audit_trail = service.get_exchange_rate_history(
            from_currency="USD",
            to_currency="EUR"
        )

        assert len(audit_trail) == 3
        assert audit_trail[0].rate == Decimal("0.90")  # Most recent first
        assert audit_trail[1].rate == Decimal("0.85")
        assert audit_trail[2].rate == Decimal("0.80")


class TestValidation:
    """Test input validation and error handling"""

    def test_negative_amount_raises_error(self, db_session, setup_currencies):
        """Test conversion with negative amount raises error"""
        service = CurrencyService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.convert(
                amount=Decimal("-100.00"),
                from_currency="USD",
                to_currency="EUR",
                conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
            )

        assert "Amount must be non-negative" in str(exc_info.value)

    def test_invalid_currency_code_raises_error(self, db_session, setup_currencies):
        """Test conversion with invalid currency code raises error"""
        service = CurrencyService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.convert(
                amount=Decimal("100.00"),
                from_currency="XXX",
                to_currency="USD",
                conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
            )

        assert "Invalid currency" in str(exc_info.value)

    def test_negative_exchange_rate_raises_error(self, db_session, setup_currencies):
        """Test creating exchange rate with negative rate raises error"""
        service = CurrencyService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.create_exchange_rate(
                from_currency="USD",
                to_currency="EUR",
                rate=Decimal("-0.85"),
                effective_date=datetime(2025, 11, 8, tzinfo=timezone.utc),
                created_by="admin"
            )

        assert "Exchange rate must be positive" in str(exc_info.value)
