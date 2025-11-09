"""
Integration tests for Multi-Currency Costing Module with existing CostingService.

Tests currency conversion in material costing calculations.
Demonstrates integration of CurrencyService with CostingService.
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.services.currency.currency_service import CurrencyService
from app.application.services.costing_service import CostingService
from app.models.material import Material, MaterialCategory, UnitOfMeasure, ProcurementType, MRPType, DimensionType
from app.models.inventory import StorageLocation, LocationType
from app.models.costing import MaterialCosting, CostLayer, CostingMethod
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
        CurrencyModel(code="INR", name="Indian Rupee", symbol="₹", decimal_places=2),
    ]
    db_session.add_all(currencies)
    db_session.commit()
    return {c.code: c for c in currencies}


@pytest.fixture
def setup_exchange_rates(db_session, setup_currencies):
    """Setup exchange rates"""
    rates = [
        ExchangeRateModel(
            from_currency_code="USD",
            to_currency_code="EUR",
            rate=Decimal("0.85"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        ),
        ExchangeRateModel(
            from_currency_code="USD",
            to_currency_code="INR",
            rate=Decimal("83.50"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="system"
        ),
    ]
    db_session.add_all(rates)
    db_session.commit()
    return rates


class TestMultiCurrencyCostingIntegration:
    """Test integration of currency service with costing calculations"""

    def test_fifo_cost_with_currency_conversion(self, db_session, setup_currencies, setup_exchange_rates):
        """Test FIFO costing with currency conversion to display currency"""
        # Setup material infrastructure
        uom = UnitOfMeasure(
            uom_code="KG",
            uom_name="Kilogram",
            dimension=DimensionType.MASS,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add(uom)
        db_session.flush()

        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="M001",
            material_name="Steel",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.flush()

        location = StorageLocation(
            organization_id=1,
            plant_id=1,
            location_code="WH01",
            location_name="Warehouse",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Create cost layer in USD: 100 units @ $10 each
        cost_layer = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH001",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        db_session.add(cost_layer)
        db_session.commit()

        # Calculate FIFO cost in USD
        costing_service = CostingService(db_session)
        usd_result = costing_service.calculate_fifo_cost(
            material_id=material.id,
            quantity=Decimal("50.0"),
            transaction_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # Verify USD calculation
        assert usd_result["total_cost"] == Decimal("500.00")  # 50 * $10
        assert usd_result["unit_cost"] == Decimal("10.00")

        # Convert to EUR for reporting
        currency_service = CurrencyService(db_session)
        eur_total = currency_service.convert(
            amount=usd_result["total_cost"],
            from_currency="USD",
            to_currency="EUR",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # Verify conversion: $500 * 0.85 = €425.00
        assert eur_total == Decimal("425.00")

    def test_standard_cost_multi_currency_display(self, db_session, setup_currencies, setup_exchange_rates):
        """Test standard costing with multi-currency display"""
        # Setup material
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension=DimensionType.QUANTITY,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add(uom)
        db_session.flush()

        category = MaterialCategory(
            organization_id=1,
            category_code="FG",
            category_name="Finished Goods"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="M002",
            material_name="Product X",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.flush()

        # Create MaterialCosting with standard cost in EUR
        costing = MaterialCosting(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            costing_method=CostingMethod.STANDARD,
            currency_code="EUR",
            standard_cost=Decimal("100.00"),  # €100 per unit
            is_active=True
        )
        db_session.add(costing)
        db_session.commit()

        # Calculate cost for 10 units in EUR
        costing_service = CostingService(db_session)
        eur_result = costing_service.calculate_standard_cost(
            material_id=material.id,
            quantity=Decimal("10.0")
        )

        # Verify EUR calculation
        assert eur_result["total_cost"] == Decimal("1000.00")  # 10 * €100
        assert eur_result["unit_cost"] == Decimal("100.00")

        # Convert to INR for Indian subsidiary reporting
        currency_service = CurrencyService(db_session)

        # First convert EUR to USD (inverse)
        usd_total = currency_service.convert(
            amount=eur_result["total_cost"],
            from_currency="EUR",
            to_currency="USD",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # Then convert USD to INR
        inr_total = currency_service.convert(
            amount=usd_total,
            from_currency="USD",
            to_currency="INR",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # Verify cross-currency conversion
        # €1000 -> $1176.47 (1/0.85) -> ₹98,255.24 (83.50)
        assert usd_total == Decimal("1176.47")
        assert inr_total == Decimal("98235.24")

    def test_cost_layers_different_currencies(self, db_session, setup_currencies, setup_exchange_rates):
        """Test cost layers stored in different currencies"""
        # Setup material
        uom = UnitOfMeasure(
            uom_code="L",
            uom_name="Liter",
            dimension=DimensionType.VOLUME,
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add(uom)
        db_session.flush()

        category = MaterialCategory(
            organization_id=1,
            category_code="CHEM",
            category_name="Chemicals"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="M003",
            material_name="Chemical A",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.flush()

        location = StorageLocation(
            organization_id=1,
            plant_id=1,
            location_code="WH02",
            location_name="Chemical Storage",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Create cost layers in different currencies
        layer_usd = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH_USD",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("50.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            transaction_reference="PO-USD-001"
        )

        layer_eur = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH_EUR",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("42.50"),
            currency_code="EUR",
            receipt_date=datetime(2025, 11, 5, tzinfo=timezone.utc),
            transaction_reference="PO-EUR-001"
        )

        db_session.add_all([layer_usd, layer_eur])
        db_session.commit()

        # Verify layers have correct currencies
        assert layer_usd.currency_code == "USD"
        assert layer_eur.currency_code == "EUR"

        # In a real scenario, you would normalize to a base currency before FIFO calculation
        # This test demonstrates that cost layers can be stored in different currencies
        currency_service = CurrencyService(db_session)

        # Convert EUR layer cost to USD for comparison
        eur_in_usd = currency_service.convert(
            amount=layer_eur.unit_cost,
            from_currency="EUR",
            to_currency="USD",
            conversion_date=datetime(2025, 11, 8, tzinfo=timezone.utc)
        )

        # €42.50 -> $50.00 (1/0.85)
        assert eur_in_usd == Decimal("50.00")


class TestCurrencyAuditTrail:
    """Test exchange rate audit trail functionality"""

    def test_exchange_rate_history_tracking(self, db_session, setup_currencies):
        """Test that exchange rate changes create audit trail"""
        currency_service = CurrencyService(db_session)

        # Create initial rate
        rate1 = currency_service.create_exchange_rate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.80"),
            effective_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
            created_by="admin"
        )

        # Update rate (creates new record)
        rate2 = currency_service.create_exchange_rate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.85"),
            effective_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
            created_by="admin"
        )

        # Another update
        rate3 = currency_service.create_exchange_rate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.90"),
            effective_date=datetime(2025, 11, 8, tzinfo=timezone.utc),
            created_by="finance_manager"
        )

        # Retrieve audit trail
        history = currency_service.get_exchange_rate_history(
            from_currency="USD",
            to_currency="EUR"
        )

        # Verify all records exist
        assert len(history) == 3
        assert history[0].rate == Decimal("0.90")
        assert history[0].created_by == "finance_manager"
        assert history[1].rate == Decimal("0.85")
        assert history[2].rate == Decimal("0.80")

        # Verify historical conversion uses correct rate
        conversion_oct = currency_service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="EUR",
            conversion_date=datetime(2025, 10, 15, tzinfo=timezone.utc)
        )
        assert conversion_oct == Decimal("80.00")  # Uses 0.80 rate

        conversion_nov_early = currency_service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="EUR",
            conversion_date=datetime(2025, 11, 5, tzinfo=timezone.utc)
        )
        assert conversion_nov_early == Decimal("85.00")  # Uses 0.85 rate

        conversion_nov_late = currency_service.convert(
            amount=Decimal("100.00"),
            from_currency="USD",
            to_currency="EUR",
            conversion_date=datetime(2025, 11, 10, tzinfo=timezone.utc)
        )
        assert conversion_nov_late == Decimal("90.00")  # Uses 0.90 rate
