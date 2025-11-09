"""
Integration tests for PlantRepository.

Test Coverage:
- Create plant with valid data
- Duplicate plant_code within organization
- Same plant_code in different organizations
- Update plant
- Delete plant (soft delete)
- List plants with filtering
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.organization import Organization
from app.models.plant import Plant
from app.infrastructure.repositories.plant_repository import PlantRepository


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_plant_repository.db"
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
def sample_organization(db_session):
    """Create a sample organization for testing"""
    org = Organization(
        org_code="ORG001",
        org_name="Test Organization",
        is_active=True
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture(scope="function")
def multiple_organizations(db_session):
    """Create multiple organizations for testing"""
    orgs = []
    for i in range(1, 4):
        org = Organization(
            org_code=f"ORG{i:03d}",
            org_name=f"Organization {i}",
            is_active=True
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        orgs.append(org)
    return orgs


class TestPlantCreation:
    """Test PlantRepository.create() method"""

    def test_create_plant_success(self, db_session, sample_organization):
        """Should create plant with valid data"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "Main Factory",
            "location": "New York, USA",
            "is_active": True
        }

        plant = repository.create(plant_data)

        assert plant.id is not None
        assert plant.plant_code == "P001"
        assert plant.plant_name == "Main Factory"
        assert plant.location == "New York, USA"
        assert plant.organization_id == sample_organization.id
        assert plant.is_active is True
        assert plant.created_at is not None

    def test_create_plant_without_location(self, db_session, sample_organization):
        """Should create plant without location"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P002",
            "plant_name": "Secondary Factory",
            "is_active": True
        }

        plant = repository.create(plant_data)

        assert plant.plant_code == "P002"
        assert plant.location is None

    def test_create_plant_duplicate_code_same_org_fails(self, db_session, sample_organization):
        """Should fail when creating plant with duplicate plant_code in same organization"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "First Plant",
            "is_active": True
        }

        # Create first plant
        repository.create(plant_data)

        # Try to create duplicate
        plant_data["plant_name"] = "Duplicate Plant"
        with pytest.raises(ValueError, match="already exists"):
            repository.create(plant_data)

    def test_create_plant_duplicate_code_different_org_succeeds(self, db_session, multiple_organizations):
        """Should allow same plant_code in different organizations"""
        repository = PlantRepository(db_session)

        plant_data_org1 = {
            "organization_id": multiple_organizations[0].id,
            "plant_code": "P001",
            "plant_name": "Org1 Plant",
            "is_active": True
        }

        plant_data_org2 = {
            "organization_id": multiple_organizations[1].id,
            "plant_code": "P001",
            "plant_name": "Org2 Plant",
            "is_active": True
        }

        # Create plant in first organization
        plant1 = repository.create(plant_data_org1)

        # Create plant with same code in second organization (should succeed)
        plant2 = repository.create(plant_data_org2)

        # Verify they are different plants
        assert plant1.id != plant2.id
        assert plant1.organization_id != plant2.organization_id
        assert plant1.plant_code == plant2.plant_code == "P001"

    def test_create_plant_invalid_organization_fails(self, db_session):
        """Should fail when creating plant with non-existent organization_id"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": 9999,
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "is_active": True
        }

        with pytest.raises(ValueError, match="Organization.*not found"):
            repository.create(plant_data)


class TestPlantRetrieval:
    """Test PlantRepository.get_by_id() and list_all() methods"""

    def test_get_by_id(self, db_session, sample_organization):
        """Should retrieve plant by ID"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "location": "New York",
            "is_active": True
        }

        created_plant = repository.create(plant_data)
        retrieved_plant = repository.get_by_id(created_plant.id)

        assert retrieved_plant is not None
        assert retrieved_plant.id == created_plant.id
        assert retrieved_plant.plant_code == "P001"

    def test_get_by_id_not_found(self, db_session):
        """Should return None for non-existent plant"""
        repository = PlantRepository(db_session)

        retrieved_plant = repository.get_by_id(9999)

        assert retrieved_plant is None

    def test_get_by_plant_code(self, db_session, sample_organization):
        """Should retrieve plant by plant_code within organization"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "is_active": True
        }

        created_plant = repository.create(plant_data)
        retrieved_plant = repository.get_by_plant_code(sample_organization.id, "P001")

        assert retrieved_plant is not None
        assert retrieved_plant.id == created_plant.id
        assert retrieved_plant.plant_code == "P001"

    def test_list_all_plants(self, db_session, sample_organization):
        """Should return paginated list of plants"""
        repository = PlantRepository(db_session)

        # Create test plants
        for i in range(5):
            plant_data = {
                "organization_id": sample_organization.id,
                "plant_code": f"P{i:03d}",
                "plant_name": f"Plant {i}",
                "is_active": True
            }
            repository.create(plant_data)

        # Get list
        result = repository.list_all()

        assert result["total"] == 5
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["total_pages"] == 1

    def test_list_plants_with_pagination(self, db_session, sample_organization):
        """Should return paginated list with custom page size"""
        repository = PlantRepository(db_session)

        # Create 10 plants
        for i in range(10):
            plant_data = {
                "organization_id": sample_organization.id,
                "plant_code": f"P{i:03d}",
                "plant_name": f"Plant {i}",
                "is_active": True
            }
            repository.create(plant_data)

        # Get first page
        result = repository.list_all(page=1, page_size=5)

        assert result["total"] == 10
        assert len(result["items"]) == 5
        assert result["page"] == 1
        assert result["page_size"] == 5
        assert result["total_pages"] == 2

        # Get second page
        result = repository.list_all(page=2, page_size=5)

        assert len(result["items"]) == 5
        assert result["page"] == 2

    def test_filter_plants_by_organization(self, db_session, multiple_organizations):
        """Should filter plants by organization_id"""
        repository = PlantRepository(db_session)

        # Create plants for different organizations
        for i, org in enumerate(multiple_organizations[:2]):
            for j in range(3):
                plant_data = {
                    "organization_id": org.id,
                    "plant_code": f"P{j:03d}",
                    "plant_name": f"Plant {j} for Org {i}",
                    "is_active": True
                }
                repository.create(plant_data)

        # Filter by first organization
        result = repository.list_all(filters={"organization_id": multiple_organizations[0].id})

        assert result["total"] == 3
        assert all(item.organization_id == multiple_organizations[0].id for item in result["items"])

        # Filter by second organization
        result = repository.list_all(filters={"organization_id": multiple_organizations[1].id})

        assert result["total"] == 3
        assert all(item.organization_id == multiple_organizations[1].id for item in result["items"])

    def test_filter_plants_by_active_status(self, db_session, sample_organization):
        """Should filter plants by is_active status"""
        repository = PlantRepository(db_session)

        # Create active plants
        for i in range(3):
            plant_data = {
                "organization_id": sample_organization.id,
                "plant_code": f"ACTIVE{i:03d}",
                "plant_name": f"Active Plant {i}",
                "is_active": True
            }
            repository.create(plant_data)

        # Create inactive plants
        for i in range(2):
            plant_data = {
                "organization_id": sample_organization.id,
                "plant_code": f"INACTIVE{i:03d}",
                "plant_name": f"Inactive Plant {i}",
                "is_active": False
            }
            repository.create(plant_data)

        # Filter by is_active=True
        result = repository.list_all(filters={"is_active": True})

        assert result["total"] == 3
        assert all(item.is_active is True for item in result["items"])

        # Filter by is_active=False
        result = repository.list_all(filters={"is_active": False})

        assert result["total"] == 2
        assert all(item.is_active is False for item in result["items"])


class TestPlantUpdate:
    """Test PlantRepository.update() method"""

    def test_update_plant_success(self, db_session, sample_organization):
        """Should update plant with valid data"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "Original Name",
            "location": "Original Location",
            "is_active": True
        }

        plant = repository.create(plant_data)

        # Update plant
        update_data = {
            "plant_name": "Updated Name",
            "location": "Updated Location"
        }
        updated_plant = repository.update(plant.id, update_data)

        assert updated_plant.plant_name == "Updated Name"
        assert updated_plant.location == "Updated Location"
        assert updated_plant.plant_code == "P001"  # Should not change

    def test_update_plant_partial(self, db_session, sample_organization):
        """Should support partial updates"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "Original Name",
            "location": "Original Location",
            "is_active": True
        }

        plant = repository.create(plant_data)

        # Update only plant_name
        update_data = {"plant_name": "Updated Name"}
        updated_plant = repository.update(plant.id, update_data)

        assert updated_plant.plant_name == "Updated Name"
        assert updated_plant.location == "Original Location"  # Should remain unchanged

    def test_update_plant_deactivate(self, db_session, sample_organization):
        """Should deactivate plant"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "is_active": True
        }

        plant = repository.create(plant_data)

        # Deactivate
        update_data = {"is_active": False}
        updated_plant = repository.update(plant.id, update_data)

        assert updated_plant.is_active is False

    def test_update_plant_not_found(self, db_session):
        """Should raise ValueError for non-existent plant"""
        repository = PlantRepository(db_session)

        update_data = {"plant_name": "Updated Name"}

        with pytest.raises(ValueError, match="not found"):
            repository.update(9999, update_data)


class TestPlantDeletion:
    """Test PlantRepository.delete() method"""

    def test_delete_plant_success(self, db_session, sample_organization):
        """Should soft delete plant"""
        repository = PlantRepository(db_session)

        plant_data = {
            "organization_id": sample_organization.id,
            "plant_code": "P001",
            "plant_name": "Test Plant",
            "is_active": True
        }

        plant = repository.create(plant_data)

        # Delete plant
        success = repository.delete(plant.id)

        assert success is True

        # Verify soft delete (is_active=False)
        deleted_plant = repository.get_by_id(plant.id)
        assert deleted_plant is not None
        assert deleted_plant.is_active is False

    def test_delete_plant_not_found(self, db_session):
        """Should return False for non-existent plant"""
        repository = PlantRepository(db_session)

        success = repository.delete(9999)

        assert success is False
