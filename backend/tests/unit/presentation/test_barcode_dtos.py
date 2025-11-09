"""
Unit tests for Barcode DTOs.

Tests Pydantic models for barcode request/response validation.
"""
import pytest
from pydantic import ValidationError


class TestBarcodeDTOs:
    """Test suite for Barcode DTOs"""

    def test_barcode_request_dto_default_values(self):
        """Test BarcodeGenerateRequest with default values"""
        from app.application.dtos.material_dto import BarcodeGenerateRequest

        request = BarcodeGenerateRequest()

        assert request.format == "CODE128"
        assert request.include_qr is False

    def test_barcode_request_dto_custom_values(self):
        """Test BarcodeGenerateRequest with custom values"""
        from app.application.dtos.material_dto import BarcodeGenerateRequest

        request = BarcodeGenerateRequest(format="CODE39", include_qr=True)

        assert request.format == "CODE39"
        assert request.include_qr is True

    def test_barcode_request_dto_all_formats(self):
        """Test BarcodeGenerateRequest accepts all valid formats"""
        from app.application.dtos.material_dto import BarcodeGenerateRequest

        formats = ["CODE128", "CODE39", "EAN13", "QR_CODE"]

        for fmt in formats:
            request = BarcodeGenerateRequest(format=fmt)
            assert request.format == fmt

    def test_barcode_request_dto_invalid_format(self):
        """Test BarcodeGenerateRequest rejects invalid format"""
        from app.application.dtos.material_dto import BarcodeGenerateRequest

        with pytest.raises(ValidationError) as exc_info:
            BarcodeGenerateRequest(format="INVALID_FORMAT")

        # Verify error message mentions format
        assert "format" in str(exc_info.value).lower()

    def test_barcode_response_dto_with_barcode_only(self):
        """Test BarcodeResponse with barcode only"""
        from app.application.dtos.material_dto import BarcodeResponse

        response = BarcodeResponse(
            material_number="MAT001",
            format="CODE128",
            barcode_image="base64encodedimage123"
        )

        assert response.material_number == "MAT001"
        assert response.format == "CODE128"
        assert response.barcode_image == "base64encodedimage123"
        assert response.qr_image is None

    def test_barcode_response_dto_with_qr(self):
        """Test BarcodeResponse with both barcode and QR code"""
        from app.application.dtos.material_dto import BarcodeResponse

        response = BarcodeResponse(
            material_number="MAT002",
            format="CODE39",
            barcode_image="barcode_base64",
            qr_image="qr_base64"
        )

        assert response.material_number == "MAT002"
        assert response.format == "CODE39"
        assert response.barcode_image == "barcode_base64"
        assert response.qr_image == "qr_base64"

    def test_barcode_response_dto_serialization(self):
        """Test BarcodeResponse can be serialized to dict"""
        from app.application.dtos.material_dto import BarcodeResponse

        response = BarcodeResponse(
            material_number="MAT003",
            format="QR_CODE",
            barcode_image="test123",
            qr_image="qrtest456"
        )

        data = response.model_dump()

        assert isinstance(data, dict)
        assert data["material_number"] == "MAT003"
        assert data["format"] == "QR_CODE"
        assert data["barcode_image"] == "test123"
        assert data["qr_image"] == "qrtest456"

    def test_barcode_request_dto_serialization(self):
        """Test BarcodeGenerateRequest can be serialized to dict"""
        from app.application.dtos.material_dto import BarcodeGenerateRequest

        request = BarcodeGenerateRequest(format="EAN13", include_qr=True)

        data = request.model_dump()

        assert isinstance(data, dict)
        assert data["format"] == "EAN13"
        assert data["include_qr"] is True
