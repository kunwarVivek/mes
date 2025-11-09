"""
Unit tests for Project Domain Entity.

Tests business logic validation in the domain layer.
"""

import pytest
from datetime import date, datetime
from app.domain.entities.project import ProjectDomain, ProjectStatus


class TestProjectDomain:
    """Test ProjectDomain entity validation"""

    def test_create_valid_project(self):
        """Should create valid project entity"""
        project = ProjectDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            project_code="PROJ-001",
            project_name="Manufacturing Project Alpha",
            description="First production project",
            bom_id=10,
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 12, 31),
            actual_start_date=None,
            actual_end_date=None,
            status=ProjectStatus.PLANNING,
            priority=5,
            is_active=True,
            created_at=datetime.now(),
            updated_at=None
        )

        assert project.id == 1
        assert project.project_code == "PROJ-001"
        assert project.project_name == "Manufacturing Project Alpha"
        assert project.status == ProjectStatus.PLANNING
        assert project.priority == 5

    def test_project_code_empty_raises_error(self):
        """Should reject empty project_code"""
        with pytest.raises(ValueError, match="project_code must be 1-50 characters"):
            ProjectDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                project_code="",  # Empty
                project_name="Test Project",
                description=None,
                bom_id=None,
                planned_start_date=None,
                planned_end_date=None,
                actual_start_date=None,
                actual_end_date=None,
                status=ProjectStatus.PLANNING,
                priority=0,
                is_active=True,
                created_at=datetime.now()
            )

    def test_project_code_too_long_raises_error(self):
        """Should reject project_code > 50 characters"""
        with pytest.raises(ValueError, match="project_code must be 1-50 characters"):
            ProjectDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                project_code="P" * 51,  # 51 characters
                project_name="Test Project",
                description=None,
                bom_id=None,
                planned_start_date=None,
                planned_end_date=None,
                actual_start_date=None,
                actual_end_date=None,
                status=ProjectStatus.PLANNING,
                priority=0,
                is_active=True,
                created_at=datetime.now()
            )

    def test_project_name_empty_raises_error(self):
        """Should reject empty project_name"""
        with pytest.raises(ValueError, match="project_name must be 1-200 characters"):
            ProjectDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                project_code="PROJ-001",
                project_name="",  # Empty
                description=None,
                bom_id=None,
                planned_start_date=None,
                planned_end_date=None,
                actual_start_date=None,
                actual_end_date=None,
                status=ProjectStatus.PLANNING,
                priority=0,
                is_active=True,
                created_at=datetime.now()
            )

    def test_project_name_too_long_raises_error(self):
        """Should reject project_name > 200 characters"""
        with pytest.raises(ValueError, match="project_name must be 1-200 characters"):
            ProjectDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                project_code="PROJ-001",
                project_name="N" * 201,  # 201 characters
                description=None,
                bom_id=None,
                planned_start_date=None,
                planned_end_date=None,
                actual_start_date=None,
                actual_end_date=None,
                status=ProjectStatus.PLANNING,
                priority=0,
                is_active=True,
                created_at=datetime.now()
            )

    def test_planned_end_before_start_raises_error(self):
        """Should reject planned_end_date < planned_start_date"""
        with pytest.raises(ValueError, match="planned_end_date must be >= planned_start_date"):
            ProjectDomain(
                id=1,
                organization_id=1,
                plant_id=1,
                project_code="PROJ-001",
                project_name="Test Project",
                description=None,
                bom_id=None,
                planned_start_date=date(2025, 12, 31),
                planned_end_date=date(2025, 1, 1),  # Before start
                actual_start_date=None,
                actual_end_date=None,
                status=ProjectStatus.PLANNING,
                priority=0,
                is_active=True,
                created_at=datetime.now()
            )

    def test_same_start_and_end_date_valid(self):
        """Should accept planned_end_date == planned_start_date"""
        project = ProjectDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            project_code="PROJ-001",
            project_name="Test Project",
            description=None,
            bom_id=None,
            planned_start_date=date(2025, 6, 15),
            planned_end_date=date(2025, 6, 15),  # Same day
            actual_start_date=None,
            actual_end_date=None,
            status=ProjectStatus.PLANNING,
            priority=0,
            is_active=True,
            created_at=datetime.now()
        )

        assert project.planned_start_date == project.planned_end_date

    def test_null_dates_valid(self):
        """Should accept None for optional date fields"""
        project = ProjectDomain(
            id=1,
            organization_id=1,
            plant_id=1,
            project_code="PROJ-001",
            project_name="Test Project",
            description=None,
            bom_id=None,
            planned_start_date=None,
            planned_end_date=None,
            actual_start_date=None,
            actual_end_date=None,
            status=ProjectStatus.PLANNING,
            priority=0,
            is_active=True,
            created_at=datetime.now()
        )

        assert project.planned_start_date is None
        assert project.planned_end_date is None


class TestProjectStatus:
    """Test ProjectStatus enum"""

    def test_project_status_values(self):
        """Should have all required status values"""
        assert ProjectStatus.PLANNING == "PLANNING"
        assert ProjectStatus.ACTIVE == "ACTIVE"
        assert ProjectStatus.ON_HOLD == "ON_HOLD"
        assert ProjectStatus.COMPLETED == "COMPLETED"
        assert ProjectStatus.CANCELLED == "CANCELLED"

    def test_project_status_count(self):
        """Should have exactly 5 status values"""
        assert len(ProjectStatus) == 5
