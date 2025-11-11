"""
Platform Admin Service - Business logic for admin dashboard operations

Handles cross-organization management, subscription control, metrics,
usage analytics, and support tools for platform administrators.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, case
from decimal import Decimal
import logging

from app.models.organization import Organization
from app.models.subscription import (
    SubscriptionModel,
    SubscriptionUsageModel,
    SubscriptionAddOnModel
)
from app.models.admin_audit_log import AdminAuditLogModel
from app.infrastructure.persistence.models import UserModel
from app.infrastructure.security.jwt_handler import JWTHandler
from app.core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    BusinessRuleException
)

logger = logging.getLogger(__name__)


class PlatformAdminService:
    """
    Service for platform admin operations

    Provides cross-organization visibility and management for platform admins.
    All operations bypass RLS and operate at platform level.
    """

    def __init__(self, db: Session):
        """
        Initialize platform admin service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.jwt_handler = JWTHandler()

    # ========================================================================
    # ORGANIZATION MANAGEMENT
    # ========================================================================

    def list_organizations(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """
        List all organizations with filters and pagination

        Args:
            search: Search by name, subdomain, or org_code
            status: Filter by active status ("active", "inactive", "all")
            tier: Filter by subscription tier
            limit: Results per page
            offset: Pagination offset

        Returns:
            tuple: (organizations list, total count, has_more)
        """
        try:
            query = self.db.query(Organization).join(
                SubscriptionModel,
                Organization.id == SubscriptionModel.organization_id
            )

            # Apply filters
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(or_(
                    Organization.org_name.ilike(search_pattern),
                    Organization.org_code.ilike(search_pattern),
                    Organization.subdomain.ilike(search_pattern)
                ))

            if status and status != "all":
                is_active = status == "active"
                query = query.filter(Organization.is_active == is_active)

            if tier:
                query = query.filter(SubscriptionModel.tier == tier)

            # Get total count
            total_count = query.count()

            # Get paginated results with subscription info
            organizations = query.limit(limit).offset(offset).all()

            # Enrich with additional data
            result = []
            for org in organizations:
                subscription = org.subscription

                # Get usage data
                usage = self.db.query(SubscriptionUsageModel).filter(
                    SubscriptionUsageModel.organization_id == org.id
                ).order_by(desc(SubscriptionUsageModel.measured_at)).first()

                # Get last activity (last updated user or entity)
                last_active = self._get_last_activity(org.id)

                result.append({
                    "id": org.id,
                    "org_code": org.org_code,
                    "org_name": org.org_name,
                    "subdomain": org.subdomain,
                    "is_active": org.is_active,
                    "subscription_tier": subscription.tier if subscription else "unknown",
                    "subscription_status": subscription.status if subscription else "unknown",
                    "user_count": usage.current_users if usage else 0,
                    "plant_count": usage.current_plants if usage else 0,
                    "storage_used_gb": float(usage.storage_used_gb) if usage else 0.0,
                    "last_active_at": last_active,
                    "created_at": org.created_at
                })

            has_more = (offset + limit) < total_count

            return result, total_count, has_more

        except Exception as e:
            logger.error(f"Failed to list organizations: {e}", exc_info=True)
            raise

    def get_organization_details(self, organization_id: int) -> Dict[str, Any]:
        """
        Get detailed organization information

        Args:
            organization_id: Organization ID

        Returns:
            Complete organization profile with metrics

        Raises:
            ResourceNotFoundException: Organization not found
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.id == organization_id
            ).first()

            if not org:
                raise ResourceNotFoundException(
                    f"Organization {organization_id} not found"
                )

            # Get subscription
            subscription = org.subscription
            subscription_data = {
                "id": subscription.id,
                "tier": subscription.tier,
                "status": subscription.status,
                "billing_cycle": subscription.billing_cycle,
                "trial_ends_at": subscription.trial_ends_at,
                "current_period_end": subscription.current_period_end,
                "stripe_customer_id": subscription.stripe_customer_id,
                "created_at": subscription.created_at
            } if subscription else None

            # Get usage
            usage = self.db.query(SubscriptionUsageModel).filter(
                SubscriptionUsageModel.organization_id == organization_id
            ).order_by(desc(SubscriptionUsageModel.measured_at)).first()

            # Get additional metrics
            metrics = self._get_organization_metrics(organization_id)

            return {
                "id": org.id,
                "org_code": org.org_code,
                "org_name": org.org_name,
                "subdomain": org.subdomain,
                "is_active": org.is_active,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
                "subscription": subscription_data,
                "user_count": usage.current_users if usage else 0,
                "plant_count": usage.current_plants if usage else 0,
                "storage_used_gb": float(usage.storage_used_gb) if usage else 0.0,
                "last_active_at": self._get_last_activity(organization_id),
                "total_work_orders": metrics["work_orders"],
                "total_materials": metrics["materials"],
                "total_machines": metrics["machines"]
            }

        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get organization details: {e}", exc_info=True)
            raise

    def update_organization(
        self,
        organization_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update organization settings

        Args:
            organization_id: Organization ID
            updates: Fields to update (is_active, org_name)

        Returns:
            Updated organization data

        Raises:
            ResourceNotFoundException: Organization not found
        """
        try:
            org = self.db.query(Organization).filter(
                Organization.id == organization_id
            ).first()

            if not org:
                raise ResourceNotFoundException(
                    f"Organization {organization_id} not found"
                )

            # Apply updates
            if "is_active" in updates:
                org.is_active = updates["is_active"]

            if "org_name" in updates:
                org.org_name = updates["org_name"]

            org.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(org)

            return self.get_organization_details(organization_id)

        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to update organization: {e}", exc_info=True)
            self.db.rollback()
            raise

    # ========================================================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================================================

    def list_subscriptions(
        self,
        status: Optional[str] = None,
        expires_soon: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List subscriptions across all organizations

        Args:
            status: Filter by status (trial, active, cancelled, past_due, suspended)
            expires_soon: Filter trials expiring in next 7 days
            limit: Results per page
            offset: Pagination offset

        Returns:
            tuple: (subscriptions list, total count)
        """
        try:
            query = self.db.query(SubscriptionModel).join(
                Organization,
                SubscriptionModel.organization_id == Organization.id
            )

            # Apply filters
            if status and status != "all":
                query = query.filter(SubscriptionModel.status == status)

            if expires_soon:
                cutoff_date = datetime.utcnow() + timedelta(days=7)
                query = query.filter(and_(
                    SubscriptionModel.status == "trial",
                    SubscriptionModel.trial_ends_at <= cutoff_date,
                    SubscriptionModel.trial_ends_at >= datetime.utcnow()
                ))

            # Get total count
            total_count = query.count()

            # Get paginated results
            subscriptions = query.limit(limit).offset(offset).all()

            result = []
            for sub in subscriptions:
                org = sub.organization

                # Calculate days until trial expiry
                days_until_expiry = None
                if sub.status == "trial" and sub.trial_ends_at:
                    delta = sub.trial_ends_at - datetime.utcnow()
                    days_until_expiry = max(0, delta.days)

                result.append({
                    "id": sub.id,
                    "organization_id": sub.organization_id,
                    "organization_name": org.org_name if org else "Unknown",
                    "tier": sub.tier,
                    "status": sub.status,
                    "billing_cycle": sub.billing_cycle,
                    "trial_ends_at": sub.trial_ends_at,
                    "days_until_trial_expiry": days_until_expiry,
                    "current_period_end": sub.current_period_end,
                    "stripe_customer_id": sub.stripe_customer_id,
                    "created_at": sub.created_at
                })

            return result, total_count

        except Exception as e:
            logger.error(f"Failed to list subscriptions: {e}", exc_info=True)
            raise

    def extend_trial(
        self,
        subscription_id: int,
        days: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Extend trial period for subscription

        Args:
            subscription_id: Subscription ID
            days: Number of days to extend (1-90)
            reason: Reason for extension (for audit)

        Returns:
            Updated subscription data

        Raises:
            ResourceNotFoundException: Subscription not found
            BusinessRuleException: Subscription not in trial status
        """
        try:
            subscription = self.db.query(SubscriptionModel).filter(
                SubscriptionModel.id == subscription_id
            ).first()

            if not subscription:
                raise ResourceNotFoundException(
                    f"Subscription {subscription_id} not found"
                )

            if subscription.status != "trial":
                raise BusinessRuleException(
                    f"Cannot extend trial: subscription status is '{subscription.status}', "
                    "must be 'trial'"
                )

            if not subscription.trial_ends_at:
                raise BusinessRuleException(
                    "Cannot extend trial: trial_ends_at is not set"
                )

            # Extend trial
            subscription.trial_ends_at = subscription.trial_ends_at + timedelta(days=days)
            subscription.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(subscription)

            logger.info(
                f"Extended trial for subscription {subscription_id} by {days} days. "
                f"Reason: {reason}"
            )

            return self._subscription_to_dict(subscription)

        except (ResourceNotFoundException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Failed to extend trial: {e}", exc_info=True)
            self.db.rollback()
            raise

    def suspend_subscription(
        self,
        subscription_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Suspend subscription manually

        Args:
            subscription_id: Subscription ID
            reason: Reason for suspension (for audit)

        Returns:
            Updated subscription data

        Raises:
            ResourceNotFoundException: Subscription not found
        """
        try:
            subscription = self.db.query(SubscriptionModel).filter(
                SubscriptionModel.id == subscription_id
            ).first()

            if not subscription:
                raise ResourceNotFoundException(
                    f"Subscription {subscription_id} not found"
                )

            subscription.status = "suspended"
            subscription.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(subscription)

            logger.info(
                f"Suspended subscription {subscription_id}. Reason: {reason}"
            )

            return self._subscription_to_dict(subscription)

        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to suspend subscription: {e}", exc_info=True)
            self.db.rollback()
            raise

    def reactivate_subscription(
        self,
        subscription_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Reactivate suspended subscription

        Args:
            subscription_id: Subscription ID
            reason: Reason for reactivation (for audit)

        Returns:
            Updated subscription data

        Raises:
            ResourceNotFoundException: Subscription not found
            BusinessRuleException: Subscription not suspended
        """
        try:
            subscription = self.db.query(SubscriptionModel).filter(
                SubscriptionModel.id == subscription_id
            ).first()

            if not subscription:
                raise ResourceNotFoundException(
                    f"Subscription {subscription_id} not found"
                )

            if subscription.status != "suspended":
                raise BusinessRuleException(
                    f"Cannot reactivate: subscription status is '{subscription.status}', "
                    "must be 'suspended'"
                )

            # Determine new status based on trial/paid
            if subscription.trial_converted:
                subscription.status = "active"
            else:
                subscription.status = "trial"

            subscription.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(subscription)

            logger.info(
                f"Reactivated subscription {subscription_id}. Reason: {reason}"
            )

            return self._subscription_to_dict(subscription)

        except (ResourceNotFoundException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Failed to reactivate subscription: {e}", exc_info=True)
            self.db.rollback()
            raise

    # ========================================================================
    # PLATFORM METRICS
    # ========================================================================

    def get_platform_metrics(self) -> Dict[str, Any]:
        """
        Get platform-wide KPI metrics

        Returns:
            Dictionary with platform metrics
        """
        try:
            # Organization counts
            total_orgs = self.db.query(Organization).count()
            active_orgs = self.db.query(Organization).filter(
                Organization.is_active == True
            ).count()
            inactive_orgs = total_orgs - active_orgs

            # Subscription counts
            active_subs = self.db.query(SubscriptionModel).filter(
                SubscriptionModel.status == "active"
            ).count()

            trial_subs = self.db.query(SubscriptionModel).filter(
                SubscriptionModel.status == "trial"
            ).count()

            cancelled_subs = self.db.query(SubscriptionModel).filter(
                SubscriptionModel.status == "cancelled"
            ).count()

            # Calculate MRR (Monthly Recurring Revenue)
            # This is a simplified calculation - in production, integrate with Stripe
            mrr = self._calculate_mrr()

            # Total users across all organizations
            total_users = self.db.query(UserModel).count()

            # Total plants
            from app.models.plant import Plant
            total_plants = self.db.query(Plant).count()

            # Total storage used
            storage_result = self.db.query(
                func.sum(SubscriptionUsageModel.storage_used_gb)
            ).scalar()
            total_storage_gb = float(storage_result) if storage_result else 0.0

            return {
                "total_organizations": total_orgs,
                "active_organizations": active_orgs,
                "inactive_organizations": inactive_orgs,
                "active_subscriptions": active_subs,
                "trial_subscriptions": trial_subs,
                "cancelled_subscriptions": cancelled_subs,
                "monthly_recurring_revenue": mrr,
                "total_users": total_users,
                "total_plants": total_plants,
                "storage_used_gb": total_storage_gb,
                "measured_at": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Failed to get platform metrics: {e}", exc_info=True)
            raise

    def get_growth_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Get growth metrics over time period

        Args:
            period_days: Number of days to analyze (default 30)

        Returns:
            Growth metrics including signups, conversions, churn
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)

            # New signups (organizations created)
            signups = self.db.query(
                func.date(Organization.created_at).label('date'),
                func.count(Organization.id).label('count')
            ).filter(
                Organization.created_at >= cutoff_date
            ).group_by(
                func.date(Organization.created_at)
            ).all()

            # Trial conversions
            conversions = self.db.query(
                func.date(SubscriptionModel.updated_at).label('date'),
                func.count(SubscriptionModel.id).label('count')
            ).filter(and_(
                SubscriptionModel.trial_converted == True,
                SubscriptionModel.updated_at >= cutoff_date
            )).group_by(
                func.date(SubscriptionModel.updated_at)
            ).all()

            # Churn count (subscriptions cancelled in period)
            churn_count = self.db.query(SubscriptionModel).filter(and_(
                SubscriptionModel.status == "cancelled",
                SubscriptionModel.cancelled_at >= cutoff_date
            )).count()

            # Calculate churn rate
            total_active_start = self.db.query(SubscriptionModel).filter(
                SubscriptionModel.status.in_(["active", "trial"])
            ).count()
            churn_rate = (churn_count / total_active_start * 100) if total_active_start > 0 else 0

            # MRR growth
            mrr_current = self._calculate_mrr()
            mrr_start = self._calculate_mrr(as_of=cutoff_date)
            mrr_growth = mrr_current - mrr_start
            mrr_growth_pct = (mrr_growth / mrr_start * 100) if mrr_start > 0 else 0

            return {
                "period_days": period_days,
                "signups": [{"date": s.date, "value": s.count} for s in signups],
                "trial_conversions": [{"date": c.date, "value": c.count} for c in conversions],
                "churn_count": churn_count,
                "churn_rate": round(Decimal(str(churn_rate)), 2),
                "mrr_growth": round(Decimal(str(mrr_growth)), 2),
                "mrr_growth_percentage": round(Decimal(str(mrr_growth_pct)), 2)
            }

        except Exception as e:
            logger.error(f"Failed to get growth metrics: {e}", exc_info=True)
            raise

    # ========================================================================
    # USAGE ANALYTICS
    # ========================================================================

    def get_top_organizations(
        self,
        metric: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top organizations by usage metric

        Args:
            metric: Metric to sort by ("users", "plants", "storage")
            limit: Number of organizations to return

        Returns:
            List of top organizations with metric values
        """
        try:
            # Map metric to column
            metric_column_map = {
                "users": SubscriptionUsageModel.current_users,
                "plants": SubscriptionUsageModel.current_plants,
                "storage": SubscriptionUsageModel.storage_used_gb
            }

            if metric not in metric_column_map:
                raise ValidationException(f"Invalid metric: {metric}")

            metric_column = metric_column_map[metric]

            # Get total for percentage calculation
            total = self.db.query(func.sum(metric_column)).scalar() or 0

            # Query top organizations
            results = self.db.query(
                Organization.id,
                Organization.org_code,
                Organization.org_name,
                SubscriptionModel.tier,
                metric_column.label('metric_value')
            ).join(
                SubscriptionUsageModel,
                Organization.id == SubscriptionUsageModel.organization_id
            ).join(
                SubscriptionModel,
                Organization.id == SubscriptionModel.organization_id
            ).order_by(
                desc(metric_column)
            ).limit(limit).all()

            organizations = []
            for r in results:
                percentage = (float(r.metric_value) / float(total) * 100) if total > 0 else 0

                organizations.append({
                    "id": r.id,
                    "org_code": r.org_code,
                    "org_name": r.org_name,
                    "tier": r.tier,
                    "metric_value": int(r.metric_value) if metric != "storage" else float(r.metric_value),
                    "percentage_of_total": round(Decimal(str(percentage)), 2)
                })

            return {
                "metric": metric,
                "organizations": organizations,
                "total_across_platform": int(total) if metric != "storage" else float(total)
            }

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to get top organizations: {e}", exc_info=True)
            raise

    def get_usage_violations(self) -> List[Dict[str, Any]]:
        """
        Get organizations exceeding their subscription limits

        Returns:
            List of usage violations with details
        """
        try:
            violations = []

            # Query organizations with usage and subscription limits
            results = self.db.query(
                Organization,
                SubscriptionModel,
                SubscriptionUsageModel
            ).join(
                SubscriptionModel,
                Organization.id == SubscriptionModel.organization_id
            ).join(
                SubscriptionUsageModel,
                Organization.id == SubscriptionUsageModel.organization_id
            ).filter(
                Organization.is_active == True
            ).all()

            for org, sub, usage in results:
                # Check user limit
                if sub.max_users and usage.current_users > sub.max_users:
                    overage = usage.current_users - sub.max_users
                    violations.append({
                        "organization_id": org.id,
                        "organization_name": org.org_name,
                        "tier": sub.tier,
                        "status": sub.status,
                        "resource_type": "users",
                        "limit": sub.max_users,
                        "current_usage": usage.current_users,
                        "overage": overage,
                        "overage_percentage": round(
                            Decimal(str(overage / sub.max_users * 100)), 2
                        )
                    })

                # Check plant limit
                if sub.max_plants and usage.current_plants > sub.max_plants:
                    overage = usage.current_plants - sub.max_plants
                    violations.append({
                        "organization_id": org.id,
                        "organization_name": org.org_name,
                        "tier": sub.tier,
                        "status": sub.status,
                        "resource_type": "plants",
                        "limit": sub.max_plants,
                        "current_usage": usage.current_plants,
                        "overage": overage,
                        "overage_percentage": round(
                            Decimal(str(overage / sub.max_plants * 100)), 2
                        )
                    })

                # Check storage limit
                if sub.storage_limit_gb and float(usage.storage_used_gb) > sub.storage_limit_gb:
                    overage = float(usage.storage_used_gb) - sub.storage_limit_gb
                    violations.append({
                        "organization_id": org.id,
                        "organization_name": org.org_name,
                        "tier": sub.tier,
                        "status": sub.status,
                        "resource_type": "storage",
                        "limit": sub.storage_limit_gb,
                        "current_usage": int(usage.storage_used_gb),
                        "overage": int(overage),
                        "overage_percentage": round(
                            Decimal(str(overage / sub.storage_limit_gb * 100)), 2
                        )
                    })

            return {
                "violations": violations,
                "total_violations": len(violations)
            }

        except Exception as e:
            logger.error(f"Failed to get usage violations: {e}", exc_info=True)
            raise

    # ========================================================================
    # SUPPORT TOOLS
    # ========================================================================

    def create_impersonation_token(
        self,
        user_id: int,
        admin_id: int,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        Generate impersonation token for support

        Args:
            user_id: User to impersonate
            admin_id: Admin performing impersonation
            duration_minutes: Token validity (default 60 minutes)

        Returns:
            Impersonation token and metadata

        Raises:
            ResourceNotFoundException: User not found
        """
        try:
            user = self.db.query(UserModel).filter(
                UserModel.id == user_id
            ).first()

            if not user:
                raise ResourceNotFoundException(f"User {user_id} not found")

            # Generate time-limited token
            expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)

            token_payload = {
                "sub": str(user.id),
                "email": user.email,
                "organization_id": user.organization_id,
                "plant_id": user.plant_id,
                "type": "impersonation",
                "impersonated_by": admin_id,
                "exp": int(expires_at.timestamp())
            }

            impersonation_token = self.jwt_handler.create_token(token_payload)

            logger.info(
                f"Created impersonation token for user {user_id} by admin {admin_id}, "
                f"expires at {expires_at}"
            )

            return {
                "impersonation_token": impersonation_token,
                "user_id": user.id,
                "user_email": user.email,
                "organization_id": user.organization_id,
                "expires_at": expires_at,
                "reason": "Support impersonation"
            }

        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to create impersonation token: {e}", exc_info=True)
            raise

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_last_activity(self, organization_id: int) -> Optional[datetime]:
        """Get last activity timestamp for organization"""
        try:
            # Check last user update
            last_user = self.db.query(func.max(UserModel.updated_at)).filter(
                UserModel.organization_id == organization_id
            ).scalar()

            return last_user

        except Exception as e:
            logger.error(f"Failed to get last activity: {e}")
            return None

    def _get_organization_metrics(self, organization_id: int) -> Dict[str, int]:
        """Get additional metrics for organization"""
        try:
            from app.models.work_order import WorkOrder
            from app.models.material import Material
            from app.models.machine import Machine

            work_orders = self.db.query(WorkOrder).filter(
                WorkOrder.organization_id == organization_id
            ).count()

            materials = self.db.query(Material).filter(
                Material.organization_id == organization_id
            ).count()

            machines = self.db.query(Machine).filter(
                Machine.organization_id == organization_id
            ).count()

            return {
                "work_orders": work_orders,
                "materials": materials,
                "machines": machines
            }

        except Exception as e:
            logger.error(f"Failed to get organization metrics: {e}")
            return {"work_orders": 0, "materials": 0, "machines": 0}

    def _calculate_mrr(self, as_of: Optional[datetime] = None) -> Decimal:
        """
        Calculate Monthly Recurring Revenue

        This is a simplified calculation. In production, integrate with Stripe
        to get actual billing amounts.
        """
        try:
            # Simplified: Estimate based on tier and billing cycle
            # In production, query Stripe for actual amounts
            tier_prices = {
                "starter": Decimal("99.00"),
                "professional": Decimal("299.00"),
                "enterprise": Decimal("999.00")
            }

            query = self.db.query(
                SubscriptionModel.tier,
                SubscriptionModel.billing_cycle,
                func.count(SubscriptionModel.id).label('count')
            ).filter(
                SubscriptionModel.status == "active"
            )

            if as_of:
                query = query.filter(SubscriptionModel.created_at <= as_of)

            results = query.group_by(
                SubscriptionModel.tier,
                SubscriptionModel.billing_cycle
            ).all()

            total_mrr = Decimal("0.00")
            for tier, cycle, count in results:
                base_price = tier_prices.get(tier, Decimal("0.00"))

                # Convert annual to monthly
                if cycle == "annual":
                    monthly_price = base_price * Decimal("0.83")  # Annual discount
                else:
                    monthly_price = base_price

                total_mrr += monthly_price * count

            return total_mrr

        except Exception as e:
            logger.error(f"Failed to calculate MRR: {e}")
            return Decimal("0.00")

    def _subscription_to_dict(self, subscription: SubscriptionModel) -> Dict[str, Any]:
        """Convert subscription model to dictionary"""
        return {
            "id": subscription.id,
            "organization_id": subscription.organization_id,
            "tier": subscription.tier,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "trial_starts_at": subscription.trial_starts_at,
            "trial_ends_at": subscription.trial_ends_at,
            "trial_converted": subscription.trial_converted,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "stripe_customer_id": subscription.stripe_customer_id,
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "created_at": subscription.created_at,
            "updated_at": subscription.updated_at,
            "cancelled_at": subscription.cancelled_at
        }
