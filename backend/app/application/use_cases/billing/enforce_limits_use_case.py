"""
Use Case: Enforce Limits

Validates resource creation requests against subscription limits.
Called before creating users, plants, or uploading files.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

from app.application.services.usage_tracking_service import UsageTrackingService
from app.application.services.subscription_service import SubscriptionService
from app.core.exceptions import BusinessRuleException
from app.domain.entities.subscription import SubscriptionStatus


logger = logging.getLogger(__name__)


class EnforceLimitsUseCase:
    """
    Use Case: Enforce Subscription Limits

    Responsibilities:
    1. Check if operation would exceed limits
    2. Provide upgrade suggestions
    3. Block operations that exceed limits

    Single Responsibility: Limit enforcement logic
    """

    def __init__(self, db: Session):
        """
        Initialize use case

        Args:
            db: Database session
        """
        self.db = db
        self.usage_service = UsageTrackingService(db)
        self.subscription_service = SubscriptionService(db)

    def can_add_user(self, organization_id: int) -> Dict[str, Any]:
        """
        Check if organization can add a new user

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary with permission and details:
            {
                "allowed": True/False,
                "reason": "...",
                "current_users": 5,
                "max_users": 10,
                "available_slots": 5
            }

        Raises:
            BusinessRuleException: If subscription is not active
        """
        self._validate_subscription_active(organization_id)

        can_add = self.usage_service.can_add_user(organization_id)
        limits = self.subscription_service.get_total_limits_with_addons(organization_id)
        current_users = self.usage_service.calculate_users_count(organization_id)

        result = {
            "allowed": can_add,
            "current_users": current_users,
            "max_users": limits.max_users,
        }

        if limits.max_users is None:
            result["reason"] = "Unlimited users (Enterprise tier)"
            result["available_slots"] = "unlimited"
        elif can_add:
            result["available_slots"] = limits.max_users - current_users
            result["reason"] = f"Within user limit ({current_users}/{limits.max_users})"
        else:
            result["available_slots"] = 0
            result["reason"] = f"User limit reached ({current_users}/{limits.max_users})"
            result["upgrade_suggestion"] = self._get_upgrade_suggestion(organization_id, "users")

        return result

    def can_add_plant(self, organization_id: int) -> Dict[str, Any]:
        """
        Check if organization can add a new plant

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary with permission and details
        """
        self._validate_subscription_active(organization_id)

        can_add = self.usage_service.can_add_plant(organization_id)
        limits = self.subscription_service.get_total_limits_with_addons(organization_id)
        current_plants = self.usage_service.calculate_plants_count(organization_id)

        result = {
            "allowed": can_add,
            "current_plants": current_plants,
            "max_plants": limits.max_plants,
        }

        if limits.max_plants is None:
            result["reason"] = "Unlimited plants (Enterprise tier)"
            result["available_slots"] = "unlimited"
        elif can_add:
            result["available_slots"] = limits.max_plants - current_plants
            result["reason"] = f"Within plant limit ({current_plants}/{limits.max_plants})"
        else:
            result["available_slots"] = 0
            result["reason"] = f"Plant limit reached ({current_plants}/{limits.max_plants})"
            result["upgrade_suggestion"] = self._get_upgrade_suggestion(organization_id, "plants")

        return result

    def can_upload_file(
        self,
        organization_id: int,
        file_size_bytes: int
    ) -> Dict[str, Any]:
        """
        Check if organization can upload a file

        Args:
            organization_id: Organization ID
            file_size_bytes: Size of file to upload in bytes

        Returns:
            Dictionary with permission and details
        """
        self._validate_subscription_active(organization_id)

        limits = self.subscription_service.get_total_limits_with_addons(organization_id)
        current_storage_gb = self.usage_service.calculate_storage_used(organization_id)
        file_size_gb = Decimal(file_size_bytes) / Decimal("1073741824")

        result = {
            "allowed": False,
            "current_storage_gb": float(current_storage_gb),
            "file_size_gb": float(file_size_gb),
            "storage_limit_gb": limits.storage_limit_gb,
        }

        if limits.storage_limit_gb is None:
            result["allowed"] = True
            result["reason"] = "Unlimited storage (Enterprise tier)"
            result["available_storage_gb"] = "unlimited"
        else:
            new_total = current_storage_gb + file_size_gb
            available = Decimal(limits.storage_limit_gb) - current_storage_gb

            if new_total <= limits.storage_limit_gb:
                result["allowed"] = True
                result["available_storage_gb"] = float(available)
                result["reason"] = f"Within storage limit ({float(new_total):.2f}GB/{limits.storage_limit_gb}GB)"
            else:
                result["available_storage_gb"] = float(available)
                result["reason"] = f"Storage limit exceeded. File would use {float(new_total):.2f}GB of {limits.storage_limit_gb}GB"
                result["upgrade_suggestion"] = self._get_upgrade_suggestion(organization_id, "storage")

        return result

    def enforce_user_limit(self, organization_id: int) -> None:
        """
        Enforce user limit before creating user

        Args:
            organization_id: Organization ID

        Raises:
            BusinessRuleException: If user limit would be exceeded
        """
        result = self.can_add_user(organization_id)

        if not result["allowed"]:
            raise BusinessRuleException(
                f"Cannot add user: {result['reason']}. "
                f"{result.get('upgrade_suggestion', 'Please upgrade your subscription.')}"
            )

    def enforce_plant_limit(self, organization_id: int) -> None:
        """
        Enforce plant limit before creating plant

        Args:
            organization_id: Organization ID

        Raises:
            BusinessRuleException: If plant limit would be exceeded
        """
        result = self.can_add_plant(organization_id)

        if not result["allowed"]:
            raise BusinessRuleException(
                f"Cannot add plant: {result['reason']}. "
                f"{result.get('upgrade_suggestion', 'Please upgrade your subscription.')}"
            )

    def enforce_storage_limit(
        self,
        organization_id: int,
        file_size_bytes: int
    ) -> None:
        """
        Enforce storage limit before file upload

        Args:
            organization_id: Organization ID
            file_size_bytes: File size in bytes

        Raises:
            BusinessRuleException: If storage limit would be exceeded
        """
        result = self.can_upload_file(organization_id, file_size_bytes)

        if not result["allowed"]:
            raise BusinessRuleException(
                f"Cannot upload file: {result['reason']}. "
                f"{result.get('upgrade_suggestion', 'Please upgrade your subscription.')}"
            )

    def _validate_subscription_active(self, organization_id: int) -> None:
        """
        Validate subscription is in active state

        Args:
            organization_id: Organization ID

        Raises:
            BusinessRuleException: If subscription is not active
        """
        subscription = self.subscription_service.get_subscription(organization_id)

        if subscription.status not in [
            SubscriptionStatus.TRIAL.value,
            SubscriptionStatus.ACTIVE.value
        ]:
            raise BusinessRuleException(
                f"Your subscription is {subscription.status}. "
                "Please update your payment method or contact support."
            )

    def _get_upgrade_suggestion(
        self,
        organization_id: int,
        resource: str
    ) -> str:
        """
        Get upgrade suggestion based on current tier and resource

        Args:
            organization_id: Organization ID
            resource: "users", "plants", or "storage"

        Returns:
            Upgrade suggestion message
        """
        from app.domain.entities.subscription import SubscriptionTier

        subscription = self.subscription_service.get_subscription(organization_id)
        current_tier = SubscriptionTier(subscription.tier)

        if current_tier == SubscriptionTier.STARTER:
            return (
                f"Upgrade to Professional tier for more {resource}, "
                "or purchase add-ons to increase your limit."
            )
        elif current_tier == SubscriptionTier.PROFESSIONAL:
            return (
                f"Upgrade to Enterprise tier for unlimited {resource}, "
                "or purchase add-ons to increase your limit."
            )
        else:
            return "Contact your account manager to discuss your needs."

    def get_all_limits_status(self, organization_id: int) -> Dict[str, Any]:
        """
        Get comprehensive status of all resource limits

        Args:
            organization_id: Organization ID

        Returns:
            Dictionary with all limit statuses
        """
        subscription = self.subscription_service.get_subscription(organization_id)
        usage_summary = self.usage_service.get_usage_summary(organization_id)

        return {
            "organization_id": organization_id,
            "subscription_tier": subscription.tier,
            "subscription_status": subscription.status,
            "users": self.can_add_user(organization_id),
            "plants": self.can_add_plant(organization_id),
            "storage": {
                "current_gb": usage_summary["usage"]["storage_gb"],
                "limit_gb": usage_summary["limits"]["storage_limit_gb"],
                "has_available": self.usage_service.has_storage_available(organization_id),
                "percentage": usage_summary["usage_percentages"]["storage_pct"]
            },
            "overall_status": {
                "within_limits": usage_summary["within_limits"],
                "violations": usage_summary["violations"]
            }
        }
