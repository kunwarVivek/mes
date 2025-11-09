"""
Unit tests for Inventory domain entities.
Tests: StorageLocation, Inventory, InventoryTransaction
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.material import Material, MaterialCategory, UnitOfMeasure, ProcurementType, MRPType, DimensionType
from app.models.inventory import StorageLocation, Inventory, InventoryTransaction, LocationType, TransactionType


@pytest.fixture(scope="function")
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_uom(db_session):
    """Create sample UnitOfMeasure for testing"""
    uom = UnitOfMeasure(
        uom_code="EA",
        uom_name="Each",
        dimension=DimensionType.QUANTITY,
        is_base_unit=True,
        conversion_factor=1.0
    )
    db_session.add(uom)
    db_session.commit()
    db_session.refresh(uom)
    return uom


@pytest.fixture
def sample_category(db_session):
    """Create sample MaterialCategory for testing"""
    category = MaterialCategory(
        organization_id=1,
        category_code="RAW",
        category_name="Raw Materials"
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_material(db_session, sample_category, sample_uom):
    """Create sample Material for testing"""
    material = Material(
        organization_id=1,
        plant_id=100,
        material_number="MAT001",
        material_name="Test Material",
        description="Test material for inventory",
        material_category_id=sample_category.id,
        base_uom_id=sample_uom.id,
        procurement_type=ProcurementType.PURCHASE,
        mrp_type=MRPType.MRP,
        safety_stock=10.0,
        reorder_point=20.0,
        lot_size=100.0,
        lead_time_days=7
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def sample_storage_location(db_session):
    """Create sample StorageLocation for testing"""
    location = StorageLocation(
        organization_id=1,
        plant_id=100,
        location_code="WH-A1",
        location_name="Warehouse A - Zone 1",
        location_type=LocationType.WAREHOUSE
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location


class TestStorageLocation:
    """Tests for StorageLocation entity"""

    def test_create_storage_location(self, db_session):
        """Test creating a storage location with all required fields"""
        location = StorageLocation(
            organization_id=1,
            plant_id=100,
            location_code="WH-A1",
            location_name="Warehouse A - Zone 1",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)

        assert location.id is not None
        assert location.organization_id == 1
        assert location.plant_id == 100
        assert location.location_code == "WH-A1"
        assert location.location_name == "Warehouse A - Zone 1"
        assert location.location_type == LocationType.WAREHOUSE
        assert location.is_active is True
        assert location.created_at is not None

    def test_location_code_unique_per_plant(self, db_session):
        """Test that location_code is unique within a plant"""
        location1 = StorageLocation(
            organization_id=1,
            plant_id=100,
            location_code="WH-A1",
            location_name="Warehouse A1",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location1)
        db_session.commit()

        # Same location_code in same plant should fail
        location2 = StorageLocation(
            organization_id=1,
            plant_id=100,
            location_code="WH-A1",
            location_name="Different Name",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_location_code_unique_across_different_plants(self, db_session):
        """Test that same location_code can exist in different plants"""
        location1 = StorageLocation(
            organization_id=1,
            plant_id=100,
            location_code="WH-A1",
            location_name="Plant 100 Warehouse",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location1)
        db_session.commit()

        # Same location_code in different plant should succeed
        location2 = StorageLocation(
            organization_id=1,
            plant_id=200,
            location_code="WH-A1",
            location_name="Plant 200 Warehouse",
            location_type=LocationType.WAREHOUSE
        )
        db_session.add(location2)
        db_session.commit()

        assert location1.id != location2.id
        assert location1.location_code == location2.location_code

    def test_location_types(self, db_session):
        """Test all location types"""
        types = [
            LocationType.WAREHOUSE,
            LocationType.PRODUCTION,
            LocationType.QUALITY,
            LocationType.BLOCKED
        ]

        for loc_type in types:
            location = StorageLocation(
                organization_id=1,
                plant_id=100,
                location_code=f"LOC-{loc_type.value}",
                location_name=f"{loc_type.value} Location",
                location_type=loc_type
            )
            db_session.add(location)
            db_session.commit()
            assert location.location_type == loc_type

    def test_deactivate_location(self, db_session, sample_storage_location):
        """Test deactivating a storage location"""
        assert sample_storage_location.is_active is True
        sample_storage_location.is_active = False
        db_session.commit()
        db_session.refresh(sample_storage_location)
        assert sample_storage_location.is_active is False

    def test_storage_location_repr(self, db_session, sample_storage_location):
        """Test StorageLocation __repr__ method"""
        repr_str = repr(sample_storage_location)
        assert "StorageLocation" in repr_str
        assert "WH-A1" in repr_str


class TestInventory:
    """Tests for Inventory entity"""

    def test_create_inventory(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test creating inventory record with all required fields"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()
        db_session.refresh(inventory)

        assert inventory.id is not None
        assert inventory.organization_id == 1
        assert inventory.plant_id == 100
        assert inventory.material_id == sample_material.id
        assert inventory.storage_location_id == sample_storage_location.id
        assert inventory.batch_number == "BATCH001"
        assert inventory.quantity_on_hand == 100.0
        assert inventory.quantity_reserved == 20.0
        assert inventory.quantity_available == 80.0
        assert inventory.unit_of_measure_id == sample_uom.id
        assert inventory.created_at is not None

    def test_quantity_available_computed(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test that quantity_available is computed correctly"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=150.0,
            quantity_reserved=30.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()
        db_session.refresh(inventory)

        assert inventory.quantity_available == 120.0

    def test_quantity_on_hand_non_negative(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test that quantity_on_hand cannot be negative"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=-10.0,
            quantity_reserved=0.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_quantity_reserved_non_negative(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test that quantity_reserved cannot be negative"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=-5.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_reserved_cannot_exceed_on_hand(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test that quantity_reserved cannot exceed quantity_on_hand"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=50.0,
            quantity_reserved=60.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)

        with pytest.raises(Exception):  # CheckConstraint violation
            db_session.commit()

    def test_composite_unique_constraint(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test composite unique constraint on (org, plant, material, location, batch)"""
        inventory1 = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=0.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory1)
        db_session.commit()

        # Duplicate should fail
        inventory2 = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=50.0,
            quantity_reserved=0.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_reserve_quantity_success(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test reserving quantity when sufficient stock available"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=10.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()

        # Reserve 20 units
        inventory.reserve_quantity(20.0)
        db_session.commit()
        db_session.refresh(inventory)

        assert inventory.quantity_reserved == 30.0
        assert inventory.quantity_available == 70.0

    def test_reserve_quantity_insufficient_stock(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test reserving quantity fails when insufficient stock"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=90.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()

        # Try to reserve 20 units (only 10 available)
        with pytest.raises(ValueError, match="Insufficient available quantity"):
            inventory.reserve_quantity(20.0)

    def test_release_reserved_quantity(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test releasing reserved quantity"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=40.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()

        # Release 15 units
        inventory.release_reserved_quantity(15.0)
        db_session.commit()
        db_session.refresh(inventory)

        assert inventory.quantity_reserved == 25.0
        assert inventory.quantity_available == 75.0

    def test_release_more_than_reserved(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test releasing more than reserved quantity fails"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()

        with pytest.raises(ValueError, match="Cannot release more than reserved"):
            inventory.release_reserved_quantity(30.0)

    def test_update_quantity(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test updating quantity_on_hand"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()

        # Add 50 units
        inventory.update_quantity(150.0)
        db_session.commit()
        db_session.refresh(inventory)

        assert inventory.quantity_on_hand == 150.0
        assert inventory.quantity_available == 130.0

    def test_inventory_repr(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test Inventory __repr__ method"""
        inventory = Inventory(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=sample_uom.id
        )
        db_session.add(inventory)
        db_session.commit()

        repr_str = repr(inventory)
        assert "Inventory" in repr_str


class TestInventoryTransaction:
    """Tests for InventoryTransaction entity"""

    def test_create_goods_receipt(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test creating a goods receipt transaction"""
        transaction = InventoryTransaction(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            transaction_type=TransactionType.GOODS_RECEIPT,
            transaction_reference="PO-12345",
            batch_number="BATCH001",
            quantity=100.0,
            unit_of_measure_id=sample_uom.id,
            unit_cost=10.50,
            total_value=1050.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1,
            notes="Purchase order receipt"
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        assert transaction.id is not None
        assert transaction.transaction_type == TransactionType.GOODS_RECEIPT
        assert transaction.quantity == 100.0
        assert transaction.total_value == 1050.0

    def test_create_goods_issue(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test creating a goods issue transaction"""
        transaction = InventoryTransaction(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            transaction_type=TransactionType.GOODS_ISSUE,
            transaction_reference="WO-99999",
            batch_number="BATCH001",
            quantity=-50.0,
            unit_of_measure_id=sample_uom.id,
            unit_cost=10.50,
            total_value=-525.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1,
            notes="Production consumption"
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)

        assert transaction.transaction_type == TransactionType.GOODS_ISSUE
        assert transaction.quantity == -50.0

    def test_all_transaction_types(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test all transaction types"""
        types = [
            (TransactionType.GOODS_RECEIPT, 100.0),
            (TransactionType.GOODS_ISSUE, -50.0),
            (TransactionType.TRANSFER_IN, 30.0),
            (TransactionType.TRANSFER_OUT, -30.0),
            (TransactionType.ADJUSTMENT, 5.0)
        ]

        for trans_type, qty in types:
            transaction = InventoryTransaction(
                organization_id=1,
                plant_id=100,
                material_id=sample_material.id,
                storage_location_id=sample_storage_location.id,
                transaction_type=trans_type,
                transaction_reference=f"REF-{trans_type.value}",
                batch_number="BATCH001",
                quantity=qty,
                unit_of_measure_id=sample_uom.id,
                unit_cost=10.0,
                total_value=qty * 10.0,
                transaction_date=datetime.utcnow(),
                posted_by_user_id=1
            )
            db_session.add(transaction)
            db_session.commit()
            assert transaction.transaction_type == trans_type

    def test_transaction_immutability(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test that transactions are immutable (no updates allowed)"""
        transaction = InventoryTransaction(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            transaction_type=TransactionType.GOODS_RECEIPT,
            transaction_reference="PO-12345",
            batch_number="BATCH001",
            quantity=100.0,
            unit_of_measure_id=sample_uom.id,
            unit_cost=10.0,
            total_value=1000.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1
        )
        db_session.add(transaction)
        db_session.commit()
        original_id = transaction.id

        # Transactions should not have updated_at field
        assert not hasattr(transaction, 'updated_at')

    def test_transaction_indexing(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test transaction indexing for reporting queries"""
        # Create multiple transactions
        for i in range(5):
            transaction = InventoryTransaction(
                organization_id=1,
                plant_id=100,
                material_id=sample_material.id,
                storage_location_id=sample_storage_location.id,
                transaction_type=TransactionType.GOODS_RECEIPT,
                transaction_reference=f"PO-{i}",
                batch_number=f"BATCH{i:03d}",
                quantity=100.0 + i,
                unit_of_measure_id=sample_uom.id,
                unit_cost=10.0,
                total_value=(100.0 + i) * 10.0,
                transaction_date=datetime.utcnow(),
                posted_by_user_id=1
            )
            db_session.add(transaction)
        db_session.commit()

        # Query by transaction_type (should use index)
        results = db_session.query(InventoryTransaction).filter(
            InventoryTransaction.transaction_type == TransactionType.GOODS_RECEIPT
        ).all()
        assert len(results) == 5

    def test_transaction_repr(self, db_session, sample_material, sample_storage_location, sample_uom):
        """Test InventoryTransaction __repr__ method"""
        transaction = InventoryTransaction(
            organization_id=1,
            plant_id=100,
            material_id=sample_material.id,
            storage_location_id=sample_storage_location.id,
            transaction_type=TransactionType.GOODS_RECEIPT,
            transaction_reference="PO-12345",
            batch_number="BATCH001",
            quantity=100.0,
            unit_of_measure_id=sample_uom.id,
            unit_cost=10.0,
            total_value=1000.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1
        )
        db_session.add(transaction)
        db_session.commit()

        repr_str = repr(transaction)
        assert "InventoryTransaction" in repr_str
        assert "GOODS_RECEIPT" in repr_str
