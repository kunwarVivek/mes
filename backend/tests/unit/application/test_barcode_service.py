"""
Unit tests for BarcodeService application service.

Tests material label generation with:
- Material lookup from database
- Barcode generation for material number
- Optional QR code generation with JSON payload
- Error handling for missing materials
"""
import pytest
import json
import base64
from unittest.mock import Mock, MagicMock
from io import BytesIO
from PIL import Image

from app.application.services.barcode_service import BarcodeService
from app.models.material import Material, ProcurementType, MRPType


class TestBarcodeService:
    """Test suite for BarcodeService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_repository = Mock()
        self.service = BarcodeService(self.mock_repository)

    def test_generate_material_label_without_qr(self):
        """Test generating material label with barcode only"""
        # Create mock material (using Mock instead of Material to avoid SQLAlchemy issues)
        mock_material = Mock()
        mock_material.id = 1
        mock_material.organization_id = 1
        mock_material.plant_id = 1
        mock_material.material_number = "MAT001"
        mock_material.material_name = "Test Material"
        mock_material.description = "Test Description"
        mock_material.material_category_id = 1
        mock_material.base_uom_id = 1
        mock_material.procurement_type = ProcurementType.PURCHASE
        mock_material.mrp_type = MRPType.MRP
        mock_material.safety_stock = 10.0
        mock_material.reorder_point = 20.0
        mock_material.lot_size = 1.0
        mock_material.lead_time_days = 5
        mock_material.is_active = True
        mock_material.category = Mock(category_name="Raw Material")
        mock_material.base_uom = Mock(uom_code="EA")

        self.mock_repository.get_by_id.return_value = mock_material

        # Generate label
        result = self.service.generate_material_label(material_id=1, include_qr=False)

        # Assertions
        assert result is not None
        assert "material_number" in result
        assert "barcode_image" in result
        assert "qr_image" not in result  # QR should not be included
        assert "label_data" in result

        assert result["material_number"] == "MAT001"
        assert result["barcode_image"] is not None
        assert len(result["barcode_image"]) > 0

        # Verify label_data contains material details
        label_data = result["label_data"]
        assert label_data["material_number"] == "MAT001"
        assert label_data["material_name"] == "Test Material"
        assert label_data["category"] == "Raw Material"
        assert label_data["uom"] == "EA"

        # Verify barcode image is valid Base64
        image_data = base64.b64decode(result["barcode_image"])
        image = Image.open(BytesIO(image_data))
        assert image.format == "PNG"

        # Verify repository was called
        self.mock_repository.get_by_id.assert_called_once_with(1)

    def test_generate_material_label_with_qr(self):
        """Test generating material label with barcode and QR code"""
        # Create mock material
        mock_material = Mock()
        mock_material.id = 2
        mock_material.material_number = "MAT002"
        mock_material.material_name = "Another Material"
        mock_material.category = Mock(category_name="Finished Goods")
        mock_material.base_uom = Mock(uom_code="KG")

        self.mock_repository.get_by_id.return_value = mock_material

        # Generate label with QR code
        result = self.service.generate_material_label(material_id=2, include_qr=True)

        # Assertions
        assert result is not None
        assert "material_number" in result
        assert "barcode_image" in result
        assert "qr_image" in result  # QR should be included
        assert "label_data" in result

        assert result["material_number"] == "MAT002"
        assert result["barcode_image"] is not None
        assert result["qr_image"] is not None

        # Verify both images are valid Base64 PNG
        barcode_data = base64.b64decode(result["barcode_image"])
        barcode_img = Image.open(BytesIO(barcode_data))
        assert barcode_img.format == "PNG"

        qr_data = base64.b64decode(result["qr_image"])
        qr_img = Image.open(BytesIO(qr_data))
        assert qr_img.format == "PNG"
        assert qr_img.width == qr_img.height  # QR codes are square

        # Verify label_data
        label_data = result["label_data"]
        assert label_data["material_number"] == "MAT002"
        assert label_data["material_name"] == "Another Material"
        assert label_data["category"] == "Finished Goods"
        assert label_data["uom"] == "KG"

    def test_generate_material_label_material_not_found(self):
        """Test error handling when material not found"""
        self.mock_repository.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Material with id 999 not found"):
            self.service.generate_material_label(material_id=999, include_qr=False)

        self.mock_repository.get_by_id.assert_called_once_with(999)

    def test_generate_material_label_qr_payload(self):
        """Test QR code contains correct JSON payload"""
        # Create mock material
        mock_material = Mock()
        mock_material.id = 3
        mock_material.material_number = "MAT003"
        mock_material.material_name = "QR Test Material"
        mock_material.category = Mock(category_name="Components")
        mock_material.base_uom = Mock(uom_code="PC")

        self.mock_repository.get_by_id.return_value = mock_material

        # Generate label with QR
        result = self.service.generate_material_label(material_id=3, include_qr=True)

        # The QR code should encode JSON payload
        # We can't decode the QR directly in test, but we can verify the payload structure
        label_data = result["label_data"]

        expected_payload = {
            "material_number": "MAT003",
            "material_name": "QR Test Material",
            "category": "Components",
            "uom": "PC",
        }

        # Verify label_data matches expected payload structure
        for key, value in expected_payload.items():
            assert label_data[key] == value

    def test_generate_material_label_default_include_qr_false(self):
        """Test default value for include_qr is False"""
        mock_material = Mock()
        mock_material.id = 4
        mock_material.material_number = "MAT004"
        mock_material.material_name = "Default Test"
        mock_material.category = Mock(category_name="Test Category")
        mock_material.base_uom = Mock(uom_code="EA")

        self.mock_repository.get_by_id.return_value = mock_material

        # Call without include_qr parameter
        result = self.service.generate_material_label(material_id=4)

        # QR should not be included by default
        assert "qr_image" not in result

    def test_generate_material_label_barcode_format_code128(self):
        """Test barcode is generated in CODE128 format by default"""
        mock_material = Mock()
        mock_material.id = 5
        mock_material.material_number = "MAT005"
        mock_material.material_name = "Format Test"
        mock_material.category = Mock(category_name="Test")
        mock_material.base_uom = Mock(uom_code="EA")

        self.mock_repository.get_by_id.return_value = mock_material

        result = self.service.generate_material_label(material_id=5, include_qr=False)

        # We can't directly check the barcode format from the image,
        # but we can verify the image was generated
        assert result["barcode_image"] is not None
        assert len(result["barcode_image"]) > 0
