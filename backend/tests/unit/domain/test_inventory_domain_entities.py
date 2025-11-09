"""
Unit tests for Inventory domain entities (pure Python).
Tests: StorageLocationDomain, InventoryDomain, InventoryTransactionDomain
"""
import pytest
from datetime import datetime
from app.domain.entities.inventory import StorageLocationDomain, InventoryDomain, InventoryTransactionDomain


class TestStorageLocationDomain:
    """Tests for StorageLocationDomain entity"""

    def test_create_storage_location(self):
        """Test creating a storage location with all required fields"""
        location = StorageLocationDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            location_code="WH-A1",
            location_name="Warehouse A - Zone 1",
            location_type="WAREHOUSE"
        )

        assert location.id == 1
        assert location.organization_id == 1
        assert location.plant_id == 100
        assert location.location_code == "WH-A1"
        assert location.location_name == "Warehouse A - Zone 1"
        assert location.location_type == "WAREHOUSE"
        assert location.is_active is True

    def test_location_code_uppercase(self):
        """Test that location code is converted to uppercase"""
        location = StorageLocationDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            location_code="wh-a1",
            location_name="Warehouse A1",
            location_type="WAREHOUSE"
        )
        assert location.location_code == "WH-A1"

    def test_invalid_organization_id(self):
        """Test that organization_id must be positive"""
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            StorageLocationDomain(
                id=1,
                organization_id=0,
                plant_id=100,
                location_code="WH-A1",
                location_name="Test",
                location_type="WAREHOUSE"
            )

    def test_invalid_plant_id(self):
        """Test that plant_id must be positive"""
        with pytest.raises(ValueError, match="Plant ID must be positive"):
            StorageLocationDomain(
                id=1,
                organization_id=1,
                plant_id=-1,
                location_code="WH-A1",
                location_name="Test",
                location_type="WAREHOUSE"
            )

    def test_empty_location_code(self):
        """Test that location code cannot be empty"""
        with pytest.raises(ValueError, match="Location code cannot be empty"):
            StorageLocationDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                location_code="",
                location_name="Test",
                location_type="WAREHOUSE"
            )

    def test_location_code_too_long(self):
        """Test that location code cannot exceed 20 characters"""
        with pytest.raises(ValueError, match="cannot exceed 20 characters"):
            StorageLocationDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                location_code="A" * 21,
                location_name="Test",
                location_type="WAREHOUSE"
            )

    def test_invalid_location_type(self):
        """Test that location type must be valid"""
        with pytest.raises(ValueError, match="Invalid location type"):
            StorageLocationDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                location_code="WH-A1",
                location_name="Test",
                location_type="INVALID"
            )

    def test_activate_deactivate(self):
        """Test activate and deactivate methods"""
        location = StorageLocationDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            location_code="WH-A1",
            location_name="Test",
            location_type="WAREHOUSE",
            is_active=False
        )
        assert location.is_active is False

        location.activate()
        assert location.is_active is True

        location.deactivate()
        assert location.is_active is False

    def test_repr(self):
        """Test __repr__ method"""
        location = StorageLocationDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            location_code="WH-A1",
            location_name="Test",
            location_type="WAREHOUSE"
        )
        repr_str = repr(location)
        assert "StorageLocation" in repr_str
        assert "WH-A1" in repr_str
        assert "WAREHOUSE" in repr_str


class TestInventoryDomain:
    """Tests for InventoryDomain entity"""

    def test_create_inventory(self):
        """Test creating inventory with all required fields"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=1
        )

        assert inventory.id == 1
        assert inventory.organization_id == 1
        assert inventory.plant_id == 100
        assert inventory.material_id == 1001
        assert inventory.storage_location_id == 5
        assert inventory.batch_number == "BATCH001"
        assert inventory.quantity_on_hand == 100.0
        assert inventory.quantity_reserved == 20.0
        assert inventory.quantity_available == 80.0
        assert inventory.unit_of_measure_id == 1

    def test_quantity_available_computed(self):
        """Test that quantity_available is computed correctly"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=150.0,
            quantity_reserved=30.0,
            unit_of_measure_id=1
        )
        assert inventory.quantity_available == 120.0

    def test_quantity_on_hand_negative(self):
        """Test that quantity_on_hand cannot be negative"""
        with pytest.raises(ValueError, match="Quantity on hand cannot be negative"):
            InventoryDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                material_id=1001,
                storage_location_id=5,
                batch_number="BATCH001",
                quantity_on_hand=-10.0,
                quantity_reserved=0.0,
                unit_of_measure_id=1
            )

    def test_quantity_reserved_negative(self):
        """Test that quantity_reserved cannot be negative"""
        with pytest.raises(ValueError, match="Quantity reserved cannot be negative"):
            InventoryDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                material_id=1001,
                storage_location_id=5,
                batch_number="BATCH001",
                quantity_on_hand=100.0,
                quantity_reserved=-5.0,
                unit_of_measure_id=1
            )

    def test_reserved_exceeds_on_hand(self):
        """Test that reserved cannot exceed on_hand"""
        with pytest.raises(ValueError, match="Reserved quantity cannot exceed quantity on hand"):
            InventoryDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                material_id=1001,
                storage_location_id=5,
                batch_number="BATCH001",
                quantity_on_hand=50.0,
                quantity_reserved=60.0,
                unit_of_measure_id=1
            )

    def test_reserve_quantity_success(self):
        """Test reserving quantity when sufficient stock available"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=10.0,
            unit_of_measure_id=1
        )

        inventory.reserve_quantity(20.0)
        assert inventory.quantity_reserved == 30.0
        assert inventory.quantity_available == 70.0

    def test_reserve_quantity_insufficient_stock(self):
        """Test reserving quantity fails when insufficient stock"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=90.0,
            unit_of_measure_id=1
        )

        with pytest.raises(ValueError, match="Insufficient available quantity"):
            inventory.reserve_quantity(20.0)

    def test_reserve_negative_quantity(self):
        """Test that reserve quantity must be positive"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=10.0,
            unit_of_measure_id=1
        )

        with pytest.raises(ValueError, match="Quantity to reserve must be positive"):
            inventory.reserve_quantity(-5.0)

    def test_release_reserved_quantity(self):
        """Test releasing reserved quantity"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=40.0,
            unit_of_measure_id=1
        )

        inventory.release_reserved_quantity(15.0)
        assert inventory.quantity_reserved == 25.0
        assert inventory.quantity_available == 75.0

    def test_release_more_than_reserved(self):
        """Test releasing more than reserved quantity fails"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=1
        )

        with pytest.raises(ValueError, match="Cannot release more than reserved"):
            inventory.release_reserved_quantity(30.0)

    def test_release_negative_quantity(self):
        """Test that release quantity must be positive"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=1
        )

        with pytest.raises(ValueError, match="Quantity to release must be positive"):
            inventory.release_reserved_quantity(-5.0)

    def test_update_quantity(self):
        """Test updating quantity_on_hand"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=1
        )

        inventory.update_quantity(150.0)
        assert inventory.quantity_on_hand == 150.0
        assert inventory.quantity_available == 130.0
        assert inventory.last_movement_date is not None

    def test_update_quantity_below_reserved(self):
        """Test that update quantity cannot go below reserved"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=50.0,
            unit_of_measure_id=1
        )

        with pytest.raises(ValueError, match="Cannot set quantity on hand below reserved"):
            inventory.update_quantity(30.0)

    def test_adjust_quantity_positive(self):
        """Test adjusting quantity positively"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=1
        )

        inventory.adjust_quantity(50.0)
        assert inventory.quantity_on_hand == 150.0

    def test_adjust_quantity_negative(self):
        """Test adjusting quantity negatively"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=1
        )

        inventory.adjust_quantity(-30.0)
        assert inventory.quantity_on_hand == 70.0

    def test_repr(self):
        """Test __repr__ method"""
        inventory = InventoryDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            batch_number="BATCH001",
            quantity_on_hand=100.0,
            quantity_reserved=20.0,
            unit_of_measure_id=1
        )
        repr_str = repr(inventory)
        assert "Inventory" in repr_str
        assert "material_id=1001" in repr_str


class TestInventoryTransactionDomain:
    """Tests for InventoryTransactionDomain entity"""

    def test_create_goods_receipt(self):
        """Test creating a goods receipt transaction"""
        transaction = InventoryTransactionDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            transaction_type="GOODS_RECEIPT",
            transaction_reference="PO-12345",
            batch_number="BATCH001",
            quantity=100.0,
            unit_of_measure_id=1,
            unit_cost=10.50,
            total_value=1050.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1,
            notes="Purchase order receipt"
        )

        assert transaction.id == 1
        assert transaction.transaction_type == "GOODS_RECEIPT"
        assert transaction.quantity == 100.0
        assert transaction.total_value == 1050.0

    def test_create_goods_issue(self):
        """Test creating a goods issue transaction"""
        transaction = InventoryTransactionDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            transaction_type="GOODS_ISSUE",
            transaction_reference="WO-99999",
            batch_number="BATCH001",
            quantity=-50.0,
            unit_of_measure_id=1,
            unit_cost=10.50,
            total_value=-525.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1,
            notes="Production consumption"
        )

        assert transaction.transaction_type == "GOODS_ISSUE"
        assert transaction.quantity == -50.0

    def test_goods_receipt_positive_quantity(self):
        """Test that GOODS_RECEIPT must have positive quantity"""
        with pytest.raises(ValueError, match="GOODS_RECEIPT must have positive quantity"):
            InventoryTransactionDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                material_id=1001,
                storage_location_id=5,
                transaction_type="GOODS_RECEIPT",
                transaction_reference="PO-12345",
                batch_number="BATCH001",
                quantity=-100.0,
                unit_of_measure_id=1,
                unit_cost=10.0,
                total_value=-1000.0,
                transaction_date=datetime.utcnow(),
                posted_by_user_id=1
            )

    def test_goods_issue_negative_quantity(self):
        """Test that GOODS_ISSUE must have negative quantity"""
        with pytest.raises(ValueError, match="GOODS_ISSUE must have negative quantity"):
            InventoryTransactionDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                material_id=1001,
                storage_location_id=5,
                transaction_type="GOODS_ISSUE",
                transaction_reference="WO-12345",
                batch_number="BATCH001",
                quantity=50.0,
                unit_of_measure_id=1,
                unit_cost=10.0,
                total_value=500.0,
                transaction_date=datetime.utcnow(),
                posted_by_user_id=1
            )

    def test_transfer_in_positive_quantity(self):
        """Test that TRANSFER_IN must have positive quantity"""
        transaction = InventoryTransactionDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            transaction_type="TRANSFER_IN",
            transaction_reference="TRF-001",
            batch_number="BATCH001",
            quantity=30.0,
            unit_of_measure_id=1,
            unit_cost=10.0,
            total_value=300.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1
        )
        assert transaction.quantity == 30.0

    def test_transfer_out_negative_quantity(self):
        """Test that TRANSFER_OUT must have negative quantity"""
        transaction = InventoryTransactionDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            transaction_type="TRANSFER_OUT",
            transaction_reference="TRF-002",
            batch_number="BATCH001",
            quantity=-30.0,
            unit_of_measure_id=1,
            unit_cost=10.0,
            total_value=-300.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1
        )
        assert transaction.quantity == -30.0

    def test_adjustment_any_quantity(self):
        """Test that ADJUSTMENT can have any quantity sign"""
        # Positive adjustment
        transaction1 = InventoryTransactionDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            transaction_type="ADJUSTMENT",
            transaction_reference="ADJ-001",
            batch_number="BATCH001",
            quantity=5.0,
            unit_of_measure_id=1,
            unit_cost=10.0,
            total_value=50.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1
        )
        assert transaction1.quantity == 5.0

        # Negative adjustment
        transaction2 = InventoryTransactionDomain(
            id=2,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            transaction_type="ADJUSTMENT",
            transaction_reference="ADJ-002",
            batch_number="BATCH001",
            quantity=-3.0,
            unit_of_measure_id=1,
            unit_cost=10.0,
            total_value=-30.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1
        )
        assert transaction2.quantity == -3.0

    def test_invalid_transaction_type(self):
        """Test that transaction type must be valid"""
        with pytest.raises(ValueError, match="Invalid transaction type"):
            InventoryTransactionDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                material_id=1001,
                storage_location_id=5,
                transaction_type="INVALID_TYPE",
                transaction_reference="REF-001",
                batch_number="BATCH001",
                quantity=10.0,
                unit_of_measure_id=1,
                unit_cost=10.0,
                total_value=100.0,
                transaction_date=datetime.utcnow(),
                posted_by_user_id=1
            )

    def test_empty_transaction_reference(self):
        """Test that transaction reference cannot be empty"""
        with pytest.raises(ValueError, match="Transaction reference cannot be empty"):
            InventoryTransactionDomain(
                id=1,
                organization_id=1,
                plant_id=100,
                material_id=1001,
                storage_location_id=5,
                transaction_type="GOODS_RECEIPT",
                transaction_reference="",
                batch_number="BATCH001",
                quantity=100.0,
                unit_of_measure_id=1,
                unit_cost=10.0,
                total_value=1000.0,
                transaction_date=datetime.utcnow(),
                posted_by_user_id=1
            )

    def test_repr(self):
        """Test __repr__ method"""
        transaction = InventoryTransactionDomain(
            id=1,
            organization_id=1,
            plant_id=100,
            material_id=1001,
            storage_location_id=5,
            transaction_type="GOODS_RECEIPT",
            transaction_reference="PO-12345",
            batch_number="BATCH001",
            quantity=100.0,
            unit_of_measure_id=1,
            unit_cost=10.0,
            total_value=1000.0,
            transaction_date=datetime.utcnow(),
            posted_by_user_id=1
        )
        repr_str = repr(transaction)
        assert "InventoryTransaction" in repr_str
        assert "GOODS_RECEIPT" in repr_str
