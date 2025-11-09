"""
Unit tests for DepartmentRepository.

Tests CRUD operations and validation logic without full API integration.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.infrastructure.repositories.department_repository import DepartmentRepository
from app.models.organization import Organization
from app.models.plant import Plant
from app.models.department import Department


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dept_repo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def sample_plant(db_session):
    """Create a sample plant for testing departments"""
    # Create organization first
    org = Organization(
        org_code="TEST001",
        org_name="Test Organization",
        is_active=True
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # Create plant
    plant = Plant(
        organization_id=org.id,
        plant_code="PLT001",
        plant_name="Test Plant",
        is_active=True
    )
    db_session.add(plant)
    db_session.commit()
    db_session.refresh(plant)

    return plant


class TestDepartmentRepositoryCreate:
    """Test DepartmentRepository.create"""

    def test_create_department_success(self, db_session, sample_plant):
        """Should create department with valid data"""
        repo = DepartmentRepository(db_session)

        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "description": "Handles all production activities",
            "is_active": True
        }

        dept = repo.create(dept_data)

        assert dept.id is not None
        assert dept.dept_code == "PROD"
        assert dept.dept_name == "Production Department"
        assert dept.description == "Handles all production activities"
        assert dept.plant_id == sample_plant.id
        assert dept.is_active is True
        assert dept.created_at is not None

    def test_create_department_duplicate_code_fails(self, db_session, sample_plant):
        """Should fail when creating duplicate dept_code in same plant"""
        repo = DepartmentRepository(db_session)

        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        # Create first department
        repo.create(dept_data)

        # Try to create duplicate
        dept_data["dept_name"] = "Another Production Department"
        with pytest.raises(ValueError) as exc_info:
            repo.create(dept_data)

        assert "already exists" in str(exc_info.value).lower()

    def test_create_department_invalid_plant_fails(self, db_session):
        """Should fail when plant_id does not exist"""
        repo = DepartmentRepository(db_session)

        dept_data = {
            "plant_id": 999,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        with pytest.raises(ValueError) as exc_info:
            repo.create(dept_data)

        assert "plant" in str(exc_info.value).lower()
        assert "not found" in str(exc_info.value).lower()


class TestDepartmentRepositoryRead:
    """Test DepartmentRepository read operations"""

    def test_get_by_id_success(self, db_session, sample_plant):
        """Should retrieve department by ID"""
        repo = DepartmentRepository(db_session)

        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        created_dept = repo.create(dept_data)

        fetched_dept = repo.get_by_id(created_dept.id)

        assert fetched_dept is not None
        assert fetched_dept.id == created_dept.id
        assert fetched_dept.dept_code == "PROD"

    def test_get_by_id_not_found(self, db_session):
        """Should return None for non-existent ID"""
        repo = DepartmentRepository(db_session)

        dept = repo.get_by_id(999)

        assert dept is None

    def test_list_all_with_plant_filter(self, db_session, sample_plant):
        """Should filter departments by plant_id"""
        repo = DepartmentRepository(db_session)

        # Create second plant
        plant2 = Plant(
            organization_id=sample_plant.organization_id,
            plant_code="PLT002",
            plant_name="Second Plant",
            is_active=True
        )
        db_session.add(plant2)
        db_session.commit()
        db_session.refresh(plant2)

        # Create departments in first plant
        for i in range(3):
            repo.create({
                "plant_id": sample_plant.id,
                "dept_code": f"DEPT{i:02d}",
                "dept_name": f"Department {i}",
                "is_active": True
            })

        # Create departments in second plant
        for i in range(2):
            repo.create({
                "plant_id": plant2.id,
                "dept_code": f"DEPT{i:02d}",
                "dept_name": f"Department {i}",
                "is_active": True
            })

        # Filter by first plant
        result = repo.list_all(filters={"plant_id": sample_plant.id})

        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert all(d.plant_id == sample_plant.id for d in result["items"])

        # Filter by second plant
        result = repo.list_all(filters={"plant_id": plant2.id})

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert all(d.plant_id == plant2.id for d in result["items"])

    def test_list_all_pagination(self, db_session, sample_plant):
        """Should paginate results correctly"""
        repo = DepartmentRepository(db_session)

        # Create 10 departments
        for i in range(10):
            repo.create({
                "plant_id": sample_plant.id,
                "dept_code": f"DEPT{i:02d}",
                "dept_name": f"Department {i}",
                "is_active": True
            })

        # Get first page
        result = repo.list_all(page=1, page_size=5)

        assert result["total"] == 10
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 5
        assert result["total_pages"] == 2

        # Get second page
        result = repo.list_all(page=2, page_size=5)

        assert len(result["items"]) == 5
        assert result["page"] == 2


class TestDepartmentRepositoryUpdate:
    """Test DepartmentRepository.update"""

    def test_update_department_success(self, db_session, sample_plant):
        """Should update department fields"""
        repo = DepartmentRepository(db_session)

        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Original Name",
            "description": "Original description",
            "is_active": True
        }

        created_dept = repo.create(dept_data)

        # Update department
        updated_dept = repo.update(created_dept.id, {
            "dept_name": "Updated Name",
            "description": "Updated description"
        })

        assert updated_dept.dept_name == "Updated Name"
        assert updated_dept.description == "Updated description"
        assert updated_dept.dept_code == "PROD"  # Should not change

    def test_update_department_not_found(self, db_session):
        """Should raise error when department not found"""
        repo = DepartmentRepository(db_session)

        with pytest.raises(ValueError) as exc_info:
            repo.update(999, {"dept_name": "Updated Name"})

        assert "not found" in str(exc_info.value).lower()


class TestDepartmentRepositoryDelete:
    """Test DepartmentRepository.delete (soft delete)"""

    def test_delete_department_success(self, db_session, sample_plant):
        """Should soft delete department"""
        repo = DepartmentRepository(db_session)

        dept_data = {
            "plant_id": sample_plant.id,
            "dept_code": "PROD",
            "dept_name": "Production Department",
            "is_active": True
        }

        created_dept = repo.create(dept_data)

        # Delete department
        success = repo.delete(created_dept.id)

        assert success is True

        # Verify soft delete
        dept = repo.get_by_id(created_dept.id)
        assert dept is not None
        assert dept.is_active is False

    def test_delete_department_not_found(self, db_session):
        """Should return False when department not found"""
        repo = DepartmentRepository(db_session)

        success = repo.delete(999)

        assert success is False
