"""
Example usage of BarcodeStorageService with MinIO integration.

This example demonstrates how to integrate the BarcodeStorageService
with the BarcodeService for material label generation with caching.
"""
from app.infrastructure.storage.minio_client import MinIOClient
from app.infrastructure.storage.barcode_storage_service import BarcodeStorageService
from app.infrastructure.utilities.barcode_generator import BarcodeGenerator
from app.application.services.barcode_service import BarcodeService
from app.infrastructure.repositories.material_repository import MaterialRepository


# Example 1: Initialize storage service with MinIO backend
def initialize_barcode_storage():
    """Initialize barcode storage service with MinIO backend."""
    # Create MinIO client
    minio_client = MinIOClient()

    # Create barcode generator
    barcode_generator = BarcodeGenerator()

    # Create storage service
    storage_service = BarcodeStorageService(
        minio_client=minio_client,
        barcode_generator=barcode_generator
    )

    return storage_service


# Example 2: Generate and cache barcode for a material
def cache_material_barcode(storage_service, org_id="org_001", material_number="MAT001"):
    """Generate and cache a material barcode."""
    # Store barcode in MinIO
    result = storage_service.store_barcode(
        entity_type="material",
        entity_id=material_number,
        org_id=org_id,
        barcode_format="CODE128",
        metadata={
            "material_name": "Test Material",
            "category": "Raw Material"
        }
    )

    print(f"Barcode cached at: {result['object_path']}")
    print(f"Stored at: {result['stored_at']}")
    return result


# Example 3: Retrieve barcode URL (cache hit scenario)
def get_cached_barcode_url(storage_service, org_id="org_001", material_number="MAT001"):
    """Retrieve presigned URL for cached barcode."""
    # Get barcode URL (will use cache if exists, regenerate if not)
    url = storage_service.get_barcode_url(
        entity_type="material",
        entity_id=material_number,
        org_id=org_id,
        barcode_format="CODE128",
        expiry_seconds=3600  # 1 hour
    )

    print(f"Barcode URL: {url}")
    return url


# Example 4: Batch generate barcodes for multiple materials
def batch_generate_barcodes(storage_service):
    """Generate barcodes for multiple materials in batch."""
    entities = [
        {"type": "material", "id": "MAT001", "org_id": "org_001"},
        {"type": "material", "id": "MAT002", "org_id": "org_001"},
        {"type": "material", "id": "MAT003", "org_id": "org_001"},
    ]

    results = storage_service.generate_batch_barcodes(
        entities=entities,
        barcode_format="CODE128"
    )

    print(f"Generated {len(results)} barcodes")
    for result in results:
        if "error" not in result:
            print(f"  - {result['entity_id']}: {result['object_path']}")
        else:
            print(f"  - {result['entity_id']}: ERROR - {result['error']}")

    return results


# Example 5: Integrate with BarcodeService (Application Layer)
def generate_material_label_with_storage(material_id=1):
    """Generate material label using BarcodeService with storage integration."""
    # Initialize dependencies
    material_repository = MaterialRepository()
    storage_service = initialize_barcode_storage()

    # Create BarcodeService with storage integration
    barcode_service = BarcodeService(
        material_repository=material_repository,
        barcode_storage_service=storage_service
    )

    # Generate label with storage (returns URLs instead of base64)
    label = barcode_service.generate_material_label(
        material_id=material_id,
        include_qr=True,
        use_storage=True  # Enable MinIO storage
    )

    print(f"Material: {label['material_number']}")
    print(f"Barcode URL: {label['barcode_url']}")
    print(f"QR URL: {label['qr_url']}")

    return label


# Example 6: Generate material label without storage (backwards compatible)
def generate_material_label_without_storage(material_id=1):
    """Generate material label using original base64 approach."""
    # Initialize dependencies
    material_repository = MaterialRepository()

    # Create BarcodeService without storage integration
    barcode_service = BarcodeService(
        material_repository=material_repository,
        barcode_storage_service=None  # No storage service
    )

    # Generate label without storage (returns base64 images)
    label = barcode_service.generate_material_label(
        material_id=material_id,
        include_qr=True,
        use_storage=False  # Disable MinIO storage
    )

    print(f"Material: {label['material_number']}")
    print(f"Barcode (base64): {label['barcode_image'][:50]}...")
    print(f"QR (base64): {label['qr_image'][:50]}...")

    return label


# Example 7: Batch generate material labels
def batch_generate_material_labels(material_ids=[1, 2, 3]):
    """Generate labels for multiple materials in batch."""
    # Initialize dependencies
    material_repository = MaterialRepository()
    storage_service = initialize_barcode_storage()

    # Create BarcodeService with storage
    barcode_service = BarcodeService(
        material_repository=material_repository,
        barcode_storage_service=storage_service
    )

    # Batch generate labels
    labels = barcode_service.generate_batch_labels(
        material_ids=material_ids,
        include_qr=False
    )

    print(f"Generated {len(labels)} labels")
    for label in labels:
        if "error" not in label:
            print(f"  - {label['material_number']}")
        else:
            print(f"  - Material {label['material_id']}: ERROR - {label['error']}")

    return labels


if __name__ == "__main__":
    print("Barcode Storage Service Examples")
    print("=" * 50)

    # Initialize storage service
    storage = initialize_barcode_storage()

    # Example 1: Cache a barcode
    print("\n1. Caching Material Barcode:")
    cache_material_barcode(storage)

    # Example 2: Get cached barcode URL
    print("\n2. Retrieving Cached Barcode URL:")
    get_cached_barcode_url(storage)

    # Example 3: Batch generation
    print("\n3. Batch Generating Barcodes:")
    batch_generate_barcodes(storage)

    print("\n" + "=" * 50)
    print("Examples complete!")
