"""
Unit tests for BOM SQLAlchemy models.
Following TDD approach: RED -> GREEN -> REFACTOR
Phase 3: Production Planning Module - Component 2
"""
import pytest
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.core.database import Base
from app.models.bom import (
    BOMHeader,
    BOMLine,
    BOMType
)
from app.models.material import Material, MaterialCategory, UnitOfMeasure


@pytest.fixture
def db_engine():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session for testing"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_dependencies(db_session):
    """Setup common test dependencies: UOM, Category, Materials"""
    # Create UOM
    uom = UnitOfMeasure(
        uom_code="EA",
        uom_name="Each",
        dimension="QUANTITY",
        is_base_unit=True,
        conversion_factor=1.0
    )
    db_session.add(uom)

    # Create Category
    category = MaterialCategory(
        organization_id=1,
        category_code="FERT",
        category_name="Finished Goods",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()

    # Create finished good material
    finished_good = Material(
        organization_id=1,
        plant_id=101,
        material_number="FG001",
        material_name="Finished Product A",
        description="Test finished good",
        material_category_id=category.id,
        base_uom_id=uom.id,
        procurement_type="MANUFACTURE",
        mrp_type="MRP",
        safety_stock=100.0,
        reorder_point=50.0,
        lot_size=10.0,
        lead_time_days=5,
        is_active=True
    )
    db_session.add(finished_good)

    # Create component materials
    component1 = Material(
        organization_id=1,
        plant_id=101,
        material_number="RM001",
        material_name="Raw Material 1",
        description="Test component",
        material_category_id=category.id,
        base_uom_id=uom.id,
        procurement_type="PURCHASE",
        mrp_type="MRP",
        safety_stock=50.0,
        reorder_point=25.0,
        lot_size=5.0,
        lead_time_days=3,
        is_active=True
    )
    db_session.add(component1)

    component2 = Material(
        organization_id=1,
        plant_id=101,
        material_number="RM002",
        material_name="Raw Material 2",
        description="Test component",
        material_category_id=category.id,
        base_uom_id=uom.id,
        procurement_type="PURCHASE",
        mrp_type="MRP",
        safety_stock=50.0,
        reorder_point=25.0,
        lot_size=5.0,
        lead_time_days=3,
        is_active=True
    )
    db_session.add(component2)
    db_session.commit()

    return {
        'uom': uom,
        'category': category,
        'finished_good': finished_good,
        'component1': component1,
        'component2': component2
    }


class TestBOMHeaderModel:
    """Tests for BOMHeader SQLAlchemy model"""

    def test_create_bom_header(self, db_session, setup_dependencies):
        """Test creating a valid BOM header"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        assert bom_header.id is not None
        assert bom_header.bom_number == "BOM-001"
        assert bom_header.bom_version == 1
        assert bom_header.is_active is True
        assert bom_header.created_at is not None

    def test_bom_header_unique_constraint(self, db_session, setup_dependencies):
        """Test unique constraint: (organization_id, plant_id, material_id, bom_version)"""
        deps = setup_dependencies
        bom1 = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM v1",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom1)
        db_session.commit()

        # Try to create duplicate BOM with same org, plant, material, version
        bom2 = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-002",  # Different BOM number
            material_id=deps['finished_good'].id,  # Same material
            bom_version=1,  # Same version
            bom_name="Product A BOM v1 duplicate",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_bom_header_different_versions_allowed(self, db_session, setup_dependencies):
        """Test that different versions of same material are allowed"""
        deps = setup_dependencies
        bom1 = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM v1",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 6, 30),
            is_active=False,
            created_by_user_id=100
        )
        db_session.add(bom1)
        db_session.commit()

        # Create version 2 (should succeed)
        bom2 = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=2,  # Different version
            bom_name="Product A BOM v2",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 7, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom2)
        db_session.commit()

        assert bom1.bom_version == 1
        assert bom2.bom_version == 2

    def test_bom_header_cascade_delete(self, db_session, setup_dependencies):
        """Test cascade delete when BOM header is deleted"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        # Add BOM lines
        bom_line = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=2.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=5.0,
            is_phantom=False,
            backflush=False
        )
        db_session.add(bom_line)
        db_session.commit()

        bom_header_id = bom_header.id
        db_session.delete(bom_header)
        db_session.commit()

        # BOM lines should be deleted
        lines = db_session.query(BOMLine).filter_by(bom_header_id=bom_header_id).all()
        assert len(lines) == 0

    def test_bom_header_indexes_exist(self, db_engine):
        """Test that indexes are created on BOM header table"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('bom_header')
        index_columns = [idx['column_names'] for idx in indexes]

        # Check for expected indexes
        assert ['organization_id'] in index_columns or ['organization_id', 'plant_id'] in index_columns
        assert ['material_id'] in index_columns
        assert ['bom_number'] in index_columns

    def test_bom_header_check_constraint_base_quantity(self, db_session, setup_dependencies):
        """Test base_quantity > 0 check constraint"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=-1.0,  # Invalid
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_bom_header_relationship_to_material(self, db_session, setup_dependencies):
        """Test BOM header relationship to Material"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        # Access relationship
        assert bom_header.material.material_number == "FG001"
        assert bom_header.unit_of_measure.uom_code == "EA"


class TestBOMLineModel:
    """Tests for BOMLine SQLAlchemy model"""

    def test_create_bom_line(self, db_session, setup_dependencies):
        """Test creating a valid BOM line"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        bom_line = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=2.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=10.0,
            operation_number=10,
            is_phantom=False,
            backflush=True
        )
        db_session.add(bom_line)
        db_session.commit()

        assert bom_line.id is not None
        assert bom_line.line_number == 10
        assert bom_line.quantity == 2.0
        assert bom_line.scrap_factor == 10.0
        assert bom_line.backflush is True
        assert bom_line.created_at is not None

    def test_bom_line_unique_constraint(self, db_session, setup_dependencies):
        """Test unique constraint: (bom_header_id, line_number)"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        bom_line1 = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=2.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=0.0,
            is_phantom=False,
            backflush=False
        )
        db_session.add(bom_line1)
        db_session.commit()

        # Try to create duplicate line number
        bom_line2 = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,  # Same line number
            component_material_id=deps['component2'].id,  # Different material
            quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=0.0,
            is_phantom=False,
            backflush=False
        )
        db_session.add(bom_line2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_bom_line_multiple_lines_different_numbers(self, db_session, setup_dependencies):
        """Test multiple BOM lines with different line numbers"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        bom_line1 = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=2.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=5.0,
            is_phantom=False,
            backflush=False
        )
        bom_line2 = BOMLine(
            bom_header_id=bom_header.id,
            line_number=20,  # Different line number
            component_material_id=deps['component2'].id,
            quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=10.0,
            is_phantom=False,
            backflush=True
        )
        db_session.add_all([bom_line1, bom_line2])
        db_session.commit()

        assert len(bom_header.bom_lines) == 2

    def test_bom_line_check_constraint_quantity(self, db_session, setup_dependencies):
        """Test quantity > 0 check constraint"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        bom_line = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=0.0,  # Invalid
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=0.0,
            is_phantom=False,
            backflush=False
        )
        db_session.add(bom_line)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_bom_line_check_constraint_scrap_factor_range(self, db_session, setup_dependencies):
        """Test scrap_factor range check constraint (0-100)"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        bom_line = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=150.0,  # Invalid (> 100)
            is_phantom=False,
            backflush=False
        )
        db_session.add(bom_line)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_bom_line_phantom_and_backflush_flags(self, db_session, setup_dependencies):
        """Test phantom and backflush boolean flags"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        bom_line = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=2.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=0.0,
            is_phantom=True,
            backflush=True
        )
        db_session.add(bom_line)
        db_session.commit()

        assert bom_line.is_phantom is True
        assert bom_line.backflush is True

    def test_bom_line_relationship_to_material(self, db_session, setup_dependencies):
        """Test BOM line relationship to component material"""
        deps = setup_dependencies
        bom_header = BOMHeader(
            organization_id=1,
            plant_id=101,
            bom_number="BOM-001",
            material_id=deps['finished_good'].id,
            bom_version=1,
            bom_name="Product A BOM",
            bom_type=BOMType.PRODUCTION,
            base_quantity=1.0,
            unit_of_measure_id=deps['uom'].id,
            effective_start_date=date(2024, 1, 1),
            effective_end_date=date(2024, 12, 31),
            is_active=True,
            created_by_user_id=100
        )
        db_session.add(bom_header)
        db_session.commit()

        bom_line = BOMLine(
            bom_header_id=bom_header.id,
            line_number=10,
            component_material_id=deps['component1'].id,
            quantity=2.0,
            unit_of_measure_id=deps['uom'].id,
            scrap_factor=0.0,
            is_phantom=False,
            backflush=False
        )
        db_session.add(bom_line)
        db_session.commit()

        # Access relationship
        assert bom_line.component_material.material_number == "RM001"
        assert bom_line.bom_header.bom_number == "BOM-001"
        assert bom_line.unit_of_measure.uom_code == "EA"

    def test_bom_line_indexes_exist(self, db_engine):
        """Test that indexes are created on BOM line table"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('bom_line')
        index_columns = [idx['column_names'] for idx in indexes]

        # Check for expected indexes
        assert ['bom_header_id'] in index_columns
        assert ['component_material_id'] in index_columns
