"""
Pydantic schemas for Platform Admin API

Request and response models for admin dashboard operations including
organization management, subscription control, metrics, and support tools.
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal


# ============================================================================
# ENUMS
# ============================================================================

class OrganizationStatusFilter(str, Enum):
    """Filter for organization status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ALL = "all"


class SubscriptionStatusFilter(str, Enum):
    """Filter for subscription status"""
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    SUSPENDED = "suspended"
    ALL = "all"


class UsageMetric(str, Enum):
    """Usage metrics for top organizations"""
    USERS = "users"
    PLANTS = "plants"
    STORAGE = "storage"


# ============================================================================
# ORGANIZATION MANAGEMENT SCHEMAS
# ============================================================================

class OrganizationListRequest(BaseModel):
    """Request for listing organizations with filters"""
    search: Optional[str] = Field(None, description="Search by name, subdomain, or org_code")
    status: OrganizationStatusFilter = Field(
        OrganizationStatusFilter.ALL,
        description="Filter by active status"
    )
    tier: Optional[str] = Field(None, description="Filter by subscription tier")
    limit: int = Field(50, ge=1, le=200, description="Results per page")
    offset: int = Field(0, ge=0, description="Pagination offset")


class OrganizationSummary(BaseModel):
    """Summary information for organization list"""
    id: int
    org_code: str
    org_name: str
    subdomain: Optional[str]
    is_active: bool
    subscription_tier: str
    subscription_status: str
    user_count: int
    plant_count: int
    storage_used_gb: Decimal
    last_active_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """Response for organization list"""
    organizations: List[OrganizationSummary]
    total_count: int
    has_more: bool
    limit: int
    offset: int


class OrganizationDetailResponse(BaseModel):
    """Detailed organization information"""
    # Organization details
    id: int
    org_code: str
    org_name: str
    subdomain: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    # Subscription details
    subscription: Dict[str, Any]

    # Usage statistics
    user_count: int
    plant_count: int
    storage_used_gb: Decimal
    last_active_at: Optional[datetime]

    # Additional metrics
    total_work_orders: int
    total_materials: int
    total_machines: int

    class Config:
        from_attributes = True


class OrganizationUpdateRequest(BaseModel):
    """Request to update organization"""
    is_active: Optional[bool] = Field(None, description="Activate or deactivate organization")
    org_name: Optional[str] = Field(None, description="Update organization name")
    reason: Optional[str] = Field(None, description="Reason for update (audit log)")


# ============================================================================
# SUBSCRIPTION MANAGEMENT SCHEMAS
# ============================================================================

class SubscriptionListRequest(BaseModel):
    """Request for listing subscriptions"""
    status: Optional[SubscriptionStatusFilter] = Field(None, description="Filter by status")
    expires_soon: bool = Field(False, description="Filter trials expiring in next 7 days")
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class SubscriptionSummary(BaseModel):
    """Summary for subscription list"""
    id: int
    organization_id: int
    organization_name: str
    tier: str
    status: str
    billing_cycle: Optional[str]
    trial_ends_at: Optional[datetime]
    days_until_trial_expiry: Optional[int]
    current_period_end: Optional[datetime]
    stripe_customer_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    """Response for subscription list"""
    subscriptions: List[SubscriptionSummary]
    total_count: int
    limit: int
    offset: int


class ExtendTrialRequest(BaseModel):
    """Request to extend trial period"""
    days: int = Field(..., ge=1, le=90, description="Number of days to extend")
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for extension")


class SuspendSubscriptionRequest(BaseModel):
    """Request to suspend subscription"""
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for suspension")


class ReactivateSubscriptionRequest(BaseModel):
    """Request to reactivate subscription"""
    reason: str = Field(..., min_length=10, max_length=500, description="Reason for reactivation")


class SubscriptionActionResponse(BaseModel):
    """Response for subscription actions"""
    success: bool
    message: str
    subscription: Dict[str, Any]


# ============================================================================
# PLATFORM METRICS SCHEMAS
# ============================================================================

class PlatformMetricsResponse(BaseModel):
    """Platform-wide KPI metrics"""
    total_organizations: int
    active_organizations: int
    inactive_organizations: int
    active_subscriptions: int
    trial_subscriptions: int
    cancelled_subscriptions: int
    monthly_recurring_revenue: Decimal
    total_users: int
    total_plants: int
    storage_used_gb: Decimal
    measured_at: datetime


class GrowthMetricDataPoint(BaseModel):
    """Data point for growth metrics"""
    date: datetime
    value: int


class GrowthMetricsResponse(BaseModel):
    """Growth metrics over time"""
    period_days: int
    signups: List[GrowthMetricDataPoint]
    trial_conversions: List[GrowthMetricDataPoint]
    churn_count: int
    churn_rate: Decimal
    mrr_growth: Decimal
    mrr_growth_percentage: Decimal


# ============================================================================
# USAGE ANALYTICS SCHEMAS
# ============================================================================

class TopOrganizationRequest(BaseModel):
    """Request for top organizations by metric"""
    metric: UsageMetric = Field(..., description="Metric to sort by")
    limit: int = Field(10, ge=1, le=50, description="Number of organizations")


class TopOrganization(BaseModel):
    """Organization with usage metrics"""
    id: int
    org_code: str
    org_name: str
    tier: str
    metric_value: int
    percentage_of_total: Decimal

    class Config:
        from_attributes = True


class TopOrganizationsResponse(BaseModel):
    """Response for top organizations"""
    metric: str
    organizations: List[TopOrganization]
    total_across_platform: int


class UsageViolation(BaseModel):
    """Organization exceeding limits"""
    organization_id: int
    organization_name: str
    tier: str
    status: str
    resource_type: str  # "users", "plants", "storage"
    limit: int
    current_usage: int
    overage: int
    overage_percentage: Decimal

    class Config:
        from_attributes = True


class UsageViolationsResponse(BaseModel):
    """Response for usage violations"""
    violations: List[UsageViolation]
    total_violations: int


# ============================================================================
# SUPPORT TOOLS SCHEMAS
# ============================================================================

class ImpersonateRequest(BaseModel):
    """Request to create impersonation token"""
    duration_minutes: int = Field(
        60,
        ge=5,
        le=240,
        description="Token validity duration (5-240 minutes)"
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for impersonation (audit logged)"
    )


class ImpersonationTokenResponse(BaseModel):
    """Response with impersonation token"""
    impersonation_token: str
    user_id: int
    user_email: str
    organization_id: Optional[int]
    expires_at: datetime
    reason: str


class AuditLogFilter(BaseModel):
    """Filters for audit log query"""
    organization_id: Optional[int] = None
    user_id: Optional[int] = None
    action: Optional[str] = None
    limit: int = Field(100, ge=1, le=500)
    offset: int = Field(0, ge=0)


class AuditLogEntry(BaseModel):
    """Single audit log entry"""
    id: int
    admin_user_id: int
    admin_email: str
    action: str
    target_type: str
    target_id: Optional[int]
    details: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response for audit logs"""
    logs: List[AuditLogEntry]
    total_count: int
    limit: int
    offset: int


# ============================================================================
# GENERAL RESPONSE SCHEMAS
# ============================================================================

class AdminActionResponse(BaseModel):
    """Generic response for admin actions"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
