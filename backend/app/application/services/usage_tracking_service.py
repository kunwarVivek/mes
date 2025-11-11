"""
Usage Tracking Service - Monitor resource consumption and enforce limits

Tracks organization resource usage (users, plants, storage) and compares
against subscription limits to enforce quota restrictions.
"""
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from decimal import Decimal
import logging

from app.models.subscription import SubscriptionModel, SubscriptionUsageModel
from app.infrastructure.persistence.models import UserModel
from app.models.plant import Plant
from app.models.infrastructure import FileUpload
from app.domain.entities.subscription import (
    CurrentUsage,
    LimitViolation,
    UsageLimits
)
from app.core.exceptions import ResourceNotFoundException
from app.application.services.subscription_service import SubscriptionService


logger = logging.getLogger(__name__)


class UsageTrackingService:
    """
    Service for tracking and enforcing resource usage limits

    Dependency Injection: Inject SQLAlchemy session
    """

    def __init__(self, db: Session):
        """
        Initialize usage tracking service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.subscription_service = SubscriptionService(db)

    def track_usage(self, organization_id: int) -> SubscriptionUsageModel:
        """
        Calculate current usage and store in database

        Args:
            organization_id: Organization ID

        Returns:
            Created SubscriptionUsageModel

        Raises:
            ResourceNotFoundException: If organization not found
        """
        # Calculate current usage
        users_count = self.calculate_users_count(organization_id)
        plants_count = self.calculate_plants_count(organization_id)
        storage_gb = self.calculate_storage_used(organization_id)

        # Create usage record
        usage = SubscriptionUsageModel(
            organization_id=organization_id,
            current_users=users_count,
            current_plants=plants_count,
            storage_used_gb=storage_gb,
            measured_at=datetime.utcnow()
        )

        self.db.add(usage)
        self.db.commit()

        logger.info(
            f"Tracked usage for organization {organization_id}: "
            f"users={users_count}, plants={plants_count}, storage={storage_gb}GB"
        )

        return usage

    def get_current_usage(self, organization_id: int) -> Optional[CurrentUsage]:
        """
        Get latest usage record for an organization

        Args:
            organization_id: Organization ID

        Returns:
            CurrentUsage domain entity, or None if no usage recorded
        """
        usage_model = self.db.query(SubscriptionUsageModel).filter(
            SubscriptionUsageModel.organization_id == organization_id
        ).order_by(SubscriptionUsageModel.measured_at.desc()).first()

        if not usage_model:
            # If no usage recorded, calculate live
            return CurrentUsage(
                current_users=self.calculate_users_count(organization_id),
                current_plants=self.calculate_plants_count(organization_id),
                storage_used_gb=self.calculate_storage_used(organization_id),
                measured_at=datetime.utcnow()
            )

        return CurrentUsage(
            current_users=usage_model.current_users,
            current_plants=usage_model.current_plants,
            storage_used_gb=Decimal(str(usage_model.storage_used_gb)),
            measured_at=usage_model.measured_at
        )

    def is_within_limits(self, organization_id: int) -> bool:
        """
        Check if organization is within subscription limits

        Args:
            organization_id: Organization ID

        Returns:
            True if within limits, False otherwise
        """
        violations = self.get_limit_violations(organization_id)
        return len(violations) == 0

    def get_limit_violations(self, organization_id: int) -> List[LimitViolation]:
        """
        Get list of resources exceeding subscription limits

        Args:
            organization_id: Organization ID

        Returns:
            List of LimitViolation objects (empty if within limits)

        Raises:
            ResourceNotFoundException: If subscription not found
        """
        # Get subscription with add-ons
        subscription = self.subscription_service.get_subscription(organization_id)
        total_limits = self.subscription_service.get_total_limits_with_addons(organization_id)

        # Get current usage
        usage = self.get_current_usage(organization_id)
        if not usage:
            return []

        violations: List[LimitViolation] = []

        # Check user limit
        if total_limits.max_users is not None and usage.current_users > total_limits.max_users:
            violations.append(LimitViolation(
                resource="users",
                limit=total_limits.max_users,
                current=usage.current_users,
                overage=usage.current_users - total_limits.max_users
            ))

        # Check plant limit
        if total_limits.max_plants is not None and usage.current_plants > total_limits.max_plants:
            violations.append(LimitViolation(
                resource="plants",
                limit=total_limits.max_plants,
                current=usage.current_plants,
                overage=usage.current_plants - total_limits.max_plants
            ))

        # Check storage limit
        if total_limits.storage_limit_gb is not None:
            storage_used = int(usage.storage_used_gb)
            if storage_used > total_limits.storage_limit_gb:
                violations.append(LimitViolation(
                    resource="storage",
                    limit=total_limits.storage_limit_gb,
                    current=storage_used,
                    overage=storage_used - total_limits.storage_limit_gb
                ))

        if violations:
            logger.warning(
                f"Limit violations for organization {organization_id}: "
                f"{[v.resource for v in violations]}"
            )

        return violations

    def can_add_user(self, organization_id: int) -> bool:
        """
        Check if organization can add another user

        Args:
            organization_id: Organization ID

        Returns:
            True if user can be added, False otherwise
        """
        total_limits = self.subscription_service.get_total_limits_with_addons(organization_id)

        # Unlimited users (Enterprise)
        if total_limits.max_users is None:
            return True

        current_users = self.calculate_users_count(organization_id)
        return current_users < total_limits.max_users

    def can_add_plant(self, organization_id: int) -> bool:
        """
        Check if organization can add another plant

        Args:
            organization_id: Organization ID

        Returns:
            True if plant can be added, False otherwise
        """
        total_limits = self.subscription_service.get_total_limits_with_addons(organization_id)

        # Unlimited plants (Enterprise)
        if total_limits.max_plants is None:
            return True

        current_plants = self.calculate_plants_count(organization_id)
        return current_plants < total_limits.max_plants

    def has_storage_available(self, organization_id: int) -> bool:
        """
        Check if organization has storage capacity available

        Args:
            organization_id: Organization ID

        Returns:
            True if storage is available, False otherwise
        """
        total_limits = self.subscription_service.get_total_limits_with_addons(organization_id)

        # Unlimited storage (Enterprise)
        if total_limits.storage_limit_gb is None:
            return True

        storage_used = self.calculate_storage_used(organization_id)
        return float(storage_used) < total_limits.storage_limit_gb

    def calculate_users_count(self, organization_id: int) -> int:
        """
        Calculate number of active users in organization

        Args:
            organization_id: Organization ID

        Returns:
            Count of active users
        """
        count = self.db.query(func.count(UserModel.id)).filter(
            and_(
                UserModel.organization_id == organization_id,
                UserModel.is_active == True
            )
        ).scalar()

        return count or 0

    def calculate_plants_count(self, organization_id: int) -> int:
        """
        Calculate number of active plants in organization

        Args:
            organization_id: Organization ID

        Returns:
            Count of active plants
        """
        count = self.db.query(func.count(Plant.id)).filter(
            and_(
                Plant.organization_id == organization_id,
                Plant.is_active == True
            )
        ).scalar()

        return count or 0

    def calculate_storage_used(self, organization_id: int) -> Decimal:
        """
        Calculate total storage used in GB

        Args:
            organization_id: Organization ID

        Returns:
            Storage used in GB (Decimal)
        """
        total_bytes = self.db.query(
            func.coalesce(func.sum(FileUpload.file_size_bytes), 0)
        ).filter(
            FileUpload.organization_id == organization_id
        ).scalar()

        # Convert bytes to GB
        gb = Decimal(str(total_bytes or 0)) / Decimal("1073741824")  # 1024^3
        return gb.quantize(Decimal("0.01"))  # Round to 2 decimal places

    def get_usage_percentage(self, organization_id: int) -> Dict[str, any]:
        """
        Get usage as percentage of limits

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary with usage percentages for each resource
        """
        total_limits = self.subscription_service.get_total_limits_with_addons(organization_id)
        usage = self.get_current_usage(organization_id)

        if not usage:
            return {
                "users_pct": 0,
                "plants_pct": 0,
                "storage_pct": 0
            }

        result = {}

        # Users percentage
        if total_limits.max_users is None:
            result["users_pct"] = "unlimited"
            result["users_usage"] = usage.current_users
        else:
            result["users_pct"] = round(
                (usage.current_users / total_limits.max_users) * 100, 1
            )
            result["users_usage"] = f"{usage.current_users}/{total_limits.max_users}"

        # Plants percentage
        if total_limits.max_plants is None:
            result["plants_pct"] = "unlimited"
            result["plants_usage"] = usage.current_plants
        else:
            result["plants_pct"] = round(
                (usage.current_plants / total_limits.max_plants) * 100, 1
            )
            result["plants_usage"] = f"{usage.current_plants}/{total_limits.max_plants}"

        # Storage percentage
        if total_limits.storage_limit_gb is None:
            result["storage_pct"] = "unlimited"
            result["storage_usage"] = f"{usage.storage_used_gb}GB"
        else:
            result["storage_pct"] = round(
                (float(usage.storage_used_gb) / total_limits.storage_limit_gb) * 100, 1
            )
            result["storage_usage"] = f"{usage.storage_used_gb}GB/{total_limits.storage_limit_gb}GB"

        return result

    def get_usage_summary(self, organization_id: int) -> Dict[str, any]:
        """
        Get comprehensive usage summary

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary with usage details, limits, and violations
        """
        subscription = self.subscription_service.get_subscription(organization_id)
        total_limits = self.subscription_service.get_total_limits_with_addons(organization_id)
        usage = self.get_current_usage(organization_id)
        violations = self.get_limit_violations(organization_id)
        percentages = self.get_usage_percentage(organization_id)

        return {
            "organization_id": organization_id,
            "subscription_tier": subscription.tier,
            "subscription_status": subscription.status,
            "usage": {
                "users": usage.current_users if usage else 0,
                "plants": usage.current_plants if usage else 0,
                "storage_gb": float(usage.storage_used_gb) if usage else 0.0,
                "measured_at": usage.measured_at.isoformat() if usage else None
            },
            "limits": {
                "max_users": total_limits.max_users,
                "max_plants": total_limits.max_plants,
                "storage_limit_gb": total_limits.storage_limit_gb
            },
            "usage_percentages": percentages,
            "within_limits": len(violations) == 0,
            "violations": [
                {
                    "resource": v.resource,
                    "limit": v.limit,
                    "current": v.current,
                    "overage": v.overage,
                    "message": v.get_message()
                }
                for v in violations
            ]
        }
