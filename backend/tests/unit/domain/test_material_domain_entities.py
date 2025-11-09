"""
Unit tests for Material domain entities (pure Python classes).
Tests business logic and validation rules.
"""
import pytest
from datetime import datetime
from app.domain.entities.material import (
    MaterialNumber,
    MaterialDomain,
    MaterialCategoryDomain,
    UnitOfMeasureDomain
)


class TestMaterialNumber:
    """Test MaterialNumber value object"""

    def test_create_valid_material_number(self):
        """Test creating a valid material number"""
        mat_num = MaterialNumber("MAT0001")
        assert mat_num.value == "MAT0001"

    def test_material_number_uppercase_conversion(self):
        """Test that material number is converted to uppercase"""
        mat_num = MaterialNumber("mat0001")
        assert mat_num.value == "MAT0001"

    def test_material_number_strip_whitespace(self):
        """Test that whitespace is stripped"""
        mat_num = MaterialNumber("  MAT0001  ")
        assert mat_num.value == "MAT0001"

    def test_material_number_max_length(self):
        """Test that material number cannot exceed 10 characters"""
        with pytest.raises(ValueError, match="cannot exceed 10 characters"):
            MaterialNumber("MATERIAL001")  # 11 chars

    def test_material_number_empty_validation(self):
        """Test that empty material number raises error"""
        with pytest.raises(ValueError, match="cannot be empty"):
            MaterialNumber("")

    def test_material_number_alphanumeric_validation(self):
        """Test that material number must be alphanumeric"""
        with pytest.raises(ValueError, match="must be alphanumeric"):
            MaterialNumber("MAT-0001")

    def test_material_number_equality(self):
        """Test equality comparison"""
        mat1 = MaterialNumber("MAT0001")
        mat2 = MaterialNumber("MAT0001")
        mat3 = MaterialNumber("MAT0002")

        assert mat1 == mat2
        assert mat1 != mat3

    def test_material_number_repr(self):
        """Test string representation"""
        mat_num = MaterialNumber("MAT0001")
        assert "MAT0001" in repr(mat_num)


class TestUnitOfMeasureDomain:
    """Test UnitOfMeasureDomain entity"""

    def test_create_base_uom(self):
        """Test creating a base unit"""
        uom = UnitOfMeasureDomain(
            id=1,
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )

        assert uom.uom_code == "EA"
        assert uom.is_base_unit is True
        assert uom.conversion_factor == 1.0

    def test_uom_code_uppercase_conversion(self):
        """Test that UOM code is converted to uppercase"""
        uom = UnitOfMeasureDomain(
            id=1,
            uom_code="kg",
            uom_name="Kilogram",
            dimension="MASS",
            is_base_unit=False,
            conversion_factor=1000.0
        )

        assert uom.uom_code == "KG"

    def test_base_unit_must_have_conversion_factor_one(self):
        """Test that base units must have conversion factor of 1.0"""
        with pytest.raises(ValueError, match="Base unit must have conversion factor of 1.0"):
            UnitOfMeasureDomain(
                id=1,
                uom_code="EA",
                uom_name="Each",
                dimension="QUANTITY",
                is_base_unit=True,
                conversion_factor=2.0  # Invalid for base unit
            )

    def test_conversion_factor_must_be_positive(self):
        """Test that conversion factor must be positive"""
        with pytest.raises(ValueError, match="Conversion factor must be positive"):
            UnitOfMeasureDomain(
                id=1,
                uom_code="KG",
                uom_name="Kilogram",
                dimension="MASS",
                is_base_unit=False,
                conversion_factor=0.0  # Invalid
            )

    def test_uom_code_cannot_be_empty(self):
        """Test that UOM code cannot be empty"""
        with pytest.raises(ValueError, match="UOM code cannot be empty"):
            UnitOfMeasureDomain(
                id=1,
                uom_code="",
                uom_name="Empty",
                dimension="QUANTITY",
                is_base_unit=True,
                conversion_factor=1.0
            )

    def test_uom_code_max_length(self):
        """Test that UOM code cannot exceed 10 characters"""
        with pytest.raises(ValueError, match="UOM code cannot exceed 10 characters"):
            UnitOfMeasureDomain(
                id=1,
                uom_code="VERYLONGCODE",
                uom_name="Long Code",
                dimension="QUANTITY",
                is_base_unit=True,
                conversion_factor=1.0
            )


class TestMaterialCategoryDomain:
    """Test MaterialCategoryDomain entity"""

    def test_create_root_category(self):
        """Test creating a root category"""
        category = MaterialCategoryDomain(
            id=1,
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            parent_category_id=None,
            is_active=True
        )

        assert category.category_code == "RAW"
        assert category.organization_id == 1
        assert category.parent_category_id is None
        assert category.is_active is True

    def test_category_code_uppercase_conversion(self):
        """Test that category code is converted to uppercase"""
        category = MaterialCategoryDomain(
            id=1,
            organization_id=1,
            category_code="raw",
            category_name="Raw Materials",
            is_active=True
        )

        assert category.category_code == "RAW"

    def test_activate_category(self):
        """Test activating a category"""
        category = MaterialCategoryDomain(
            id=1,
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=False
        )

        category.activate()
        assert category.is_active is True

    def test_deactivate_category(self):
        """Test deactivating a category"""
        category = MaterialCategoryDomain(
            id=1,
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )

        category.deactivate()
        assert category.is_active is False

    def test_category_code_cannot_be_empty(self):
        """Test that category code cannot be empty"""
        with pytest.raises(ValueError, match="Category code cannot be empty"):
            MaterialCategoryDomain(
                id=1,
                organization_id=1,
                category_code="",
                category_name="Empty Code",
                is_active=True
            )

    def test_category_code_max_length(self):
        """Test that category code cannot exceed 20 characters"""
        with pytest.raises(ValueError, match="Category code cannot exceed 20 characters"):
            MaterialCategoryDomain(
                id=1,
                organization_id=1,
                category_code="VERYLONGCATEGORYCODE1",
                category_name="Long Code",
                is_active=True
            )

    def test_organization_id_must_be_positive(self):
        """Test that organization ID must be positive"""
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            MaterialCategoryDomain(
                id=1,
                organization_id=0,
                category_code="RAW",
                category_name="Raw Materials",
                is_active=True
            )


class TestMaterialDomain:
    """Test MaterialDomain entity"""

    def test_create_material(self):
        """Test creating a material with valid data"""
        mat_num = MaterialNumber("MAT0001")
        material = MaterialDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number=mat_num,
            material_name="Steel Plate 10mm",
            description="Steel plate",
            material_category_id=1,
            base_uom_id=1,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=100.0,
            reorder_point=50.0,
            lot_size=500.0,
            lead_time_days=7,
            is_active=True
        )

        assert material.material_number.value == "MAT0001"
        assert material.organization_id == 1
        assert material.plant_id == 101
        assert material.safety_stock == 100.0
        assert material.is_active is True

    def test_activate_material(self):
        """Test activating a material"""
        mat_num = MaterialNumber("MAT0001")
        material = MaterialDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number=mat_num,
            material_name="Test Material",
            description="Test",
            material_category_id=1,
            base_uom_id=1,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=0.0,
            reorder_point=0.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=False
        )

        material.activate()
        assert material.is_active is True

    def test_deactivate_material(self):
        """Test deactivating a material"""
        mat_num = MaterialNumber("MAT0001")
        material = MaterialDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number=mat_num,
            material_name="Test Material",
            description="Test",
            material_category_id=1,
            base_uom_id=1,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=0.0,
            reorder_point=0.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )

        material.deactivate()
        assert material.is_active is False

    def test_update_safety_stock(self):
        """Test updating safety stock"""
        mat_num = MaterialNumber("MAT0001")
        material = MaterialDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number=mat_num,
            material_name="Test Material",
            description="Test",
            material_category_id=1,
            base_uom_id=1,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=100.0,
            reorder_point=50.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )

        material.update_safety_stock(200.0)
        assert material.safety_stock == 200.0

    def test_update_safety_stock_negative_validation(self):
        """Test that safety stock cannot be updated to negative"""
        mat_num = MaterialNumber("MAT0001")
        material = MaterialDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number=mat_num,
            material_name="Test Material",
            description="Test",
            material_category_id=1,
            base_uom_id=1,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=100.0,
            reorder_point=50.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )

        with pytest.raises(ValueError, match="Safety stock cannot be negative"):
            material.update_safety_stock(-10.0)

    def test_update_reorder_point(self):
        """Test updating reorder point"""
        mat_num = MaterialNumber("MAT0001")
        material = MaterialDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number=mat_num,
            material_name="Test Material",
            description="Test",
            material_category_id=1,
            base_uom_id=1,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=100.0,
            reorder_point=50.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )

        material.update_reorder_point(75.0)
        assert material.reorder_point == 75.0

    def test_update_lead_time(self):
        """Test updating lead time"""
        mat_num = MaterialNumber("MAT0001")
        material = MaterialDomain(
            id=1,
            organization_id=1,
            plant_id=101,
            material_number=mat_num,
            material_name="Test Material",
            description="Test",
            material_category_id=1,
            base_uom_id=1,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=100.0,
            reorder_point=50.0,
            lot_size=1.0,
            lead_time_days=7,
            is_active=True
        )

        material.update_lead_time(14)
        assert material.lead_time_days == 14

    def test_safety_stock_negative_validation(self):
        """Test that safety stock cannot be negative"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Safety stock cannot be negative"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="MRP",
                safety_stock=-10.0,
                reorder_point=50.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )

    def test_reorder_point_negative_validation(self):
        """Test that reorder point cannot be negative"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Reorder point cannot be negative"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="MRP",
                safety_stock=100.0,
                reorder_point=-50.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )

    def test_lot_size_must_be_positive(self):
        """Test that lot size must be positive"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Lot size must be positive"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="MRP",
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=0.0,
                lead_time_days=0,
                is_active=True
            )

    def test_lead_time_negative_validation(self):
        """Test that lead time cannot be negative"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Lead time cannot be negative"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="MRP",
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=1.0,
                lead_time_days=-5,
                is_active=True
            )

    def test_invalid_procurement_type(self):
        """Test that invalid procurement type raises error"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Invalid procurement type"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="INVALID",
                mrp_type="MRP",
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )

    def test_invalid_mrp_type(self):
        """Test that invalid MRP type raises error"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Invalid MRP type"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="INVALID",
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )

    def test_organization_id_must_be_positive(self):
        """Test that organization ID must be positive"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Organization ID must be positive"):
            MaterialDomain(
                id=1,
                organization_id=0,
                plant_id=101,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="MRP",
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )

    def test_plant_id_must_be_positive(self):
        """Test that plant ID must be positive"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Plant ID must be positive"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=0,
                material_number=mat_num,
                material_name="Test Material",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="MRP",
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )

    def test_material_name_cannot_be_empty(self):
        """Test that material name cannot be empty"""
        mat_num = MaterialNumber("MAT0001")

        with pytest.raises(ValueError, match="Material name cannot be empty"):
            MaterialDomain(
                id=1,
                organization_id=1,
                plant_id=101,
                material_number=mat_num,
                material_name="",
                description="Test",
                material_category_id=1,
                base_uom_id=1,
                procurement_type="PURCHASE",
                mrp_type="MRP",
                safety_stock=100.0,
                reorder_point=50.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )
