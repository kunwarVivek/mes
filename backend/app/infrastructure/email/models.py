"""Email models and DTOs for Billion Mail integration."""
from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class EmailRecipient(BaseModel):
    """Email recipient DTO."""
    email: EmailStr
    name: str


class EmailAttachment(BaseModel):
    """Email attachment DTO."""
    filename: str
    content: bytes
    content_type: str


class EmailMessage(BaseModel):
    """Email message DTO with support for text, HTML, and attachments."""
    to: EmailRecipient
    subject: str
    body_text: str
    body_html: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    attachments: List[EmailAttachment] = Field(default_factory=list)


class EmailStatus(str, Enum):
    """Email delivery status for audit tracking."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class EmailAuditLog(BaseModel):
    """Email audit log for tracking sent emails."""
    recipient_email: str
    subject: str
    status: EmailStatus
    queue_msg_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
