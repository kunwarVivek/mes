"""
BOM Explosion Demonstration
Shows how multilevel BOM explosion works with phantom items and scrap factors.

Example Structure:
Product A (1 unit) requires:
  - Material B: 2 units, scrap 10% = 2.2 units
    - Material B is PHANTOM (has its own BOM)
    - Material B BOM: requires Material D (3 units per B, scrap 5%)
    - Total Material D needed: 2.2 * 3 * 1.05 = 6.93 units
  - Material C: 1 unit, scrap 5% = 1.05 units

Final result (flattened):
  - Material D: 6.93 units (from phantom explosion)
  - Material C: 1.05 units
"""

from app.domain.services.bom_service import BOMExplosionService


class MockBOMRepository:
    """Mock repository for demonstration"""

    def __init__(self):
        # Product A BOM (top-level)
        self.product_a_bom = {
            'id': 1,
            'material_id': 100,  # Product A
            'base_quantity': 1.0,
            'bom_lines': [
                {
                    'line_number': 10,
                    'component_material_id': 101,  # Material B (phantom)
                    'quantity': 2.0,
                    'scrap_factor': 10.0,  # 10% scrap
                    'is_phantom': True,  # Material B has its own BOM
                    'unit_of_measure_id': 1
                },
                {
                    'line_number': 20,
                    'component_material_id': 102,  # Material C
                    'quantity': 1.0,
                    'scrap_factor': 5.0,  # 5% scrap
                    'is_phantom': False,
                    'unit_of_measure_id': 1
                }
            ]
        }

        # Material B BOM (sub-level, phantom)
        self.material_b_bom = {
            'id': 2,
            'material_id': 101,  # Material B
            'base_quantity': 1.0,
            'bom_lines': [
                {
                    'line_number': 10,
                    'component_material_id': 103,  # Material D
                    'quantity': 3.0,
                    'scrap_factor': 5.0,  # 5% scrap
                    'is_phantom': False,
                    'unit_of_measure_id': 1
                }
            ]
        }

        self.boms = {
            1: self.product_a_bom,
            2: self.material_b_bom
        }

    def get_bom_header(self, bom_header_id):
        return self.boms.get(bom_header_id)

    def get_bom_by_material(self, material_id):
        for bom in self.boms.values():
            if bom['material_id'] == material_id:
                return bom
        return None


def demonstrate_bom_explosion():
    """Demonstrate BOM explosion with multilevel phantom items"""
    print("=" * 80)
    print("BOM Explosion Demonstration")
    print("=" * 80)
    print()

    # Setup
    repository = MockBOMRepository()
    service = BOMExplosionService(repository)

    # Show BOM structure
    print("BOM Structure:")
    print("-" * 80)
    print("Product A (1 unit):")
    print("  ├─ Material B: 2 units, scrap 10% = 2.2 units (PHANTOM)")
    print("  │   └─ Material D: 3 units per B, scrap 5% = 3.15 units per B")
    print("  │       Total: 2.2 * 3.15 = 6.93 units")
    print("  └─ Material C: 1 unit, scrap 5% = 1.05 units")
    print()

    # Explode for 1 unit
    print("Exploding BOM for 1 unit of Product A:")
    print("-" * 80)
    result = service.explode_bom(bom_header_id=1, required_quantity=1.0)

    for material_id, details in sorted(result.items()):
        print(f"\nMaterial ID {material_id}:")
        print(f"  Total Quantity: {details['total_quantity']:.2f} units")
        print(f"  UOM ID: {details['unit_of_measure_id']}")
        print(f"  Details:")
        for detail in details['details']:
            print(f"    - Level {detail['level']}: {detail['quantity']:.2f} units")

    print()
    print("=" * 80)

    # Explode for 10 units
    print("Exploding BOM for 10 units of Product A:")
    print("-" * 80)
    result_10 = service.explode_bom(bom_header_id=1, required_quantity=10.0)

    for material_id, details in sorted(result_10.items()):
        print(f"\nMaterial ID {material_id}:")
        print(f"  Total Quantity: {details['total_quantity']:.2f} units")

    print()
    print("=" * 80)
    print("Key Observations:")
    print("-" * 80)
    print("1. Material B (phantom) is NOT in the result - it was exploded")
    print("2. Material D appears because phantom Material B was exploded")
    print("3. Scrap factors are applied at each level")
    print("4. Quantities multiply down the BOM tree")
    print("5. For 10 units, all quantities scale proportionally")
    print()


def demonstrate_circular_reference_detection():
    """Demonstrate circular reference detection"""
    from app.domain.services.bom_service import BOMValidationService, CircularReferenceError

    print("=" * 80)
    print("Circular Reference Detection Demonstration")
    print("=" * 80)
    print()

    class MockCircularBOMRepository:
        def __init__(self, has_cycle=False):
            if has_cycle:
                # Create a cycle: A -> B -> C -> A
                self.boms = {
                    1: {
                        'id': 1,
                        'material_id': 100,
                        'bom_lines': [
                            {'component_material_id': 101, 'is_phantom': True}
                        ]
                    },
                    2: {
                        'id': 2,
                        'material_id': 101,
                        'bom_lines': [
                            {'component_material_id': 102, 'is_phantom': True}
                        ]
                    },
                    3: {
                        'id': 3,
                        'material_id': 102,
                        'bom_lines': [
                            {'component_material_id': 100, 'is_phantom': True}  # Cycle back to A
                        ]
                    }
                }
            else:
                # No cycle: A -> B -> C
                self.boms = {
                    1: {
                        'id': 1,
                        'material_id': 100,
                        'bom_lines': [
                            {'component_material_id': 101, 'is_phantom': True}
                        ]
                    },
                    2: {
                        'id': 2,
                        'material_id': 101,
                        'bom_lines': [
                            {'component_material_id': 102, 'is_phantom': False}
                        ]
                    }
                }

        def get_bom_header(self, bom_header_id):
            return self.boms.get(bom_header_id)

        def get_bom_by_material(self, material_id):
            for bom in self.boms.values():
                if bom['material_id'] == material_id:
                    return bom
            return None

    # Test valid BOM (no cycle)
    print("Testing valid BOM (no circular reference):")
    print("-" * 80)
    valid_repo = MockCircularBOMRepository(has_cycle=False)
    service = BOMValidationService(valid_repo)
    try:
        result = service.validate_no_circular_reference(bom_header_id=1)
        print(f"✓ Validation passed: {result}")
    except CircularReferenceError as e:
        print(f"✗ Validation failed: {e}")
    print()

    # Test invalid BOM (has cycle)
    print("Testing invalid BOM (circular reference: A -> B -> C -> A):")
    print("-" * 80)
    invalid_repo = MockCircularBOMRepository(has_cycle=True)
    service = BOMValidationService(invalid_repo)
    try:
        result = service.validate_no_circular_reference(bom_header_id=1)
        print(f"✓ Validation passed: {result}")
    except CircularReferenceError as e:
        print(f"✗ Validation failed (expected): {e}")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    demonstrate_bom_explosion()
    print("\n")
    demonstrate_circular_reference_detection()
