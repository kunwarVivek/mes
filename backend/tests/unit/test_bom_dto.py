"""
Unit tests for BOM (Bill of Materials) DTOs.

Tests Pydantic validation and serialization.
"""

import pytest
from datetime import datetime, date
from pydantic import ValidationError

from app.application.dtos.bom_dto import (
    BOMHeaderCreateRequest,
    BOMHeaderUpdateRequest,
    BOMHeaderResponse,
    BOMLineCreateRequest,
    BOMLineResponse,
)


class TestBOMHeaderCreateRequest:
    """Test BOMHeaderCreateRequest DTO validation"""

    def test_create_request_valid_minimal(self):
        """Should accept minimal valid BOM header data"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "bom_number": "BOM-001",
            "material_id": 10,
            "bom_name": "Test BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": 1,
            "created_by_user_id": 1
        }

        dto = BOMHeaderCreateRequest(**data)

        assert dto.organization_id == 1
        assert dto.plant_id == 1
        assert dto.bom_number == "BOM-001"
        assert dto.material_id == 10
        assert dto.bom_name == "Test BOM"
        assert dto.bom_type == "PRODUCTION"
        assert dto.base_quantity == 1.0
        assert dto.unit_of_measure_id == 1
        assert dto.created_by_user_id == 1
        assert dto.bom_version == 1  # Default value
        assert dto.is_active is True  # Default value

    def test_create_request_valid_full(self):
        """Should accept full BOM header data with all fields"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "bom_number": "BOM-002",
            "material_id": 20,
            "bom_version": 2,
            "bom_name": "Advanced BOM",
            "bom_type": "ENGINEERING",
            "base_quantity": 100.0,
            "unit_of_measure_id": 2,
            "effective_start_date": date(2025, 1, 1),
            "effective_end_date": date(2025, 12, 31),
            "is_active": False,
            "created_by_user_id": 5
        }

        dto = BOMHeaderCreateRequest(**data)

        assert dto.bom_version == 2
        assert dto.bom_type == "ENGINEERING"
        assert dto.effective_start_date == date(2025, 1, 1)
        assert dto.effective_end_date == date(2025, 12, 31)
        assert dto.is_active is False

    def test_create_request_missing_required_fields(self):
        """Should reject missing required fields"""
        data = {
            "bom_number": "BOM-001",
            "material_id": 10
            # Missing organization_id, plant_id, bom_name, etc.
        }

        with pytest.raises(ValidationError):
            BOMHeaderCreateRequest(**data)

    def test_create_request_bom_number_too_long(self):
        """Should reject bom_number exceeding 50 characters"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "bom_number": "B" * 51,  # Too long
            "material_id": 10,
            "bom_name": "Test BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": 1,
            "created_by_user_id": 1
        }

        with pytest.raises(ValidationError):
            BOMHeaderCreateRequest(**data)

    def test_create_request_base_quantity_must_be_positive(self):
        """Should reject base_quantity <= 0"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "bom_number": "BOM-001",
            "material_id": 10,
            "bom_name": "Test BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 0.0,  # Invalid
            "unit_of_measure_id": 1,
            "created_by_user_id": 1
        }

        with pytest.raises(ValidationError):
            BOMHeaderCreateRequest(**data)

    def test_create_request_bom_version_must_be_at_least_one(self):
        """Should reject bom_version < 1"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "bom_number": "BOM-001",
            "material_id": 10,
            "bom_version": 0,  # Invalid
            "bom_name": "Test BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": 1,
            "created_by_user_id": 1
        }

        with pytest.raises(ValidationError):
            BOMHeaderCreateRequest(**data)

    def test_create_request_invalid_bom_type(self):
        """Should reject invalid bom_type"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "bom_number": "BOM-001",
            "material_id": 10,
            "bom_name": "Test BOM",
            "bom_type": "INVALID_TYPE",
            "base_quantity": 1.0,
            "unit_of_measure_id": 1,
            "created_by_user_id": 1
        }

        with pytest.raises(ValidationError):
            BOMHeaderCreateRequest(**data)


class TestBOMHeaderUpdateRequest:
    """Test BOMHeaderUpdateRequest DTO validation"""

    def test_update_request_all_fields(self):
        """Should accept all update fields"""
        data = {
            "bom_name": "Updated BOM Name",
            "effective_start_date": date(2025, 2, 1),
            "effective_end_date": date(2025, 11, 30),
            "is_active": False
        }

        dto = BOMHeaderUpdateRequest(**data)

        assert dto.bom_name == "Updated BOM Name"
        assert dto.effective_start_date == date(2025, 2, 1)
        assert dto.effective_end_date == date(2025, 11, 30)
        assert dto.is_active is False

    def test_update_request_partial(self):
        """Should accept partial updates"""
        data = {
            "bom_name": "Partially Updated"
        }

        dto = BOMHeaderUpdateRequest(**data)

        assert dto.bom_name == "Partially Updated"
        assert dto.effective_start_date is None
        assert dto.effective_end_date is None
        assert dto.is_active is None

    def test_update_request_empty(self):
        """Should accept empty update (all fields optional)"""
        data = {}

        dto = BOMHeaderUpdateRequest(**data)

        assert dto.bom_name is None
        assert dto.is_active is None


class TestBOMHeaderResponse:
    """Test BOMHeaderResponse DTO"""

    def test_response_from_dict_minimal(self):
        """Should create response from dict with minimal fields"""
        data = {
            "id": 1,
            "organization_id": 1,
            "plant_id": 1,
            "bom_number": "BOM-001",
            "material_id": 10,
            "bom_version": 1,
            "bom_name": "Test BOM",
            "bom_type": "PRODUCTION",
            "base_quantity": 1.0,
            "unit_of_measure_id": 1,
            "effective_start_date": None,
            "effective_end_date": None,
            "is_active": True,
            "created_by_user_id": 1,
            "created_at": datetime.now(),
            "updated_at": None
        }

        dto = BOMHeaderResponse(**data)

        assert dto.id == 1
        assert dto.bom_number == "BOM-001"
        assert dto.bom_version == 1
        assert dto.is_active is True


class TestBOMLineCreateRequest:
    """Test BOMLineCreateRequest DTO validation"""

    def test_create_line_request_valid_minimal(self):
        """Should accept minimal valid BOM line data"""
        data = {
            "bom_header_id": 1,
            "line_number": 10,
            "component_material_id": 100,
            "quantity": 2.0,
            "unit_of_measure_id": 1
        }

        dto = BOMLineCreateRequest(**data)

        assert dto.bom_header_id == 1
        assert dto.line_number == 10
        assert dto.component_material_id == 100
        assert dto.quantity == 2.0
        assert dto.unit_of_measure_id == 1
        assert dto.scrap_factor == 0.0  # Default
        assert dto.is_phantom is False  # Default
        assert dto.backflush is False  # Default

    def test_create_line_request_valid_full(self):
        """Should accept full BOM line data"""
        data = {
            "bom_header_id": 1,
            "line_number": 20,
            "component_material_id": 200,
            "quantity": 5.0,
            "unit_of_measure_id": 2,
            "scrap_factor": 10.5,
            "operation_number": 30,
            "is_phantom": True,
            "backflush": True
        }

        dto = BOMLineCreateRequest(**data)

        assert dto.scrap_factor == 10.5
        assert dto.operation_number == 30
        assert dto.is_phantom is True
        assert dto.backflush is True

    def test_create_line_request_missing_required_fields(self):
        """Should reject missing required fields"""
        data = {
            "line_number": 10,
            "quantity": 2.0
            # Missing bom_header_id, component_material_id, unit_of_measure_id
        }

        with pytest.raises(ValidationError):
            BOMLineCreateRequest(**data)

    def test_create_line_request_quantity_must_be_positive(self):
        """Should reject quantity <= 0"""
        data = {
            "bom_header_id": 1,
            "line_number": 10,
            "component_material_id": 100,
            "quantity": 0.0,  # Invalid
            "unit_of_measure_id": 1
        }

        with pytest.raises(ValidationError):
            BOMLineCreateRequest(**data)

    def test_create_line_request_line_number_must_be_positive(self):
        """Should reject line_number <= 0"""
        data = {
            "bom_header_id": 1,
            "line_number": 0,  # Invalid
            "component_material_id": 100,
            "quantity": 2.0,
            "unit_of_measure_id": 1
        }

        with pytest.raises(ValidationError):
            BOMLineCreateRequest(**data)

    def test_create_line_request_scrap_factor_out_of_range(self):
        """Should reject scrap_factor outside 0-100 range"""
        data = {
            "bom_header_id": 1,
            "line_number": 10,
            "component_material_id": 100,
            "quantity": 2.0,
            "unit_of_measure_id": 1,
            "scrap_factor": 150.0  # Invalid (>100)
        }

        with pytest.raises(ValidationError):
            BOMLineCreateRequest(**data)


class TestBOMLineResponse:
    """Test BOMLineResponse DTO"""

    def test_line_response_from_dict(self):
        """Should create BOM line response from dict"""
        data = {
            "id": 1,
            "bom_header_id": 1,
            "line_number": 10,
            "component_material_id": 100,
            "quantity": 2.0,
            "unit_of_measure_id": 1,
            "scrap_factor": 5.0,
            "operation_number": None,
            "is_phantom": False,
            "backflush": False,
            "created_at": datetime.now(),
            "updated_at": None
        }

        dto = BOMLineResponse(**data)

        assert dto.id == 1
        assert dto.bom_header_id == 1
        assert dto.line_number == 10
        assert dto.quantity == 2.0
        assert dto.scrap_factor == 5.0
