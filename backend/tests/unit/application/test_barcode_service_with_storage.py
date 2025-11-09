"""
Unit tests for enhanced BarcodeService with MinIO storage integration.

Tests barcode generation with caching:
- Generate and cache material barcodes
- Cache-aware barcode retrieval
- Batch label generation
- Integration with BarcodeStorageService
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from app.application.services.barcode_service import BarcodeService
from app.infrastructure.repositories.material_repository import MaterialRepository
from app.infrastructure.storage.barcode_storage_service import BarcodeStorageService


class TestBarcodeServiceWithStorage:
    """Test suite for BarcodeService with MinIO storage integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_repository = Mock(spec=MaterialRepository)
        self.mock_storage_service = Mock(spec=BarcodeStorageService)

        # Create service with storage integration
        self.service = BarcodeService(
            material_repository=self.mock_repository,
            barcode_storage_service=self.mock_storage_service
        )

    def test_generate_material_label_with_storage_cache(self):
        """Test generating material label uses storage service for caching"""
        # Arrange
        mock_material = Mock()
        mock_material.id = 1
        mock_material.organization_id = 1
        mock_material.material_number = "MAT001"
        mock_material.material_name = "Test Material"
        mock_material.category = Mock(category_name="Raw Material")
        mock_material.base_uom = Mock(uom_code="EA")

        self.mock_repository.get_by_id.return_value = mock_material

        # Mock storage service returns presigned URL
        mock_barcode_url = "http://minio:9000/bucket/org_1/material/MAT001_CODE128.png?signature=xyz"
        self.mock_storage_service.get_barcode_url.return_value = mock_barcode_url

        # Act
        result = self.service.generate_material_label(
            material_id=1,
            include_qr=False,
            use_storage=True
        )

        # Assert
        assert result is not None
        assert result["material_number"] == "MAT001"
        assert "barcode_url" in result
        assert result["barcode_url"] == mock_barcode_url

        # Verify storage service was called
        self.mock_storage_service.get_barcode_url.assert_called_once()

    def test_generate_material_label_without_storage_uses_base64(self):
        """Test generating material label without storage returns base64 (original behavior)"""
        # Arrange
        mock_material = Mock()
        mock_material.id = 2
        mock_material.material_number = "MAT002"
        mock_material.material_name = "Another Material"
        mock_material.category = Mock(category_name="Components")
        mock_material.base_uom = Mock(uom_code="KG")

        self.mock_repository.get_by_id.return_value = mock_material

        # Act
        result = self.service.generate_material_label(
            material_id=2,
            include_qr=False,
            use_storage=False  # Don't use storage
        )

        # Assert
        assert result is not None
        assert result["material_number"] == "MAT002"
        assert "barcode_image" in result  # Base64 image
        assert "barcode_url" not in result  # No URL

        # Verify storage service was NOT called
        self.mock_storage_service.get_barcode_url.assert_not_called()

    def test_generate_batch_labels(self):
        """Test batch generation of material labels with storage"""
        # Arrange
        material_ids = [1, 2, 3]

        # Mock materials - need to handle multiple get_by_id calls
        def get_material_by_id(mat_id):
            mock_mat = Mock()
            mock_mat.id = mat_id
            mock_mat.organization_id = 1
            mock_mat.material_number = f"MAT{mat_id:03d}"
            mock_mat.material_name = f"Material {mat_id}"
            mock_mat.category = Mock(category_name="Test Category")
            mock_mat.base_uom = Mock(uom_code="EA")
            return mock_mat

        self.mock_repository.get_by_id.side_effect = get_material_by_id

        # Mock storage batch generation
        mock_batch_results = [
            {
                "entity_type": "material",
                "entity_id": f"MAT{i:03d}",
                "org_id": "org_1",
                "format": "CODE128",
                "object_path": f"org_1/material/MAT{i:03d}_CODE128.png"
            }
            for i in material_ids
        ]
        self.mock_storage_service.generate_batch_barcodes.return_value = mock_batch_results

        # Act
        results = self.service.generate_batch_labels(
            material_ids=material_ids,
            include_qr=False
        )

        # Assert
        assert len(results) == 3

        for i, result in enumerate(results):
            assert result["material_number"] == f"MAT{material_ids[i]:03d}"
            assert "barcode_metadata" in result

        # Verify batch generation was called
        self.mock_storage_service.generate_batch_barcodes.assert_called_once()

    def test_generate_material_label_with_qr_and_storage(self):
        """Test generating label with both barcode and QR code using storage"""
        # Arrange
        mock_material = Mock()
        mock_material.id = 5
        mock_material.organization_id = 1
        mock_material.material_number = "MAT005"
        mock_material.material_name = "QR Test"
        mock_material.category = Mock(category_name="Test")
        mock_material.base_uom = Mock(uom_code="EA")

        self.mock_repository.get_by_id.return_value = mock_material

        # Mock storage URLs for both barcode and QR
        self.mock_storage_service.get_barcode_url.side_effect = [
            "http://minio/barcode.png",
            "http://minio/qr.png"
        ]

        # Act
        result = self.service.generate_material_label(
            material_id=5,
            include_qr=True,
            use_storage=True
        )

        # Assert
        assert "barcode_url" in result
        assert "qr_url" in result
        assert result["barcode_url"] == "http://minio/barcode.png"
        assert result["qr_url"] == "http://minio/qr.png"

        # Verify storage service was called twice (barcode + QR)
        assert self.mock_storage_service.get_barcode_url.call_count == 2

    def test_generate_material_label_storage_default_false(self):
        """Test that use_storage defaults to False (backwards compatibility)"""
        # Arrange
        mock_material = Mock()
        mock_material.id = 6
        mock_material.material_number = "MAT006"
        mock_material.material_name = "Default Test"
        mock_material.category = Mock(category_name="Test")
        mock_material.base_uom = Mock(uom_code="EA")

        self.mock_repository.get_by_id.return_value = mock_material

        # Act - don't specify use_storage parameter
        result = self.service.generate_material_label(material_id=6)

        # Assert - should use base64 (original behavior)
        assert "barcode_image" in result
        assert "barcode_url" not in result

        # Storage service should not be called
        self.mock_storage_service.get_barcode_url.assert_not_called()

    def test_generate_batch_labels_without_storage_service(self):
        """Test batch generation works even without storage service (backwards compatibility)"""
        # Arrange - create service without storage service
        service_no_storage = BarcodeService(
            material_repository=self.mock_repository,
            barcode_storage_service=None
        )

        mock_material = Mock()
        mock_material.id = 1
        mock_material.organization_id = 1
        mock_material.material_number = "MAT001"
        mock_material.material_name = "Test"
        mock_material.category = Mock(category_name="Test")
        mock_material.base_uom = Mock(uom_code="EA")

        self.mock_repository.get_by_id.return_value = mock_material

        # Act
        results = service_no_storage.generate_batch_labels(
            material_ids=[1],
            include_qr=False
        )

        # Assert - should still work with base64
        assert len(results) == 1
        assert "barcode_image" in results[0]
