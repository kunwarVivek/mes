from fastapi import APIRouter
from app.presentation.api.v1 import (
    users, auth, materials, machines, quality, shifts, maintenance,
    organizations, plants, departments, projects, production_logs, lanes, bom,
    roles, custom_fields, workflows, logistics, reporting, project_management,
    traceability, branding, infrastructure, inventory, inventory_alerts, metrics,
    scheduling, onboarding, health, billing, subscription, webhooks, platform_admin,
    jobs
)

api_router = APIRouter()

# Health Check Endpoints (no prefix - accessible at /api/v1/health)
api_router.include_router(health.router)

# Authentication & Onboarding
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])

# Subscription & Billing
api_router.include_router(subscription.router, tags=["subscription"])
api_router.include_router(billing.router, tags=["billing"])
api_router.include_router(webhooks.router, tags=["webhooks"])

# Platform Admin (requires superuser access)
api_router.include_router(platform_admin.router, tags=["platform-admin"])

# Scheduled Jobs (internal API only)
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(roles.router, prefix="/roles", tags=["rbac"])
api_router.include_router(custom_fields.router, tags=["configuration"])
api_router.include_router(workflows.router, tags=["workflow-engine"])
api_router.include_router(logistics.router, tags=["logistics"])
api_router.include_router(reporting.router, tags=["reporting"])
api_router.include_router(project_management.router, tags=["project-management"])
api_router.include_router(traceability.router, tags=["traceability"])
api_router.include_router(branding.router, tags=["branding"])
api_router.include_router(infrastructure.router, tags=["infrastructure"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(plants.router, prefix="/plants", tags=["plants"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(inventory.router, tags=["inventory"])  # Material transactions (receive, issue, adjust)
api_router.include_router(inventory_alerts.router, tags=["inventory-alerts"])  # Real-time alerts and alert history
api_router.include_router(scheduling.router, tags=["scheduling"])  # Gantt chart, conflict detection, validation
api_router.include_router(machines.router, prefix="/machines", tags=["machines"])
api_router.include_router(quality.router, tags=["quality"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
api_router.include_router(maintenance.router, tags=["maintenance"])
api_router.include_router(production_logs.router, prefix="/production-logs", tags=["production-logs"])
api_router.include_router(lanes.router, tags=["lanes"])
api_router.include_router(bom.router, prefix="/bom", tags=["bom"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

__all__ = ["api_router"]
