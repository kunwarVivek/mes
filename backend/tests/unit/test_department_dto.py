"""
Unit tests for Department DTOs.

Tests Pydantic validation and serialization.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.application.dtos.department_dto import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentResponse,
)


class TestDepartmentCreateRequest:
    """Test DepartmentCreateRequest DTO validation"""

    def test_create_request_valid(self):
        """Should accept valid department data"""
        data = {
            "plant_id": 1,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "description": "Handles production",
            "is_active": True
        }

        dto = DepartmentCreateRequest(**data)

        assert dto.plant_id == 1
        assert dto.dept_code == "PROD"
        assert dto.dept_name == "Production Department"
        assert dto.description == "Handles production"
        assert dto.is_active is True

    def test_create_request_without_description(self):
        """Should accept department without description"""
        data = {
            "plant_id": 1,
            "dept_code": "QC",
            "dept_name": "Quality Control",
            "is_active": True
        }

        dto = DepartmentCreateRequest(**data)

        assert dto.description is None

    def test_create_request_default_is_active(self):
        """Should default is_active to True"""
        data = {
            "plant_id": 1,
            "dept_code": "PROD",
            "dept_name": "Production Department"
        }

        dto = DepartmentCreateRequest(**data)

        assert dto.is_active is True

    def test_create_request_missing_required_fields(self):
        """Should reject missing required fields"""
        data = {
            "dept_code": "PROD",
            "dept_name": "Production Department"
            # Missing plant_id
        }

        with pytest.raises(ValidationError):
            DepartmentCreateRequest(**data)

    def test_create_request_dept_code_too_short(self):
        """Should reject dept_code less than 2 characters"""
        data = {
            "plant_id": 1,
            "dept_code": "P",  # Too short
            "dept_name": "Production Department"
        }

        with pytest.raises(ValidationError):
            DepartmentCreateRequest(**data)

    def test_create_request_dept_code_too_long(self):
        """Should reject dept_code more than 20 characters"""
        data = {
            "plant_id": 1,
            "dept_code": "P" * 21,  # Too long
            "dept_name": "Production Department"
        }

        with pytest.raises(ValidationError):
            DepartmentCreateRequest(**data)

    def test_create_request_dept_name_empty(self):
        """Should reject empty dept_name"""
        data = {
            "plant_id": 1,
            "dept_code": "PROD",
            "dept_name": ""  # Empty
        }

        with pytest.raises(ValidationError):
            DepartmentCreateRequest(**data)


class TestDepartmentUpdateRequest:
    """Test DepartmentUpdateRequest DTO validation"""

    def test_update_request_all_fields(self):
        """Should accept all update fields"""
        data = {
            "dept_name": "Updated Name",
            "description": "Updated description",
            "is_active": False
        }

        dto = DepartmentUpdateRequest(**data)

        assert dto.dept_name == "Updated Name"
        assert dto.description == "Updated description"
        assert dto.is_active is False

    def test_update_request_partial(self):
        """Should accept partial updates"""
        data = {
            "dept_name": "Updated Name"
        }

        dto = DepartmentUpdateRequest(**data)

        assert dto.dept_name == "Updated Name"
        assert dto.description is None
        assert dto.is_active is None

    def test_update_request_empty(self):
        """Should accept empty update (all fields optional)"""
        data = {}

        dto = DepartmentUpdateRequest(**data)

        assert dto.dept_name is None
        assert dto.description is None
        assert dto.is_active is None


class TestDepartmentResponse:
    """Test DepartmentResponse DTO"""

    def test_response_from_dict(self):
        """Should create response from dict"""
        data = {
            "id": 1,
            "plant_id": 1,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "description": "Handles production",
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": None
        }

        dto = DepartmentResponse(**data)

        assert dto.id == 1
        assert dto.plant_id == 1
        assert dto.dept_code == "PROD"
        assert dto.dept_name == "Production Department"
        assert dto.description == "Handles production"
        assert dto.is_active is True
        assert dto.created_at is not None
        assert dto.updated_at is None
