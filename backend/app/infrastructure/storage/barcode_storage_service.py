"""
BarcodeStorageService - MinIO-backed barcode caching service.

Provides barcode storage and retrieval with:
- MinIO S3-compatible storage backend
- Cache management (hit/miss scenarios)
- Presigned URL generation for temporary access
- Batch barcode generation
- Automatic cache regeneration on miss
"""
import logging
import tempfile
import os
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.infrastructure.storage.minio_client import MinIOClient
from app.infrastructure.utilities.barcode_generator import BarcodeGenerator

logger = logging.getLogger(__name__)


class BarcodeStorageService:
    """
    Service for storing and retrieving barcodes from MinIO cache.

    Features:
    - Automatic barcode generation and caching
    - Cache hit/miss detection
    - Presigned URL generation
    - Batch operations
    - Metadata tracking
    """

    SUPPORTED_FORMATS = ["CODE128", "CODE39", "EAN13", "QR_CODE", "DATAMATRIX"]
    DEFAULT_EXPIRY_SECONDS = 3600  # 1 hour

    def __init__(
        self,
        minio_client: MinIOClient,
        barcode_generator: BarcodeGenerator
    ):
        """
        Initialize BarcodeStorageService.

        Args:
            minio_client: MinIO client for storage operations
            barcode_generator: Barcode generator utility
        """
        self.minio_client = minio_client
        self.barcode_generator = barcode_generator

    def store_barcode(
        self,
        entity_type: str,
        entity_id: str,
        org_id: str,
        barcode_format: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate and store barcode in MinIO cache.

        Args:
            entity_type: Type of entity (material, inventory, work_order)
            entity_id: Unique identifier for the entity
            org_id: Organization identifier
            barcode_format: Barcode format (CODE128, QR_CODE, etc.)
            metadata: Optional custom metadata to store with barcode

        Returns:
            Dictionary with barcode metadata:
            - entity_type: Entity type
            - entity_id: Entity ID
            - org_id: Organization ID
            - format: Barcode format
            - object_path: MinIO object path
            - stored_at: Timestamp of storage

        Raises:
            ValueError: If barcode_format is invalid
        """
        if barcode_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Invalid barcode format: {barcode_format}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        logger.info(
            f"Storing barcode for {entity_type}/{entity_id} "
            f"(org: {org_id}, format: {barcode_format})"
        )

        # Generate barcode
        barcode_data = self.barcode_generator.generate_material_barcode(
            entity_id, format=barcode_format
        )

        # Build object path
        object_path = self._build_object_path(
            org_id, entity_type, entity_id, barcode_format
        )

        # Save to temporary file
        temp_file = self._save_to_temp_file(barcode_data["image_base64"])

        try:
            # Upload to MinIO
            storage_metadata = metadata or {}
            storage_metadata.update({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "barcode_format": barcode_format,
                "checksum": barcode_data["checksum"]
            })

            self.minio_client.upload_file(
                file_path=temp_file,
                object_name=object_path,
                content_type="image/png",
                metadata=storage_metadata
            )

            logger.info(f"Successfully stored barcode at: {object_path}")

            return {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "org_id": org_id,
                "format": barcode_format,
                "object_path": object_path,
                "stored_at": datetime.utcnow().isoformat()
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def get_barcode_url(
        self,
        entity_type: str,
        entity_id: str,
        org_id: str,
        barcode_format: str,
        expiry_seconds: int = DEFAULT_EXPIRY_SECONDS
    ) -> str:
        """
        Get presigned URL for barcode. Generates and caches if not exists.

        Args:
            entity_type: Type of entity (material, inventory, work_order)
            entity_id: Unique identifier for the entity
            org_id: Organization identifier
            barcode_format: Barcode format
            expiry_seconds: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL for barcode download

        Raises:
            ValueError: If barcode_format is invalid
        """
        if barcode_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Invalid barcode format: {barcode_format}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        object_path = self._build_object_path(
            org_id, entity_type, entity_id, barcode_format
        )

        # Check if barcode exists (cache hit)
        try:
            self.minio_client.get_file_metadata(object_path)
            logger.info(f"Cache HIT for {object_path}")

        except Exception as e:
            # Cache miss - generate and store barcode
            logger.info(f"Cache MISS for {object_path}: {str(e)}")
            logger.info("Regenerating barcode...")

            self.store_barcode(
                entity_type=entity_type,
                entity_id=entity_id,
                org_id=org_id,
                barcode_format=barcode_format
            )

        # Generate presigned URL
        url = self.minio_client.generate_presigned_url(
            object_name=object_path,
            expiry_seconds=expiry_seconds
        )

        logger.info(f"Generated presigned URL (expires in {expiry_seconds}s)")
        return url

    def generate_batch_barcodes(
        self,
        entities: List[Dict[str, str]],
        barcode_format: str
    ) -> List[Dict[str, Any]]:
        """
        Generate barcodes for multiple entities in batch.

        Args:
            entities: List of entity dictionaries with keys:
                - type: Entity type
                - id: Entity ID
                - org_id: Organization ID
            barcode_format: Barcode format to use for all entities

        Returns:
            List of barcode metadata dictionaries (includes errors for failures)
        """
        logger.info(f"Batch generating {len(entities)} barcodes")

        results = []

        for entity in entities:
            try:
                result = self.store_barcode(
                    entity_type=entity["type"],
                    entity_id=entity["id"],
                    org_id=entity["org_id"],
                    barcode_format=barcode_format
                )
                results.append(result)

            except Exception as e:
                logger.error(
                    f"Failed to generate barcode for {entity['type']}/{entity['id']}: {str(e)}"
                )
                # Include error in results for partial failure handling
                results.append({
                    "entity_type": entity["type"],
                    "entity_id": entity["id"],
                    "org_id": entity["org_id"],
                    "format": barcode_format,
                    "error": str(e)
                })

        logger.info(f"Batch generation complete: {len(results)} results")
        return results

    def delete_barcode(
        self,
        entity_type: str,
        entity_id: str,
        org_id: str,
        barcode_format: str
    ) -> bool:
        """
        Delete barcode from cache.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            org_id: Organization ID
            barcode_format: Barcode format

        Returns:
            True if deletion successful, False otherwise
        """
        object_path = self._build_object_path(
            org_id, entity_type, entity_id, barcode_format
        )

        logger.info(f"Deleting barcode: {object_path}")

        result = self.minio_client.delete_file(object_path)

        if result:
            logger.info(f"Successfully deleted barcode: {object_path}")
        else:
            logger.warning(f"Failed to delete barcode: {object_path}")

        return result

    def _build_object_path(
        self,
        org_id: str,
        entity_type: str,
        entity_id: str,
        barcode_format: str
    ) -> str:
        """
        Build MinIO object path for barcode.

        Format: {org_id}/{entity_type}/{entity_id}_{format}.png

        Args:
            org_id: Organization identifier
            entity_type: Entity type
            entity_id: Entity ID
            barcode_format: Barcode format

        Returns:
            Object path string
        """
        filename = f"{entity_id}_{barcode_format}.png"
        return f"{org_id}/{entity_type}/{filename}"

    def _save_to_temp_file(self, image_base64: str) -> str:
        """
        Save base64 image to temporary file.

        Args:
            image_base64: Base64-encoded image data

        Returns:
            Path to temporary file
        """
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.png',
            delete=False
        ) as temp_file:
            temp_file.write(image_bytes)
            return temp_file.name
