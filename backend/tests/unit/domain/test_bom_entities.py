"""
Unit tests for BOM (Bill of Materials) domain entities.
Tests BOMHeader and BOMLine domain entities following TDD approach.
"""
import pytest
from datetime import datetime, date, timedelta
from app.domain.entities.bom import (
    BOMHeaderDomain,
    BOMLineDomain,
    BOMNumber,
    BOMType
)


class TestBOMNumber:
    """Tests for BOMNumber value object"""

    def test_create_valid_bom_number(self):
        """Test creating a valid BOM number"""
        bom_num = BOMNumber("BOM-001")
        assert bom_num.value == "BOM-001"

    def test_bom_number_strips_whitespace(self):
        """Test BOM number strips whitespace"""
        bom_num = BOMNumber("  BOM-002  ")
        assert bom_num.value == "BOM-002"

    def test_bom_number_uppercase_conversion(self):
        """Test BOM number converts to uppercase"""
        bom_num = BOMNumber("bom-003")
        assert bom_num.value == "BOM-003"

    def test_bom_number_empty_raises_error(self):
        """Test empty BOM number raises ValueError"""
        with pytest.raises(ValueError, match="BOM number cannot be empty"):
            BOMNumber("")

    def test_bom_number_max_length_50(self):
        """Test BOM number max length is 50 characters"""
        with pytest.raises(ValueError, match="BOM number cannot exceed 50 characters"):
            BOMNumber("A" * 51)

    def test_bom_number_equality(self):
        """Test BOM number equality comparison"""
        bom1 = BOMNumber("BOM-001")
        bom2 = BOMNumber("BOM-001")
        bom3 = BOMNumber("BOM-002")
        assert bom1 == bom2
        assert bom1 != bom3

    def test_bom_number_repr(self):
        """Test BOM number string representation"""
        bom_num = BOMNumber("BOM-001")
        assert repr(bom_num) == "BOMNumber('BOM-001')"


class TestBOMHeaderDomain:
    """Tests for BOMHeader domain entity"""

    def test_create_valid_bom_header(self):
        """Test creating a valid BOM header"""
        bom_num = BOMNumber("BOM-001")
        header = BOMHeaderDomain(
            id=1,
            organization_id=100,
            plant_id=200,
            bom_number=bom_num,
            material_id=1000,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=10,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=500
        )
        assert header.id == 1
        assert header.organization_id == 100
        assert header.plant_id == 200
        assert header.bom_number.value == "BOM-001"
        assert header.material_id == 1000
        assert header.bom_version == 1
        assert header.bom_name == "Product A BOM"
        assert header.bom_type == BOMType.PRODUCTION
        assert header.base_quantity == 1.0
        assert header.is_active is True

    def test_bom_header_base_quantity_positive(self):
        """Test BOM header base quantity must be positive"""
        bom_num = BOMNumber("BOM-001")
        with pytest.raises(ValueError, match="Base quantity must be positive"):
            BOMHeaderDomain(
                id=1,
                organization_id=100,
                plant_id=200,
                bom_number=bom_num,
                material_id=1000,
                bom_version=1,
                bom_name="Product A BOM",
                bom_type=BOMType.PRODUCTION,
                base_quantity=0.0,  # Invalid
                unit_of_measure_id=10,
                effective_start_date=date(2024, 1, 1),
                effective_end_date=date(2024, 12, 31),
                is_active=True,
                created_by_user_id=500
            )

    def test_bom_header_version_minimum_one(self):
        """Test BOM header version must be at least 1"""
        bom_num = BOMNumber("BOM-001")
        with pytest.raises(ValueError, match="BOM version must be at least 1"):
            BOMHeaderDomain(
                id=1,
                organization_id=100,
                plant_id=200,
                bom_number=bom_num,
                material_id=1000,
                bom_version=0,  # Invalid
                bom_name="Product A BOM",
                bom_type=BOMType.PRODUCTION,
                base_quantity=1.0,
                unit_of_measure_id=10,
                effective_start_date=date(2024, 1, 1),
                effective_end_date=date(2024, 12, 31),
                is_active=True,
                created_by_user_id=500
            )

    def test_bom_header_effective_dates_validation(self):
        """Test BOM header effective_start_date must be before effective_end_date"""
        bom_num = BOMNumber("BOM-001")
        with pytest.raises(ValueError, match="Effective start date must be before or equal to effective end date"):
            BOMHeaderDomain(
                id=1,
                organization_id=100,
                plant_id=200,
                bom_number=bom_num,
                material_id=1000,
                bom_version=1,
                bom_name="Product A BOM",
                bom_type=BOMType.PRODUCTION,
                base_quantity=1.0,
                unit_of_measure_id=10,
                effective_start_date=date(2024, 12, 31),  # After end date
                effective_end_date=date(2024, 1, 1),
                is_active=True,
                created_by_user_id=500
            )

    def test_bom_header_organization_id_positive(self):
        """Test BOM header organization_id must be positive"""
        bom_num = BOMNumber("BOM-001")
        with pytest.raises(ValueError, match="Organization ID must be positive"):
            BOMHeaderDomain(
                id=1,
                organization_id=0,  # Invalid
                plant_id=200,
                bom_number=bom_num,
                material_id=1000,
                bom_version=1,
                bom_name="Product A BOM",
                bom_type=BOMType.PRODUCTION,
                base_quantity=1.0,
                unit_of_measure_id=10,
                effective_start_date=date(2024, 1, 1),
                effective_end_date=date(2024, 12, 31),
                is_active=True,
                created_by_user_id=500
            )

    def test_bom_header_plant_id_positive(self):
        """Test BOM header plant_id must be positive"""
        bom_num = BOMNumber("BOM-001")
        with pytest.raises(ValueError, match="Plant ID must be positive"):
            BOMHeaderDomain(
                id=1,
                organization_id=100,
                plant_id=-1,  # Invalid
                bom_number=bom_num,
                material_id=1000,
                bom_version=1,
                bom_name="Product A BOM",
                bom_type=BOMType.PRODUCTION,
                base_quantity=1.0,
                unit_of_measure_id=10,
                effective_start_date=date(2024, 1, 1),
                effective_end_date=date(2024, 12, 31),
                is_active=True,
                created_by_user_id=500
            )

    def test_bom_header_activate(self):
        """Test BOM header activate() business logic"""
        bom_num = BOMNumber("BOM-001")
        header = BOMHeaderDomain(
            id=1,
            organization_id=100,
            plant_id=200,
            bom_number=bom_num,
            material_id=1000,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=10,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=False,
            created_by_user_id=500
        )
        header.activate()
        assert header.is_active is True

    def test_bom_header_deactivate(self):
        """Test BOM header deactivate() business logic"""
        bom_num = BOMNumber("BOM-001")
        header = BOMHeaderDomain(
            id=1,
            organization_id=100,
            plant_id=200,
            bom_number=bom_num,
            material_id=1000,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=10,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=500
        )
        header.deactivate()
        assert header.is_active is False

    def test_bom_header_create_new_version(self):
        """Test BOM header create_new_version() business logic"""
        bom_num = BOMNumber("BOM-001")
        header = BOMHeaderDomain(
            id=1,
            organization_id=100,
            plant_id=200,
            bom_number=bom_num,
            material_id=1000,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=10,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=500
        )
        new_version = header.create_new_version(
            new_effective_start=date(2025, 1, 1),
            new_effective_end=date(2025, 12, 31)
        )
        assert new_version.bom_version == 2
        assert new_version.effective_start_date == date(2025, 1, 1)
        assert new_version.is_active is False  # New version starts inactive
        assert new_version.id is None  # New entity, not yet persisted

    def test_bom_header_repr(self):
        """Test BOM header string representation"""
        bom_num = BOMNumber("BOM-001")
        header = BOMHeaderDomain(
            id=1,
            organization_id=100,
            plant_id=200,
            bom_number=bom_num,
            material_id=1000,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=10,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=500
        )
        assert "BOM-001" in repr(header)
        assert "version=1" in repr(header)


class TestBOMLineDomain:
    """Tests for BOMLine domain entity"""

    def test_create_valid_bom_line(self):
        """Test creating a valid BOM line"""
        line = BOMLineDomain(
            id=1,
            bom_header_id=100,
            line_number=10,
            component_material_id=2000,
            quantity=5.0,
            unit_of_measure_id=10,
            scrap_factor=10.0,
            operation_number=10,
            is_phantom=False,
            backflush=True
        )
        assert line.id == 1
        assert line.bom_header_id == 100
        assert line.line_number == 10
        assert line.component_material_id == 2000
        assert line.quantity == 5.0
        assert line.scrap_factor == 10.0
        assert line.is_phantom is False
        assert line.backflush is True

    def test_bom_line_quantity_positive(self):
        """Test BOM line quantity must be positive"""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            BOMLineDomain(
                id=1,
                bom_header_id=100,
                line_number=10,
                component_material_id=2000,
                quantity=0.0,  # Invalid
                unit_of_measure_id=10,
                scrap_factor=0.0,
                operation_number=None,
                is_phantom=False,
                backflush=False
            )

    def test_bom_line_scrap_factor_range(self):
        """Test BOM line scrap factor must be between 0 and 100"""
        with pytest.raises(ValueError, match="Scrap factor must be between 0 and 100"):
            BOMLineDomain(
                id=1,
                bom_header_id=100,
                line_number=10,
                component_material_id=2000,
                quantity=5.0,
                unit_of_measure_id=10,
                scrap_factor=150.0,  # Invalid
                operation_number=None,
                is_phantom=False,
                backflush=False
            )

    def test_bom_line_scrap_factor_negative(self):
        """Test BOM line scrap factor cannot be negative"""
        with pytest.raises(ValueError, match="Scrap factor must be between 0 and 100"):
            BOMLineDomain(
                id=1,
                bom_header_id=100,
                line_number=10,
                component_material_id=2000,
                quantity=5.0,
                unit_of_measure_id=10,
                scrap_factor=-5.0,  # Invalid
                operation_number=None,
                is_phantom=False,
                backflush=False
            )

    def test_bom_line_line_number_positive(self):
        """Test BOM line line_number must be positive"""
        with pytest.raises(ValueError, match="Line number must be positive"):
            BOMLineDomain(
                id=1,
                bom_header_id=100,
                line_number=0,  # Invalid
                component_material_id=2000,
                quantity=5.0,
                unit_of_measure_id=10,
                scrap_factor=0.0,
                operation_number=None,
                is_phantom=False,
                backflush=False
            )

    def test_bom_line_calculate_net_quantity_with_scrap(self):
        """Test BOM line calculate_net_quantity_with_scrap() method"""
        line = BOMLineDomain(
            id=1,
            bom_header_id=100,
            line_number=10,
            component_material_id=2000,
            quantity=10.0,
            unit_of_measure_id=10,
            scrap_factor=10.0,  # 10% scrap
            operation_number=None,
            is_phantom=False,
            backflush=False
        )
        net_quantity = line.calculate_net_quantity_with_scrap()
        assert net_quantity == 11.0  # 10.0 * (1 + 10/100) = 11.0

    def test_bom_line_calculate_net_quantity_no_scrap(self):
        """Test BOM line calculate_net_quantity_with_scrap() with no scrap"""
        line = BOMLineDomain(
            id=1,
            bom_header_id=100,
            line_number=10,
            component_material_id=2000,
            quantity=10.0,
            unit_of_measure_id=10,
            scrap_factor=0.0,  # No scrap
            operation_number=None,
            is_phantom=False,
            backflush=False
        )
        net_quantity = line.calculate_net_quantity_with_scrap()
        assert net_quantity == 10.0

    def test_bom_line_repr(self):
        """Test BOM line string representation"""
        line = BOMLineDomain(
            id=1,
            bom_header_id=100,
            line_number=10,
            component_material_id=2000,
            quantity=5.0,
            unit_of_measure_id=10,
            scrap_factor=10.0,
            operation_number=10,
            is_phantom=False,
            backflush=True
        )
        assert "line_num=10" in repr(line)
        assert "component_mat_id=2000" in repr(line)
