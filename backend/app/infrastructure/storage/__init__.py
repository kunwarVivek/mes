"""Storage infrastructure components.

Provides MinIO S3-compatible object storage for documents, photos, barcodes, and other files.
"""

from .minio_client import MinIOClient
from .barcode_storage_service import BarcodeStorageService

__all__ = ["MinIOClient", "BarcodeStorageService"]
