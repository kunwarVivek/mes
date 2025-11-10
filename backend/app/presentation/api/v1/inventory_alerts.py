"""
Inventory Alerts API Endpoints

Provides real-time inventory alerts via WebSocket and alert history management.

WebSocket Endpoint:
- ws://localhost:8000/api/v1/inventory/alerts/ws - Real-time alert stream

REST Endpoints:
- GET /api/v1/inventory/alerts - Get alert history
- POST /api/v1/inventory/alerts/{id}/acknowledge - Acknowledge alert
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import asyncio
import logging

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_user_context
from app.models.inventory_alert import InventoryAlert
from app.models.material import Material
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory/alerts", tags=["Inventory Alerts"])


# ============================================================================
# Pydantic Schemas (inline for now)
# ============================================================================

from pydantic import BaseModel, Field

class InventoryAlertResponse(BaseModel):
    """Response schema for inventory alert"""
    id: int
    organization_id: int
    plant_id: int
    material_id: int
    material_code: Optional[str] = None
    material_description: Optional[str] = None
    storage_location_id: Optional[int] = None
    alert_type: str = Field(description="LOW_STOCK, OUT_OF_STOCK, RESTOCKED")
    severity: str = Field(description="INFO, WARNING, CRITICAL")
    message: str
    quantity_on_hand: float
    reorder_point: Optional[float] = None
    max_stock_level: Optional[float] = None
    is_acknowledged: bool
    acknowledged_by_user_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime


class InventoryAlertListResponse(BaseModel):
    """Response schema for alert list"""
    total: int
    unacknowledged_count: int
    critical_count: int
    alerts: List[InventoryAlertResponse]


class AcknowledgeAlertRequest(BaseModel):
    """Request schema for acknowledging alert"""
    notes: Optional[str] = None


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time inventory alerts.

    Listens to PostgreSQL NOTIFY on 'inventory_alerts' channel and broadcasts
    to all connected WebSocket clients.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.db_listener_task = None

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def listen_to_database(self, db: Session):
        """
        Listen to PostgreSQL NOTIFY on 'inventory_alerts' channel.

        This runs in a background task and broadcasts notifications to all WebSocket clients.
        """
        try:
            # Get raw connection
            raw_conn = db.connection().connection

            # Set up LISTEN
            cursor = raw_conn.cursor()
            cursor.execute("LISTEN inventory_alerts;")
            logger.info("Started listening to inventory_alerts channel")

            while True:
                # Poll for notifications (non-blocking with timeout)
                raw_conn.poll()

                # Check for notifications
                while raw_conn.notifies:
                    notify = raw_conn.notifies.pop(0)
                    try:
                        # Parse notification payload (JSON string)
                        alert_data = json.loads(notify.payload)
                        logger.info(f"Received inventory alert: {alert_data['alert_type']} for material {alert_data['material_code']}")

                        # Broadcast to all WebSocket clients
                        await self.broadcast(alert_data)

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse notification payload: {e}")
                    except Exception as e:
                        logger.error(f"Error processing notification: {e}")

                # Sleep briefly to avoid busy-waiting
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Database listener error: {e}")
        finally:
            cursor.close()


# Global connection manager
manager = WebSocketConnectionManager()


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_inventory_alerts(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time inventory alerts.

    **Connection**: ws://localhost:8000/api/v1/inventory/alerts/ws

    **Message Format**:
    ```json
    {
        "alert_type": "LOW_STOCK",
        "severity": "WARNING",
        "material_id": 123,
        "material_code": "MAT-001",
        "message": "Material MAT-001 is below reorder point",
        "quantity_on_hand": 45.0,
        "reorder_point": 100.0,
        "organization_id": 1,
        "plant_id": 10,
        "timestamp": "2024-11-10T15:30:00Z"
    }
    ```

    **Alert Types**:
    - LOW_STOCK: Inventory below reorder point
    - OUT_OF_STOCK: Inventory is zero
    - RESTOCKED: Inventory restored above reorder point

    **Severity Levels**:
    - INFO: Quantity 75-100% of reorder point
    - WARNING: Quantity 50-75% of reorder point
    - CRITICAL: Quantity <50% of reorder point or out of stock
    """
    await manager.connect(websocket)

    # Start database listener if not already running
    if manager.db_listener_task is None or manager.db_listener_task.done():
        manager.db_listener_task = asyncio.create_task(manager.listen_to_database(db))
        logger.info("Started database listener task")

    try:
        # Keep connection alive and handle client messages
        while True:
            # Wait for client message (ping/pong for keep-alive)
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected gracefully")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/", response_model=InventoryAlertListResponse)
def get_inventory_alerts(
    is_acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgement status"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, CRITICAL)"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type (LOW_STOCK, OUT_OF_STOCK, RESTOCKED)"),
    material_id: Optional[int] = Query(None, description="Filter by material ID"),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back (default: 7)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum alerts to return"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Get inventory alert history with filtering.

    Returns alerts from the last N days (default: 7 days) with optional filters.

    **Query Parameters**:
    - **is_acknowledged**: Filter by acknowledgement status (true/false)
    - **severity**: Filter by severity (INFO, WARNING, CRITICAL)
    - **alert_type**: Filter by type (LOW_STOCK, OUT_OF_STOCK, RESTOCKED)
    - **material_id**: Filter by specific material
    - **days**: Number of days to look back (1-90, default: 7)
    - **limit**: Maximum alerts to return (1-1000, default: 100)

    **Response**:
    - **total**: Total alerts matching filters
    - **unacknowledged_count**: Number of unacknowledged alerts
    - **critical_count**: Number of critical alerts
    - **alerts**: List of alert details
    """
    try:
        # Get user context for RLS
        from app.infrastructure.security.dependencies import _set_rls_context
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Build query
        query = db.query(InventoryAlert)

        # Apply filters
        if is_acknowledged is not None:
            query = query.filter(InventoryAlert.is_acknowledged == is_acknowledged)

        if severity:
            query = query.filter(InventoryAlert.severity == severity.upper())

        if alert_type:
            query = query.filter(InventoryAlert.alert_type == alert_type.upper())

        if material_id:
            query = query.filter(InventoryAlert.material_id == material_id)

        # Date range filter
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(InventoryAlert.created_at >= start_date)

        # Order by created_at DESC (newest first)
        query = query.order_by(InventoryAlert.created_at.desc())

        # Get total count before limit
        total_count = query.count()

        # Apply limit
        alerts = query.limit(limit).all()

        # Calculate counts
        unacknowledged_count = db.query(InventoryAlert).filter(
            InventoryAlert.is_acknowledged == False,
            InventoryAlert.created_at >= start_date
        ).count()

        critical_count = db.query(InventoryAlert).filter(
            InventoryAlert.severity == 'CRITICAL',
            InventoryAlert.is_acknowledged == False,
            InventoryAlert.created_at >= start_date
        ).count()

        # Build response
        alert_responses = []
        for alert in alerts:
            # Get material details
            material = db.query(Material).filter(Material.id == alert.material_id).first()

            alert_responses.append(InventoryAlertResponse(
                id=alert.id,
                organization_id=alert.organization_id,
                plant_id=alert.plant_id,
                material_id=alert.material_id,
                material_code=material.material_code if material else None,
                material_description=material.description if material else None,
                storage_location_id=alert.storage_location_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
                quantity_on_hand=float(alert.quantity_on_hand),
                reorder_point=float(alert.reorder_point) if alert.reorder_point else None,
                max_stock_level=float(alert.max_stock_level) if alert.max_stock_level else None,
                is_acknowledged=alert.is_acknowledged,
                acknowledged_by_user_id=alert.acknowledged_by_user_id,
                acknowledged_at=alert.acknowledged_at,
                created_at=alert.created_at
            ))

        return InventoryAlertListResponse(
            total=total_count,
            unacknowledged_count=unacknowledged_count,
            critical_count=critical_count,
            alerts=alert_responses
        )

    except Exception as e:
        logger.error(f"Failed to fetch alerts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{alert_id}/acknowledge", response_model=InventoryAlertResponse)
def acknowledge_alert(
    alert_id: int,
    request_data: AcknowledgeAlertRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Acknowledge an inventory alert.

    Marks the alert as acknowledged and records the user and timestamp.

    **Business Rules**:
    - Alert must exist and be unacknowledged
    - User ID is recorded from authenticated session
    - Timestamp is set to current time

    **Permissions**:
    - Requires: `inventory.manage` permission
    """
    try:
        # Get user context
        from app.infrastructure.security.dependencies import _set_rls_context
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")
        user_id = user_context.get("id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Get alert
        alert = db.query(InventoryAlert).filter(InventoryAlert.id == alert_id).first()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found"
            )

        if alert.is_acknowledged:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert is already acknowledged"
            )

        # Update alert
        alert.is_acknowledged = True
        alert.acknowledged_by_user_id = user_id
        alert.acknowledged_at = datetime.utcnow()

        db.commit()
        db.refresh(alert)

        # Get material details for response
        material = db.query(Material).filter(Material.id == alert.material_id).first()

        logger.info(f"Alert {alert_id} acknowledged by user {user_id}")

        return InventoryAlertResponse(
            id=alert.id,
            organization_id=alert.organization_id,
            plant_id=alert.plant_id,
            material_id=alert.material_id,
            material_code=material.material_code if material else None,
            material_description=material.description if material else None,
            storage_location_id=alert.storage_location_id,
            alert_type=alert.alert_type,
            severity=alert.severity,
            message=alert.message,
            quantity_on_hand=float(alert.quantity_on_hand),
            reorder_point=float(alert.reorder_point) if alert.reorder_point else None,
            max_stock_level=float(alert.max_stock_level) if alert.max_stock_level else None,
            is_acknowledged=alert.is_acknowledged,
            acknowledged_by_user_id=alert.acknowledged_by_user_id,
            acknowledged_at=alert.acknowledged_at,
            created_at=alert.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
