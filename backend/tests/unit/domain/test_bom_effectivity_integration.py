"""
Integration tests for BOM Effectivity with BOM Explosion Service.
Demonstrates how effectivity dates work during BOM explosion.
"""
import pytest
from datetime import date
from app.domain.services.bom_service import BOMExplosionService
from app.domain.services.bom_effectivity_service import BOMEffectivityService


class TestBOMExplosionWithEffectivity:
    """Integration tests for BOM explosion using effectivity dates"""

    @pytest.fixture
    def integrated_repository(self):
        """Repository with time-variant BOMs for testing"""
        class IntegratedBOMRepository:
            def __init__(self):
                # Material 100 has different component requirements over time
                # Q1 2024: Uses Material 200 (old design)
                # Q3 2024: Uses Material 300 (new design)
                self.bom_headers = {
                    1: {
                        'id': 1,
                        'material_id': 100,
                        'organization_id': 1,
                        'plant_id': 1,
                        'bom_number': 'BOM-100-V1',
                        'bom_version': 1,
                        'effective_start_date': date(2024, 1, 1),
                        'effective_end_date': date(2024, 6, 30),
                        'is_active': True,
                        'bom_lines': [
                            {
                                'line_number': 10,
                                'component_material_id': 200,  # Old component
                                'quantity': 2.0,
                                'scrap_factor': 10.0,
                                'is_phantom': False,
                                'unit_of_measure_id': 10
                            }
                        ]
                    },
                    2: {
                        'id': 2,
                        'material_id': 100,
                        'organization_id': 1,
                        'plant_id': 1,
                        'bom_number': 'BOM-100-V2',
                        'bom_version': 2,
                        'effective_start_date': date(2024, 7, 1),
                        'effective_end_date': None,  # Open-ended
                        'is_active': True,
                        'bom_lines': [
                            {
                                'line_number': 10,
                                'component_material_id': 300,  # New component
                                'quantity': 1.5,
                                'scrap_factor': 5.0,
                                'is_phantom': False,
                                'unit_of_measure_id': 10
                            }
                        ]
                    }
                }

                # Store by material for effectivity service
                self.boms_by_material = {
                    100: [self.bom_headers[1], self.bom_headers[2]]
                }

            def get_bom_header(self, bom_header_id):
                return self.bom_headers.get(bom_header_id)

            def get_bom_by_material(self, material_id):
                # Return first BOM (fallback behavior)
                for bom in self.bom_headers.values():
                    if bom['material_id'] == material_id:
                        return bom
                return None

            def get_boms_by_material(self, material_id, organization_id, plant_id):
                """Get all BOMs for effectivity service"""
                return self.boms_by_material.get(material_id, [])

            def get_active_boms_by_material(self, material_id, organization_id, plant_id):
                """Get only active BOMs"""
                boms = self.get_boms_by_material(material_id, organization_id, plant_id)
                return [bom for bom in boms if bom['is_active']]

        return IntegratedBOMRepository()

    def test_explosion_uses_effective_bom_for_q1(self, integrated_repository):
        """Test BOM explosion uses correct BOM version for Q1 2024 production"""
        effectivity_service = BOMEffectivityService(integrated_repository)
        explosion_service = BOMExplosionService(
            integrated_repository,
            effectivity_service=effectivity_service
        )

        # Explode for Q1 2024 production
        result = explosion_service.explode_bom(
            bom_header_id=1,
            required_quantity=10.0,
            production_date=date(2024, 3, 15),
            organization_id=1,
            plant_id=1
        )

        # Should use old component (Material 200)
        # Quantity: 2.0 * 1.1 (scrap) * 10 = 22.0
        assert 200 in result
        assert result[200]['total_quantity'] == 22.0
        assert 300 not in result  # New component not used

    def test_explosion_uses_effective_bom_for_q3(self, integrated_repository):
        """Test BOM explosion uses correct BOM version for Q3 2024 production"""
        effectivity_service = BOMEffectivityService(integrated_repository)
        explosion_service = BOMExplosionService(
            integrated_repository,
            effectivity_service=effectivity_service
        )

        # Explode for Q3 2024 production
        result = explosion_service.explode_bom(
            bom_header_id=2,
            required_quantity=10.0,
            production_date=date(2024, 9, 15),
            organization_id=1,
            plant_id=1
        )

        # Should use new component (Material 300)
        # Quantity: 1.5 * 1.05 (scrap) * 10 = 15.75
        assert 300 in result
        assert result[300]['total_quantity'] == pytest.approx(15.75)
        assert 200 not in result  # Old component not used

    def test_explosion_without_effectivity_uses_default(self, integrated_repository):
        """Test BOM explosion without effectivity parameters uses default lookup"""
        explosion_service = BOMExplosionService(integrated_repository)

        # Explode without effectivity parameters
        result = explosion_service.explode_bom(
            bom_header_id=1,
            required_quantity=10.0
        )

        # Should still work with default behavior
        assert 200 in result
        assert result[200]['total_quantity'] == 22.0

    def test_explosion_backward_compatible(self, integrated_repository):
        """Test that BOM explosion is backward compatible (effectivity_service=None)"""
        explosion_service = BOMExplosionService(
            integrated_repository,
            effectivity_service=None  # Explicit None
        )

        result = explosion_service.explode_bom(
            bom_header_id=1,
            required_quantity=5.0
        )

        # Should work without effectivity service
        assert 200 in result
        assert result[200]['total_quantity'] == 11.0  # 2 * 1.1 * 5

    def test_effectivity_service_standalone(self, integrated_repository):
        """Test effectivity service can be used standalone"""
        service = BOMEffectivityService(integrated_repository)

        # Get BOM for Q1 production
        bom_q1 = service.get_effective_bom(
            material_id=100,
            production_date=date(2024, 3, 15),
            organization_id=1,
            plant_id=1
        )

        # Get BOM for Q3 production
        bom_q3 = service.get_effective_bom(
            material_id=100,
            production_date=date(2024, 9, 15),
            organization_id=1,
            plant_id=1
        )

        # Should return different BOMs
        assert bom_q1['id'] == 1
        assert bom_q1['bom_version'] == 1
        assert bom_q3['id'] == 2
        assert bom_q3['bom_version'] == 2

        # Verify component differences
        assert bom_q1['bom_lines'][0]['component_material_id'] == 200
        assert bom_q3['bom_lines'][0]['component_material_id'] == 300
