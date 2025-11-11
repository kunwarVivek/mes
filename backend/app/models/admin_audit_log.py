"""
SQLAlchemy model for Admin Audit Logs

Tracks all platform admin actions for security, compliance, and accountability.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base


class AdminAuditLogModel(Base):
    """
    Admin audit log model - Security and compliance tracking

    Records every action performed by platform admins including:
    - Organization management (activate/deactivate)
    - Subscription changes (extend trial, suspend, reactivate)
    - User impersonation for support
    - Metrics and data access

    Business Rules:
    - Immutable records (no updates/deletes after creation)
    - Retained indefinitely for compliance
    - Indexed for fast querying by admin, organization, action
    """
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True)

    # Admin performing action
    admin_user_id = Column(Integer, nullable=False, index=True)

    # Action details
    action = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)  # organization, subscription, user, etc.
    target_id = Column(Integer, nullable=True, index=True)  # ID of affected resource

    # Additional context (JSON for flexibility)
    details = Column(JSON, nullable=True)

    # Timestamp (immutable)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index('idx_audit_admin_user', 'admin_user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_target', 'target_type', 'target_id'),
        Index('idx_audit_created', 'created_at'),
        Index('idx_audit_admin_action', 'admin_user_id', 'action'),  # Composite for user activity
    )

    def __repr__(self):
        return (
            f"<AdminAuditLog(admin_user_id={self.admin_user_id}, "
            f"action='{self.action}', target={self.target_type}:{self.target_id})>"
        )
