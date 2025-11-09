"""
Unit tests for BOM Effectivity Domain Service.
Tests effectivity date logic following TDD approach (RED -> GREEN -> REFACTOR).
"""
import pytest
from datetime import date, datetime
from app.domain.services.bom_effectivity_service import (
    BOMEffectivityService,
    OverlappingEffectivityError,
    NoActiveBOMError
)


class TestBOMEffectivityService:
    """Tests for BOM effectivity date selection and validation"""

    @pytest.fixture
    def mock_bom_repository(self):
        """Mock BOM repository for testing effectivity logic"""
        class MockBOMRepository:
            def __init__(self):
                # Store BOMs by material_id for easy lookup
                self.boms_by_material = {
                    # Material 100 has three BOMs with different effectivity periods
                    100: [
                        {
                            'id': 1,
                            'material_id': 100,
                            'organization_id': 1,
                            'plant_id': 1,
                            'bom_number': 'BOM-100-V1',
                            'bom_version': 1,
                            'effective_start_date': date(2024, 1, 1),
                            'effective_end_date': date(2024, 6, 30),
                            'is_active': True
                        },
                        {
                            'id': 2,
                            'material_id': 100,
                            'organization_id': 1,
                            'plant_id': 1,
                            'bom_number': 'BOM-100-V2',
                            'bom_version': 2,
                            'effective_start_date': date(2024, 7, 1),
                            'effective_end_date': date(2024, 12, 31),
                            'is_active': True
                        },
                        {
                            'id': 3,
                            'material_id': 100,
                            'organization_id': 1,
                            'plant_id': 1,
                            'bom_number': 'BOM-100-V3',
                            'bom_version': 3,
                            'effective_start_date': date(2025, 1, 1),
                            'effective_end_date': None,  # Open-ended
                            'is_active': True
                        }
                    ],
                    # Material 200 has one active and one inactive BOM
                    200: [
                        {
                            'id': 4,
                            'material_id': 200,
                            'organization_id': 1,
                            'plant_id': 1,
                            'bom_number': 'BOM-200-V1',
                            'bom_version': 1,
                            'effective_start_date': date(2024, 1, 1),
                            'effective_end_date': date(2024, 12, 31),
                            'is_active': False  # Manually deactivated
                        },
                        {
                            'id': 5,
                            'material_id': 200,
                            'organization_id': 1,
                            'plant_id': 1,
                            'bom_number': 'BOM-200-V2',
                            'bom_version': 2,
                            'effective_start_date': date(2025, 1, 1),
                            'effective_end_date': None,
                            'is_active': True
                        }
                    ],
                    # Material 300 has legacy BOM without effectivity dates
                    300: [
                        {
                            'id': 6,
                            'material_id': 300,
                            'organization_id': 1,
                            'plant_id': 1,
                            'bom_number': 'BOM-300-LEGACY',
                            'bom_version': 1,
                            'effective_start_date': None,  # Legacy
                            'effective_end_date': None,
                            'is_active': True
                        }
                    ]
                }

            def get_boms_by_material(self, material_id, organization_id, plant_id):
                """Get all BOMs for a material in org/plant context"""
                boms = self.boms_by_material.get(material_id, [])
                return [
                    bom for bom in boms
                    if bom['organization_id'] == organization_id
                    and bom['plant_id'] == plant_id
                ]

            def get_active_boms_by_material(self, material_id, organization_id, plant_id):
                """Get only active BOMs for a material"""
                boms = self.get_boms_by_material(material_id, organization_id, plant_id)
                return [bom for bom in boms if bom['is_active']]

        return MockBOMRepository()

    # Test 1: Select BOM by date - within first period
    def test_select_bom_by_date_first_period(self, mock_bom_repository):
        """Test BOM selection for date in first effectivity period"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2024, 3, 15)  # Within Jan-Jun 2024
        bom = service.get_effective_bom(
            material_id=100,
            production_date=production_date,
            organization_id=1,
            plant_id=1
        )

        assert bom is not None
        assert bom['id'] == 1
        assert bom['bom_version'] == 1
        assert bom['bom_number'] == 'BOM-100-V1'

    # Test 2: Select BOM by date - within second period
    def test_select_bom_by_date_second_period(self, mock_bom_repository):
        """Test BOM selection for date in second effectivity period"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2024, 9, 1)  # Within Jul-Dec 2024
        bom = service.get_effective_bom(
            material_id=100,
            production_date=production_date,
            organization_id=1,
            plant_id=1
        )

        assert bom is not None
        assert bom['id'] == 2
        assert bom['bom_version'] == 2

    # Test 3: Select BOM by date - open-ended period
    def test_select_bom_by_date_open_ended(self, mock_bom_repository):
        """Test BOM selection for date in open-ended effectivity period"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2025, 6, 1)  # Future date, open-ended BOM
        bom = service.get_effective_bom(
            material_id=100,
            production_date=production_date,
            organization_id=1,
            plant_id=1
        )

        assert bom is not None
        assert bom['id'] == 3
        assert bom['bom_version'] == 3
        assert bom['effective_end_date'] is None

    # Test 4: Select BOM at exact start date boundary
    def test_select_bom_at_start_date_boundary(self, mock_bom_repository):
        """Test BOM selection at exact start date (inclusive)"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2024, 7, 1)  # Exact start of second period
        bom = service.get_effective_bom(
            material_id=100,
            production_date=production_date,
            organization_id=1,
            plant_id=1
        )

        assert bom is not None
        assert bom['id'] == 2
        assert bom['bom_version'] == 2

    # Test 5: Select BOM at exact end date boundary
    def test_select_bom_at_end_date_boundary(self, mock_bom_repository):
        """Test BOM selection at exact end date (inclusive)"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2024, 6, 30)  # Exact end of first period
        bom = service.get_effective_bom(
            material_id=100,
            production_date=production_date,
            organization_id=1,
            plant_id=1
        )

        assert bom is not None
        assert bom['id'] == 1
        assert bom['bom_version'] == 1

    # Test 6: No BOM found for date (gap in coverage)
    def test_no_bom_for_date_gap(self, mock_bom_repository):
        """Test when no BOM covers the production date"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2023, 12, 31)  # Before all BOMs

        with pytest.raises(NoActiveBOMError, match="No active BOM found"):
            service.get_effective_bom(
                material_id=100,
                production_date=production_date,
                organization_id=1,
                plant_id=1
            )

    # Test 7: Respect is_active flag (manually deactivated BOM)
    def test_respect_is_active_flag(self, mock_bom_repository):
        """Test that manually deactivated BOMs are not selected"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2024, 6, 1)  # Within deactivated BOM period

        with pytest.raises(NoActiveBOMError, match="No active BOM found"):
            service.get_effective_bom(
                material_id=200,
                production_date=production_date,
                organization_id=1,
                plant_id=1
            )

    # Test 8: Legacy BOM without effectivity dates (always active)
    def test_legacy_bom_without_dates(self, mock_bom_repository):
        """Test that legacy BOMs without dates are treated as always effective"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2024, 1, 1)  # Any date
        bom = service.get_effective_bom(
            material_id=300,
            production_date=production_date,
            organization_id=1,
            plant_id=1
        )

        assert bom is not None
        assert bom['id'] == 6
        assert bom['effective_start_date'] is None
        assert bom['effective_end_date'] is None

    # Test 9: Validate no overlapping dates for same material
    def test_validate_no_overlapping_dates_valid(self, mock_bom_repository):
        """Test validation passes when no overlaps exist"""
        service = BOMEffectivityService(mock_bom_repository)

        # Material 100 has non-overlapping BOMs
        result = service.validate_no_overlapping_effectivity(
            material_id=100,
            organization_id=1,
            plant_id=1
        )

        assert result is True

    # Test 10: Validate overlapping dates detection
    def test_validate_overlapping_dates_detected(self, mock_bom_repository):
        """Test validation detects overlapping effectivity periods"""
        # Add overlapping BOM to mock data
        mock_bom_repository.boms_by_material[100].append({
            'id': 99,
            'material_id': 100,
            'organization_id': 1,
            'plant_id': 1,
            'bom_number': 'BOM-100-OVERLAP',
            'bom_version': 4,
            'effective_start_date': date(2024, 6, 15),  # Overlaps with V1 and V2
            'effective_end_date': date(2024, 8, 15),
            'is_active': True
        })

        service = BOMEffectivityService(mock_bom_repository)

        with pytest.raises(OverlappingEffectivityError, match="Overlapping effectivity dates"):
            service.validate_no_overlapping_effectivity(
                material_id=100,
                organization_id=1,
                plant_id=1
            )

    # Test 11: Open-ended BOMs can't overlap with future BOMs
    def test_validate_open_ended_overlap(self, mock_bom_repository):
        """Test that open-ended BOMs can't overlap with future BOMs"""
        # Add another BOM after open-ended one
        mock_bom_repository.boms_by_material[100].append({
            'id': 98,
            'material_id': 100,
            'organization_id': 1,
            'plant_id': 1,
            'bom_number': 'BOM-100-FUTURE',
            'bom_version': 5,
            'effective_start_date': date(2025, 6, 1),  # After open-ended BOM start
            'effective_end_date': date(2025, 12, 31),
            'is_active': True
        })

        service = BOMEffectivityService(mock_bom_repository)

        with pytest.raises(OverlappingEffectivityError, match="Overlapping effectivity dates"):
            service.validate_no_overlapping_effectivity(
                material_id=100,
                organization_id=1,
                plant_id=1
            )

    # Test 12: BOM Explosion should use effectivity date
    def test_bom_explosion_with_effectivity(self, mock_bom_repository):
        """Test that BOM explosion service uses effectivity dates"""
        # Add BOM lines to mock data
        mock_bom_repository.boms_by_material[100][0]['bom_lines'] = [
            {
                'line_number': 10,
                'component_material_id': 500,
                'quantity': 2.0,
                'scrap_factor': 10.0,
                'is_phantom': False,
                'unit_of_measure_id': 10
            }
        ]
        mock_bom_repository.boms_by_material[100][1]['bom_lines'] = [
            {
                'line_number': 10,
                'component_material_id': 600,  # Different component in V2
                'quantity': 3.0,
                'scrap_factor': 5.0,
                'is_phantom': False,
                'unit_of_measure_id': 10
            }
        ]

        service = BOMEffectivityService(mock_bom_repository)

        # Get BOM for production in Q1 2024
        bom_q1 = service.get_effective_bom(
            material_id=100,
            production_date=date(2024, 3, 1),
            organization_id=1,
            plant_id=1
        )

        # Get BOM for production in Q3 2024
        bom_q3 = service.get_effective_bom(
            material_id=100,
            production_date=date(2024, 9, 1),
            organization_id=1,
            plant_id=1
        )

        # Different BOMs should be selected
        assert bom_q1['id'] != bom_q3['id']
        assert bom_q1['bom_lines'][0]['component_material_id'] == 500
        assert bom_q3['bom_lines'][0]['component_material_id'] == 600

    # Test 13: Validation ignores inactive BOMs
    def test_validate_ignores_inactive_boms(self, mock_bom_repository):
        """Test that validation doesn't flag overlaps with inactive BOMs"""
        # Material 200 has inactive BOM that would overlap if it were active
        service = BOMEffectivityService(mock_bom_repository)

        # Should pass because BOM 4 is inactive
        result = service.validate_no_overlapping_effectivity(
            material_id=200,
            organization_id=1,
            plant_id=1
        )

        assert result is True

    # Test 14: Organization/Plant isolation
    def test_organization_plant_isolation(self, mock_bom_repository):
        """Test that BOMs are isolated by organization and plant"""
        service = BOMEffectivityService(mock_bom_repository)

        production_date = date(2024, 3, 15)

        # Should find BOM in org 1, plant 1
        bom = service.get_effective_bom(
            material_id=100,
            production_date=production_date,
            organization_id=1,
            plant_id=1
        )
        assert bom is not None

        # Should not find BOM in different org/plant
        with pytest.raises(NoActiveBOMError):
            service.get_effective_bom(
                material_id=100,
                production_date=production_date,
                organization_id=2,  # Different org
                plant_id=1
            )
