"""
Unit tests for BarcodeStorageService - MinIO-backed barcode caching.

Tests barcode storage, retrieval, caching, and batch operations with:
- MinIO storage integration (mocked)
- Cache hit/miss scenarios
- Presigned URL generation
- Batch barcode generation
- Cache eviction and TTL
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, ANY
from datetime import datetime, timedelta
from io import BytesIO
import base64

from app.infrastructure.storage.barcode_storage_service import BarcodeStorageService
from app.infrastructure.utilities.barcode_generator import BarcodeGenerator


class TestBarcodeStorageService:
    """Test suite for BarcodeStorageService with MinIO backend"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_minio_client = Mock()
        self.mock_barcode_generator = Mock(spec=BarcodeGenerator)
        self.service = BarcodeStorageService(
            minio_client=self.mock_minio_client,
            barcode_generator=self.mock_barcode_generator
        )

    def test_store_barcode_new_cache_miss(self):
        """Test storing a new barcode (cache miss scenario)"""
        # Arrange
        entity_type = "material"
        entity_id = "MAT001"
        org_id = "org_123"
        barcode_format = "CODE128"

        # Mock barcode generation
        mock_barcode_data = {
            "barcode_data": entity_id,
            "format": barcode_format,
            "image_base64": "base64encodedimage==",
            "checksum": "abc12345"
        }
        self.mock_barcode_generator.generate_material_barcode.return_value = mock_barcode_data

        # Mock MinIO upload
        expected_object_path = f"{org_id}/{entity_type}/{entity_id}_{barcode_format}.png"
        self.mock_minio_client.upload_file.return_value = expected_object_path

        # Act
        result = self.service.store_barcode(
            entity_type=entity_type,
            entity_id=entity_id,
            org_id=org_id,
            barcode_format=barcode_format
        )

        # Assert
        assert result is not None
        assert result["entity_type"] == entity_type
        assert result["entity_id"] == entity_id
        assert result["org_id"] == org_id
        assert result["format"] == barcode_format
        assert result["object_path"] == expected_object_path
        assert "stored_at" in result

        # Verify barcode was generated
        self.mock_barcode_generator.generate_material_barcode.assert_called_once_with(
            entity_id, format=barcode_format
        )

        # Verify MinIO upload was called
        self.mock_minio_client.upload_file.assert_called_once()

    def test_get_barcode_url_cache_hit(self):
        """Test retrieving barcode URL from cache (cache hit)"""
        # Arrange
        entity_type = "inventory"
        entity_id = "INV001"
        org_id = "org_456"
        barcode_format = "QR_CODE"

        # Mock cache hit - barcode already exists in MinIO
        expected_object_path = f"{org_id}/{entity_type}/{entity_id}_{barcode_format}.png"
        expected_url = f"http://minio:9000/bucket/{expected_object_path}?signature=xyz"

        self.mock_minio_client.generate_presigned_url.return_value = expected_url

        # Mock that object exists
        self.mock_minio_client.get_file_metadata.return_value = {
            "size": 1024,
            "content_type": "image/png",
            "last_modified": datetime.utcnow()
        }

        # Act
        url = self.service.get_barcode_url(
            entity_type=entity_type,
            entity_id=entity_id,
            org_id=org_id,
            barcode_format=barcode_format,
            expiry_seconds=3600
        )

        # Assert
        assert url == expected_url

        # Verify presigned URL was generated
        self.mock_minio_client.generate_presigned_url.assert_called_once()

        # Verify barcode was NOT regenerated (cache hit)
        self.mock_barcode_generator.generate_material_barcode.assert_not_called()

    def test_get_barcode_url_cache_miss_regenerates(self):
        """Test cache miss triggers barcode regeneration"""
        # Arrange
        entity_type = "work_order"
        entity_id = "WO001"
        org_id = "org_789"
        barcode_format = "CODE128"

        # Mock cache miss - object doesn't exist
        self.mock_minio_client.get_file_metadata.side_effect = Exception("Object not found")

        # Mock barcode generation (using valid base64 - minimal PNG data)
        mock_barcode_data = {
            "barcode_data": entity_id,
            "format": barcode_format,
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "checksum": "def67890"
        }
        self.mock_barcode_generator.generate_material_barcode.return_value = mock_barcode_data

        # Mock MinIO upload and URL generation
        expected_object_path = f"{org_id}/{entity_type}/{entity_id}_{barcode_format}.png"
        self.mock_minio_client.upload_file.return_value = expected_object_path
        expected_url = f"http://minio:9000/bucket/{expected_object_path}?signature=abc"
        self.mock_minio_client.generate_presigned_url.return_value = expected_url

        # Act
        url = self.service.get_barcode_url(
            entity_type=entity_type,
            entity_id=entity_id,
            org_id=org_id,
            barcode_format=barcode_format
        )

        # Assert
        assert url == expected_url

        # Verify barcode was regenerated
        self.mock_barcode_generator.generate_material_barcode.assert_called_once()

        # Verify upload happened
        self.mock_minio_client.upload_file.assert_called_once()

    def test_generate_batch_barcodes(self):
        """Test batch generation of multiple barcodes"""
        # Arrange
        entities = [
            {"type": "material", "id": "MAT001", "org_id": "org_1"},
            {"type": "material", "id": "MAT002", "org_id": "org_1"},
            {"type": "inventory", "id": "INV001", "org_id": "org_1"},
        ]
        barcode_format = "CODE128"

        # Mock barcode generation for each entity
        def mock_generate(entity_id, format):
            return {
                "barcode_data": entity_id,
                "format": format,
                "image_base64": f"base64_{entity_id}",
                "checksum": f"check_{entity_id}"
            }

        self.mock_barcode_generator.generate_material_barcode.side_effect = mock_generate

        # Mock MinIO uploads
        def mock_upload(file_path, object_name, content_type, metadata):
            return object_name

        self.mock_minio_client.upload_file.side_effect = mock_upload

        # Act
        results = self.service.generate_batch_barcodes(
            entities=entities,
            barcode_format=barcode_format
        )

        # Assert
        assert len(results) == 3

        for i, result in enumerate(results):
            assert result["entity_type"] == entities[i]["type"]
            assert result["entity_id"] == entities[i]["id"]
            assert result["org_id"] == entities[i]["org_id"]
            assert result["format"] == barcode_format

        # Verify all barcodes were generated
        assert self.mock_barcode_generator.generate_material_barcode.call_count == 3

        # Verify all uploads happened
        assert self.mock_minio_client.upload_file.call_count == 3

    def test_delete_barcode(self):
        """Test deleting barcode from cache"""
        # Arrange
        entity_type = "material"
        entity_id = "MAT999"
        org_id = "org_delete"
        barcode_format = "QR_CODE"

        # Mock successful deletion
        self.mock_minio_client.delete_file.return_value = True

        # Act
        result = self.service.delete_barcode(
            entity_type=entity_type,
            entity_id=entity_id,
            org_id=org_id,
            barcode_format=barcode_format
        )

        # Assert
        assert result is True

        # Verify MinIO delete was called with correct object path
        expected_object_path = f"{org_id}/{entity_type}/{entity_id}_{barcode_format}.png"
        self.mock_minio_client.delete_file.assert_called_once_with(expected_object_path)

    def test_store_barcode_with_metadata(self):
        """Test storing barcode with custom metadata"""
        # Arrange
        entity_type = "material"
        entity_id = "MAT_META"
        org_id = "org_meta"
        barcode_format = "CODE128"
        custom_metadata = {
            "material_name": "Test Material",
            "category": "Raw Material"
        }

        # Mock barcode generation
        mock_barcode_data = {
            "barcode_data": entity_id,
            "format": barcode_format,
            "image_base64": "base64meta==",
            "checksum": "meta123"
        }
        self.mock_barcode_generator.generate_material_barcode.return_value = mock_barcode_data

        # Mock MinIO upload
        expected_object_path = f"{org_id}/{entity_type}/{entity_id}_{barcode_format}.png"
        self.mock_minio_client.upload_file.return_value = expected_object_path

        # Act
        result = self.service.store_barcode(
            entity_type=entity_type,
            entity_id=entity_id,
            org_id=org_id,
            barcode_format=barcode_format,
            metadata=custom_metadata
        )

        # Assert
        assert result is not None

        # Verify MinIO upload was called with metadata
        call_args = self.mock_minio_client.upload_file.call_args
        assert call_args.kwargs.get("metadata") is not None

    def test_get_barcode_url_default_expiry(self):
        """Test default expiry time for presigned URLs"""
        # Arrange
        entity_type = "material"
        entity_id = "MAT_EXPIRY"
        org_id = "org_exp"
        barcode_format = "CODE128"

        # Mock cache hit
        self.mock_minio_client.get_file_metadata.return_value = {
            "size": 1024,
            "content_type": "image/png"
        }
        self.mock_minio_client.generate_presigned_url.return_value = "http://url"

        # Act
        self.service.get_barcode_url(
            entity_type=entity_type,
            entity_id=entity_id,
            org_id=org_id,
            barcode_format=barcode_format
        )

        # Assert - default expiry should be 3600 seconds (1 hour)
        call_args = self.mock_minio_client.generate_presigned_url.call_args
        assert call_args.kwargs.get("expiry_seconds", 3600) == 3600

    def test_store_barcode_invalid_format(self):
        """Test storing barcode with invalid format raises error"""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid barcode format"):
            self.service.store_barcode(
                entity_type="material",
                entity_id="MAT001",
                org_id="org_1",
                barcode_format="INVALID_FORMAT"
            )

    def test_batch_generation_handles_partial_failures(self):
        """Test batch generation continues on individual failures"""
        # Arrange
        entities = [
            {"type": "material", "id": "MAT_OK", "org_id": "org_1"},
            {"type": "material", "id": "MAT_FAIL", "org_id": "org_1"},
            {"type": "material", "id": "MAT_OK2", "org_id": "org_1"},
        ]

        # Mock generation - second one fails (using valid base64)
        valid_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        def mock_generate_with_failure(entity_id, format):
            if entity_id == "MAT_FAIL":
                raise Exception("Generation failed")
            return {
                "barcode_data": entity_id,
                "format": format,
                "image_base64": valid_base64,
                "checksum": f"check_{entity_id}"
            }

        self.mock_barcode_generator.generate_material_barcode.side_effect = mock_generate_with_failure
        self.mock_minio_client.upload_file.return_value = "path"

        # Act
        results = self.service.generate_batch_barcodes(
            entities=entities,
            barcode_format="CODE128"
        )

        # Assert - should have 2 successful results and 1 error
        successful = [r for r in results if "error" not in r]
        failed = [r for r in results if "error" in r]

        assert len(successful) == 2
        assert len(failed) == 1
        assert failed[0]["entity_id"] == "MAT_FAIL"
