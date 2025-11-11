"""
Audit Logger for Platform Admin Actions

Provides structured logging of all admin actions to database for
security auditing, compliance, and accountability.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from app.models.admin_audit_log import AdminAuditLogModel

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Service for logging and retrieving admin audit logs

    All platform admin actions should be logged including:
    - Organization management (activate/deactivate)
    - Subscription changes (trial extension, suspension, reactivation)
    - User impersonation
    - Data access and exports
    - Configuration changes

    Audit logs are immutable and retained for compliance.
    """

    def __init__(self, db: Session):
        """
        Initialize audit logger

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def log_action(
        self,
        admin_user_id: int,
        action: str,
        target_type: str,
        target_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AdminAuditLogModel:
        """
        Log an admin action to database

        Args:
            admin_user_id: ID of admin user performing action
            action: Action performed (e.g., "suspend_subscription", "extend_trial")
            target_type: Type of resource (e.g., "organization", "subscription", "user")
            target_id: ID of affected resource (optional)
            details: Additional context as JSON (optional)

        Returns:
            AdminAuditLogModel: Created audit log entry

        Example:
            ```python
            audit_logger.log_action(
                admin_user_id=admin.id,
                action="suspend_subscription",
                target_type="subscription",
                target_id=123,
                details={
                    "reason": "Payment fraud detected",
                    "previous_status": "active",
                    "new_status": "suspended"
                }
            )
            ```
        """
        try:
            audit_log = AdminAuditLogModel(
                admin_user_id=admin_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details or {}
            )

            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)

            logger.info(
                f"Audit log created: action={action}, "
                f"admin_user_id={admin_user_id}, "
                f"target={target_type}:{target_id}"
            )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            self.db.rollback()
            # Don't raise - audit logging should never break the operation
            return None

    def get_logs(
        self,
        admin_user_id: Optional[int] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[AdminAuditLogModel], int]:
        """
        Query audit logs with filters

        Args:
            admin_user_id: Filter by admin user
            action: Filter by action type
            target_type: Filter by target type
            target_id: Filter by specific target ID
            limit: Maximum results (default 100)
            offset: Pagination offset (default 0)

        Returns:
            tuple: (list of audit logs, total count)

        Example:
            ```python
            # Get all subscription actions
            logs, count = audit_logger.get_logs(
                target_type="subscription",
                limit=50
            )

            # Get all actions by specific admin
            logs, count = audit_logger.get_logs(
                admin_user_id=5,
                limit=100
            )
            ```
        """
        try:
            query = self.db.query(AdminAuditLogModel)

            # Apply filters
            if admin_user_id is not None:
                query = query.filter(AdminAuditLogModel.admin_user_id == admin_user_id)

            if action is not None:
                query = query.filter(AdminAuditLogModel.action == action)

            if target_type is not None:
                query = query.filter(AdminAuditLogModel.target_type == target_type)

            if target_id is not None:
                query = query.filter(AdminAuditLogModel.target_id == target_id)

            # Get total count before pagination
            total_count = query.count()

            # Apply pagination and ordering
            logs = query.order_by(desc(AdminAuditLogModel.created_at)) \
                       .limit(limit) \
                       .offset(offset) \
                       .all()

            return logs, total_count

        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}", exc_info=True)
            return [], 0

    def get_user_activity(
        self,
        admin_user_id: int,
        days: int = 30,
        limit: int = 100
    ) -> List[AdminAuditLogModel]:
        """
        Get recent activity for a specific admin user

        Args:
            admin_user_id: Admin user ID
            days: Number of days to look back (default 30)
            limit: Maximum results (default 100)

        Returns:
            List of audit log entries
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            logs = self.db.query(AdminAuditLogModel) \
                         .filter(AdminAuditLogModel.admin_user_id == admin_user_id) \
                         .filter(AdminAuditLogModel.created_at >= cutoff_date) \
                         .order_by(desc(AdminAuditLogModel.created_at)) \
                         .limit(limit) \
                         .all()

            return logs

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}", exc_info=True)
            return []

    def get_resource_history(
        self,
        target_type: str,
        target_id: int,
        limit: int = 50
    ) -> List[AdminAuditLogModel]:
        """
        Get complete history of admin actions on a specific resource

        Useful for:
        - Tracking organization changes over time
        - Subscription status history
        - Compliance audits

        Args:
            target_type: Type of resource (e.g., "organization", "subscription")
            target_id: Resource ID
            limit: Maximum results (default 50)

        Returns:
            List of audit log entries in reverse chronological order
        """
        try:
            logs = self.db.query(AdminAuditLogModel) \
                         .filter(and_(
                             AdminAuditLogModel.target_type == target_type,
                             AdminAuditLogModel.target_id == target_id
                         )) \
                         .order_by(desc(AdminAuditLogModel.created_at)) \
                         .limit(limit) \
                         .all()

            return logs

        except Exception as e:
            logger.error(f"Failed to get resource history: {e}", exc_info=True)
            return []

    def get_action_count(
        self,
        admin_user_id: Optional[int] = None,
        action: Optional[str] = None,
        days: int = 30
    ) -> int:
        """
        Count admin actions within time period

        Useful for:
        - Activity monitoring
        - Rate limiting decisions
        - Usage analytics

        Args:
            admin_user_id: Filter by admin (optional)
            action: Filter by action type (optional)
            days: Number of days to look back (default 30)

        Returns:
            Count of matching actions
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(AdminAuditLogModel) \
                          .filter(AdminAuditLogModel.created_at >= cutoff_date)

            if admin_user_id is not None:
                query = query.filter(AdminAuditLogModel.admin_user_id == admin_user_id)

            if action is not None:
                query = query.filter(AdminAuditLogModel.action == action)

            return query.count()

        except Exception as e:
            logger.error(f"Failed to count actions: {e}", exc_info=True)
            return 0
