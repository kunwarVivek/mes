"""
Unit tests for CostingService application service.
Phase 2: Material Management - Material Costing

Tests FIFO, LIFO, Weighted Average, and Standard costing calculations.
"""
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.application.services.costing_service import CostingService
from app.models.material import Material, MaterialCategory, UnitOfMeasure, ProcurementType, MRPType, DimensionType
from app.models.inventory import StorageLocation, LocationType, InventoryTransaction, TransactionType
from app.models.costing import MaterialCosting, CostLayer, CostingMethod
from app.models.currency import Currency as CurrencyModel


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

    # Setup default USD currency for backward compatibility
    usd_currency = CurrencyModel(
        code="USD",
        name="US Dollar",
        symbol="$",
        decimal_places=2
    )
    session.add(usd_currency)
    session.commit()

    yield session
    session.close()


class TestCostingServiceFIFO:
    """Test FIFO (First In First Out) costing calculations"""

    def test_calculate_fifo_single_batch(self, db_session):
        """Test FIFO cost calculation with single batch"""
        # Setup: Create material and cost layer
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

        # Create cost layer: 100 units @ $10
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
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        db_session.add(cost_layer)
        db_session.commit()

        # Test: Calculate cost for 50 units
        service = CostingService(db_session)
        result = service.calculate_fifo_cost(
            material_id=material.id,
            quantity=Decimal("50.0"),
            transaction_date=datetime(2025, 1, 15, tzinfo=timezone.utc)
        )

        # Verify
        assert result["total_cost"] == Decimal("500.00")  # 50 * $10
        assert result["unit_cost"] == Decimal("10.00")
        assert len(result["batches_used"]) == 1
        assert result["batches_used"][0]["batch_number"] == "BATCH001"
        assert result["batches_used"][0]["quantity_consumed"] == Decimal("50.0")

    def test_calculate_fifo_multiple_batches_complete(self, db_session):
        """Test FIFO with multiple batches, consuming oldest first"""
        # Setup
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
            category_code="COMP",
            category_name="Components"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="M002",
            material_name="Widget",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.REORDER
        )
        db_session.add(material)
        db_session.flush()

        location = StorageLocation(
            organization_id=1,
            plant_id=1,
            location_code="WH02",
            location_name="Component Storage",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Create cost layers:
        # Batch 1: 100 units @ $10 on Jan 1
        layer1 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH001",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        # Batch 2: 50 units @ $12 on Jan 5
        layer2 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH002",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("12.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 1, 5, tzinfo=timezone.utc),
            transaction_reference="PO-002"
        )
        db_session.add_all([layer1, layer2])
        db_session.commit()

        # Test: Issue 120 units (should consume all of batch 1 + 20 from batch 2)
        service = CostingService(db_session)
        result = service.calculate_fifo_cost(
            material_id=material.id,
            quantity=Decimal("120.0"),
            transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc)
        )

        # Verify
        # Cost = (100 * $10) + (20 * $12) = $1,000 + $240 = $1,240
        assert result["total_cost"] == Decimal("1240.00")
        assert result["unit_cost"] == Decimal("10.33")  # $1,240 / 120
        assert len(result["batches_used"]) == 2
        assert result["batches_used"][0]["batch_number"] == "BATCH001"
        assert result["batches_used"][0]["quantity_consumed"] == Decimal("100.0")
        assert result["batches_used"][1]["batch_number"] == "BATCH002"
        assert result["batches_used"][1]["quantity_consumed"] == Decimal("20.0")

    def test_calculate_fifo_insufficient_inventory(self, db_session):
        """Test FIFO with insufficient inventory raises error"""
        # Setup
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
            material_number="M003",
            material_name="Copper",
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
            location_code="WH03",
            location_name="Metal Storage",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Create cost layer with only 50 units
        cost_layer = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH001",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("15.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        db_session.add(cost_layer)
        db_session.commit()

        # Test: Try to issue 100 units (only 50 available)
        service = CostingService(db_session)
        with pytest.raises(ValueError) as exc_info:
            service.calculate_fifo_cost(
                material_id=material.id,
                quantity=Decimal("100.0"),
                transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc)
            )

        # Verify
        assert "Insufficient inventory" in str(exc_info.value)


class TestCostingServiceLIFO:
    """Test LIFO (Last In First Out) costing calculations"""

    def test_calculate_lifo_multiple_batches(self, db_session):
        """Test LIFO cost calculation consuming newest batches first"""
        # Setup
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
            category_code="COMP",
            category_name="Components"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="M004",
            material_name="Component X",
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
            location_code="WH04",
            location_name="Component Warehouse",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Create cost layers:
        # Batch 1: 100 units @ $10 on Jan 1 (oldest)
        layer1 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH001",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        # Batch 2: 50 units @ $12 on Jan 5 (newest)
        layer2 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH002",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("12.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 1, 5, tzinfo=timezone.utc),
            transaction_reference="PO-002"
        )
        db_session.add_all([layer1, layer2])
        db_session.commit()

        # Test: Issue 120 units using LIFO (should consume batch 2 fully + 70 from batch 1)
        service = CostingService(db_session)
        result = service.calculate_lifo_cost(
            material_id=material.id,
            quantity=Decimal("120.0"),
            transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc)
        )

        # Verify
        # Cost = (50 * $12) + (70 * $10) = $600 + $700 = $1,300
        assert result["total_cost"] == Decimal("1300.00")
        assert result["unit_cost"] == Decimal("10.83")  # $1,300 / 120
        assert len(result["batches_used"]) == 2
        # LIFO: newest first
        assert result["batches_used"][0]["batch_number"] == "BATCH002"
        assert result["batches_used"][0]["quantity_consumed"] == Decimal("50.0")
        assert result["batches_used"][1]["batch_number"] == "BATCH001"
        assert result["batches_used"][1]["quantity_consumed"] == Decimal("70.0")


class TestCostingServiceWeightedAverage:
    """Test Weighted Average costing calculations"""

    def test_calculate_weighted_average_cost(self, db_session):
        """Test weighted average cost calculation across multiple receipts"""
        # Setup
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
            material_number="M005",
            material_name="Plastic Resin",
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
            location_code="WH05",
            location_name="Raw Materials",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Create cost layers to simulate receipts:
        # Receipt 1: 100 units @ $10
        layer1 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH001",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        # Receipt 2: 50 units @ $12
        layer2 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH002",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("12.00"),
            currency_code="USD",
            receipt_date=datetime(2025, 1, 5, tzinfo=timezone.utc),
            transaction_reference="PO-002"
        )
        db_session.add_all([layer1, layer2])
        db_session.commit()

        # Test: Calculate weighted average cost for 120 units
        # Weighted avg = (100*$10 + 50*$12) / 150 = ($1,000 + $600) / 150 = $10.67
        service = CostingService(db_session)
        result = service.calculate_weighted_average_cost(
            material_id=material.id,
            quantity=Decimal("120.0"),
            transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc)
        )

        # Verify
        assert result["unit_cost"] == Decimal("10.67")
        assert result["total_cost"] == Decimal("1280.40")  # 120 * $10.67
        assert result["batches_used"] == []  # Weighted average doesn't track batches

    def test_update_moving_average(self, db_session):
        """Test updating moving average cost with new receipt"""
        # Setup
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
            material_number="M006",
            material_name="Solvent A",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.REORDER
        )
        db_session.add(material)
        db_session.flush()

        # Create MaterialCosting with current average
        costing = MaterialCosting(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            costing_method=CostingMethod.WEIGHTED_AVERAGE,
            currency_code="USD",
            current_average_cost=Decimal("10.00"),
            is_active=True
        )
        db_session.add(costing)
        db_session.commit()

        # Test: Update with new receipt of 50 units @ $12
        # Current: 100 units @ $10 (assumed)
        # New: (100*$10 + 50*$12) / 150 = $10.67
        service = CostingService(db_session)
        new_avg = service.update_moving_average(
            material_id=material.id,
            current_quantity=Decimal("100.0"),
            current_average_cost=Decimal("10.00"),
            new_quantity=Decimal("50.0"),
            new_unit_cost=Decimal("12.00")
        )

        # Verify
        assert new_avg == Decimal("10.67")


class TestCostingServiceStandard:
    """Test Standard costing calculations"""

    def test_calculate_standard_cost(self, db_session):
        """Test standard cost calculation (simple multiplication)"""
        # Setup
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
            material_number="M007",
            material_name="Product X",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.flush()

        # Create MaterialCosting with standard cost
        costing = MaterialCosting(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            costing_method=CostingMethod.STANDARD,
            currency_code="USD",
            standard_cost=Decimal("50.00"),
            is_active=True
        )
        db_session.add(costing)
        db_session.commit()

        # Test: Calculate cost for 100 units
        service = CostingService(db_session)
        result = service.calculate_standard_cost(
            material_id=material.id,
            quantity=Decimal("100.0")
        )

        # Verify
        assert result["total_cost"] == Decimal("5000.00")  # 100 * $50
        assert result["unit_cost"] == Decimal("50.00")
        assert result["batches_used"] == []  # Standard cost doesn't track batches

    def test_calculate_standard_cost_no_costing_record(self, db_session):
        """Test standard cost calculation when no costing record exists"""
        # Setup
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
            material_number="M008",
            material_name="Unknown Material",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.commit()

        # Test: Try to calculate standard cost without costing record
        service = CostingService(db_session)
        with pytest.raises(ValueError) as exc_info:
            service.calculate_standard_cost(
                material_id=material.id,
                quantity=Decimal("50.0")
            )

        # Verify
        assert "No costing record found" in str(exc_info.value)


class TestCostingServiceEdgeCases:
    """Test edge cases and error handling"""

    def test_zero_quantity_request(self, db_session):
        """Test that requesting zero quantity raises error"""
        # Setup
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
            category_code="MISC",
            category_name="Miscellaneous"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="M009",
            material_name="Item",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.REORDER
        )
        db_session.add(material)
        db_session.commit()

        # Test: Request cost for zero quantity
        service = CostingService(db_session)
        with pytest.raises(ValueError) as exc_info:
            service.calculate_fifo_cost(
                material_id=material.id,
                quantity=Decimal("0.0"),
                transaction_date=datetime.now(timezone.utc)
            )

        # Verify
        assert "Quantity must be positive" in str(exc_info.value)
