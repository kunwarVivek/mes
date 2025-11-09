from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from fastapi import Request
from app.core.config import settings
from app.infrastructure.database.rls import set_rls_context, clear_rls_context
import logging

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db(request: Request = None) -> Generator[Session, None, None]:
    """
    Database session dependency with automatic RLS context management.

    This dependency:
    1. Creates a new database session
    2. Automatically sets RLS context if user is authenticated (from request.state.user)
    3. Yields the session for use in endpoint
    4. Clears RLS context and closes session on cleanup

    Args:
        request: FastAPI Request object (optional, injected by dependency)

    Yields:
        SQLAlchemy Session with RLS context set for authenticated users

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            # RLS context automatically set from JWT claims
            return db.query(Item).all()  # Filtered by RLS policies
    """
    db = SessionLocal()
    rls_context_set = False

    try:
        logger.debug("Database session created")

        # Set RLS context if user is authenticated
        if request is not None and hasattr(request, 'state') and hasattr(request.state, 'user'):
            user = request.state.user
            org_id = user.get('organization_id')
            plant_id = user.get('plant_id')

            # Only set RLS context if organization_id is present
            if org_id is not None:
                try:
                    set_rls_context(db, organization_id=org_id, plant_id=plant_id)
                    rls_context_set = True
                    logger.debug(f"RLS context set for user {user.get('id')}: org_id={org_id}, plant_id={plant_id}")
                except Exception as e:
                    # Log warning but don't fail the request (degraded mode)
                    logger.warning(f"Failed to set RLS context: {e}")

        yield db

    finally:
        # Clear RLS context if it was set
        if rls_context_set:
            try:
                clear_rls_context(db)
                logger.debug("RLS context cleared")
            except Exception as e:
                logger.warning(f"Failed to clear RLS context: {e}")

        db.close()
        logger.debug("Database session closed")
