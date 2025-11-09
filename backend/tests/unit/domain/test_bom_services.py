"""
Unit tests for BOM (Bill of Materials) domain services.
Tests BOM explosion and validation services following TDD approach.
"""
import pytest
from datetime import datetime
from app.domain.services.bom_service import (
    BOMExplosionService,
    BOMValidationService,
    CircularReferenceError
)


class TestBOMExplosionService:
    """Tests for BOM explosion service"""

    @pytest.fixture
    def mock_bom_repository(self):
        """Mock BOM repository for testing"""
        class MockBOMRepository:
            def __init__(self):
                # Simple single-level BOM
                # Product A (id=1) requires:
                #   - Material B (id=2): 2 units, scrap 10%
                #   - Material C (id=3): 1 unit, scrap 5%
                self.bom_headers = {
                    1: {
                        'id': 1,
                        'material_id': 100,
                        'base_quantity': 1.0,
                        'bom_lines': [
                            {
                                'line_number': 10,
                                'component_material_id': 2,
                                'quantity': 2.0,
                                'scrap_factor': 10.0,
                                'is_phantom': False,
                                'unit_of_measure_id': 10
                            },
                            {
                                'line_number': 20,
                                'component_material_id': 3,
                                'quantity': 1.0,
                                'scrap_factor': 5.0,
                                'is_phantom': False,
                                'unit_of_measure_id': 10
                            }
                        ]
                    },
                    # Multilevel BOM
                    # Product X (id=2) requires:
                    #   - Material Y (id=4): 3 units, scrap 0%, PHANTOM (has its own BOM id=3)
                    #   - Material Z (id=5): 2 units, scrap 10%
                    2: {
                        'id': 2,
                        'material_id': 101,
                        'base_quantity': 1.0,
                        'bom_lines': [
                            {
                                'line_number': 10,
                                'component_material_id': 4,
                                'quantity': 3.0,
                                'scrap_factor': 0.0,
                                'is_phantom': True,
                                'unit_of_measure_id': 10
                            },
                            {
                                'line_number': 20,
                                'component_material_id': 5,
                                'quantity': 2.0,
                                'scrap_factor': 10.0,
                                'is_phantom': False,
                                'unit_of_measure_id': 10
                            }
                        ]
                    },
                    # Sub-BOM for Material Y (id=4)
                    # Material Y requires:
                    #   - Material W (id=6): 2 units, scrap 5%
                    3: {
                        'id': 3,
                        'material_id': 4,  # Material Y
                        'base_quantity': 1.0,
                        'bom_lines': [
                            {
                                'line_number': 10,
                                'component_material_id': 6,
                                'quantity': 2.0,
                                'scrap_factor': 5.0,
                                'is_phantom': False,
                                'unit_of_measure_id': 10
                            }
                        ]
                    }
                }

            def get_bom_header(self, bom_header_id):
                return self.bom_headers.get(bom_header_id)

            def get_bom_by_material(self, material_id):
                """Get BOM header by material_id"""
                for bom in self.bom_headers.values():
                    if bom['material_id'] == material_id:
                        return bom
                return None

        return MockBOMRepository()

    def test_explode_single_level_bom(self, mock_bom_repository):
        """Test BOM explosion for single-level BOM"""
        service = BOMExplosionService(mock_bom_repository)
        result = service.explode_bom(bom_header_id=1, required_quantity=1.0)

        # Expected results:
        # Material B: 2 * 1.1 (scrap) = 2.2 units
        # Material C: 1 * 1.05 (scrap) = 1.05 units
        assert 2 in result  # Material B
        assert 3 in result  # Material C
        assert result[2]['total_quantity'] == 2.2
        assert result[3]['total_quantity'] == 1.05
        assert result[2]['unit_of_measure_id'] == 10
        assert len(result[2]['details']) == 1
        assert result[2]['details'][0]['level'] == 1

    def test_explode_single_level_bom_with_multiplier(self, mock_bom_repository):
        """Test BOM explosion with quantity multiplier"""
        service = BOMExplosionService(mock_bom_repository)
        result = service.explode_bom(bom_header_id=1, required_quantity=5.0)

        # Expected results for 5 units:
        # Material B: 2 * 1.1 * 5 = 11.0 units
        # Material C: 1 * 1.05 * 5 = 5.25 units
        assert result[2]['total_quantity'] == 11.0
        assert result[3]['total_quantity'] == 5.25

    def test_explode_multilevel_bom(self, mock_bom_repository):
        """Test BOM explosion for multilevel (phantom) BOM"""
        service = BOMExplosionService(mock_bom_repository)
        result = service.explode_bom(bom_header_id=2, required_quantity=1.0)

        # Product X requires:
        #   - Material Y (phantom, 3 units) -> explodes to Material W
        #   - Material Z (2 units, scrap 10%) = 2.2 units
        # Material Y requires:
        #   - Material W (2 units, scrap 5%) = 2.1 units per Y
        # Total Material W: 3 * 2.1 = 6.3 units
        assert 5 in result  # Material Z (not phantom)
        assert 6 in result  # Material W (from phantom explosion)
        assert 4 not in result  # Material Y should not be in result (phantom)

        assert result[5]['total_quantity'] == pytest.approx(2.2)  # Material Z
        assert result[6]['total_quantity'] == pytest.approx(6.3)  # Material W (3 * 2 * 1.05)
        assert result[6]['details'][0]['level'] == 2  # Level 2 (nested)

    def test_explode_bom_invalid_bom_id(self, mock_bom_repository):
        """Test BOM explosion with invalid BOM header ID"""
        service = BOMExplosionService(mock_bom_repository)
        with pytest.raises(ValueError, match="BOM header not found"):
            service.explode_bom(bom_header_id=999, required_quantity=1.0)

    def test_explode_bom_zero_quantity(self, mock_bom_repository):
        """Test BOM explosion with zero required quantity"""
        service = BOMExplosionService(mock_bom_repository)
        with pytest.raises(ValueError, match="Required quantity must be positive"):
            service.explode_bom(bom_header_id=1, required_quantity=0.0)

    def test_explode_bom_aggregates_duplicate_materials(self, mock_bom_repository):
        """Test BOM explosion aggregates same material from multiple lines"""
        # Add a BOM with duplicate materials
        mock_bom_repository.bom_headers[4] = {
            'id': 4,
            'material_id': 200,
            'base_quantity': 1.0,
            'bom_lines': [
                {
                    'line_number': 10,
                    'component_material_id': 2,
                    'quantity': 1.0,
                    'scrap_factor': 0.0,
                    'is_phantom': False,
                    'unit_of_measure_id': 10
                },
                {
                    'line_number': 20,
                    'component_material_id': 2,  # Same material
                    'quantity': 2.0,
                    'scrap_factor': 0.0,
                    'is_phantom': False,
                    'unit_of_measure_id': 10
                }
            ]
        }

        service = BOMExplosionService(mock_bom_repository)
        result = service.explode_bom(bom_header_id=4, required_quantity=1.0)

        # Material 2 appears twice: 1.0 + 2.0 = 3.0
        assert result[2]['total_quantity'] == 3.0
        assert len(result[2]['details']) == 2  # Two detail lines


class TestBOMValidationService:
    """Tests for BOM validation service"""

    @pytest.fixture
    def mock_bom_repository_with_cycles(self):
        """Mock BOM repository with circular references for testing"""
        class MockBOMRepository:
            def __init__(self):
                self.bom_headers = {}

            def get_bom_header(self, bom_header_id):
                return self.bom_headers.get(bom_header_id)

            def get_bom_by_material(self, material_id):
                for bom in self.bom_headers.values():
                    if bom['material_id'] == material_id:
                        return bom
                return None

        return MockBOMRepository()

    def test_validate_no_circular_reference_simple(self, mock_bom_repository_with_cycles):
        """Test validation with no circular reference (simple BOM)"""
        # Product A (mat 1) -> Material B (mat 2), Material C (mat 3)
        mock_bom_repository_with_cycles.bom_headers[1] = {
            'id': 1,
            'material_id': 1,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 2, 'quantity': 1.0, 'is_phantom': False},
                {'component_material_id': 3, 'quantity': 1.0, 'is_phantom': False}
            ]
        }

        service = BOMValidationService(mock_bom_repository_with_cycles)
        # Should not raise any exception
        result = service.validate_no_circular_reference(bom_header_id=1)
        assert result is True

    def test_validate_direct_circular_reference(self, mock_bom_repository_with_cycles):
        """Test validation detects direct circular reference"""
        # Product A (mat 1) -> Material A (mat 1) - DIRECT CYCLE
        mock_bom_repository_with_cycles.bom_headers[1] = {
            'id': 1,
            'material_id': 1,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 1, 'quantity': 1.0, 'is_phantom': True}  # Self-reference
            ]
        }

        service = BOMValidationService(mock_bom_repository_with_cycles)
        with pytest.raises(CircularReferenceError, match="Circular reference detected in BOM"):
            service.validate_no_circular_reference(bom_header_id=1)

    def test_validate_indirect_circular_reference(self, mock_bom_repository_with_cycles):
        """Test validation detects indirect circular reference"""
        # Product A (mat 1) -> Material B (mat 2, phantom) -> Material A (mat 1) - INDIRECT CYCLE
        mock_bom_repository_with_cycles.bom_headers[1] = {
            'id': 1,
            'material_id': 1,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 2, 'quantity': 1.0, 'is_phantom': True}
            ]
        }
        mock_bom_repository_with_cycles.bom_headers[2] = {
            'id': 2,
            'material_id': 2,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 1, 'quantity': 1.0, 'is_phantom': True}  # Cycles back
            ]
        }

        service = BOMValidationService(mock_bom_repository_with_cycles)
        with pytest.raises(CircularReferenceError, match="Circular reference detected in BOM"):
            service.validate_no_circular_reference(bom_header_id=1)

    def test_validate_three_level_circular_reference(self, mock_bom_repository_with_cycles):
        """Test validation detects three-level circular reference"""
        # A (mat 1) -> B (mat 2, phantom) -> C (mat 3, phantom) -> A (mat 1) - 3-LEVEL CYCLE
        mock_bom_repository_with_cycles.bom_headers[1] = {
            'id': 1,
            'material_id': 1,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 2, 'quantity': 1.0, 'is_phantom': True}
            ]
        }
        mock_bom_repository_with_cycles.bom_headers[2] = {
            'id': 2,
            'material_id': 2,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 3, 'quantity': 1.0, 'is_phantom': True}
            ]
        }
        mock_bom_repository_with_cycles.bom_headers[3] = {
            'id': 3,
            'material_id': 3,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 1, 'quantity': 1.0, 'is_phantom': True}  # Cycles back
            ]
        }

        service = BOMValidationService(mock_bom_repository_with_cycles)
        with pytest.raises(CircularReferenceError, match="Circular reference detected in BOM"):
            service.validate_no_circular_reference(bom_header_id=1)

    def test_validate_complex_no_cycle(self, mock_bom_repository_with_cycles):
        """Test validation with complex multilevel BOM but no cycle"""
        # A (1) -> B (2, phantom), C (3)
        # B (2) -> D (4), E (5)
        # No cycles
        mock_bom_repository_with_cycles.bom_headers[1] = {
            'id': 1,
            'material_id': 1,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 2, 'quantity': 1.0, 'is_phantom': True},
                {'component_material_id': 3, 'quantity': 1.0, 'is_phantom': False}
            ]
        }
        mock_bom_repository_with_cycles.bom_headers[2] = {
            'id': 2,
            'material_id': 2,
            'base_quantity': 1.0,
            'bom_lines': [
                {'component_material_id': 4, 'quantity': 1.0, 'is_phantom': False},
                {'component_material_id': 5, 'quantity': 1.0, 'is_phantom': False}
            ]
        }

        service = BOMValidationService(mock_bom_repository_with_cycles)
        result = service.validate_no_circular_reference(bom_header_id=1)
        assert result is True

    def test_validate_bom_not_found(self, mock_bom_repository_with_cycles):
        """Test validation with non-existent BOM header"""
        service = BOMValidationService(mock_bom_repository_with_cycles)
        with pytest.raises(ValueError, match="BOM header not found"):
            service.validate_no_circular_reference(bom_header_id=999)
