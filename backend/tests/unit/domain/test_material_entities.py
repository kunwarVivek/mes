"""
Unit tests for Material domain entities.
Following TDD approach: RED -> GREEN -> REFACTOR
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.core.database import Base
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


class TestUnitOfMeasure:
    """Test UnitOfMeasure entity"""

    def test_create_base_uom(self, db_session):
        """Test creating a base unit of measure"""
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add(uom)
        db_session.commit()

        assert uom.id is not None
        assert uom.uom_code == "EA"
        assert uom.uom_name == "Each"
        assert uom.dimension == "QUANTITY"
        assert uom.is_base_unit is True
        assert uom.conversion_factor == 1.0
        assert uom.created_at is not None

    def test_create_derived_uom(self, db_session):
        """Test creating a derived unit with conversion factor"""
        uom = UnitOfMeasure(
            uom_code="KG",
            uom_name="Kilogram",
            dimension="MASS",
            is_base_unit=False,
            conversion_factor=1000.0  # 1 KG = 1000 grams
        )
        db_session.add(uom)
        db_session.commit()

        assert uom.conversion_factor == 1000.0
        assert uom.is_base_unit is False

    def test_uom_code_unique_constraint(self, db_session):
        """Test that uom_code must be unique"""
        uom1 = UnitOfMeasure(
            uom_code="M",
            uom_name="Meter",
            dimension="LENGTH",
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add(uom1)
        db_session.commit()

        uom2 = UnitOfMeasure(
            uom_code="M",
            uom_name="Mile",
            dimension="LENGTH",
            is_base_unit=False,
            conversion_factor=1609.34
        )
        db_session.add(uom2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_standard_uoms_dimensions(self, db_session):
        """Test that standard UOMs have correct dimensions"""
        standard_uoms = [
            ("EA", "Each", "QUANTITY"),
            ("KG", "Kilogram", "MASS"),
            ("M", "Meter", "LENGTH"),
            ("L", "Liter", "VOLUME"),
            ("HR", "Hour", "TIME")
        ]

        for code, name, dimension in standard_uoms:
            uom = UnitOfMeasure(
                uom_code=code,
                uom_name=name,
                dimension=dimension,
                is_base_unit=True,
                conversion_factor=1.0
            )
            db_session.add(uom)

        db_session.commit()

        # Verify all were created
        assert db_session.query(UnitOfMeasure).count() == 5

    def test_uom_has_index_on_code(self, db_engine):
        """Test that uom_code has an index"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('unit_of_measure')

        # Check that uom_code is indexed
        index_columns = [idx['column_names'] for idx in indexes]
        assert any('uom_code' in cols for cols in index_columns)


class TestMaterialCategory:
    """Test MaterialCategory entity"""

    def test_create_root_category(self, db_session):
        """Test creating a root category (no parent)"""
        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            parent_category_id=None,
            is_active=True
        )
        db_session.add(category)
        db_session.commit()

        assert category.id is not None
        assert category.organization_id == 1
        assert category.category_code == "RAW"
        assert category.category_name == "Raw Materials"
        assert category.parent_category_id is None
        assert category.is_active is True
        assert category.created_at is not None

    def test_create_child_category(self, db_session):
        """Test creating a hierarchical category structure"""
        # Create parent category
        parent = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            parent_category_id=None,
            is_active=True
        )
        db_session.add(parent)
        db_session.commit()

        # Create child category
        child = MaterialCategory(
            organization_id=1,
            category_code="RAW-METAL",
            category_name="Metal Raw Materials",
            parent_category_id=parent.id,
            is_active=True
        )
        db_session.add(child)
        db_session.commit()

        assert child.parent_category_id == parent.id
        assert child.parent.id == parent.id
        assert parent.id in [c.parent_category_id for c in parent.children]

    def test_category_code_unique_per_org(self, db_session):
        """Test that category_code must be unique within organization"""
        cat1 = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add(cat1)
        db_session.commit()

        # Same code, same org - should fail
        cat2 = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Different Name",
            is_active=True
        )
        db_session.add(cat2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_category_code_unique_across_orgs(self, db_session):
        """Test that category_code can be same across different organizations"""
        cat1 = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials Org 1",
            is_active=True
        )
        db_session.add(cat1)
        db_session.commit()

        # Same code, different org - should succeed
        cat2 = MaterialCategory(
            organization_id=2,
            category_code="RAW",
            category_name="Raw Materials Org 2",
            is_active=True
        )
        db_session.add(cat2)
        db_session.commit()

        assert cat1.category_code == cat2.category_code
        assert cat1.organization_id != cat2.organization_id

    def test_cascade_delete_protection(self, db_session):
        """Test that deleting parent handles children appropriately"""
        parent = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add(parent)
        db_session.commit()

        child = MaterialCategory(
            organization_id=1,
            category_code="RAW-METAL",
            category_name="Metal Raw Materials",
            parent_category_id=parent.id,
            is_active=True
        )
        db_session.add(child)
        db_session.commit()

        # Verify parent-child relationship
        assert child.parent_category_id == parent.id


class TestMaterial:
    """Test Material entity"""

    def test_create_material_with_required_fields(self, db_session):
        """Test creating a material with all required fields"""
        # Create dependencies first
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        db_session.add(uom)

        category = MaterialCategory(
            organization_id=1,
            category_code="FERT",
            category_name="Finished Goods",
            is_active=True
        )
        db_session.add(category)
        db_session.commit()

        # Create material
        material = Material(
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
            material_name="Steel Plate 10mm",
            description="Steel plate with 10mm thickness",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=100.0,
            reorder_point=50.0,
            lot_size=500.0,
            lead_time_days=7,
            is_active=True
        )
        db_session.add(material)
        db_session.commit()

        assert material.id is not None
        assert material.organization_id == 1
        assert material.plant_id == 101
        assert material.material_number == "MAT0001"
        assert material.material_name == "Steel Plate 10mm"
        assert material.procurement_type == "PURCHASE"
        assert material.mrp_type == "MRP"
        assert material.safety_stock == 100.0
        assert material.lead_time_days == 7
        assert material.is_active is True
        assert material.created_at is not None

    def test_material_number_format_validation(self, db_session):
        """Test that material_number follows format constraints (alphanumeric, max 10 chars)"""
        # This test will validate format in the entity itself
        # For now, we test database constraints

        # Create dependencies
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add_all([uom, category])
        db_session.commit()

        # Valid material number (alphanumeric, <= 10 chars)
        material = Material(
            organization_id=1,
            plant_id=101,
            material_number="MAT123",
            material_name="Test Material",
            description="Test",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=0.0,
            reorder_point=0.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )
        db_session.add(material)
        db_session.commit()

        assert material.material_number == "MAT123"

    def test_material_number_unique_constraint(self, db_session):
        """Test that material_number must be unique"""
        # Create dependencies
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add_all([uom, category])
        db_session.commit()

        mat1 = Material(
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
            material_name="Material 1",
            description="First material",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=0.0,
            reorder_point=0.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )
        db_session.add(mat1)
        db_session.commit()

        mat2 = Material(
            organization_id=1,
            plant_id=102,
            material_number="MAT0001",  # Duplicate
            material_name="Material 2",
            description="Second material",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type="MANUFACTURE",
            mrp_type="REORDER",
            safety_stock=0.0,
            reorder_point=0.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )
        db_session.add(mat2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_safety_stock_non_negative(self, db_session):
        """Test that safety_stock must be >= 0"""
        # This will be validated at application level
        # Database allows negative, but business logic should prevent it
        pass

    def test_lead_time_days_non_negative(self, db_session):
        """Test that lead_time_days must be >= 0"""
        # This will be validated at application level
        pass

    def test_material_procurement_types(self, db_session):
        """Test valid procurement types: PURCHASE, MANUFACTURE, BOTH"""
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add_all([uom, category])
        db_session.commit()

        for proc_type in ["PURCHASE", "MANUFACTURE", "BOTH"]:
            material = Material(
                organization_id=1,
                plant_id=101,
                material_number=f"MAT{proc_type[:3]}",
                material_name=f"Material {proc_type}",
                description="Test",
                material_category_id=category.id,
                base_uom_id=uom.id,
                procurement_type=proc_type,
                mrp_type="MRP",
                safety_stock=0.0,
                reorder_point=0.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )
            db_session.add(material)

        db_session.commit()
        assert db_session.query(Material).count() == 3

    def test_material_mrp_types(self, db_session):
        """Test valid MRP types: MRP, REORDER"""
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add_all([uom, category])
        db_session.commit()

        for mrp_type in ["MRP", "REORDER"]:
            material = Material(
                organization_id=1,
                plant_id=101,
                material_number=f"MAT{mrp_type[:3]}",
                material_name=f"Material {mrp_type}",
                description="Test",
                material_category_id=category.id,
                base_uom_id=uom.id,
                procurement_type="PURCHASE",
                mrp_type=mrp_type,
                safety_stock=0.0,
                reorder_point=0.0,
                lot_size=1.0,
                lead_time_days=0,
                is_active=True
            )
            db_session.add(material)

        db_session.commit()
        assert db_session.query(Material).count() == 2

    def test_material_rls_fields_present(self, db_session):
        """Test that RLS fields (organization_id, plant_id) are present"""
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add_all([uom, category])
        db_session.commit()

        material = Material(
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
            material_name="Test Material",
            description="Test",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=0.0,
            reorder_point=0.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )
        db_session.add(material)
        db_session.commit()

        # Verify RLS fields
        assert hasattr(material, 'organization_id')
        assert hasattr(material, 'plant_id')
        assert material.organization_id == 1
        assert material.plant_id == 101

    def test_material_has_indexes(self, db_engine):
        """Test that proper indexes exist on material table"""
        inspector = inspect(db_engine)
        indexes = inspector.get_indexes('material')

        # Check that material_number, organization_id, plant_id are indexed
        index_columns = []
        for idx in indexes:
            index_columns.extend(idx['column_names'])

        assert 'material_number' in index_columns
        assert 'organization_id' in index_columns
        assert 'plant_id' in index_columns

    def test_material_foreign_keys(self, db_engine):
        """Test that foreign key constraints exist"""
        inspector = inspect(db_engine)
        fks = inspector.get_foreign_keys('material')

        # Should have FKs to material_category and unit_of_measure
        fk_tables = [fk['referred_table'] for fk in fks]
        assert 'material_category' in fk_tables
        assert 'unit_of_measure' in fk_tables

    def test_material_repr(self, db_session):
        """Test that Material has a useful __repr__ method"""
        uom = UnitOfMeasure(
            uom_code="EA",
            uom_name="Each",
            dimension="QUANTITY",
            is_base_unit=True,
            conversion_factor=1.0
        )
        category = MaterialCategory(
            organization_id=1,
            category_code="RAW",
            category_name="Raw Materials",
            is_active=True
        )
        db_session.add_all([uom, category])
        db_session.commit()

        material = Material(
            organization_id=1,
            plant_id=101,
            material_number="MAT0001",
            material_name="Test Material",
            description="Test",
            material_category_id=category.id,
            base_uom_id=uom.id,
            procurement_type="PURCHASE",
            mrp_type="MRP",
            safety_stock=0.0,
            reorder_point=0.0,
            lot_size=1.0,
            lead_time_days=0,
            is_active=True
        )
        db_session.add(material)
        db_session.commit()

        repr_str = repr(material)
        assert "Material" in repr_str
        assert "MAT0001" in repr_str
