from fastapi import APIRouter
from app.presentation.api.v1 import users, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["api_router"]
