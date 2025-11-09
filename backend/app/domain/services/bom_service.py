"""
Domain services for BOM (Bill of Materials) business logic.
Includes BOM explosion and validation services.
"""
from typing import Dict, List, Any, Optional
from datetime import date


class CircularReferenceError(Exception):
    """Raised when circular reference is detected in BOM structure"""
    pass


class BOMExplosionService:
    """Service for BOM explosion (recursive multilevel expansion)"""

    def __init__(self, bom_repository, effectivity_service=None):
        """
        Initialize BOM explosion service.

        Args:
            bom_repository: Repository with methods:
                - get_bom_header(bom_header_id) -> dict
                - get_bom_by_material(material_id) -> dict
            effectivity_service: Optional BOMEffectivityService for date-based BOM selection
        """
        self.bom_repository = bom_repository
        self.effectivity_service = effectivity_service

    def explode_bom(
        self,
        bom_header_id: int,
        required_quantity: float,
        production_date: Optional[date] = None,
        organization_id: Optional[int] = None,
        plant_id: Optional[int] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Recursively explode multilevel BOM to get flat list of all materials needed.

        Args:
            bom_header_id: ID of the BOM header to explode
            required_quantity: Quantity of finished good required
            production_date: Optional production date for effectivity-based BOM selection
            organization_id: Optional organization context for effectivity
            plant_id: Optional plant context for effectivity

        Returns:
            Dictionary mapping material_id to:
            {
                'total_quantity': float,
                'unit_of_measure_id': int,
                'details': [{
                    'level': int,
                    'parent_material_id': int,
                    'quantity': float
                }]
            }

        Raises:
            ValueError: If BOM header not found or quantity invalid
        """
        if required_quantity <= 0:
            raise ValueError("Required quantity must be positive")

        bom_header = self.bom_repository.get_bom_header(bom_header_id)
        if not bom_header:
            raise ValueError("BOM header not found")

        # Result accumulator
        materials_needed = {}

        # Explode BOM recursively
        self._explode_recursive(
            bom_header=bom_header,
            parent_quantity=required_quantity,
            level=1,
            parent_material_id=None,
            materials_needed=materials_needed,
            production_date=production_date,
            organization_id=organization_id,
            plant_id=plant_id
        )

        return materials_needed

    def _explode_recursive(
        self,
        bom_header: dict,
        parent_quantity: float,
        level: int,
        parent_material_id: int,
        materials_needed: dict,
        production_date: Optional[date] = None,
        organization_id: Optional[int] = None,
        plant_id: Optional[int] = None
    ) -> None:
        """
        Recursively explode BOM lines.

        Args:
            bom_header: BOM header dictionary
            parent_quantity: Quantity from parent level
            level: Current explosion level
            parent_material_id: Material ID of parent BOM
            materials_needed: Accumulator dictionary
            production_date: Optional production date for effectivity-based BOM selection
            organization_id: Optional organization context
            plant_id: Optional plant context
        """
        for line in bom_header.get('bom_lines', []):
            component_material_id = line['component_material_id']
            quantity = line['quantity']
            scrap_factor = line['scrap_factor']
            is_phantom = line['is_phantom']
            unit_of_measure_id = line['unit_of_measure_id']

            # Calculate net quantity with scrap
            net_quantity = quantity * (1 + scrap_factor / 100)
            total_quantity = net_quantity * parent_quantity

            # If phantom, explode further
            if is_phantom:
                # Use effectivity service if available and parameters provided
                if (self.effectivity_service and production_date and
                    organization_id and plant_id):
                    try:
                        phantom_bom = self.effectivity_service.get_effective_bom(
                            material_id=component_material_id,
                            production_date=production_date,
                            organization_id=organization_id,
                            plant_id=plant_id
                        )
                    except Exception:
                        # Fall back to default BOM lookup
                        phantom_bom = self.bom_repository.get_bom_by_material(component_material_id)
                else:
                    phantom_bom = self.bom_repository.get_bom_by_material(component_material_id)

                if phantom_bom:
                    self._explode_recursive(
                        bom_header=phantom_bom,
                        parent_quantity=total_quantity,
                        level=level + 1,
                        parent_material_id=bom_header.get('material_id'),
                        materials_needed=materials_needed,
                        production_date=production_date,
                        organization_id=organization_id,
                        plant_id=plant_id
                    )
                    continue  # Don't add phantom material to result

            # Add or accumulate material
            if component_material_id not in materials_needed:
                materials_needed[component_material_id] = {
                    'total_quantity': 0.0,
                    'unit_of_measure_id': unit_of_measure_id,
                    'details': []
                }

            materials_needed[component_material_id]['total_quantity'] += total_quantity
            materials_needed[component_material_id]['details'].append({
                'level': level,
                'parent_material_id': parent_material_id,
                'quantity': total_quantity
            })


class BOMValidationService:
    """Service for BOM validation logic"""

    def __init__(self, bom_repository):
        """
        Initialize BOM validation service.

        Args:
            bom_repository: Repository with methods:
                - get_bom_header(bom_header_id) -> dict
                - get_bom_by_material(material_id) -> dict
        """
        self.bom_repository = bom_repository

    def validate_no_circular_reference(self, bom_header_id: int) -> bool:
        """
        Validate that BOM does not have circular references.

        Args:
            bom_header_id: ID of the BOM header to validate

        Returns:
            True if no circular reference found

        Raises:
            CircularReferenceError: If circular reference detected
            ValueError: If BOM header not found
        """
        bom_header = self.bom_repository.get_bom_header(bom_header_id)
        if not bom_header:
            raise ValueError("BOM header not found")

        # Track visited materials to detect cycles
        visited = set()
        current_path = set()

        # Start validation from root material
        root_material_id = bom_header['material_id']
        self._check_circular_recursive(
            material_id=root_material_id,
            visited=visited,
            current_path=current_path
        )

        return True

    def _check_circular_recursive(
        self,
        material_id: int,
        visited: set,
        current_path: set
    ) -> None:
        """
        Recursively check for circular references.

        Args:
            material_id: Current material ID being checked
            visited: Set of all visited materials
            current_path: Set of materials in current path (for cycle detection)

        Raises:
            CircularReferenceError: If circular reference detected
        """
        # If material is in current path, we have a cycle
        if material_id in current_path:
            raise CircularReferenceError(
                f"Circular reference detected in BOM: material {material_id} "
                f"references itself (directly or indirectly)"
            )

        # If already visited in a different path, no need to check again
        if material_id in visited:
            return

        # Add to current path and visited
        current_path.add(material_id)
        visited.add(material_id)

        # Get BOM for this material
        bom = self.bom_repository.get_bom_by_material(material_id)
        if bom:
            # Check all phantom components recursively
            for line in bom.get('bom_lines', []):
                if line.get('is_phantom'):
                    component_material_id = line['component_material_id']
                    self._check_circular_recursive(
                        material_id=component_material_id,
                        visited=visited,
                        current_path=current_path
                    )

        # Remove from current path (backtrack)
        current_path.remove(material_id)
