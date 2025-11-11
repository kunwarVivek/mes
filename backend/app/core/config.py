from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Literal

class Settings(BaseSettings):
    PROJECT_NAME: str = "Unison API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "unison"
    POSTGRES_PASSWORD: str = "unison_dev_password"
    POSTGRES_DB: str = "unison_erp"
    POSTGRES_PORT: str = "5432"

    DATABASE_URL: str = ""

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # PGMQ (PostgreSQL Message Queue) Configuration
    PGMQ_QUEUE_PREFIX: str = "unison"
    PGMQ_RETRY_COUNT: int = 3
    PGMQ_VISIBILITY_TIMEOUT: int = 30

    # MinIO Object Storage Configuration
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "unison-storage"
    MINIO_SECURE: bool = False

    # Email Service Adapter Configuration
    EMAIL_PROVIDER: Literal["smtp", "sendgrid", "aws_ses"] = "smtp"

    # SMTP Settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True

    # SendGrid Settings
    SENDGRID_API_KEY: str = ""

    # AWS SES Settings
    AWS_SES_REGION: str = "us-east-1"
    AWS_SES_ACCESS_KEY: str = ""
    AWS_SES_SECRET_KEY: str = ""

    # Multi-Currency Configuration
    DEFAULT_CURRENCY: str = "USD"
    EXCHANGE_RATE_API_KEY: str = ""
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate-api.com/v4/latest"

    # Stripe Payment Configuration
    STRIPE_SECRET_KEY: str = ""  # sk_test_... or sk_live_...
    STRIPE_PUBLISHABLE_KEY: str = ""  # pk_test_... or pk_live_...
    STRIPE_WEBHOOK_SECRET: str = ""  # whsec_...
    STRIPE_CHECKOUT_SUCCESS_URL: str = "http://localhost:3000/billing/success"
    STRIPE_CHECKOUT_CANCEL_URL: str = "http://localhost:3000/billing/cancel"

    # Row-Level Security (RLS) Configuration
    RLS_ENABLED: bool = True
    RLS_AUDIT_LOG_ENABLED: bool = True

    # JWT Configuration
    # SECURITY WARNING: Override this in production via environment variable
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars-required"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        Validate SECRET_KEY for production security.

        Requirements:
        - Must not be the default value
        - Must be at least 32 characters long

        Raises:
            ValueError: If SECRET_KEY is default or too short
        """
        if v == "your-secret-key-change-in-production":
            raise ValueError(
                "SECRET_KEY cannot use default value in production. "
                "Set a strong secret key via environment variable or .env file."
            )

        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters long for security. "
                f"Current length: {len(v)}"
            )

        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
