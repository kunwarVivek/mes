"""
Analytics Service - Business metrics and KPIs

Provides data for admin dashboards and business intelligence.
Calculates MRR, churn, trial conversion, cohorts, and forecasts.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case, extract
from decimal import Decimal

from app.models.subscription import SubscriptionModel, InvoiceModel
from app.models.organization import OrganizationModel
from app.domain.entities.subscription import SubscriptionStatus, SubscriptionTier, BillingCycle
from app.config.pricing import PRICING_TIERS

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for calculating business analytics and KPIs

    Metrics:
    - MRR (Monthly Recurring Revenue)
    - ARR (Annual Recurring Revenue)
    - Trial conversion rate
    - Churn rate
    - Customer lifetime value (CLTV)
    - Cohort retention
    """

    def __init__(self, db: Session):
        self.db = db

    def get_mrr_breakdown(self) -> Dict[str, Any]:
        """
        Calculate MRR breakdown by tier and billing cycle

        Returns:
            Dictionary with MRR by tier, billing cycle, and total
        """
        subscriptions = self.db.query(SubscriptionModel).filter(
            SubscriptionModel.status == SubscriptionStatus.ACTIVE.value
        ).all()

        mrr_by_tier = {
            "starter": 0,
            "professional": 0,
            "enterprise": 0,
        }

        mrr_by_cycle = {
            "monthly": 0,
            "annual": 0,
        }

        total_mrr = 0

        for sub in subscriptions:
            # Get monthly price for this tier
            tier_pricing = PRICING_TIERS.get(sub.tier, {})

            if sub.billing_cycle == BillingCycle.MONTHLY.value:
                monthly_price = tier_pricing.get("monthly_price", 0)
            else:  # Annual
                annual_price = tier_pricing.get("annual_price", 0)
                monthly_price = annual_price / 12

            # Add to totals
            mrr_by_tier[sub.tier] += monthly_price
            mrr_by_cycle[sub.billing_cycle] += monthly_price
            total_mrr += monthly_price

        return {
            "total_mrr": total_mrr / 100,  # Convert cents to dollars
            "mrr_by_tier": {k: v / 100 for k, v in mrr_by_tier.items()},
            "mrr_by_cycle": {k: v / 100 for k, v in mrr_by_cycle.items()},
            "customer_count": len(subscriptions),
            "arpu": (total_mrr / len(subscriptions) / 100) if subscriptions else 0,
        }

    def get_mrr_growth(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Calculate MRR growth over time

        Args:
            months: Number of months to include

        Returns:
            List of dictionaries with date, MRR, new MRR, churned MRR
        """
        results = []
        end_date = datetime.now(timezone.utc)

        for i in range(months):
            # Calculate date for this month
            month_date = end_date - timedelta(days=30 * (months - i - 1))
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get active subscriptions at this point in time
            active_subs = self.db.query(SubscriptionModel).filter(
                and_(
                    SubscriptionModel.created_at <= month_start,
                    or_(
                        SubscriptionModel.status == SubscriptionStatus.ACTIVE.value,
                        SubscriptionModel.status == SubscriptionStatus.TRIAL.value
                    )
                )
            ).all()

            # Calculate MRR
            month_mrr = 0
            for sub in active_subs:
                tier_pricing = PRICING_TIERS.get(sub.tier, {})
                if sub.billing_cycle == BillingCycle.MONTHLY.value:
                    monthly_price = tier_pricing.get("monthly_price", 0)
                else:
                    annual_price = tier_pricing.get("annual_price", 0)
                    monthly_price = annual_price / 12
                month_mrr += monthly_price

            # Get new subscriptions this month
            new_subs = self.db.query(SubscriptionModel).filter(
                and_(
                    SubscriptionModel.created_at >= month_start,
                    SubscriptionModel.created_at < month_start + timedelta(days=30),
                    SubscriptionModel.status == SubscriptionStatus.ACTIVE.value
                )
            ).count()

            # Get churned subscriptions this month
            churned_subs = self.db.query(SubscriptionModel).filter(
                and_(
                    SubscriptionModel.updated_at >= month_start,
                    SubscriptionModel.updated_at < month_start + timedelta(days=30),
                    SubscriptionModel.status == SubscriptionStatus.CANCELLED.value
                )
            ).count()

            results.append({
                "date": month_start.strftime("%Y-%m"),
                "mrr": month_mrr / 100,
                "new_customers": new_subs,
                "churned_customers": churned_subs,
                "net_customers": new_subs - churned_subs,
            })

        return results

    def get_trial_conversion_metrics(self) -> Dict[str, Any]:
        """
        Calculate trial conversion metrics

        Returns:
            Dictionary with conversion rates and trial statistics
        """
        # Total trials created
        total_trials = self.db.query(func.count(SubscriptionModel.id)).filter(
            SubscriptionModel.status.in_([
                SubscriptionStatus.TRIAL.value,
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.CANCELLED.value
            ])
        ).scalar()

        # Converted trials
        converted_trials = self.db.query(func.count(SubscriptionModel.id)).filter(
            SubscriptionModel.trial_converted == True
        ).scalar()

        # Active trials
        active_trials = self.db.query(func.count(SubscriptionModel.id)).filter(
            SubscriptionModel.status == SubscriptionStatus.TRIAL.value
        ).scalar()

        # Expired trials (not converted)
        now = datetime.now(timezone.utc)
        expired_trials = self.db.query(func.count(SubscriptionModel.id)).filter(
            and_(
                SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                SubscriptionModel.trial_ends_at < now,
                SubscriptionModel.trial_converted == False
            )
        ).scalar()

        # Calculate conversion rate
        conversion_rate = (converted_trials / total_trials * 100) if total_trials > 0 else 0

        # Average time to convert
        avg_days_to_convert = self.db.query(
            func.avg(
                func.extract('epoch', SubscriptionModel.updated_at - SubscriptionModel.created_at) / 86400
            )
        ).filter(
            SubscriptionModel.trial_converted == True
        ).scalar() or 0

        return {
            "total_trials": total_trials,
            "converted_trials": converted_trials,
            "active_trials": active_trials,
            "expired_trials": expired_trials,
            "conversion_rate": round(conversion_rate, 2),
            "avg_days_to_convert": round(float(avg_days_to_convert), 1),
        }

    def get_churn_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Calculate churn metrics for a given period

        Args:
            period_days: Period to calculate churn over (default 30 days)

        Returns:
            Dictionary with churn rate, churned customers, and reasons
        """
        period_start = datetime.now(timezone.utc) - timedelta(days=period_days)

        # Customers at start of period
        customers_start = self.db.query(func.count(SubscriptionModel.id)).filter(
            and_(
                SubscriptionModel.created_at < period_start,
                SubscriptionModel.status == SubscriptionStatus.ACTIVE.value
            )
        ).scalar()

        # Churned during period
        churned_count = self.db.query(func.count(SubscriptionModel.id)).filter(
            and_(
                SubscriptionModel.updated_at >= period_start,
                SubscriptionModel.status == SubscriptionStatus.CANCELLED.value
            )
        ).scalar()

        # Calculate churn rate
        churn_rate = (churned_count / customers_start * 100) if customers_start > 0 else 0

        # MRR churned
        churned_subs = self.db.query(SubscriptionModel).filter(
            and_(
                SubscriptionModel.updated_at >= period_start,
                SubscriptionModel.status == SubscriptionStatus.CANCELLED.value
            )
        ).all()

        mrr_churned = 0
        for sub in churned_subs:
            tier_pricing = PRICING_TIERS.get(sub.tier, {})
            if sub.billing_cycle == BillingCycle.MONTHLY.value:
                monthly_price = tier_pricing.get("monthly_price", 0)
            else:
                annual_price = tier_pricing.get("annual_price", 0)
                monthly_price = annual_price / 12
            mrr_churned += monthly_price

        return {
            "period_days": period_days,
            "customers_start": customers_start,
            "churned_count": churned_count,
            "churn_rate": round(churn_rate, 2),
            "mrr_churned": mrr_churned / 100,
            "mrr_churn_rate": round((mrr_churned / (customers_start * 4900) * 100), 2) if customers_start > 0 else 0,
        }

    def get_cohort_retention(self, cohort_month: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Calculate cohort retention rates

        Args:
            cohort_month: Optional specific cohort month (YYYY-MM)

        Returns:
            List of cohorts with retention rates by month
        """
        # Get cohorts (month of signup)
        if cohort_month:
            # Specific cohort
            cohort_start = datetime.strptime(cohort_month, "%Y-%m")
            cohorts = [(cohort_start.year, cohort_start.month)]
        else:
            # Last 12 months of cohorts
            cohorts = []
            for i in range(12):
                date = datetime.now(timezone.utc) - timedelta(days=30 * i)
                cohorts.append((date.year, date.month))

        results = []

        for year, month in cohorts:
            cohort_start = datetime(year, month, 1, tzinfo=timezone.utc)
            cohort_end = (cohort_start + timedelta(days=32)).replace(day=1)

            # Get all customers who signed up in this cohort
            cohort_customers = self.db.query(SubscriptionModel.id).filter(
                and_(
                    SubscriptionModel.created_at >= cohort_start,
                    SubscriptionModel.created_at < cohort_end
                )
            ).all()

            cohort_size = len(cohort_customers)
            cohort_ids = [c[0] for c in cohort_customers]

            if cohort_size == 0:
                continue

            # Calculate retention for each month after signup
            retention_by_month = []
            for month_num in range(6):  # 6 months of retention
                retention_month = cohort_start + timedelta(days=30 * (month_num + 1))

                # Count how many are still active
                still_active = self.db.query(func.count(SubscriptionModel.id)).filter(
                    and_(
                        SubscriptionModel.id.in_(cohort_ids),
                        SubscriptionModel.status == SubscriptionStatus.ACTIVE.value,
                        SubscriptionModel.created_at < retention_month
                    )
                ).scalar()

                retention_rate = (still_active / cohort_size * 100) if cohort_size > 0 else 0
                retention_by_month.append({
                    "month": month_num + 1,
                    "retained": still_active,
                    "retention_rate": round(retention_rate, 2),
                })

            results.append({
                "cohort_month": cohort_start.strftime("%Y-%m"),
                "cohort_size": cohort_size,
                "retention": retention_by_month,
            })

        return results

    def get_revenue_forecast(self, months: int = 6) -> List[Dict[str, Any]]:
        """
        Forecast revenue based on current trends

        Args:
            months: Number of months to forecast

        Returns:
            List of forecasted revenue by month
        """
        # Get current MRR
        current_mrr_data = self.get_mrr_breakdown()
        current_mrr = current_mrr_data["total_mrr"]

        # Get growth rate from last 3 months
        growth_history = self.get_mrr_growth(months=3)
        if len(growth_history) >= 2:
            # Calculate average MRR growth rate
            growth_rates = []
            for i in range(1, len(growth_history)):
                prev_mrr = growth_history[i-1]["mrr"]
                curr_mrr = growth_history[i]["mrr"]
                if prev_mrr > 0:
                    growth_rate = (curr_mrr - prev_mrr) / prev_mrr
                    growth_rates.append(growth_rate)

            avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0.05
        else:
            # Default to 5% growth if not enough data
            avg_growth_rate = 0.05

        # Generate forecast
        forecasts = []
        forecasted_mrr = current_mrr

        for i in range(months):
            forecast_date = datetime.now(timezone.utc) + timedelta(days=30 * (i + 1))
            forecasted_mrr = forecasted_mrr * (1 + avg_growth_rate)

            forecasts.append({
                "date": forecast_date.strftime("%Y-%m"),
                "forecasted_mrr": round(forecasted_mrr, 2),
                "forecasted_arr": round(forecasted_mrr * 12, 2),
                "growth_rate": round(avg_growth_rate * 100, 2),
            })

        return forecasts
