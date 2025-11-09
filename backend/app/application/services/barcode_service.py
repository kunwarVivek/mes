"""
BarcodeService - Application layer service for material barcode generation.

Orchestrates barcode generation workflow:
- Fetch material from database via MaterialRepository
- Generate barcode for material number
- Optionally generate QR code with JSON payload
- Return label data with Base64-encoded images OR MinIO URLs
- Support for MinIO storage caching (optional)
"""
import json
from typing import Dict, Optional, List
import logging

from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.utilities.barcode_generator import BarcodeGenerator


logger = logging.getLogger(__name__)


class BarcodeService:
    """
    Application service for generating material labels with barcodes.

    Coordinates between MaterialRepository and BarcodeGenerator to create
    material labels with barcodes and optional QR codes.

    Supports optional MinIO storage integration for caching.
    """

    def __init__(
        self,
        material_repository: MaterialRepository,
        barcode_storage_service: Optional['BarcodeStorageService'] = None
    ):
        """
        Initialize BarcodeService.

        Args:
            material_repository: Repository for material data access
            barcode_storage_service: Optional storage service for barcode caching
        """
        self._repository = material_repository
        self._barcode_generator = BarcodeGenerator()
        self._storage_service = barcode_storage_service

    def generate_material_label(
        self,
        material_id: int,
        include_qr: bool = False,
        use_storage: bool = False
    ) -> Dict:
        """
        Generate material label with barcode and optional QR code.

        Args:
            material_id: Material ID to generate label for
            include_qr: If True, include QR code with JSON payload
            use_storage: If True, use MinIO storage for caching (returns URLs instead of base64)

        Returns:
            Dictionary with:
            - material_number: Material number
            - barcode_image: Base64-encoded barcode image (if use_storage=False)
            - barcode_url: Presigned URL to barcode (if use_storage=True)
            - qr_image: Base64-encoded QR code image (if include_qr=True and use_storage=False)
            - qr_url: Presigned URL to QR code (if include_qr=True and use_storage=True)
            - label_data: Material details (material_number, material_name, category, uom)

        Raises:
            ValueError: If material not found
        """
        logger.info(f"Generating label for material ID: {material_id} (storage: {use_storage})")

        # Fetch material from database
        material = self._repository.get_by_id(material_id)

        if not material:
            logger.error(f"Material with id {material_id} not found")
            raise ValueError(f"Material with id {material_id} not found")

        # Extract material details
        material_number = material.material_number
        material_name = material.material_name
        category_name = material.category.category_name if material.category else "Unknown"
        uom_code = material.base_uom.uom_code if material.base_uom else "EA"
        org_id = str(material.organization_id)

        # Build label data
        label_data = {
            "material_number": material_number,
            "material_name": material_name,
            "category": category_name,
            "uom": uom_code,
        }

        # Build result
        result = {
            "material_number": material_number,
            "label_data": label_data,
        }

        # Generate barcode - use storage or base64
        if use_storage and self._storage_service:
            logger.info("Using MinIO storage for barcode")

            # Get barcode URL from storage (generates if cache miss)
            barcode_url = self._storage_service.get_barcode_url(
                entity_type="material",
                entity_id=material_number,
                org_id=org_id,
                barcode_format="CODE128"
            )
            result["barcode_url"] = barcode_url

        else:
            # Original behavior - generate base64
            barcode_result = self._barcode_generator.generate_material_barcode(
                material_number, format="CODE128"
            )
            result["barcode_image"] = barcode_result["image_base64"]

        # Generate QR code if requested
        if include_qr:
            logger.info(f"Generating QR code for material: {material_number}")

            # QR code contains JSON payload with material details
            qr_payload = json.dumps(label_data)

            if use_storage and self._storage_service:
                # Get QR URL from storage
                qr_url = self._storage_service.get_barcode_url(
                    entity_type="material",
                    entity_id=material_number,
                    org_id=org_id,
                    barcode_format="QR_CODE"
                )
                result["qr_url"] = qr_url

            else:
                # Original behavior - generate base64
                qr_result = self._barcode_generator.generate_material_barcode(
                    qr_payload, format="QR_CODE"
                )
                result["qr_image"] = qr_result["image_base64"]

        logger.info(f"Label generated successfully for material: {material_number}")
        return result

    def generate_batch_labels(
        self,
        material_ids: List[int],
        include_qr: bool = False
    ) -> List[Dict]:
        """
        Generate labels for multiple materials in batch.

        Args:
            material_ids: List of material IDs
            include_qr: If True, include QR codes

        Returns:
            List of label dictionaries with barcode metadata
        """
        logger.info(f"Batch generating labels for {len(material_ids)} materials")

        results = []

        # Prepare batch entities for storage service
        if self._storage_service:
            entities = []

            for material_id in material_ids:
                material = self._repository.get_by_id(material_id)
                if material:
                    entities.append({
                        "type": "material",
                        "id": material.material_number,
                        "org_id": str(material.organization_id)
                    })

            # Batch generate barcodes in storage
            batch_results = self._storage_service.generate_batch_barcodes(
                entities=entities,
                barcode_format="CODE128"
            )

            # Build result with material details
            for material_id in material_ids:
                material = self._repository.get_by_id(material_id)
                if material:
                    # Find corresponding batch result
                    batch_metadata = next(
                        (r for r in batch_results if r.get("entity_id") == material.material_number),
                        None
                    )

                    label_data = {
                        "material_number": material.material_number,
                        "material_name": material.material_name,
                        "category": material.category.category_name if material.category else "Unknown",
                        "uom": material.base_uom.uom_code if material.base_uom else "EA",
                    }

                    results.append({
                        "material_number": material.material_number,
                        "label_data": label_data,
                        "barcode_metadata": batch_metadata
                    })

        else:
            # Fallback to individual generation
            for material_id in material_ids:
                try:
                    label = self.generate_material_label(
                        material_id=material_id,
                        include_qr=include_qr,
                        use_storage=False
                    )
                    results.append(label)
                except Exception as e:
                    logger.error(f"Failed to generate label for material {material_id}: {str(e)}")
                    results.append({
                        "material_id": material_id,
                        "error": str(e)
                    })

        logger.info(f"Batch label generation complete: {len(results)} results")
        return results
