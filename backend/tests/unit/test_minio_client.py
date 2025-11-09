"""Test suite for MinIO Storage Client."""

import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from pathlib import Path
from io import BytesIO
from app.infrastructure.storage.minio_client import MinIOClient
from app.core.config import settings


class TestMinIOClientInitialization:
    """Test MinIOClient initialization and configuration."""

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_client_initialization_with_settings(self, mock_minio_class):
        """Should initialize MinIO client with configuration from settings."""
        # Arrange
        mock_client_instance = Mock()
        mock_minio_class.return_value = mock_client_instance

        # Act
        client = MinIOClient()

        # Assert
        mock_minio_class.assert_called_once_with(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        assert client.bucket_name == settings.MINIO_BUCKET

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_bucket_auto_creation_when_not_exists(self, mock_minio_class):
        """Should automatically create bucket if it doesn't exist."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = False
        mock_minio_class.return_value = mock_client_instance

        # Act
        MinIOClient()

        # Assert
        mock_client_instance.bucket_exists.assert_called_once_with(settings.MINIO_BUCKET)
        mock_client_instance.make_bucket.assert_called_once_with(settings.MINIO_BUCKET)

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_bucket_not_created_when_exists(self, mock_minio_class):
        """Should not create bucket if it already exists."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client_instance

        # Act
        MinIOClient()

        # Assert
        mock_client_instance.bucket_exists.assert_called_once_with(settings.MINIO_BUCKET)
        mock_client_instance.make_bucket.assert_not_called()


class TestMinIOClientUpload:
    """Test file upload functionality."""

    @patch('app.infrastructure.storage.minio_client.Minio')
    @patch('builtins.open', new_callable=mock_open, read_data=b'test file content')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_upload_file_success(self, mock_getsize, mock_exists, mock_file, mock_minio_class):
        """Should successfully upload file to MinIO."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client_instance
        mock_exists.return_value = True
        mock_getsize.return_value = 100

        client = MinIOClient()
        file_path = "/tmp/test.pdf"
        object_name = "org_123/documents/doc_456/test.pdf"
        content_type = "application/pdf"

        # Act
        result = client.upload_file(file_path, object_name, content_type)

        # Assert
        mock_exists.assert_called_with(file_path)
        mock_file.assert_called_once_with(file_path, 'rb')
        mock_client_instance.put_object.assert_called_once()
        call_args = mock_client_instance.put_object.call_args
        assert call_args[1]['bucket_name'] == settings.MINIO_BUCKET
        assert call_args[1]['object_name'] == object_name
        assert call_args[1]['length'] == 100
        assert call_args[1]['content_type'] == content_type
        assert result == object_name

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_upload_file_with_organized_path(self, mock_minio_class):
        """Should upload file with organized folder structure."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()
        org_id = "org_789"
        entity_type = "products"
        entity_id = "prod_111"
        filename = "barcode.png"

        # Act
        object_name = client.build_object_path(org_id, entity_type, entity_id, filename)

        # Assert
        expected_path = f"{org_id}/{entity_type}/{entity_id}/{filename}"
        assert object_name == expected_path

    @patch('app.infrastructure.storage.minio_client.Minio')
    @patch('builtins.open', side_effect=FileNotFoundError("File not found"))
    def test_upload_file_not_found(self, mock_file, mock_minio_class):
        """Should raise error when file to upload doesn't exist."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            client.upload_file("/nonexistent/file.pdf", "test/file.pdf", "application/pdf")


class TestMinIOClientDownload:
    """Test file download functionality."""

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_download_file_success(self, mock_minio_class):
        """Should successfully download file from MinIO."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()
        object_name = "org_123/documents/doc_456/test.pdf"
        destination_path = "/tmp/downloaded_test.pdf"

        # Act
        result = client.download_file(object_name, destination_path)

        # Assert
        mock_client_instance.fget_object.assert_called_once_with(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name,
            file_path=destination_path
        )
        assert result == destination_path

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_download_file_object_not_found(self, mock_minio_class):
        """Should raise error when object doesn't exist in MinIO."""
        # Arrange
        from minio.error import S3Error

        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_client_instance.fget_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="/test/file.pdf",
            request_id="123",
            host_id="456",
            response="error"
        )
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            client.download_file("nonexistent/file.pdf", "/tmp/test.pdf")
        assert "not found" in str(exc_info.value).lower() or "NoSuchKey" in str(exc_info.value)


class TestMinIOClientDelete:
    """Test file deletion functionality."""

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_delete_file_success(self, mock_minio_class):
        """Should successfully delete file from MinIO."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()
        object_name = "org_123/documents/doc_456/test.pdf"

        # Act
        result = client.delete_file(object_name)

        # Assert
        mock_client_instance.remove_object.assert_called_once_with(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name
        )
        assert result is True

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_delete_file_handles_errors(self, mock_minio_class):
        """Should handle errors during file deletion."""
        # Arrange
        from minio.error import S3Error

        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_client_instance.remove_object.side_effect = S3Error(
            code="InternalError",
            message="Server error",
            resource="/test/file.pdf",
            request_id="123",
            host_id="456",
            response="error"
        )
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()

        # Act
        result = client.delete_file("test/file.pdf")

        # Assert
        assert result is False


class TestMinIOClientPresignedURL:
    """Test presigned URL generation functionality."""

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_generate_presigned_url_default_expiry(self, mock_minio_class):
        """Should generate presigned URL with default 1-hour expiry."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_client_instance.presigned_get_object.return_value = "https://minio.example.com/presigned-url"
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()
        object_name = "org_123/documents/doc_456/test.pdf"

        # Act
        result = client.generate_presigned_url(object_name)

        # Assert
        from datetime import timedelta
        mock_client_instance.presigned_get_object.assert_called_once()
        call_args = mock_client_instance.presigned_get_object.call_args
        assert call_args[1]['bucket_name'] == settings.MINIO_BUCKET
        assert call_args[1]['object_name'] == object_name
        assert call_args[1]['expires'] == timedelta(seconds=3600)
        assert result == "https://minio.example.com/presigned-url"

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_generate_presigned_url_custom_expiry(self, mock_minio_class):
        """Should generate presigned URL with custom expiry time."""
        # Arrange
        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_client_instance.presigned_get_object.return_value = "https://minio.example.com/presigned-url"
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()
        object_name = "org_123/photos/photo_789/image.jpg"
        custom_expiry = 7200  # 2 hours

        # Act
        result = client.generate_presigned_url(object_name, expiry_seconds=custom_expiry)

        # Assert
        from datetime import timedelta
        call_args = mock_client_instance.presigned_get_object.call_args
        assert call_args[1]['expires'] == timedelta(seconds=custom_expiry)

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_generate_presigned_url_handles_errors(self, mock_minio_class):
        """Should handle errors during presigned URL generation."""
        # Arrange
        from minio.error import S3Error

        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_client_instance.presigned_get_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="/test/file.pdf",
            request_id="123",
            host_id="456",
            response="error"
        )
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()

        # Act & Assert
        with pytest.raises(Exception):
            client.generate_presigned_url("nonexistent/file.pdf")


class TestMinIOClientMetadata:
    """Test file metadata operations."""

    @patch('app.infrastructure.storage.minio_client.Minio')
    def test_get_file_metadata(self, mock_minio_class):
        """Should retrieve file metadata from MinIO."""
        # Arrange
        mock_stat = Mock()
        mock_stat.size = 1024
        mock_stat.content_type = "application/pdf"
        mock_stat.last_modified = "2024-11-08T10:00:00Z"
        mock_stat.etag = "abc123"

        mock_client_instance = Mock()
        mock_client_instance.bucket_exists.return_value = True
        mock_client_instance.stat_object.return_value = mock_stat
        mock_minio_class.return_value = mock_client_instance

        client = MinIOClient()
        object_name = "org_123/documents/doc_456/test.pdf"

        # Act
        metadata = client.get_file_metadata(object_name)

        # Assert
        mock_client_instance.stat_object.assert_called_once_with(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name
        )
        assert metadata['size'] == 1024
        assert metadata['content_type'] == "application/pdf"
        assert 'last_modified' in metadata
        assert 'etag' in metadata
