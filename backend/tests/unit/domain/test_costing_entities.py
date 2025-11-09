"""
Unit tests for Costing domain entities.
Phase 2: Material Management - Material Costing

Tests MaterialCosting and CostLayer entities.
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.core.database import Base
from app.models.costing import MaterialCosting, CostLayer, CostingMethod
from app.models.material import Material, MaterialCategory, UnitOfMeasure, ProcurementType, MRPType, DimensionType
from app.models.inventory import StorageLocation, LocationType


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


class TestMaterialCosting:
    """Test MaterialCosting entity creation and validation"""

    def test_create_material_costing_standard(self, db_session):
        """Test creating MaterialCosting with STANDARD method"""
        # Setup: Create dependencies
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
            material_name="Steel Bar",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.flush()

        # Test: Create MaterialCosting
        costing = MaterialCosting(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            costing_method=CostingMethod.STANDARD,
            standard_cost=Decimal("100.50"),
            is_active=True
        )
        db_session.add(costing)
        db_session.commit()

        # Verify
        assert costing.id is not None
        assert costing.organization_id == 1
        assert costing.plant_id == 1
        assert costing.material_id == material.id
        assert costing.costing_method == CostingMethod.STANDARD
        assert costing.standard_cost == Decimal("100.50")
        assert costing.is_active is True
        assert costing.created_at is not None

    def test_create_material_costing_weighted_average(self, db_session):
        """Test creating MaterialCosting with WEIGHTED_AVERAGE method"""
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
            plant_id=2,
            material_number="M002",
            material_name="Product A",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.MANUFACTURE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.flush()

        # Test
        costing = MaterialCosting(
            organization_id=1,
            plant_id=2,
            material_id=material.id,
            costing_method=CostingMethod.WEIGHTED_AVERAGE,
            current_average_cost=Decimal("75.25"),
            is_active=True
        )
        db_session.add(costing)
        db_session.commit()

        # Verify
        assert costing.current_average_cost == Decimal("75.25")
        assert costing.costing_method == CostingMethod.WEIGHTED_AVERAGE

    def test_unique_constraint_per_material_per_plant(self, db_session):
        """Test that only one costing record is allowed per material per plant"""
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
            material_number="M003",
            material_name="Chemical X",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.REORDER
        )
        db_session.add(material)
        db_session.flush()

        # Create first costing record
        costing1 = MaterialCosting(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            costing_method=CostingMethod.FIFO,
            is_active=True
        )
        db_session.add(costing1)
        db_session.commit()

        # Test: Try to create duplicate
        costing2 = MaterialCosting(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            costing_method=CostingMethod.LIFO,
            is_active=True
        )
        db_session.add(costing2)

        # Verify: Should raise IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_negative_cost_validation(self, db_session):
        """Test that negative costs are rejected by check constraint"""
        # Setup
        uom = UnitOfMeasure(
            uom_code="M",
            uom_name="Meter",
            dimension=DimensionType.LENGTH,
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
            material_number="M004",
            material_name="Wire",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type=ProcurementType.PURCHASE,
            mrp_type=MRPType.MRP
        )
        db_session.add(material)
        db_session.flush()

        # Test: Try to create with negative standard_cost
        costing = MaterialCosting(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            costing_method=CostingMethod.STANDARD,
            standard_cost=Decimal("-10.00"),
            is_active=True
        )
        db_session.add(costing)

        # Verify: Should raise IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestCostLayer:
    """Test CostLayer entity for FIFO/LIFO tracking"""

    def test_create_cost_layer(self, db_session):
        """Test creating a cost layer for FIFO/LIFO tracking"""
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
            material_name="Copper Wire",
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
            location_name="Main Warehouse",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Test: Create cost layer
        cost_layer = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH001",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.50"),
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        db_session.add(cost_layer)
        db_session.commit()

        # Verify
        assert cost_layer.id is not None
        assert cost_layer.quantity_received == Decimal("100.0")
        assert cost_layer.quantity_remaining == Decimal("100.0")
        assert cost_layer.unit_cost == Decimal("10.50")
        assert cost_layer.batch_number == "BATCH001"

    def test_consume_quantity_partial(self, db_session):
        """Test consuming partial quantity from cost layer"""
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
            material_number="M006",
            material_name="Bolt M10",
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
            location_name="Component Warehouse",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        cost_layer = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH002",
            quantity_received=Decimal("200.0"),
            quantity_remaining=Decimal("200.0"),
            unit_cost=Decimal("0.50"),
            receipt_date=datetime.now(timezone.utc),
            transaction_reference="PO-002"
        )
        db_session.add(cost_layer)
        db_session.commit()

        # Test: Consume 50 units
        cost_layer.consume_quantity(Decimal("50.0"))
        db_session.commit()

        # Verify
        assert cost_layer.quantity_remaining == Decimal("150.0")
        assert cost_layer.quantity_received == Decimal("200.0")  # Unchanged

    def test_consume_quantity_full(self, db_session):
        """Test consuming full quantity from cost layer"""
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
            material_number="M007",
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
            location_code="WH03",
            location_name="Raw Material Storage",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        cost_layer = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH003",
            quantity_received=Decimal("75.0"),
            quantity_remaining=Decimal("75.0"),
            unit_cost=Decimal("25.00"),
            receipt_date=datetime.now(timezone.utc),
            transaction_reference="PO-003"
        )
        db_session.add(cost_layer)
        db_session.commit()

        # Test: Consume all 75 units
        cost_layer.consume_quantity(Decimal("75.0"))
        db_session.commit()

        # Verify
        assert cost_layer.quantity_remaining == Decimal("0.0")

    def test_consume_quantity_exceeds_remaining(self, db_session):
        """Test that consuming more than remaining quantity raises error"""
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
            material_number="M008",
            material_name="Solvent",
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
            location_code="WH04",
            location_name="Chemical Storage",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        cost_layer = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH004",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("30.0"),
            unit_cost=Decimal("15.00"),
            receipt_date=datetime.now(timezone.utc),
            transaction_reference="PO-004"
        )
        db_session.add(cost_layer)
        db_session.commit()

        # Test: Try to consume more than remaining
        with pytest.raises(ValueError) as exc_info:
            cost_layer.consume_quantity(Decimal("40.0"))

        # Verify
        assert "Insufficient remaining quantity" in str(exc_info.value)
        assert cost_layer.quantity_remaining == Decimal("30.0")  # Unchanged

    def test_quantity_remaining_validation(self, db_session):
        """Test that quantity_remaining cannot exceed quantity_received"""
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
            material_number="M009",
            material_name="Aluminum",
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
            location_name="Metal Storage",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.flush()

        # Test: Create with quantity_remaining > quantity_received
        cost_layer = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH005",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("150.0"),  # Invalid: more than received
            unit_cost=Decimal("20.00"),
            receipt_date=datetime.now(timezone.utc),
            transaction_reference="PO-005"
        )
        db_session.add(cost_layer)

        # Verify: Should raise IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()
