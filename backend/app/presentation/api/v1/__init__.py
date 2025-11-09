from fastapi import APIRouter
from app.presentation.api.v1 import users, auth, materials, machines, quality, shifts, maintenance, organizations, plants, departments, projects, production_logs, lanes

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(plants.router, prefix="/plants", tags=["plants"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(machines.router, prefix="/machines", tags=["machines"])
api_router.include_router(quality.router, tags=["quality"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
api_router.include_router(maintenance.router, tags=["maintenance"])
api_router.include_router(production_logs.router, prefix="/production-logs", tags=["production-logs"])
api_router.include_router(lanes.router, tags=["lanes"])

__all__ = ["api_router"]
