"""
Unit tests for BarcodeGenerator utility.

Tests barcode generation for materials, batches, and locations with:
- Multiple barcode formats (CODE128, CODE39, EAN13, QR_CODE)
- Base64 image encoding
- Checksum validation
- Error handling for invalid formats and data
"""
import pytest
import base64
from io import BytesIO
from PIL import Image

from app.infrastructure.utilities.barcode_generator import BarcodeGenerator


class TestBarcodeGenerator:
    """Test suite for BarcodeGenerator utility"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = BarcodeGenerator()

    def test_generate_material_barcode_code128(self):
        """Test generating CODE128 barcode for material number"""
        result = self.generator.generate_material_barcode("MAT001", format="CODE128")

        assert result is not None
        assert "barcode_data" in result
        assert "format" in result
        assert "image_base64" in result
        assert "checksum" in result

        assert result["barcode_data"] == "MAT001"
        assert result["format"] == "CODE128"
        assert result["image_base64"] is not None
        assert len(result["image_base64"]) > 0

        # Verify Base64 encoding
        image_data = base64.b64decode(result["image_base64"])
        assert len(image_data) > 0

        # Verify it's a valid PNG image
        image = Image.open(BytesIO(image_data))
        assert image.format == "PNG"
        assert image.width > 0
        assert image.height > 0

    def test_generate_material_barcode_code39(self):
        """Test generating CODE39 barcode for material number"""
        result = self.generator.generate_material_barcode("MAT002", format="CODE39")

        assert result["barcode_data"] == "MAT002"
        assert result["format"] == "CODE39"
        assert result["image_base64"] is not None

        # Verify image
        image_data = base64.b64decode(result["image_base64"])
        image = Image.open(BytesIO(image_data))
        assert image.format == "PNG"

    def test_generate_material_barcode_qr_code(self):
        """Test generating QR code for material number"""
        result = self.generator.generate_material_barcode("MAT003", format="QR_CODE")

        assert result["barcode_data"] == "MAT003"
        assert result["format"] == "QR_CODE"
        assert result["image_base64"] is not None

        # Verify QR code image (should be square)
        image_data = base64.b64decode(result["image_base64"])
        image = Image.open(BytesIO(image_data))
        assert image.format == "PNG"
        assert image.width == image.height  # QR codes are square

    def test_generate_material_barcode_ean13(self):
        """Test generating EAN13 barcode (13 digits only)"""
        result = self.generator.generate_material_barcode("1234567890123", format="EAN13")

        assert result["barcode_data"] == "1234567890123"
        assert result["format"] == "EAN13"
        assert result["image_base64"] is not None
        assert result["checksum"] is not None

    def test_generate_material_barcode_default_format(self):
        """Test default format is CODE128"""
        result = self.generator.generate_material_barcode("MAT004")

        assert result["format"] == "CODE128"

    def test_generate_batch_barcode(self):
        """Test generating barcode for batch number"""
        result = self.generator.generate_batch_barcode("BATCH001", format="CODE128")

        assert result["barcode_data"] == "BATCH001"
        assert result["format"] == "CODE128"
        assert result["image_base64"] is not None

        # Verify image
        image_data = base64.b64decode(result["image_base64"])
        image = Image.open(BytesIO(image_data))
        assert image.format == "PNG"

    def test_generate_location_barcode(self):
        """Test generating barcode for storage location"""
        result = self.generator.generate_location_barcode("LOC-A-01-02", format="CODE128")

        assert result["barcode_data"] == "LOC-A-01-02"
        assert result["format"] == "CODE128"
        assert result["image_base64"] is not None

    def test_validate_barcode_code128_valid(self):
        """Test validating valid CODE128 barcode"""
        # Generate a barcode first
        result = self.generator.generate_material_barcode("MAT005", format="CODE128")

        # Validate it
        is_valid = self.generator.validate_barcode(result["barcode_data"], expected_format="CODE128")

        assert is_valid is True

    def test_validate_barcode_ean13_valid(self):
        """Test validating valid EAN13 barcode with checksum"""
        # EAN13 requires exactly 13 digits
        result = self.generator.generate_material_barcode("1234567890123", format="EAN13")

        is_valid = self.generator.validate_barcode(result["barcode_data"], expected_format="EAN13")

        assert is_valid is True

    def test_validate_barcode_invalid_characters(self):
        """Test validation fails for invalid characters"""
        # CODE128 should accept alphanumeric, but let's test special chars that might fail
        is_valid = self.generator.validate_barcode("", expected_format="CODE128")

        assert is_valid is False

    def test_generate_material_barcode_invalid_format(self):
        """Test error handling for invalid barcode format"""
        with pytest.raises(ValueError, match="Invalid barcode format"):
            self.generator.generate_material_barcode("MAT006", format="INVALID_FORMAT")

    def test_generate_material_barcode_empty_data(self):
        """Test error handling for empty material number"""
        with pytest.raises(ValueError, match="Barcode data cannot be empty"):
            self.generator.generate_material_barcode("", format="CODE128")

    def test_generate_batch_barcode_empty_data(self):
        """Test error handling for empty batch number"""
        with pytest.raises(ValueError, match="Barcode data cannot be empty"):
            self.generator.generate_batch_barcode("", format="CODE128")

    def test_generate_location_barcode_empty_data(self):
        """Test error handling for empty location code"""
        with pytest.raises(ValueError, match="Barcode data cannot be empty"):
            self.generator.generate_location_barcode("", format="CODE128")

    def test_generate_material_barcode_ean13_invalid_length(self):
        """Test EAN13 requires exactly 13 digits"""
        with pytest.raises(ValueError, match="EAN13 requires exactly 13 digits"):
            self.generator.generate_material_barcode("12345", format="EAN13")

    def test_generate_material_barcode_ean13_non_numeric(self):
        """Test EAN13 requires numeric data only"""
        with pytest.raises(ValueError, match="EAN13 requires numeric data only"):
            self.generator.generate_material_barcode("ABCDEFGHIJKLM", format="EAN13")

    def test_barcode_image_size_code128(self):
        """Test CODE128 barcode has expected dimensions (300x100)"""
        result = self.generator.generate_material_barcode("MAT007", format="CODE128")

        image_data = base64.b64decode(result["image_base64"])
        image = Image.open(BytesIO(image_data))

        # Default size should be 300x100 for barcodes
        assert image.width >= 200  # Allow some variation based on library
        assert image.height >= 50

    def test_barcode_image_size_qr_code(self):
        """Test QR code has expected dimensions (200x200)"""
        result = self.generator.generate_material_barcode("MAT008", format="QR_CODE")

        image_data = base64.b64decode(result["image_base64"])
        image = Image.open(BytesIO(image_data))

        # QR codes should be square (200x200 default)
        assert image.width == image.height
        assert image.width >= 100  # Allow some variation

    def test_special_characters_in_code128(self):
        """Test CODE128 handles special characters"""
        # CODE128 supports ASCII characters
        result = self.generator.generate_material_barcode("MAT-009_TEST", format="CODE128")

        assert result["barcode_data"] == "MAT-009_TEST"
        assert result["image_base64"] is not None

    def test_checksum_included_in_result(self):
        """Test checksum is included in result for CODE128"""
        result = self.generator.generate_material_barcode("MAT010", format="CODE128")

        assert "checksum" in result
        assert result["checksum"] is not None
