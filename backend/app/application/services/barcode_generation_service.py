"""
BarcodeGenerationService - Application layer service for barcode/QR code generation.

Provides comprehensive barcode generation with:
- Multiple formats: CODE128, QR Code, Data Matrix
- MinIO storage integration
- PDF label generation
- Base64 and file-based output
- Batch processing support

Uses python-barcode and qrcode libraries with MinIO for storage.
"""
import base64
import io
import tempfile
import os
from typing import Dict, List, Optional, Any, BinaryIO
from datetime import datetime
from io import BytesIO
import logging

import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader

from app.infrastructure.utilities.barcode_generator import BarcodeGenerator
from app.infrastructure.storage.minio_client import MinIOClient

logger = logging.getLogger(__name__)


class BarcodeGenerationService:
    """
    Service for generating barcodes, QR codes, and data matrix codes.

    Supports multiple output formats (Base64, MinIO storage, PDF labels)
    and batch processing.
    """

    SUPPORTED_FORMATS = ["CODE128", "CODE39", "EAN13", "QR_CODE", "DATAMATRIX"]
    DEFAULT_DPI = 300
    DEFAULT_BARCODE_HEIGHT = 15.0  # mm

    def __init__(
        self,
        minio_client: Optional[MinIOClient] = None,
        barcode_generator: Optional[BarcodeGenerator] = None,
    ):
        """
        Initialize BarcodeGenerationService.

        Args:
            minio_client: Optional MinIO client for storage
            barcode_generator: Optional barcode generator utility
        """
        self._minio_client = minio_client
        self._barcode_generator = barcode_generator or BarcodeGenerator()

    def generate_code128(
        self,
        data: str,
        include_text: bool = True,
        module_height: float = DEFAULT_BARCODE_HEIGHT,
    ) -> Dict[str, Any]:
        """
        Generate CODE128 barcode.

        Args:
            data: Data to encode
            include_text: Include human-readable text
            module_height: Barcode height in mm

        Returns:
            Dictionary with:
            - format: Barcode format
            - data: Encoded data
            - image_base64: Base64-encoded image
            - width: Image width in pixels
            - height: Image height in pixels
        """
        logger.info(f"Generating CODE128 barcode for: {data}")

        if not data or not data.strip():
            raise ValueError("Barcode data cannot be empty")

        # Generate barcode using python-barcode
        code128_class = barcode.get_barcode_class("code128")
        barcode_instance = code128_class(data, writer=ImageWriter())

        # Generate to buffer
        buffer = BytesIO()
        barcode_instance.write(
            buffer,
            options={
                "write_text": include_text,
                "module_height": module_height,
                "text_distance": 5.0,
                "font_size": 10,
            },
        )

        # Get image info
        buffer.seek(0)
        img = Image.open(buffer)
        width, height = img.size

        # Convert to Base64
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        logger.info(f"Generated CODE128 barcode: {width}x{height}px")

        return {
            "format": "CODE128",
            "data": data,
            "image_base64": image_base64,
            "width": width,
            "height": height,
            "module_height": module_height,
        }

    def generate_qr_code(
        self,
        data: str,
        version: int = 1,
        error_correction: str = "H",
        box_size: int = 10,
        border: int = 4,
    ) -> Dict[str, Any]:
        """
        Generate QR code with configurable parameters.

        Args:
            data: Data to encode (can be JSON, URL, text, etc.)
            version: QR version (1-40, higher = more data)
            error_correction: Error correction level (L, M, Q, H)
            box_size: Size of each box in pixels
            border: Border size in boxes

        Returns:
            Dictionary with:
            - format: QR_CODE
            - data: Encoded data
            - image_base64: Base64-encoded image
            - width: Image width in pixels
            - height: Image height in pixels
            - version: QR version used
        """
        logger.info(f"Generating QR code (version={version}, error_correction={error_correction})")

        if not data:
            raise ValueError("QR code data cannot be empty")

        # Map error correction levels
        error_correction_map = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H,
        }

        ec_level = error_correction_map.get(error_correction, qrcode.constants.ERROR_CORRECT_H)

        # Generate QR code
        qr = qrcode.QRCode(
            version=version,
            error_correction=ec_level,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to Base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        width, height = img.size

        logger.info(f"Generated QR code: {width}x{height}px (version={qr.version})")

        return {
            "format": "QR_CODE",
            "data": data,
            "image_base64": image_base64,
            "width": width,
            "height": height,
            "version": qr.version,
            "error_correction": error_correction,
        }

    def generate_datamatrix(
        self,
        data: str,
        size: str = "auto",
    ) -> Dict[str, Any]:
        """
        Generate Data Matrix 2D barcode.

        Note: This is a placeholder implementation. For production use,
        install python-datamatrix or treepoem library.

        Args:
            data: Data to encode
            size: Matrix size (auto, 10x10, 12x12, etc.)

        Returns:
            Dictionary with barcode details

        Raises:
            NotImplementedError: Data Matrix requires additional library
        """
        logger.warning("Data Matrix generation requires additional library (treepoem or pylibdmtx)")

        # Fallback to QR code for now
        logger.info("Falling back to QR code generation")
        result = self.generate_qr_code(data)
        result["format"] = "DATAMATRIX_FALLBACK_QR"
        result["note"] = "Data Matrix not available, using QR code"

        return result

    def save_to_minio(
        self,
        image_base64: str,
        org_id: str,
        entity_type: str,
        entity_id: str,
        barcode_format: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Save barcode image to MinIO storage.

        Args:
            image_base64: Base64-encoded image
            org_id: Organization ID
            entity_type: Entity type (material, work_order, shipment, package)
            entity_id: Entity ID
            barcode_format: Barcode format
            metadata: Optional metadata

        Returns:
            Dictionary with:
            - object_path: MinIO object path
            - file_url: Presigned URL (if available)
            - stored_at: Storage timestamp

        Raises:
            ValueError: If MinIO client not configured
        """
        if not self._minio_client:
            raise ValueError("MinIO client not configured")

        logger.info(f"Saving barcode to MinIO: {entity_type}/{entity_id}")

        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        try:
            # Build object path
            filename = f"{entity_id}_{barcode_format}.png"
            object_path = self._minio_client.build_object_path(
                org_id=org_id,
                entity_type=entity_type,
                entity_id=entity_id,
                filename=filename,
            )

            # Prepare metadata
            storage_metadata = metadata or {}
            storage_metadata.update(
                {
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                    "barcode_format": barcode_format,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            )

            # Upload to MinIO
            self._minio_client.upload_file(
                file_path=temp_path,
                object_name=object_path,
                content_type="image/png",
                metadata=storage_metadata,
            )

            # Generate presigned URL
            file_url = self._minio_client.generate_presigned_url(
                object_name=object_path, expiry_seconds=3600
            )

            logger.info(f"Saved barcode to MinIO: {object_path}")

            return {
                "object_path": object_path,
                "file_url": file_url,
                "stored_at": datetime.utcnow().isoformat(),
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def create_label_pdf(
        self,
        labels: List[Dict[str, Any]],
        page_size: str = "letter",
        labels_per_page: int = 6,
    ) -> bytes:
        """
        Generate printable PDF with barcode labels.

        Args:
            labels: List of label dictionaries with:
                - image_base64: Barcode image
                - title: Label title
                - subtitle: Optional subtitle
                - data: Encoded data (shown below barcode)
            page_size: Page size (letter, A4)
            labels_per_page: Number of labels per page (2, 4, 6, 8)

        Returns:
            PDF bytes

        Raises:
            ValueError: If invalid parameters
        """
        logger.info(f"Creating label PDF with {len(labels)} labels")

        if not labels:
            raise ValueError("No labels provided")

        # Select page size
        if page_size == "letter":
            page_width, page_height = letter
        elif page_size == "A4":
            page_width, page_height = A4
        else:
            raise ValueError(f"Invalid page size: {page_size}")

        # Create PDF buffer
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Calculate label positions
        margin = 0.5 * inch
        usable_width = page_width - (2 * margin)
        usable_height = page_height - (2 * margin)

        # Determine grid layout
        if labels_per_page == 2:
            cols, rows = 1, 2
        elif labels_per_page == 4:
            cols, rows = 2, 2
        elif labels_per_page == 6:
            cols, rows = 2, 3
        elif labels_per_page == 8:
            cols, rows = 2, 4
        else:
            raise ValueError(f"Invalid labels_per_page: {labels_per_page}")

        label_width = usable_width / cols
        label_height = usable_height / rows

        # Draw labels
        for idx, label_data in enumerate(labels):
            # Calculate position on grid
            page_idx = idx % labels_per_page
            col = page_idx % cols
            row = page_idx // cols

            # Position
            x = margin + (col * label_width)
            y = page_height - margin - ((row + 1) * label_height)

            # Draw label border (optional)
            pdf.rect(x, y, label_width, label_height, stroke=1, fill=0)

            # Draw title
            if "title" in label_data:
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(x + 10, y + label_height - 20, label_data["title"])

            # Draw subtitle
            if "subtitle" in label_data:
                pdf.setFont("Helvetica", 9)
                pdf.drawString(x + 10, y + label_height - 35, label_data["subtitle"])

            # Draw barcode image
            if "image_base64" in label_data:
                # Decode base64 image
                image_bytes = base64.b64decode(label_data["image_base64"])
                image = Image.open(BytesIO(image_bytes))

                # Calculate image dimensions (fit to label)
                max_img_width = label_width - 20
                max_img_height = label_height - 80
                img_width, img_height = image.size

                # Scale to fit
                scale = min(max_img_width / img_width, max_img_height / img_height)
                scaled_width = img_width * scale
                scaled_height = img_height * scale

                # Center image
                img_x = x + (label_width - scaled_width) / 2
                img_y = y + 40

                # Draw image
                pdf.drawInlineImage(
                    ImageReader(image),
                    img_x,
                    img_y,
                    width=scaled_width,
                    height=scaled_height,
                )

            # Draw data text below barcode
            if "data" in label_data:
                pdf.setFont("Courier", 8)
                text_y = y + 25
                pdf.drawCentredString(x + label_width / 2, text_y, label_data["data"])

            # Start new page if needed
            if (idx + 1) % labels_per_page == 0 and idx < len(labels) - 1:
                pdf.showPage()

        # Save PDF
        pdf.save()

        # Get PDF bytes
        buffer.seek(0)
        pdf_bytes = buffer.read()

        logger.info(f"Created PDF with {len(labels)} labels")

        return pdf_bytes

    def generate_batch_barcodes(
        self,
        items: List[Dict[str, Any]],
        barcode_format: str = "CODE128",
        save_to_storage: bool = False,
        org_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate barcodes for multiple items in batch.

        Args:
            items: List of item dictionaries with:
                - data: Data to encode
                - entity_type: Optional entity type (for storage)
                - entity_id: Optional entity ID (for storage)
            barcode_format: Barcode format to use
            save_to_storage: Save to MinIO storage
            org_id: Organization ID (required if save_to_storage=True)

        Returns:
            List of result dictionaries with barcode details

        Raises:
            ValueError: If invalid parameters
        """
        logger.info(f"Batch generating {len(items)} {barcode_format} barcodes")

        if save_to_storage and not org_id:
            raise ValueError("org_id required when save_to_storage=True")

        results = []

        for item in items:
            try:
                data = item.get("data")
                if not data:
                    raise ValueError("Item missing 'data' field")

                # Generate barcode
                if barcode_format == "CODE128":
                    result = self.generate_code128(data)
                elif barcode_format == "QR_CODE":
                    result = self.generate_qr_code(data)
                elif barcode_format == "DATAMATRIX":
                    result = self.generate_datamatrix(data)
                else:
                    raise ValueError(f"Unsupported format: {barcode_format}")

                # Save to storage if requested
                if save_to_storage and self._minio_client:
                    entity_type = item.get("entity_type", "unknown")
                    entity_id = item.get("entity_id", data)

                    storage_result = self.save_to_minio(
                        image_base64=result["image_base64"],
                        org_id=org_id,
                        entity_type=entity_type,
                        entity_id=str(entity_id),
                        barcode_format=barcode_format,
                    )

                    result["storage"] = storage_result

                results.append({"success": True, "data": data, "result": result})

            except Exception as e:
                logger.error(f"Failed to generate barcode for item: {e}")
                results.append(
                    {"success": False, "data": item.get("data"), "error": str(e)}
                )

        logger.info(f"Batch generation complete: {len(results)} results")

        return results
