import pytest
from app.core.config import Settings


class TestConfigurationSettings:
    """Test suite for configuration settings validation."""

    def test_redis_configuration_removed(self):
        """Verify Redis configuration has been removed."""
        settings = Settings()

        # These attributes should not exist
        assert not hasattr(settings, 'REDIS_HOST'), "REDIS_HOST should be removed"
        assert not hasattr(settings, 'REDIS_PORT'), "REDIS_PORT should be removed"

    def test_pgmq_configuration_exists(self):
        """Verify PGMQ (PostgreSQL Message Queue) settings are present."""
        settings = Settings()

        # PGMQ settings should exist
        assert hasattr(settings, 'PGMQ_QUEUE_PREFIX'), "PGMQ_QUEUE_PREFIX must be configured"
        assert hasattr(settings, 'PGMQ_RETRY_COUNT'), "PGMQ_RETRY_COUNT must be configured"
        assert hasattr(settings, 'PGMQ_VISIBILITY_TIMEOUT'), "PGMQ_VISIBILITY_TIMEOUT must be configured"

        # Validate default values
        assert settings.PGMQ_QUEUE_PREFIX == "unison"
        assert settings.PGMQ_RETRY_COUNT == 3
        assert settings.PGMQ_VISIBILITY_TIMEOUT == 30

    def test_minio_configuration_exists(self):
        """Verify MinIO object storage settings are present."""
        settings = Settings()

        # MinIO settings should exist
        assert hasattr(settings, 'MINIO_ENDPOINT'), "MINIO_ENDPOINT must be configured"
        assert hasattr(settings, 'MINIO_ACCESS_KEY'), "MINIO_ACCESS_KEY must be configured"
        assert hasattr(settings, 'MINIO_SECRET_KEY'), "MINIO_SECRET_KEY must be configured"
        assert hasattr(settings, 'MINIO_BUCKET'), "MINIO_BUCKET must be configured"
        assert hasattr(settings, 'MINIO_SECURE'), "MINIO_SECURE must be configured"

        # Validate default values
        assert settings.MINIO_ENDPOINT == "localhost:9000"
        assert settings.MINIO_BUCKET == "unison-storage"
        assert settings.MINIO_SECURE is False

    def test_email_adapter_configuration_exists(self):
        """Verify email service adapter settings are present."""
        settings = Settings()

        # Email provider settings should exist
        assert hasattr(settings, 'EMAIL_PROVIDER'), "EMAIL_PROVIDER must be configured"

        # SMTP settings
        assert hasattr(settings, 'SMTP_HOST'), "SMTP_HOST must be configured"
        assert hasattr(settings, 'SMTP_PORT'), "SMTP_PORT must be configured"
        assert hasattr(settings, 'SMTP_USER'), "SMTP_USER must be configured"
        assert hasattr(settings, 'SMTP_PASSWORD'), "SMTP_PASSWORD must be configured"
        assert hasattr(settings, 'SMTP_TLS'), "SMTP_TLS must be configured"

        # SendGrid settings
        assert hasattr(settings, 'SENDGRID_API_KEY'), "SENDGRID_API_KEY must be configured"

        # AWS SES settings
        assert hasattr(settings, 'AWS_SES_REGION'), "AWS_SES_REGION must be configured"
        assert hasattr(settings, 'AWS_SES_ACCESS_KEY'), "AWS_SES_ACCESS_KEY must be configured"
        assert hasattr(settings, 'AWS_SES_SECRET_KEY'), "AWS_SES_SECRET_KEY must be configured"

        # Validate defaults
        assert settings.EMAIL_PROVIDER == "smtp"
        assert settings.SMTP_PORT == 587
        assert settings.SMTP_TLS is True

    def test_multi_currency_configuration_exists(self):
        """Verify multi-currency support settings are present."""
        settings = Settings()

        # Multi-currency settings should exist
        assert hasattr(settings, 'DEFAULT_CURRENCY'), "DEFAULT_CURRENCY must be configured"
        assert hasattr(settings, 'EXCHANGE_RATE_API_KEY'), "EXCHANGE_RATE_API_KEY must be configured"
        assert hasattr(settings, 'EXCHANGE_RATE_API_URL'), "EXCHANGE_RATE_API_URL must be configured"

        # Validate defaults
        assert settings.DEFAULT_CURRENCY == "USD"
        assert settings.EXCHANGE_RATE_API_URL == "https://api.exchangerate-api.com/v4/latest"

    def test_rls_configuration_exists(self):
        """Verify Row-Level Security (RLS) settings are present."""
        settings = Settings()

        # RLS settings should exist
        assert hasattr(settings, 'RLS_ENABLED'), "RLS_ENABLED must be configured"
        assert hasattr(settings, 'RLS_AUDIT_LOG_ENABLED'), "RLS_AUDIT_LOG_ENABLED must be configured"

        # Validate defaults
        assert settings.RLS_ENABLED is True
        assert settings.RLS_AUDIT_LOG_ENABLED is True

    def test_existing_configuration_preserved(self):
        """Verify existing configuration settings are preserved."""
        settings = Settings()

        # Core settings should still exist
        assert hasattr(settings, 'PROJECT_NAME')
        assert hasattr(settings, 'VERSION')
        assert hasattr(settings, 'API_V1_STR')

        # Database settings should still exist
        assert hasattr(settings, 'POSTGRES_SERVER')
        assert hasattr(settings, 'POSTGRES_USER')
        assert hasattr(settings, 'POSTGRES_PASSWORD')
        assert hasattr(settings, 'POSTGRES_DB')
        assert hasattr(settings, 'POSTGRES_PORT')
        assert hasattr(settings, 'DATABASE_URL')

        # JWT settings should still exist
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'ALGORITHM')
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')

        # CORS settings should still exist
        assert hasattr(settings, 'BACKEND_CORS_ORIGINS')

    def test_configuration_grouping(self):
        """Verify configuration settings are logically grouped."""
        settings = Settings()

        # This is a structural test - we verify that related settings exist together
        # PGMQ group
        pgmq_settings = ['PGMQ_QUEUE_PREFIX', 'PGMQ_RETRY_COUNT', 'PGMQ_VISIBILITY_TIMEOUT']
        for setting in pgmq_settings:
            assert hasattr(settings, setting), f"PGMQ setting {setting} missing"

        # MinIO group
        minio_settings = ['MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'MINIO_BUCKET']
        for setting in minio_settings:
            assert hasattr(settings, setting), f"MinIO setting {setting} missing"

        # Email group
        email_settings = ['EMAIL_PROVIDER', 'SMTP_HOST', 'SMTP_PORT']
        for setting in email_settings:
            assert hasattr(settings, setting), f"Email setting {setting} missing"

        # Currency group
        currency_settings = ['DEFAULT_CURRENCY', 'EXCHANGE_RATE_API_KEY']
        for setting in currency_settings:
            assert hasattr(settings, setting), f"Currency setting {setting} missing"

        # RLS group
        rls_settings = ['RLS_ENABLED', 'RLS_AUDIT_LOG_ENABLED']
        for setting in rls_settings:
            assert hasattr(settings, setting), f"RLS setting {setting} missing"

    def test_email_provider_validation(self):
        """Verify EMAIL_PROVIDER only accepts valid values."""
        settings = Settings()

        # Valid providers
        valid_providers = ["smtp", "sendgrid", "aws_ses"]
        assert settings.EMAIL_PROVIDER in valid_providers

        # The Literal type hint ensures type safety at development time
        # Runtime validation is handled by Pydantic
