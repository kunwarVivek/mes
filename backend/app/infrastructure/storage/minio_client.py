"""MinIO Storage Client for S3-compatible file storage."""

from datetime import timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from functools import wraps
from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError, NewConnectionError
from app.core.config import settings

logger = logging.getLogger(__name__)


def retry_on_network_error(max_retries: int = 3):
    """Decorator to retry operations on network failures.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (MaxRetryError, NewConnectionError, ConnectionError) as e:
                    last_exception = e
                    logger.warning(
                        f"Network error in {func.__name__} (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    if attempt == max_retries - 1:
                        raise Exception(
                            f"Failed after {max_retries} attempts: {str(last_exception)}"
                        ) from last_exception
            return None
        return wrapper
    return decorator


class MinIOClient:
    """S3-compatible MinIO client for file storage operations.

    Provides methods for uploading, downloading, deleting files and generating
    presigned URLs with automatic bucket creation and organized folder structure.

    Features:
        - Automatic bucket creation
        - Organized folder structure: {org_id}/{entity_type}/{entity_id}/{filename}
        - Retry logic for network failures
        - Connection pooling via urllib3
        - Comprehensive error handling
    """

    def __init__(self, max_retries: int = 3):
        """Initialize MinIO client with configuration from settings.

        Args:
            max_retries: Maximum retry attempts for network operations

        Automatically creates bucket if it doesn't exist.
        """
        self.max_retries = max_retries
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
        logger.info(f"MinIOClient initialized for bucket: {self.bucket_name}")

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist.

        Raises:
            Exception: If bucket creation fails
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.debug(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to ensure bucket exists: {e}")
            raise Exception(f"Bucket initialization failed: {str(e)}") from e

    def build_object_path(
        self,
        org_id: str,
        entity_type: str,
        entity_id: str,
        filename: str
    ) -> str:
        """Build organized object path: {org_id}/{entity_type}/{entity_id}/{filename}.

        Args:
            org_id: Organization identifier
            entity_type: Type of entity (documents, photos, barcodes, etc.)
            entity_id: Specific entity identifier
            filename: Name of the file

        Returns:
            Formatted object path string
        """
        return f"{org_id}/{entity_type}/{entity_id}/{filename}"

    @retry_on_network_error(max_retries=3)
    def upload_file(
        self,
        file_path: str,
        object_name: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload file to MinIO storage with retry logic.

        Args:
            file_path: Local path to file to upload
            object_name: Object name/key in MinIO (use build_object_path for organization)
            content_type: MIME type of the file
            metadata: Optional metadata to attach to the object

        Returns:
            Object name/key of uploaded file

        Raises:
            FileNotFoundError: If local file doesn't exist
            Exception: If upload fails after retries
        """
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)

        try:
            with open(file_path, 'rb') as file_data:
                self.client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    data=file_data,
                    length=file_size,
                    content_type=content_type,
                    metadata=metadata
                )
            logger.info(f"Successfully uploaded: {object_name} ({file_size} bytes)")
            return object_name
        except S3Error as e:
            logger.error(f"S3 error uploading {object_name}: {e}")
            raise Exception(f"Upload failed: {str(e)}") from e

    @retry_on_network_error(max_retries=3)
    def download_file(
        self,
        object_name: str,
        destination_path: str
    ) -> str:
        """Download file from MinIO storage with retry logic.

        Args:
            object_name: Object name/key in MinIO
            destination_path: Local path where file should be saved

        Returns:
            Local path to downloaded file

        Raises:
            Exception: If object doesn't exist or download fails after retries
        """
        import os

        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(destination_path)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)

            self.client.fget_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=destination_path
            )
            logger.info(f"Successfully downloaded: {object_name} to {destination_path}")
            return destination_path
        except S3Error as e:
            logger.error(f"S3 error downloading {object_name}: {e}")
            if e.code == "NoSuchKey":
                raise Exception(f"Object not found: {object_name}") from e
            raise Exception(f"Download failed: {str(e)}") from e

    @retry_on_network_error(max_retries=3)
    def delete_file(self, object_name: str) -> bool:
        """Delete file from MinIO storage with retry logic.

        Args:
            object_name: Object name/key in MinIO

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"Successfully deleted: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete {object_name}: {e}")
            return False

    @retry_on_network_error(max_retries=3)
    def generate_presigned_url(
        self,
        object_name: str,
        expiry_seconds: int = 3600
    ) -> str:
        """Generate temporary presigned URL for file download.

        Args:
            object_name: Object name/key in MinIO
            expiry_seconds: URL expiration time in seconds (default: 1 hour, max: 7 days)

        Returns:
            Presigned URL string

        Raises:
            ValueError: If expiry_seconds exceeds 7 days
            Exception: If URL generation fails
        """
        max_expiry = 7 * 24 * 3600  # 7 days in seconds
        if expiry_seconds > max_expiry:
            raise ValueError(f"Expiry cannot exceed {max_expiry} seconds (7 days)")

        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expiry_seconds)
            )
            logger.info(f"Generated presigned URL for {object_name} (expires in {expiry_seconds}s)")
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            raise Exception(f"Presigned URL generation failed: {str(e)}") from e

    @retry_on_network_error(max_retries=3)
    def get_file_metadata(self, object_name: str) -> Dict[str, Any]:
        """Retrieve file metadata from MinIO.

        Args:
            object_name: Object name/key in MinIO

        Returns:
            Dictionary containing file metadata (size, content_type, last_modified, etag, metadata)

        Raises:
            Exception: If object doesn't exist
        """
        try:
            stat = self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )

            metadata = {
                'size': stat.size,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified,
                'etag': stat.etag
            }

            # Include custom metadata if available
            if hasattr(stat, 'metadata') and stat.metadata:
                metadata['metadata'] = stat.metadata

            logger.debug(f"Retrieved metadata for {object_name}")
            return metadata
        except S3Error as e:
            logger.error(f"Failed to get metadata for {object_name}: {e}")
            if e.code == "NoSuchKey":
                raise Exception(f"Object not found: {object_name}") from e
            raise Exception(f"Metadata retrieval failed: {str(e)}") from e

    def list_objects(
        self,
        prefix: str = "",
        recursive: bool = True
    ) -> list:
        """List objects in bucket with optional prefix filter.

        Args:
            prefix: Filter objects by prefix (e.g., "org_123/documents/")
            recursive: List recursively (default: True)

        Returns:
            List of object names

        Raises:
            Exception: If listing fails
        """
        try:
            objects = self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            object_list = [obj.object_name for obj in objects]
            logger.info(f"Listed {len(object_list)} objects with prefix '{prefix}'")
            return object_list
        except S3Error as e:
            logger.error(f"Failed to list objects with prefix '{prefix}': {e}")
            raise Exception(f"Object listing failed: {str(e)}") from e
