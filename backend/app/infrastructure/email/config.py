"""Billion Mail email configuration."""
from typing import Optional
from pydantic import BaseModel


class BillionMailConfig(BaseModel):
    """Configuration for Billion Mail SMTP integration.

    Settings specific to Billion Mail self-hosted email server.
    These can be overridden via environment variables.
    """

    # SMTP Server Settings
    host: str = "localhost"
    port: int = 587
    user: str = ""
    password: str = ""
    use_tls: bool = True

    # Email Defaults
    default_from_email: Optional[str] = None
    default_from_name: str = "Unison ERP"

    # PGMQ Queue Settings
    email_queue_name: str = "email_notifications"
    retry_count: int = 3
    visibility_timeout: int = 30

    # Email Behavior
    send_async: bool = True  # Default to async via PGMQ
    enable_audit_log: bool = True  # Track all sent emails

    class Config:
        """Pydantic configuration."""
        env_prefix = "BILLION_MAIL_"
