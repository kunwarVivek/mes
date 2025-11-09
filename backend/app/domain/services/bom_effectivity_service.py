"""
Domain service for BOM Effectivity Date Management.
Handles BOM selection based on production dates and validates effectivity rules.
"""
from datetime import date
from typing import Optional, List, Dict, Any


class NoActiveBOMError(Exception):
    """Raised when no active BOM found for given criteria"""
    pass


class OverlappingEffectivityError(Exception):
    """Raised when overlapping effectivity dates detected for same material"""
    pass


class BOMEffectivityService:
    """Service for BOM effectivity date logic and validation"""

    def __init__(self, bom_repository):
        """
        Initialize BOM effectivity service.

        Args:
            bom_repository: Repository with methods:
                - get_boms_by_material(material_id, organization_id, plant_id) -> List[dict]
                - get_active_boms_by_material(material_id, organization_id, plant_id) -> List[dict]
        """
        self.bom_repository = bom_repository

    def get_effective_bom(
        self,
        material_id: int,
        production_date: date,
        organization_id: int,
        plant_id: int
    ) -> Dict[str, Any]:
        """
        Get the effective BOM for a material on a specific production date.

        Selects BOM based on:
        1. Active status (is_active = True)
        2. Effectivity date range (production_date within start/end dates)
        3. Organization and plant context

        Args:
            material_id: Material ID to find BOM for
            production_date: Date of production
            organization_id: Organization context
            plant_id: Plant context

        Returns:
            BOM header dictionary

        Raises:
            NoActiveBOMError: If no active BOM found for the criteria
        """
        # Get all active BOMs for this material
        boms = self.bom_repository.get_active_boms_by_material(
            material_id=material_id,
            organization_id=organization_id,
            plant_id=plant_id
        )

        if not boms:
            raise NoActiveBOMError(
                f"No active BOM found for material {material_id} "
                f"in org {organization_id}, plant {plant_id}"
            )

        # Filter BOMs by effectivity date
        effective_boms = []
        for bom in boms:
            if self._is_effective_on_date(bom, production_date):
                effective_boms.append(bom)

        if not effective_boms:
            raise NoActiveBOMError(
                f"No active BOM found for material {material_id} "
                f"on date {production_date} in org {organization_id}, plant {plant_id}"
            )

        # If multiple BOMs match (shouldn't happen with proper validation),
        # return the one with highest version number
        effective_boms.sort(key=lambda b: b['bom_version'], reverse=True)
        return effective_boms[0]

    def validate_no_overlapping_effectivity(
        self,
        material_id: int,
        organization_id: int,
        plant_id: int
    ) -> bool:
        """
        Validate that no overlapping effectivity dates exist for a material.

        Only checks active BOMs. Inactive BOMs are ignored.

        Args:
            material_id: Material ID to validate
            organization_id: Organization context
            plant_id: Plant context

        Returns:
            True if no overlaps detected

        Raises:
            OverlappingEffectivityError: If overlapping dates detected
        """
        # Get all active BOMs for this material
        boms = self.bom_repository.get_active_boms_by_material(
            material_id=material_id,
            organization_id=organization_id,
            plant_id=plant_id
        )

        # Check each pair of BOMs for overlaps
        for i, bom1 in enumerate(boms):
            for bom2 in boms[i + 1:]:
                if self._date_ranges_overlap(bom1, bom2):
                    raise OverlappingEffectivityError(
                        f"Overlapping effectivity dates detected for material {material_id}: "
                        f"BOM {bom1['bom_number']} ({bom1['effective_start_date']} to {bom1['effective_end_date']}) "
                        f"overlaps with BOM {bom2['bom_number']} "
                        f"({bom2['effective_start_date']} to {bom2['effective_end_date']})"
                    )

        return True

    def _is_effective_on_date(self, bom: Dict[str, Any], check_date: date) -> bool:
        """
        Check if a BOM is effective on a specific date.

        Rules:
        - If both start and end dates are None (legacy BOM): always effective
        - If only start date exists: effective from start date onwards
        - If both dates exist: effective within the range (inclusive)

        Args:
            bom: BOM dictionary with effective_start_date and effective_end_date
            check_date: Date to check

        Returns:
            True if BOM is effective on the date
        """
        start_date = bom.get('effective_start_date')
        end_date = bom.get('effective_end_date')

        # Legacy BOM without dates - always effective
        if start_date is None and end_date is None:
            return True

        # BOM with only start date - effective from start onwards
        if start_date is not None and end_date is None:
            return check_date >= start_date

        # BOM with both dates - check if within range (inclusive)
        if start_date is not None and end_date is not None:
            return start_date <= check_date <= end_date

        # BOM with only end date (unusual case) - effective up to end date
        if start_date is None and end_date is not None:
            return check_date <= end_date

        return False

    def _date_ranges_overlap(self, bom1: Dict[str, Any], bom2: Dict[str, Any]) -> bool:
        """
        Check if two BOMs have overlapping effectivity date ranges.

        Args:
            bom1: First BOM dictionary
            bom2: Second BOM dictionary

        Returns:
            True if the date ranges overlap
        """
        start1 = bom1.get('effective_start_date')
        end1 = bom1.get('effective_end_date')
        start2 = bom2.get('effective_start_date')
        end2 = bom2.get('effective_end_date')

        # Handle legacy BOMs (no dates)
        # If either BOM has no dates, it overlaps with everything
        if (start1 is None and end1 is None) or (start2 is None and end2 is None):
            return True

        # Convert None end dates to far future for comparison
        from datetime import date as date_type
        FAR_FUTURE = date_type(9999, 12, 31)

        # Normalize dates
        effective_start1 = start1 or date_type(1900, 1, 1)
        effective_end1 = end1 or FAR_FUTURE
        effective_start2 = start2 or date_type(1900, 1, 1)
        effective_end2 = end2 or FAR_FUTURE

        # Check for overlap using standard interval overlap logic:
        # Two ranges [a,b] and [c,d] overlap if: a <= d AND c <= b
        return effective_start1 <= effective_end2 and effective_start2 <= effective_end1
