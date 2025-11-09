"""
Unit tests for Project DTOs.

Tests Pydantic validation and serialization.
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from app.application.dtos.project_dto import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
)
from app.domain.entities.project import ProjectStatus


class TestProjectCreateRequest:
    """Test ProjectCreateRequest DTO validation"""

    def test_create_request_valid_full(self):
        """Should accept valid project data with all fields"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Manufacturing Project Alpha",
            "description": "First production project",
            "bom_id": 10,
            "planned_start_date": "2025-01-01",
            "planned_end_date": "2025-12-31",
            "status": "PLANNING",
            "priority": 5
        }

        dto = ProjectCreateRequest(**data)

        assert dto.organization_id == 1
        assert dto.plant_id == 1
        assert dto.project_code == "PROJ-001"
        assert dto.project_name == "Manufacturing Project Alpha"
        assert dto.description == "First production project"
        assert dto.bom_id == 10
        assert dto.planned_start_date == date(2025, 1, 1)
        assert dto.planned_end_date == date(2025, 12, 31)
        assert dto.status == ProjectStatus.PLANNING
        assert dto.priority == 5

    def test_create_request_minimal(self):
        """Should accept minimal required fields"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Test Project"
        }

        dto = ProjectCreateRequest(**data)

        assert dto.organization_id == 1
        assert dto.plant_id == 1
        assert dto.project_code == "PROJ-001"
        assert dto.project_name == "Test Project"
        assert dto.description is None
        assert dto.bom_id is None
        assert dto.planned_start_date is None
        assert dto.planned_end_date is None
        assert dto.status == ProjectStatus.PLANNING  # Default
        assert dto.priority == 0  # Default

    def test_create_request_project_code_uppercase_format(self):
        """Should validate project_code pattern (uppercase alphanumeric with - and _)"""
        valid_codes = ["PROJ-001", "ALPHA_2025", "MFG-PLANT1", "P123"]

        for code in valid_codes:
            data = {
                "organization_id": 1,
                "plant_id": 1,
                "project_code": code,
                "project_name": "Test Project"
            }
            dto = ProjectCreateRequest(**data)
            assert dto.project_code == code

    def test_create_request_project_code_lowercase_rejects(self):
        """Should reject project_code with lowercase letters"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "proj-001",  # Lowercase
            "project_name": "Test Project"
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_project_code_too_long(self):
        """Should reject project_code > 50 characters"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "P" * 51,  # 51 characters
            "project_name": "Test Project"
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_project_name_too_long(self):
        """Should reject project_name > 200 characters"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "N" * 201  # 201 characters
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_missing_required_fields(self):
        """Should reject missing required fields"""
        data = {
            "project_code": "PROJ-001",
            "project_name": "Test Project"
            # Missing organization_id and plant_id
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_invalid_organization_id(self):
        """Should reject organization_id <= 0"""
        data = {
            "organization_id": 0,  # Invalid
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Test Project"
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_invalid_plant_id(self):
        """Should reject plant_id <= 0"""
        data = {
            "organization_id": 1,
            "plant_id": -1,  # Invalid
            "project_code": "PROJ-001",
            "project_name": "Test Project"
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_invalid_bom_id(self):
        """Should reject bom_id <= 0"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Test Project",
            "bom_id": 0  # Invalid
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_negative_priority(self):
        """Should reject priority < 0"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Test Project",
            "priority": -1  # Invalid
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)

    def test_create_request_invalid_status(self):
        """Should reject invalid status value"""
        data = {
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Test Project",
            "status": "INVALID_STATUS"
        }

        with pytest.raises(ValidationError):
            ProjectCreateRequest(**data)


class TestProjectUpdateRequest:
    """Test ProjectUpdateRequest DTO validation"""

    def test_update_request_all_fields(self):
        """Should accept all update fields"""
        data = {
            "project_name": "Updated Project Name",
            "description": "Updated description",
            "bom_id": 20,
            "planned_start_date": "2025-02-01",
            "planned_end_date": "2025-11-30",
            "actual_start_date": "2025-02-05",
            "actual_end_date": "2025-11-25",
            "status": "ACTIVE",
            "priority": 10,
            "is_active": False
        }

        dto = ProjectUpdateRequest(**data)

        assert dto.project_name == "Updated Project Name"
        assert dto.description == "Updated description"
        assert dto.bom_id == 20
        assert dto.planned_start_date == date(2025, 2, 1)
        assert dto.planned_end_date == date(2025, 11, 30)
        assert dto.actual_start_date == date(2025, 2, 5)
        assert dto.actual_end_date == date(2025, 11, 25)
        assert dto.status == ProjectStatus.ACTIVE
        assert dto.priority == 10
        assert dto.is_active is False

    def test_update_request_partial(self):
        """Should accept partial updates"""
        data = {
            "project_name": "Updated Name",
            "priority": 7
        }

        dto = ProjectUpdateRequest(**data)

        assert dto.project_name == "Updated Name"
        assert dto.priority == 7
        assert dto.description is None
        assert dto.status is None

    def test_update_request_empty(self):
        """Should accept empty update (all fields optional)"""
        data = {}

        dto = ProjectUpdateRequest(**data)

        assert dto.project_name is None
        assert dto.description is None
        assert dto.status is None

    def test_update_request_invalid_bom_id(self):
        """Should reject invalid bom_id"""
        data = {
            "bom_id": 0  # Invalid
        }

        with pytest.raises(ValidationError):
            ProjectUpdateRequest(**data)

    def test_update_request_negative_priority(self):
        """Should reject negative priority"""
        data = {
            "priority": -5  # Invalid
        }

        with pytest.raises(ValidationError):
            ProjectUpdateRequest(**data)


class TestProjectResponse:
    """Test ProjectResponse DTO"""

    def test_response_from_dict(self):
        """Should create response from dict"""
        data = {
            "id": 1,
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Manufacturing Project",
            "description": "Test description",
            "bom_id": 10,
            "planned_start_date": date(2025, 1, 1),
            "planned_end_date": date(2025, 12, 31),
            "actual_start_date": None,
            "actual_end_date": None,
            "status": ProjectStatus.PLANNING,
            "priority": 5,
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": None
        }

        dto = ProjectResponse(**data)

        assert dto.id == 1
        assert dto.organization_id == 1
        assert dto.plant_id == 1
        assert dto.project_code == "PROJ-001"
        assert dto.project_name == "Manufacturing Project"
        assert dto.status == ProjectStatus.PLANNING
        assert dto.priority == 5
        assert dto.is_active is True


class TestProjectListResponse:
    """Test ProjectListResponse DTO"""

    def test_list_response_empty(self):
        """Should create empty list response"""
        data = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10
        }

        dto = ProjectListResponse(**data)

        assert len(dto.items) == 0
        assert dto.total == 0
        assert dto.page == 1
        assert dto.page_size == 10

    def test_list_response_with_items(self):
        """Should create list response with items"""
        project_data = {
            "id": 1,
            "organization_id": 1,
            "plant_id": 1,
            "project_code": "PROJ-001",
            "project_name": "Test Project",
            "description": None,
            "bom_id": None,
            "planned_start_date": None,
            "planned_end_date": None,
            "actual_start_date": None,
            "actual_end_date": None,
            "status": ProjectStatus.PLANNING,
            "priority": 0,
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": None
        }

        data = {
            "items": [ProjectResponse(**project_data)],
            "total": 1,
            "page": 1,
            "page_size": 10
        }

        dto = ProjectListResponse(**data)

        assert len(dto.items) == 1
        assert dto.items[0].project_code == "PROJ-001"
        assert dto.total == 1
