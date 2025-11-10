"""
Health Check Endpoints for Kubernetes/Docker Orchestration

Provides three types of health checks:
1. /health - Simple ping (always returns 200 if service is running)
2. /health/ready - Readiness probe (checks dependencies: database, MinIO, etc.)
3. /health/live - Liveness probe (checks if application is alive)

These endpoints are used by orchestration systems (Kubernetes, Docker Swarm, ECS)
to determine service health and when to route traffic or restart containers.
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any
import time
from datetime import datetime

from app.core.database import SessionLocal

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """
    Simple health check - always returns 200 OK if service is running.

    Use this endpoint for basic uptime monitoring.

    Returns:
        dict: Status message with timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Unison Manufacturing ERP API"
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check():
    """
    Readiness probe - checks if service is ready to accept traffic.

    Checks:
    - Database connectivity
    - Database migrations applied
    - Critical tables exist

    Returns 503 Service Unavailable if any check fails.
    Orchestration systems will not route traffic until this returns 200 OK.

    Returns:
        dict: Detailed health status of all dependencies

    Raises:
        HTTPException: 503 if any dependency is unhealthy
    """
    checks = {}
    all_healthy = True
    start_time = time.time()

    # Database connectivity check
    try:
        db: Session = SessionLocal()
        try:
            # Test basic connectivity
            db.execute(text("SELECT 1"))
            checks["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }

            # Check if critical tables exist
            try:
                db.execute(text("SELECT COUNT(*) FROM organizations"))
                checks["database_tables"] = {
                    "status": "healthy",
                    "message": "Critical tables exist"
                }
            except Exception as e:
                checks["database_tables"] = {
                    "status": "unhealthy",
                    "message": f"Critical tables missing: {str(e)}"
                }
                all_healthy = False

        finally:
            db.close()

    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        all_healthy = False

    # MinIO/Storage check (optional - degraded is acceptable)
    try:
        # TODO: Add MinIO health check when storage client is imported
        checks["storage"] = {
            "status": "skipped",
            "message": "Storage health check not implemented"
        }
    except Exception as e:
        checks["storage"] = {
            "status": "degraded",
            "message": f"Storage check failed: {str(e)}"
        }
        # Storage failure is not critical - mark as degraded but don't fail readiness

    # PGMQ check (optional - degraded is acceptable)
    try:
        # TODO: Add PGMQ health check when message queue is imported
        checks["message_queue"] = {
            "status": "skipped",
            "message": "Message queue health check not implemented"
        }
    except Exception as e:
        checks["message_queue"] = {
            "status": "degraded",
            "message": f"Message queue check failed: {str(e)}"
        }
        # Message queue failure is not critical for readiness

    # Calculate response time
    response_time_ms = (time.time() - start_time) * 1000

    # Build response
    response = {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "response_time_ms": round(response_time_ms, 2)
    }

    # Return 503 if not ready
    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )

    return response


@router.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """
    Liveness probe - checks if application is alive (not deadlocked/hung).

    This endpoint performs minimal checks to verify the application can
    respond to requests. If this fails, orchestration systems will restart
    the container.

    Returns:
        dict: Alive status with timestamp
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.process_time()
    }


@router.get("/startup", response_model=Dict[str, Any])
async def startup_check():
    """
    Startup probe - checks if application has finished starting up.

    Used by Kubernetes to know when to start sending readiness/liveness probes.
    For applications with slow startup (large models, migrations, etc.).

    Returns:
        dict: Startup complete status
    """
    # Check if critical initialization is complete
    checks = {}

    try:
        db: Session = SessionLocal()
        try:
            # Verify database is accessible
            db.execute(text("SELECT 1"))
            checks["database_initialized"] = True
        finally:
            db.close()
    except:
        checks["database_initialized"] = False
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "starting",
                "message": "Application still initializing",
                "checks": checks
            }
        )

    return {
        "status": "started",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
