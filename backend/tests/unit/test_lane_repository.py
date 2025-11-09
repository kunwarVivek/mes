"""
Unit tests for Lane Repository
Testing database operations and business logic
"""
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
# Import ALL models to ensure they're registered with Base.metadata
import app.models  # This imports everything from models.__init__.py
from app.infrastructure.persistence.models import UserModel as User
from app.models.organization import Organization
from app.models.plant import Plant
from app.models.department import Department
from app.models.project import Project
from app.models.work_order import WorkOrder, OrderType, OrderStatus
from app.models.lane import Lane, LaneAssignment
from app.domain.entities.lane import LaneAssignmentStatus
from app.application.dtos.lane_dto import (
    LaneCreateRequest,
    LaneUpdateRequest,
    LaneAssignmentCreateRequest,
    LaneAssignmentUpdateRequest
)
from app.infrastructure.repositories.lane_repository import LaneRepository


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_lane_repository.db"
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


@pytest.fixture
def test_organization(db_session):
    """Create test organization"""
    org = Organization(
        id=1,
        org_code="TEST",
        org_name="Test Organization"
    )
    db_session.add(org)
    db_session.commit()
    return org


@pytest.fixture
def test_plant(db_session, test_organization):
    """Create test plant"""
    plant = Plant(
        id=1,
        organization_id=test_organization.id,
        plant_code="P001",
        plant_name="Test Plant"
    )
    db_session.add(plant)
    db_session.commit()
    return plant


@pytest.fixture
def test_project(db_session, test_organization, test_plant):
    """Create test project"""
    project = Project(
        id=1,
        organization_id=test_organization.id,
        plant_id=test_plant.id,
        project_code="PROJ001",
        project_name="Test Project"
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def test_work_order(db_session, test_organization, test_plant):
    """Create test work order"""
    wo = WorkOrder(
        id=100,
        organization_id=test_organization.id,
        plant_id=test_plant.id,
        work_order_number="WO-001",
        order_type=OrderType.PRODUCTION,
        order_status=OrderStatus.PLANNED,
        planned_quantity=100,
        material_id=1,  # Required field
        created_by_user_id=1  # Required field
    )
    db_session.add(wo)
    db_session.commit()
    return wo


class TestLaneRepositoryCRUD:
    """Test Lane CRUD operations"""

    def test_create_lane(self, db_session, test_plant):
        """Test creating a new lane"""
        repo = LaneRepository(db_session)
        dto = LaneCreateRequest(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Assembly Line 1",
            capacity_per_day=Decimal("100.000")
        )

        lane = repo.create_lane(dto)

        assert lane.id is not None
        assert lane.plant_id == test_plant.id
        assert lane.lane_code == "L001"
        assert lane.lane_name == "Assembly Line 1"
        assert lane.capacity_per_day == Decimal("100.000")
        assert lane.is_active is True

    def test_create_duplicate_lane_code_same_plant_fails(self, db_session, test_plant):
        """Test that duplicate lane_code in same plant is rejected"""
        repo = LaneRepository(db_session)
        dto1 = LaneCreateRequest(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Line 1",
            capacity_per_day=Decimal("100.000")
        )
        repo.create_lane(dto1)

        # Try to create another lane with same code in same plant
        dto2 = LaneCreateRequest(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Line 2",
            capacity_per_day=Decimal("200.000")
        )

        with pytest.raises(ValueError, match="Lane code L001 already exists"):
            repo.create_lane(dto2)

    def test_create_same_lane_code_different_plants(self, db_session, test_organization, test_plant):
        """Test that same lane_code is allowed in different plants"""
        # Create second plant
        plant2 = Plant(
            organization_id=test_organization.id,
            plant_code="P002",
            plant_name="Plant 2"
        )
        db_session.add(plant2)
        db_session.commit()

        repo = LaneRepository(db_session)

        # Create lane in plant 1 (test_plant)
        dto1 = LaneCreateRequest(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Line 1 in Plant 1",
            capacity_per_day=Decimal("100.000")
        )
        lane1 = repo.create_lane(dto1)

        # Create lane with same code in plant 2 - should succeed
        dto2 = LaneCreateRequest(
            plant_id=plant2.id,
            lane_code="L001",
            lane_name="Line 1 in Plant 2",
            capacity_per_day=Decimal("200.000")
        )
        lane2 = repo.create_lane(dto2)

        assert lane1.lane_code == lane2.lane_code
        assert lane1.plant_id != lane2.plant_id

    def test_get_lane_by_id(self, db_session, test_plant):
        """Test retrieving lane by ID"""
        repo = LaneRepository(db_session)
        dto = LaneCreateRequest(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Test Lane",
            capacity_per_day=Decimal("100.000")
        )
        created = repo.create_lane(dto)

        lane = repo.get_lane_by_id(created.id)

        assert lane is not None
        assert lane.id == created.id
        assert lane.lane_code == "L001"

    def test_get_nonexistent_lane_returns_none(self, db_session):
        """Test getting nonexistent lane returns None"""
        repo = LaneRepository(db_session)

        lane = repo.get_lane_by_id(999)

        assert lane is None

    def test_list_lanes_all(self, db_session, test_plant):
        """Test listing all lanes"""
        repo = LaneRepository(db_session)

        # Create multiple lanes
        for i in range(3):
            dto = LaneCreateRequest(
                plant_id=test_plant.id,
                lane_code=f"L00{i+1}",
                lane_name=f"Line {i+1}",
                capacity_per_day=Decimal("100.000")
            )
            repo.create_lane(dto)

        result = repo.list_lanes(page=1, page_size=10)

        assert result["total"] == 3
        assert len(result["items"]) == 3
        assert result["page"] == 1
        assert result["page_size"] == 10

    def test_list_lanes_filter_by_plant(self, db_session, test_organization):
        """Test listing lanes filtered by plant"""
        # Create two plants
        plant1 = Plant(organization_id=test_organization.id, plant_code="P001", plant_name="Plant 1")
        plant2 = Plant(organization_id=test_organization.id, plant_code="P002", plant_name="Plant 2")
        db_session.add_all([plant1, plant2])
        db_session.commit()

        repo = LaneRepository(db_session)

        # Create lanes in both plants
        dto1 = LaneCreateRequest(plant_id=plant1.id, lane_code="L001", lane_name="Line 1", capacity_per_day=Decimal("100"))
        dto2 = LaneCreateRequest(plant_id=plant2.id, lane_code="L001", lane_name="Line 1", capacity_per_day=Decimal("100"))
        repo.create_lane(dto1)
        repo.create_lane(dto2)

        result = repo.list_lanes(plant_id=plant1.id)

        assert result["total"] == 1
        assert result["items"][0].plant_id == plant1.id

    def test_list_lanes_filter_by_is_active(self, db_session, test_plant):
        """Test listing lanes filtered by active status"""
        repo = LaneRepository(db_session)

        # Create active and inactive lanes
        dto1 = LaneCreateRequest(plant_id=test_plant.id, lane_code="L001", lane_name="Active", capacity_per_day=Decimal("100"))
        dto2 = LaneCreateRequest(plant_id=test_plant.id, lane_code="L002", lane_name="Inactive", capacity_per_day=Decimal("100"))
        lane1 = repo.create_lane(dto1)
        lane2 = repo.create_lane(dto2)

        # Deactivate second lane
        lane2.is_active = False
        db_session.commit()

        result = repo.list_lanes(is_active=True)

        assert result["total"] == 1
        assert result["items"][0].id == lane1.id

    def test_list_lanes_pagination(self, db_session, test_plant):
        """Test lane pagination"""
        repo = LaneRepository(db_session)

        # Create 5 lanes
        for i in range(5):
            dto = LaneCreateRequest(
                plant_id=test_plant.id,
                lane_code=f"L00{i+1}",
                lane_name=f"Line {i+1}",
                capacity_per_day=Decimal("100")
            )
            repo.create_lane(dto)

        # Get page 1 with 2 items
        result = repo.list_lanes(page=1, page_size=2)

        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["page"] == 1

        # Get page 2
        result = repo.list_lanes(page=2, page_size=2)

        assert result["total"] == 5
        assert len(result["items"]) == 2
        assert result["page"] == 2

    def test_update_lane(self, db_session, test_plant):
        """Test updating a lane"""
        repo = LaneRepository(db_session)
        dto = LaneCreateRequest(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Original Name",
            capacity_per_day=Decimal("100.000")
        )
        lane = repo.create_lane(dto)

        update_dto = LaneUpdateRequest(
            lane_name="Updated Name",
            capacity_per_day=Decimal("150.000")
        )
        updated = repo.update_lane(lane.id, update_dto)

        assert updated is not None
        assert updated.lane_name == "Updated Name"
        assert updated.capacity_per_day == Decimal("150.000")
        assert updated.lane_code == "L001"  # Unchanged

    def test_update_nonexistent_lane_returns_none(self, db_session):
        """Test updating nonexistent lane returns None"""
        repo = LaneRepository(db_session)
        update_dto = LaneUpdateRequest(lane_name="Updated")

        result = repo.update_lane(999, update_dto)

        assert result is None

    def test_delete_lane_soft_delete(self, db_session, test_plant):
        """Test soft deleting a lane"""
        repo = LaneRepository(db_session)
        dto = LaneCreateRequest(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Test Lane",
            capacity_per_day=Decimal("100.000")
        )
        lane = repo.create_lane(dto)

        success = repo.delete_lane(lane.id)

        assert success is True
        # Lane still exists but is inactive
        deleted_lane = repo.get_lane_by_id(lane.id)
        assert deleted_lane is not None
        assert deleted_lane.is_active is False

    def test_delete_nonexistent_lane_returns_false(self, db_session):
        """Test deleting nonexistent lane returns False"""
        repo = LaneRepository(db_session)

        success = repo.delete_lane(999)

        assert success is False


class TestLaneAssignmentRepositoryCRUD:
    """Test Lane Assignment CRUD operations"""

    def test_create_assignment(self, db_session, test_organization, test_plant, test_work_order, test_project):
        """Test creating a lane assignment"""
        # First create a lane
        lane = Lane(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Test Lane",
            capacity_per_day=Decimal("100.000")
        )
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)
        dto = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            project_id=test_project.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000"),
            priority=1,
            notes="Test assignment"
        )

        assignment = repo.create_assignment(dto)

        assert assignment.id is not None
        assert assignment.organization_id == test_organization.id
        assert assignment.lane_id == lane.id
        assert assignment.work_order_id == test_work_order.id
        assert assignment.project_id == test_project.id
        assert assignment.scheduled_start == date(2025, 1, 1)
        assert assignment.scheduled_end == date(2025, 1, 5)
        assert assignment.allocated_capacity == Decimal("50.000")
        assert assignment.status == LaneAssignmentStatus.PLANNED

    def test_create_assignment_capacity_validation(self, db_session, test_organization, test_plant, test_work_order):
        """Test assignment rejects capacity > lane capacity"""
        lane = Lane(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Test Lane",
            capacity_per_day=Decimal("100.000")
        )
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)
        dto = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("150.000")  # Exceeds lane capacity
        )

        with pytest.raises(ValueError, match="exceeds lane daily capacity"):
            repo.create_assignment(dto)

    def test_create_assignment_nonexistent_lane_fails(self, db_session, test_organization, test_plant, test_work_order):
        """Test assignment to nonexistent lane fails"""
        repo = LaneRepository(db_session)
        dto = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=999,  # Nonexistent
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000")
        )

        with pytest.raises(ValueError, match="Lane 999 not found"):
            repo.create_assignment(dto)

    def test_get_assignment_by_id(self, db_session, test_organization, test_plant, test_work_order):
        """Test retrieving assignment by ID"""
        lane = Lane(plant_id=test_plant.id, lane_code="L001", lane_name="Test", capacity_per_day=Decimal("100"))
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)
        dto = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50.000")
        )
        created = repo.create_assignment(dto)

        assignment = repo.get_assignment_by_id(created.id)

        assert assignment is not None
        assert assignment.id == created.id

    def test_list_assignments_filter_by_lane(self, db_session, test_organization, test_plant, test_work_order):
        """Test listing assignments filtered by lane"""
        lane1 = Lane(plant_id=test_plant.id, lane_code="L001", lane_name="Lane 1", capacity_per_day=Decimal("100"))
        lane2 = Lane(plant_id=test_plant.id, lane_code="L002", lane_name="Lane 2", capacity_per_day=Decimal("100"))
        db_session.add_all([lane1, lane2])
        db_session.commit()

        repo = LaneRepository(db_session)

        # Create assignments for both lanes
        dto1 = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane1.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50")
        )
        dto2 = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane2.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50")
        )
        repo.create_assignment(dto1)
        repo.create_assignment(dto2)

        result = repo.list_assignments(lane_id=lane1.id)

        assert result["total"] == 1
        assert result["items"][0].lane_id == lane1.id

    def test_list_assignments_filter_by_date_range(self, db_session, test_organization, test_plant, test_work_order):
        """Test listing assignments filtered by date range"""
        lane = Lane(plant_id=test_plant.id, lane_code="L001", lane_name="Lane", capacity_per_day=Decimal("100"))
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)

        # Create assignments with different dates
        dto1 = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50")
        )
        dto2 = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 2, 1),
            scheduled_end=date(2025, 2, 5),
            allocated_capacity=Decimal("50")
        )
        repo.create_assignment(dto1)
        repo.create_assignment(dto2)

        # Filter for January assignments
        result = repo.list_assignments(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))

        assert result["total"] == 1
        assert result["items"][0].scheduled_start == date(2025, 1, 1)

    def test_list_assignments_filter_by_status(self, db_session, test_organization, test_plant, test_work_order):
        """Test listing assignments filtered by status"""
        lane = Lane(plant_id=test_plant.id, lane_code="L001", lane_name="Lane", capacity_per_day=Decimal("100"))
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)

        dto = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50")
        )
        assignment = repo.create_assignment(dto)

        # Update to ACTIVE
        assignment.status = LaneAssignmentStatus.ACTIVE
        db_session.commit()

        result = repo.list_assignments(status=LaneAssignmentStatus.ACTIVE)

        assert result["total"] == 1
        assert result["items"][0].status == LaneAssignmentStatus.ACTIVE

    def test_update_assignment(self, db_session, test_organization, test_plant, test_work_order):
        """Test updating an assignment"""
        lane = Lane(plant_id=test_plant.id, lane_code="L001", lane_name="Lane", capacity_per_day=Decimal("100"))
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)
        dto = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50")
        )
        assignment = repo.create_assignment(dto)

        update_dto = LaneAssignmentUpdateRequest(
            allocated_capacity=Decimal("60"),
            status=LaneAssignmentStatus.ACTIVE,
            notes="Updated"
        )
        updated = repo.update_assignment(assignment.id, update_dto)

        assert updated is not None
        assert updated.allocated_capacity == Decimal("60")
        assert updated.status == LaneAssignmentStatus.ACTIVE
        assert updated.notes == "Updated"

    def test_delete_assignment(self, db_session, test_organization, test_plant, test_work_order):
        """Test deleting an assignment"""
        lane = Lane(plant_id=test_plant.id, lane_code="L001", lane_name="Lane", capacity_per_day=Decimal("100"))
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)
        dto = LaneAssignmentCreateRequest(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 1),
            scheduled_end=date(2025, 1, 5),
            allocated_capacity=Decimal("50")
        )
        assignment = repo.create_assignment(dto)

        success = repo.delete_assignment(assignment.id)

        assert success is True
        assert repo.get_assignment_by_id(assignment.id) is None


class TestLaneCapacityCalculation:
    """Test lane capacity calculation functionality"""

    def test_get_lane_capacity_no_assignments(self, db_session, test_plant):
        """Test capacity calculation with no assignments"""
        lane = Lane(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Test Lane",
            capacity_per_day=Decimal("100.000")
        )
        db_session.add(lane)
        db_session.commit()

        repo = LaneRepository(db_session)
        capacity = repo.get_lane_capacity(lane.id, date(2025, 1, 15))

        assert capacity is not None
        assert capacity.lane_id == lane.id
        assert capacity.total_capacity == Decimal("100.000")
        assert capacity.allocated_capacity == Decimal("0")
        assert capacity.available_capacity == Decimal("100.000")
        assert capacity.utilization_rate == Decimal("0.00")
        assert capacity.assignment_count == 0

    def test_get_lane_capacity_with_assignments(self, db_session, test_organization, test_plant, test_work_order):
        """Test capacity calculation with assignments"""
        lane = Lane(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Test Lane",
            capacity_per_day=Decimal("100.000")
        )
        db_session.add(lane)
        db_session.commit()

        # Create assignments that overlap Jan 15
        assignment1 = LaneAssignment(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 10),
            scheduled_end=date(2025, 1, 20),
            allocated_capacity=Decimal("30.000"),
            status=LaneAssignmentStatus.ACTIVE
        )
        assignment2 = LaneAssignment(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 15),
            scheduled_end=date(2025, 1, 25),
            allocated_capacity=Decimal("45.000"),
            status=LaneAssignmentStatus.PLANNED
        )
        db_session.add_all([assignment1, assignment2])
        db_session.commit()

        repo = LaneRepository(db_session)
        capacity = repo.get_lane_capacity(lane.id, date(2025, 1, 15))

        assert capacity is not None
        assert capacity.allocated_capacity == Decimal("75.000")  # 30 + 45
        assert capacity.available_capacity == Decimal("25.000")  # 100 - 75
        assert capacity.utilization_rate == Decimal("75.00")  # 75%
        assert capacity.assignment_count == 2

    def test_get_lane_capacity_excludes_completed_cancelled(self, db_session, test_organization, test_plant, test_work_order):
        """Test capacity calculation excludes completed/cancelled assignments"""
        lane = Lane(
            plant_id=test_plant.id,
            lane_code="L001",
            lane_name="Test Lane",
            capacity_per_day=Decimal("100.000")
        )
        db_session.add(lane)
        db_session.commit()

        # Active assignment
        assignment1 = LaneAssignment(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 10),
            scheduled_end=date(2025, 1, 20),
            allocated_capacity=Decimal("30.000"),
            status=LaneAssignmentStatus.ACTIVE
        )
        # Completed assignment - should not count
        assignment2 = LaneAssignment(
            organization_id=test_organization.id,
            plant_id=test_plant.id,
            lane_id=lane.id,
            work_order_id=test_work_order.id,
            scheduled_start=date(2025, 1, 10),
            scheduled_end=date(2025, 1, 20),
            allocated_capacity=Decimal("50.000"),
            status=LaneAssignmentStatus.COMPLETED
        )
        db_session.add_all([assignment1, assignment2])
        db_session.commit()

        repo = LaneRepository(db_session)
        capacity = repo.get_lane_capacity(lane.id, date(2025, 1, 15))

        assert capacity.allocated_capacity == Decimal("30.000")  # Only active
        assert capacity.assignment_count == 1

    def test_get_lane_capacity_nonexistent_lane(self, db_session):
        """Test capacity for nonexistent lane returns None"""
        repo = LaneRepository(db_session)

        capacity = repo.get_lane_capacity(999, date(2025, 1, 15))

        assert capacity is None
