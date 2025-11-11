"""
Analytics API - Business intelligence endpoints

Provides metrics for admin dashboards:
- MRR/ARR tracking
- Trial conversion rates
- Churn analysis
- Cohort retention
- Revenue forecasting

Access: Requires is_superuser=true
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.infrastructure.persistence.database import get_db
from app.application.services.analytics_service import AnalyticsService
from app.infrastructure.security.admin_required import require_platform_admin
from app.infrastructure.persistence.models import UserModel
from app.infrastructure.security.jwt import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/mrr/breakdown")
@require_platform_admin
async def get_mrr_breakdown(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get MRR breakdown by tier and billing cycle

    Returns:
        - total_mrr: Total monthly recurring revenue
        - mrr_by_tier: MRR split by tier (starter, professional, enterprise)
        - mrr_by_cycle: MRR split by billing cycle (monthly, annual)
        - customer_count: Number of paying customers
        - arpu: Average revenue per user
    """
    service = AnalyticsService(db)
    return service.get_mrr_breakdown()


@router.get("/mrr/growth")
@require_platform_admin
async def get_mrr_growth(
    months: int = Query(12, ge=1, le=24, description="Number of months to include"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get MRR growth over time

    Args:
        months: Number of months to include (1-24)

    Returns:
        List of monthly data points with:
        - date: Month (YYYY-MM)
        - mrr: Monthly recurring revenue
        - new_customers: New customers this month
        - churned_customers: Churned customers this month
        - net_customers: Net customer change
    """
    service = AnalyticsService(db)
    return service.get_mrr_growth(months=months)


@router.get("/trials/conversion")
@require_platform_admin
async def get_trial_conversion_metrics(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get trial conversion metrics

    Returns:
        - total_trials: Total trials created
        - converted_trials: Trials converted to paid
        - active_trials: Currently active trials
        - expired_trials: Trials that expired without converting
        - conversion_rate: Percentage of trials that convert
        - avg_days_to_convert: Average days from trial start to conversion
    """
    service = AnalyticsService(db)
    return service.get_trial_conversion_metrics()


@router.get("/churn")
@require_platform_admin
async def get_churn_metrics(
    period_days: int = Query(30, ge=1, le=365, description="Period to calculate churn"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get churn metrics

    Args:
        period_days: Period to calculate churn over (default 30 days)

    Returns:
        - period_days: Period analyzed
        - customers_start: Customers at start of period
        - churned_count: Customers who churned
        - churn_rate: Percentage of customers churned
        - mrr_churned: MRR lost to churn
        - mrr_churn_rate: Percentage of MRR churned
    """
    service = AnalyticsService(db)
    return service.get_churn_metrics(period_days=period_days)


@router.get("/cohorts/retention")
@require_platform_admin
async def get_cohort_retention(
    cohort_month: Optional[str] = Query(None, description="Specific cohort month (YYYY-MM)"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get cohort retention analysis

    Args:
        cohort_month: Optional specific cohort to analyze (YYYY-MM format)

    Returns:
        List of cohorts with:
        - cohort_month: Month customers signed up
        - cohort_size: Number of customers in cohort
        - retention: List of retention rates by month
            - month: Months after signup (1-6)
            - retained: Number still active
            - retention_rate: Percentage still active
    """
    service = AnalyticsService(db)
    return service.get_cohort_retention(cohort_month=cohort_month)


@router.get("/forecast")
@require_platform_admin
async def get_revenue_forecast(
    months: int = Query(6, ge=1, le=12, description="Months to forecast"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get revenue forecast based on current trends

    Args:
        months: Number of months to forecast (1-12)

    Returns:
        List of forecasted monthly data:
        - date: Forecast month (YYYY-MM)
        - forecasted_mrr: Predicted MRR
        - forecasted_arr: Predicted ARR (MRR × 12)
        - growth_rate: Assumed growth rate percentage
    """
    service = AnalyticsService(db)
    return service.get_revenue_forecast(months=months)


@router.get("/dashboard/summary")
@require_platform_admin
async def get_analytics_dashboard_summary(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get complete analytics dashboard summary

    Combines all key metrics into single response for dashboard.

    Returns:
        - mrr: MRR breakdown
        - trials: Trial conversion metrics
        - churn: Churn metrics (30 days)
        - growth: MRR growth (last 6 months)
        - forecast: Revenue forecast (next 6 months)
    """
    service = AnalyticsService(db)

    return {
        "mrr": service.get_mrr_breakdown(),
        "trials": service.get_trial_conversion_metrics(),
        "churn": service.get_churn_metrics(period_days=30),
        "growth": service.get_mrr_growth(months=6),
        "forecast": service.get_revenue_forecast(months=6),
    }
