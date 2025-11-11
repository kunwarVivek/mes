"""
Use Case: Track Usage

Calculates and records resource usage for organizations.
Typically called by a scheduled job (e.g., every 6 hours).
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.subscription import SubscriptionModel
from app.domain.entities.subscription import SubscriptionStatus
from app.application.services.usage_tracking_service import UsageTrackingService


logger = logging.getLogger(__name__)


class TrackUsageUseCase:
    """
    Use Case: Track Resource Usage

    Responsibilities:
    1. Find active subscriptions
    2. Calculate current usage (users, plants, storage)
    3. Store usage snapshots
    4. Identify organizations at/over limits

    Single Responsibility: Periodic usage tracking
    """

    def __init__(self, db: Session):
        """
        Initialize use case

        Args:
            db: Database session
        """
        self.db = db
        self.usage_service = UsageTrackingService(db)

    def execute(self, organization_ids: List[int] = None) -> Dict[str, Any]:
        """
        Execute usage tracking for organizations

        Args:
            organization_ids: Optional list of specific organization IDs.
                            If None, tracks all active subscriptions.

        Returns:
            Dictionary with tracking summary:
            {
                "tracked_count": 150,
                "at_limit_count": 5,
                "organizations_at_limit": [
                    {
                        "organization_id": 123,
                        "violations": ["users", "storage"]
                    }
                ],
                "failed_count": 2,
                "failed_org_ids": [456, 789]
            }
        """
        logger.info("Running usage tracking job")

        # Step 1: Get organizations to track
        if organization_ids:
            orgs_to_track = organization_ids
        else:
            orgs_to_track = self._get_active_subscriptions()

        # Step 2: Track usage for each organization
        tracked = []
        failed = []
        at_limit = []

        for org_id in orgs_to_track:
            try:
                # Track usage
                usage = self.usage_service.track_usage(org_id)
                tracked.append(org_id)

                # Check if at/over limits
                violations = self.usage_service.get_limit_violations(org_id)
                if violations:
                    at_limit.append({
                        "organization_id": org_id,
                        "violations": [v.resource for v in violations]
                    })

                logger.debug(
                    f"Tracked usage for org {org_id}: "
                    f"users={usage.current_users}, "
                    f"plants={usage.current_plants}, "
                    f"storage={usage.storage_used_gb}GB"
                )

            except Exception as e:
                logger.error(f"Failed to track usage for organization {org_id}: {e}")
                failed.append(org_id)

        result = {
            "tracked_count": len(tracked),
            "at_limit_count": len(at_limit),
            "organizations_at_limit": at_limit,
            "failed_count": len(failed),
            "failed_org_ids": failed
        }

        logger.info(
            f"Usage tracking completed: {result['tracked_count']} tracked, "
            f"{result['at_limit_count']} at limit, {result['failed_count']} failed"
        )

        # Step 3: Send alerts for organizations at limit
        if at_limit:
            self._send_limit_alerts(at_limit)

        return result

    def _get_active_subscriptions(self) -> List[int]:
        """
        Get list of organization IDs with active subscriptions

        Returns:
            List of organization IDs
        """
        subscriptions = self.db.query(SubscriptionModel.organization_id).filter(
            SubscriptionModel.status.in_([
                SubscriptionStatus.TRIAL.value,
                SubscriptionStatus.ACTIVE.value
            ])
        ).all()

        return [s.organization_id for s in subscriptions]

    def _send_limit_alerts(self, organizations_at_limit: List[Dict[str, Any]]) -> None:
        """
        Send alerts for organizations at/over limits

        Args:
            organizations_at_limit: List of organizations with violations

        TODO: Implement alert notification
        """
        for org_info in organizations_at_limit:
            org_id = org_info["organization_id"]
            violations = org_info["violations"]

            logger.warning(
                f"Organization {org_id} is at/over limit for: {', '.join(violations)}"
            )

            # TODO: Send alert email/notification
            # notification_service.send_limit_alert(
            #     organization_id=org_id,
            #     violations=violations
            # )

    def track_single_organization(self, organization_id: int) -> Dict[str, Any]:
        """
        Track usage for a single organization (on-demand)

        Args:
            organization_id: Organization ID

        Returns:
            Usage summary dictionary
        """
        logger.info(f"Tracking usage for organization {organization_id}")

        try:
            # Track usage
            usage = self.usage_service.track_usage(organization_id)

            # Get full usage summary
            summary = self.usage_service.get_usage_summary(organization_id)

            logger.info(
                f"Successfully tracked usage for organization {organization_id}: "
                f"{summary['usage']}"
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to track usage for organization {organization_id}: {e}")
            raise

    def get_usage_trends(
        self,
        organization_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage trends for an organization over time

        Args:
            organization_id: Organization ID
            days: Number of days to analyze

        Returns:
            Dictionary with usage trends
        """
        from datetime import datetime, timedelta
        from app.models.subscription import SubscriptionUsageModel

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        usage_history = self.db.query(SubscriptionUsageModel).filter(
            and_(
                SubscriptionUsageModel.organization_id == organization_id,
                SubscriptionUsageModel.measured_at >= cutoff_date
            )
        ).order_by(SubscriptionUsageModel.measured_at.asc()).all()

        if not usage_history:
            return {
                "organization_id": organization_id,
                "days_analyzed": days,
                "data_points": 0,
                "trends": None
            }

        # Calculate trends
        user_values = [u.current_users for u in usage_history]
        plant_values = [u.current_plants for u in usage_history]
        storage_values = [float(u.storage_used_gb) for u in usage_history]

        return {
            "organization_id": organization_id,
            "days_analyzed": days,
            "data_points": len(usage_history),
            "trends": {
                "users": {
                    "min": min(user_values),
                    "max": max(user_values),
                    "avg": sum(user_values) / len(user_values),
                    "current": user_values[-1]
                },
                "plants": {
                    "min": min(plant_values),
                    "max": max(plant_values),
                    "avg": sum(plant_values) / len(plant_values),
                    "current": plant_values[-1]
                },
                "storage_gb": {
                    "min": min(storage_values),
                    "max": max(storage_values),
                    "avg": sum(storage_values) / len(storage_values),
                    "current": storage_values[-1]
                }
            },
            "history": [
                {
                    "measured_at": u.measured_at.isoformat(),
                    "users": u.current_users,
                    "plants": u.current_plants,
                    "storage_gb": float(u.storage_used_gb)
                }
                for u in usage_history
            ]
        }
