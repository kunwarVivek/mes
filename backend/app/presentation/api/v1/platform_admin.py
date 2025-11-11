"""
Platform Admin API Endpoints

Comprehensive admin dashboard for managing organizations, subscriptions,
metrics, usage analytics, and support tools across the entire platform.

Security:
- All endpoints require platform admin privileges (is_superuser=True)
- All actions are audit logged for compliance
- Cross-organization access bypasses RLS
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.infrastructure.security.admin_required import (
    require_platform_admin,
    log_admin_action,
    AdminActionLogger
)
from app.domain.entities.user import User
from app.application.services.platform_admin_service import PlatformAdminService
from app.infrastructure.logging.audit_logger import AuditLogger
from app.presentation.schemas.platform_admin import (
    # Organization
    OrganizationListRequest,
    OrganizationListResponse,
    OrganizationDetailResponse,
    OrganizationUpdateRequest,
    # Subscription
    SubscriptionListRequest,
    SubscriptionListResponse,
    ExtendTrialRequest,
    SuspendSubscriptionRequest,
    ReactivateSubscriptionRequest,
    SubscriptionActionResponse,
    # Metrics
    PlatformMetricsResponse,
    GrowthMetricsResponse,
    # Usage
    TopOrganizationRequest,
    TopOrganizationsResponse,
    UsageViolationsResponse,
    UsageMetric,
    # Support
    ImpersonateRequest,
    ImpersonationTokenResponse,
    AuditLogFilter,
    AuditLogResponse,
    AuditLogEntry,
    # General
    AdminActionResponse,
    OrganizationStatusFilter,
    SubscriptionStatusFilter
)
from app.core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    BusinessRuleException
)

router = APIRouter(prefix="/admin", tags=["Platform Admin"])
logger = logging.getLogger(__name__)


def get_admin_service(db: Session = Depends(get_db)) -> PlatformAdminService:
    """Dependency injection for PlatformAdminService"""
    return PlatformAdminService(db)


def get_audit_logger(db: Session = Depends(get_db)) -> AuditLogger:
    """Dependency injection for AuditLogger"""
    return AuditLogger(db)


# ============================================================================
# ORGANIZATION MANAGEMENT
# ============================================================================

@router.get("/organizations", response_model=OrganizationListResponse)
async def list_organizations(
    search: Optional[str] = Query(None, description="Search by name, subdomain, or org_code"),
    status: OrganizationStatusFilter = Query(
        OrganizationStatusFilter.ALL,
        description="Filter by active status"
    ),
    tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    limit: int = Query(50, ge=1, le=200, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    List all organizations with filters and pagination.

    **Admin Access Required**: Platform administrators only

    Provides cross-organization visibility with:
    - Search by name, org_code, or subdomain
    - Filter by active status
    - Filter by subscription tier
    - Pagination support

    **Audit Logged**: Yes

    Args:
        search: Search term for name/code/subdomain
        status: Filter by active status (active/inactive/all)
        tier: Filter by subscription tier
        limit: Results per page (1-200)
        offset: Pagination offset
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        OrganizationListResponse with organizations list and pagination info
    """
    try:
        log_admin_action(
            admin_user=admin_user,
            action="list_organizations",
            target_type="organization",
            details={
                "search": search,
                "status": status.value,
                "tier": tier,
                "limit": limit,
                "offset": offset
            },
            db=db
        )

        organizations, total_count, has_more = admin_service.list_organizations(
            search=search,
            status=status.value if status != OrganizationStatusFilter.ALL else None,
            tier=tier,
            limit=limit,
            offset=offset
        )

        return OrganizationListResponse(
            organizations=organizations,
            total_count=total_count,
            has_more=has_more,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list organizations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list organizations"
        )


@router.get("/organizations/{organization_id}", response_model=OrganizationDetailResponse)
async def get_organization(
    organization_id: int,
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Get detailed organization information.

    **Admin Access Required**: Platform administrators only

    Returns complete organization profile including:
    - Organization details
    - Subscription information
    - Usage statistics
    - Activity metrics

    **Audit Logged**: Yes

    Args:
        organization_id: Organization ID
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        OrganizationDetailResponse with complete org profile

    Raises:
        HTTPException 404: Organization not found
    """
    try:
        log_admin_action(
            admin_user=admin_user,
            action="get_organization_details",
            target_type="organization",
            target_id=organization_id,
            db=db
        )

        org_details = admin_service.get_organization_details(organization_id)

        return OrganizationDetailResponse(**org_details)

    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get organization: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization"
        )


@router.patch("/organizations/{organization_id}", response_model=OrganizationDetailResponse)
async def update_organization(
    organization_id: int,
    request: OrganizationUpdateRequest,
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Update organization settings.

    **Admin Access Required**: Platform administrators only

    Allows updating:
    - is_active: Activate or deactivate organization
    - org_name: Update organization name

    Common use cases:
    - Suspending non-paying customers (set is_active=False)
    - Reactivating organizations after payment issues resolved
    - Correcting organization name typos

    **Audit Logged**: Yes (with reason if provided)

    Args:
        organization_id: Organization ID
        request: Update request with changes and optional reason
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        OrganizationDetailResponse with updated organization

    Raises:
        HTTPException 404: Organization not found
    """
    try:
        updates = {}
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.org_name is not None:
            updates["org_name"] = request.org_name

        with AdminActionLogger(
            admin_user=admin_user,
            action="update_organization",
            target_type="organization",
            target_id=organization_id,
            details={
                "updates": updates,
                "reason": request.reason
            },
            db=db
        ):
            org_details = admin_service.update_organization(
                organization_id=organization_id,
                updates=updates
            )

        return OrganizationDetailResponse(**org_details)

    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update organization: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization"
        )


# ============================================================================
# SUBSCRIPTION MANAGEMENT
# ============================================================================

@router.get("/subscriptions", response_model=SubscriptionListResponse)
async def list_subscriptions(
    status: Optional[SubscriptionStatusFilter] = Query(
        None,
        description="Filter by subscription status"
    ),
    expires_soon: bool = Query(
        False,
        description="Filter trials expiring in next 7 days"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    List subscriptions across all organizations.

    **Admin Access Required**: Platform administrators only

    Filters:
    - status: trial, active, cancelled, past_due, suspended
    - expires_soon: trials expiring within 7 days (for proactive outreach)

    **Audit Logged**: Yes

    Args:
        status: Filter by subscription status
        expires_soon: Filter trials expiring soon
        limit: Results per page
        offset: Pagination offset
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        SubscriptionListResponse with subscriptions and count
    """
    try:
        log_admin_action(
            admin_user=admin_user,
            action="list_subscriptions",
            target_type="subscription",
            details={
                "status": status.value if status else None,
                "expires_soon": expires_soon,
                "limit": limit,
                "offset": offset
            },
            db=db
        )

        subscriptions, total_count = admin_service.list_subscriptions(
            status=status.value if status and status != SubscriptionStatusFilter.ALL else None,
            expires_soon=expires_soon,
            limit=limit,
            offset=offset
        )

        return SubscriptionListResponse(
            subscriptions=subscriptions,
            total_count=total_count,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list subscriptions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list subscriptions"
        )


@router.post("/subscriptions/{subscription_id}/extend-trial", response_model=SubscriptionActionResponse)
async def extend_trial(
    subscription_id: int,
    request: ExtendTrialRequest,
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Extend trial period for subscription.

    **Admin Access Required**: Platform administrators only

    Use cases:
    - Customer success team extending trials during sales process
    - Resolving technical issues that impacted trial experience
    - Strategic accounts requiring additional evaluation time

    **Audit Logged**: Yes (with reason)

    Args:
        subscription_id: Subscription ID
        request: Extension request with days and reason
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        SubscriptionActionResponse with updated subscription

    Raises:
        HTTPException 404: Subscription not found
        HTTPException 400: Subscription not in trial status
    """
    try:
        with AdminActionLogger(
            admin_user=admin_user,
            action="extend_trial",
            target_type="subscription",
            target_id=subscription_id,
            details={
                "days": request.days,
                "reason": request.reason
            },
            db=db
        ):
            subscription = admin_service.extend_trial(
                subscription_id=subscription_id,
                days=request.days,
                reason=request.reason
            )

        return SubscriptionActionResponse(
            success=True,
            message=f"Trial extended by {request.days} days",
            subscription=subscription
        )

    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to extend trial: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extend trial"
        )


@router.post("/subscriptions/{subscription_id}/suspend", response_model=SubscriptionActionResponse)
async def suspend_subscription(
    subscription_id: int,
    request: SuspendSubscriptionRequest,
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Suspend subscription manually.

    **Admin Access Required**: Platform administrators only

    Use cases:
    - Payment fraud detected
    - Terms of service violations
    - Non-payment after multiple attempts
    - Account security concerns

    **WARNING**: This immediately blocks organization access.

    **Audit Logged**: Yes (with reason)

    Args:
        subscription_id: Subscription ID
        request: Suspension request with reason
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        SubscriptionActionResponse with updated subscription

    Raises:
        HTTPException 404: Subscription not found
    """
    try:
        with AdminActionLogger(
            admin_user=admin_user,
            action="suspend_subscription",
            target_type="subscription",
            target_id=subscription_id,
            details={"reason": request.reason},
            db=db
        ):
            subscription = admin_service.suspend_subscription(
                subscription_id=subscription_id,
                reason=request.reason
            )

        return SubscriptionActionResponse(
            success=True,
            message="Subscription suspended",
            subscription=subscription
        )

    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to suspend subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend subscription"
        )


@router.post("/subscriptions/{subscription_id}/reactivate", response_model=SubscriptionActionResponse)
async def reactivate_subscription(
    subscription_id: int,
    request: ReactivateSubscriptionRequest,
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Reactivate suspended subscription.

    **Admin Access Required**: Platform administrators only

    Use cases:
    - Payment issue resolved
    - False positive fraud detection
    - Customer appeal approved
    - Account verification completed

    **Audit Logged**: Yes (with reason)

    Args:
        subscription_id: Subscription ID
        request: Reactivation request with reason
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        SubscriptionActionResponse with updated subscription

    Raises:
        HTTPException 404: Subscription not found
        HTTPException 400: Subscription not suspended
    """
    try:
        with AdminActionLogger(
            admin_user=admin_user,
            action="reactivate_subscription",
            target_type="subscription",
            target_id=subscription_id,
            details={"reason": request.reason},
            db=db
        ):
            subscription = admin_service.reactivate_subscription(
                subscription_id=subscription_id,
                reason=request.reason
            )

        return SubscriptionActionResponse(
            success=True,
            message="Subscription reactivated",
            subscription=subscription
        )

    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to reactivate subscription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate subscription"
        )


# ============================================================================
# PLATFORM METRICS
# ============================================================================

@router.get("/metrics", response_model=PlatformMetricsResponse)
async def get_platform_metrics(
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Get platform-wide KPI metrics.

    **Admin Access Required**: Platform administrators only

    Returns:
    - Organization counts (total, active, inactive)
    - Subscription counts by status
    - Monthly Recurring Revenue (MRR)
    - Total users across platform
    - Total plants
    - Storage usage

    **Audit Logged**: Yes

    Args:
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        PlatformMetricsResponse with all KPIs
    """
    try:
        log_admin_action(
            admin_user=admin_user,
            action="get_platform_metrics",
            target_type="platform",
            db=db
        )

        metrics = admin_service.get_platform_metrics()

        return PlatformMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Failed to get platform metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get platform metrics"
        )


@router.get("/metrics/growth", response_model=GrowthMetricsResponse)
async def get_growth_metrics(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Get growth metrics over time period.

    **Admin Access Required**: Platform administrators only

    Returns:
    - New signups by day
    - Trial conversions by day
    - Churn count and rate
    - MRR growth

    **Audit Logged**: Yes

    Args:
        period: Time period (7d, 30d, 90d)
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        GrowthMetricsResponse with growth data

    Raises:
        HTTPException 400: Invalid period
    """
    try:
        # Parse period
        period_map = {"7d": 7, "30d": 30, "90d": 90}
        if period not in period_map:
            raise ValidationException("Period must be one of: 7d, 30d, 90d")

        period_days = period_map[period]

        log_admin_action(
            admin_user=admin_user,
            action="get_growth_metrics",
            target_type="platform",
            details={"period": period},
            db=db
        )

        metrics = admin_service.get_growth_metrics(period_days=period_days)

        return GrowthMetricsResponse(**metrics)

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get growth metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get growth metrics"
        )


# ============================================================================
# USAGE ANALYTICS
# ============================================================================

@router.get("/usage/top-organizations", response_model=TopOrganizationsResponse)
async def get_top_organizations(
    metric: UsageMetric = Query(..., description="Metric to sort by"),
    limit: int = Query(10, ge=1, le=50, description="Number of organizations"),
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Get top organizations by usage metric.

    **Admin Access Required**: Platform administrators only

    Useful for:
    - Capacity planning
    - Identifying power users
    - Account management prioritization
    - Resource allocation

    **Audit Logged**: Yes

    Args:
        metric: Metric to sort by (users, plants, storage)
        limit: Number of organizations (1-50)
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        TopOrganizationsResponse with ranked organizations
    """
    try:
        log_admin_action(
            admin_user=admin_user,
            action="get_top_organizations",
            target_type="platform",
            details={"metric": metric.value, "limit": limit},
            db=db
        )

        result = admin_service.get_top_organizations(
            metric=metric.value,
            limit=limit
        )

        return TopOrganizationsResponse(**result)

    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get top organizations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top organizations"
        )


@router.get("/usage/violations", response_model=UsageViolationsResponse)
async def get_usage_violations(
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Get organizations exceeding their subscription limits.

    **Admin Access Required**: Platform administrators only

    Identifies organizations that have exceeded:
    - User limits
    - Plant limits
    - Storage limits

    Use cases:
    - Proactive account management
    - Upsell opportunities
    - Limit enforcement
    - Fair usage monitoring

    **Audit Logged**: Yes

    Args:
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        UsageViolationsResponse with violations list
    """
    try:
        log_admin_action(
            admin_user=admin_user,
            action="get_usage_violations",
            target_type="platform",
            db=db
        )

        result = admin_service.get_usage_violations()

        return UsageViolationsResponse(**result)

    except Exception as e:
        logger.error(f"Failed to get usage violations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage violations"
        )


# ============================================================================
# SUPPORT TOOLS
# ============================================================================

@router.post("/impersonate/{user_id}", response_model=ImpersonationTokenResponse)
async def impersonate_user(
    user_id: int,
    request: ImpersonateRequest,
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    admin_service: PlatformAdminService = Depends(get_admin_service)
):
    """
    Generate impersonation token for support.

    **Admin Access Required**: Platform administrators only

    **SECURITY CRITICAL**: This creates a time-limited JWT token that allows
    admin to access the system as the target user.

    Use cases:
    - Debugging user-reported issues
    - Reproducing problems in user's environment
    - Customer support demonstrations
    - Training and onboarding assistance

    **Token Characteristics**:
    - Time-limited (5-240 minutes, default 60)
    - Includes impersonated_by field for audit
    - Logged with reason for compliance

    **Audit Logged**: Yes (with reason)

    Args:
        user_id: User ID to impersonate
        request: Impersonation request with duration and reason
        admin_user: Authenticated admin user
        db: Database session
        admin_service: Admin service

    Returns:
        ImpersonationTokenResponse with token and metadata

    Raises:
        HTTPException 404: User not found
    """
    try:
        with AdminActionLogger(
            admin_user=admin_user,
            action="impersonate_user",
            target_type="user",
            target_id=user_id,
            details={
                "duration_minutes": request.duration_minutes,
                "reason": request.reason
            },
            db=db
        ):
            result = admin_service.create_impersonation_token(
                user_id=user_id,
                admin_id=admin_user.id,
                duration_minutes=request.duration_minutes
            )

        result["reason"] = request.reason

        return ImpersonationTokenResponse(**result)

    except ResourceNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create impersonation token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create impersonation token"
        )


@router.get("/audit-logs", response_model=AuditLogResponse)
async def get_audit_logs(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    user_id: Optional[int] = Query(None, description="Filter by user"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    View audit logs across organizations.

    **Admin Access Required**: Platform administrators only

    Query admin action history with filters:
    - By organization (target_type=organization, target_id=org_id)
    - By user (admin_user_id or target_type=user)
    - By action type

    **Audit Logged**: Yes (viewing audit logs is itself logged)

    Args:
        organization_id: Filter by organization
        user_id: Filter by user
        action: Filter by action type
        limit: Results per page
        offset: Pagination offset
        admin_user: Authenticated admin user
        db: Database session
        audit_logger: Audit logger service

    Returns:
        AuditLogResponse with logs and pagination
    """
    try:
        # Log this audit log access
        log_admin_action(
            admin_user=admin_user,
            action="view_audit_logs",
            target_type="audit_log",
            details={
                "organization_id": organization_id,
                "user_id": user_id,
                "action": action
            },
            db=db
        )

        # Determine filters
        filters = {}
        if user_id:
            filters["admin_user_id"] = user_id
        if action:
            filters["action"] = action
        if organization_id:
            filters["target_type"] = "organization"
            filters["target_id"] = organization_id

        # Get logs
        logs, total_count = audit_logger.get_logs(
            limit=limit,
            offset=offset,
            **filters
        )

        # Convert to response schema
        log_entries = []
        for log in logs:
            # Get admin email from UserModel
            from app.infrastructure.persistence.models import UserModel
            admin = db.query(UserModel).filter(
                UserModel.id == log.admin_user_id
            ).first()

            log_entries.append(AuditLogEntry(
                id=log.id,
                admin_user_id=log.admin_user_id,
                admin_email=admin.email if admin else "unknown",
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                details=log.details or {},
                created_at=log.created_at
            ))

        return AuditLogResponse(
            logs=log_entries,
            total_count=total_count,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs"
        )
