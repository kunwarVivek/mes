"""
Business Logic Verification Tests for Costing Service.
Phase 2: Material Management - Material Costing

Validates the exact business logic examples from requirements.
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.application.services.costing_service import CostingService
from app.models.material import Material, MaterialCategory, UnitOfMeasure, ProcurementType, MRPType, DimensionType
from app.models.inventory import StorageLocation, LocationType
from app.models.costing import CostLayer


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


class TestBusinessLogicExamples:
    """Verify exact business logic examples from requirements"""

    def test_fifo_example_from_requirements(self, db_session):
        """
        FIFO Example from requirements:
        Material A has batches: [100@$10 on Jan 1, 50@$12 on Jan 5]
        Issue 120 units -> Cost = (100*$10 + 20*$12) = $1,240, Unit cost = $10.33
        """
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
            category_code="TEST",
            category_name="Test Category"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT-A",
            material_name="Material A",
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

        # Create cost layers as specified
        layer1 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH-JAN1",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.00"),
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        layer2 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH-JAN5",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("12.00"),
            receipt_date=datetime(2025, 1, 5, tzinfo=timezone.utc),
            transaction_reference="PO-002"
        )
        db_session.add_all([layer1, layer2])
        db_session.commit()

        # Test: Issue 120 units using FIFO
        service = CostingService(db_session)
        result = service.calculate_fifo_cost(
            material_id=material.id,
            quantity=Decimal("120.0"),
            transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc)
        )

        # Verify exact business logic
        assert result["total_cost"] == Decimal("1240.00"), "Total cost should be $1,240"
        assert result["unit_cost"] == Decimal("10.33"), "Unit cost should be $10.33"
        assert len(result["batches_used"]) == 2
        assert result["batches_used"][0]["quantity_consumed"] == Decimal("100.0")
        assert result["batches_used"][1]["quantity_consumed"] == Decimal("20.0")

    def test_lifo_example_from_requirements(self, db_session):
        """
        LIFO Example from requirements:
        Same batches: [100@$10 on Jan 1, 50@$12 on Jan 5]
        Issue 120 units -> Cost = (50*$12 + 70*$10) = $1,300, Unit cost = $10.83
        """
        # Setup (same as FIFO)
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
            category_code="TEST",
            category_name="Test Category"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT-A",
            material_name="Material A",
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

        # Create cost layers
        layer1 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH-JAN1",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.00"),
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        layer2 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH-JAN5",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("12.00"),
            receipt_date=datetime(2025, 1, 5, tzinfo=timezone.utc),
            transaction_reference="PO-002"
        )
        db_session.add_all([layer1, layer2])
        db_session.commit()

        # Test: Issue 120 units using LIFO
        service = CostingService(db_session)
        result = service.calculate_lifo_cost(
            material_id=material.id,
            quantity=Decimal("120.0"),
            transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc)
        )

        # Verify exact business logic
        assert result["total_cost"] == Decimal("1300.00"), "Total cost should be $1,300"
        assert result["unit_cost"] == Decimal("10.83"), "Unit cost should be $10.83"
        assert len(result["batches_used"]) == 2
        # LIFO: newest first
        assert result["batches_used"][0]["quantity_consumed"] == Decimal("50.0")
        assert result["batches_used"][1]["quantity_consumed"] == Decimal("70.0")

    def test_weighted_average_example_from_requirements(self, db_session):
        """
        Weighted Average Example from requirements:
        (100@$10 + 50@$12) / 150 = $10.67
        Issue 120 units -> Cost = 120*$10.67 = $1,280.40
        """
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
            category_code="TEST",
            category_name="Test Category"
        )
        db_session.add(category)
        db_session.flush()

        material = Material(
            organization_id=1,
            plant_id=1,
            material_number="MAT-A",
            material_name="Material A",
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

        # Create cost layers
        layer1 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH-JAN1",
            quantity_received=Decimal("100.0"),
            quantity_remaining=Decimal("100.0"),
            unit_cost=Decimal("10.00"),
            receipt_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
            transaction_reference="PO-001"
        )
        layer2 = CostLayer(
            organization_id=1,
            plant_id=1,
            material_id=material.id,
            storage_location_id=location.id,
            batch_number="BATCH-JAN5",
            quantity_received=Decimal("50.0"),
            quantity_remaining=Decimal("50.0"),
            unit_cost=Decimal("12.00"),
            receipt_date=datetime(2025, 1, 5, tzinfo=timezone.utc),
            transaction_reference="PO-002"
        )
        db_session.add_all([layer1, layer2])
        db_session.commit()

        # Test: Issue 120 units using Weighted Average
        service = CostingService(db_session)
        result = service.calculate_weighted_average_cost(
            material_id=material.id,
            quantity=Decimal("120.0"),
            transaction_date=datetime(2025, 1, 10, tzinfo=timezone.utc)
        )

        # Verify exact business logic
        assert result["unit_cost"] == Decimal("10.67"), "Unit cost should be $10.67"
        assert result["total_cost"] == Decimal("1280.40"), "Total cost should be $1,280.40"
        assert result["batches_used"] == []  # Weighted average doesn't track batches
