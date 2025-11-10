"""
Inventory Management API Endpoints

Provides RESTful API for material transactions:
- POST /api/v1/materials/{material_id}/receive - Goods receipt
- POST /api/v1/materials/{material_id}/issue - Goods issue
- POST /api/v1/materials/{material_id}/adjust - Inventory adjustment
- GET /api/v1/materials/{material_id}/transactions - Transaction history
- GET /api/v1/materials/{material_id}/inventory - Inventory balances
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user, get_user_context, _set_rls_context
from app.models.material import Material
from app.models.inventory import InventoryTransaction, TransactionType
from app.infrastructure.repositories.inventory_repository import (
    InventoryTransactionRepository,
    InventoryRepository
)
from app.application.use_cases.inventory import (
    ReceiveMaterialUseCase,
    IssueMaterialUseCase,
    AdjustInventoryUseCase
)
from app.application.use_cases.inventory.receive_material import ReceiveMaterialDTO
from app.application.use_cases.inventory.issue_material import IssueMaterialDTO
from app.application.use_cases.inventory.adjust_inventory import AdjustInventoryDTO
from app.presentation.schemas.inventory import (
    ReceiveMaterialRequest,
    IssueMaterialRequest,
    AdjustInventoryRequest,
    MaterialTransactionResponse,
    InventoryBalanceResponse,
    TransactionHistoryResponse,
    InventorySummaryResponse
)
from app.core.exceptions import (
    EntityNotFoundException,
    ValidationException,
    InsufficientInventoryException,
    BusinessRuleViolationException
)
from fastapi import Request

router = APIRouter(prefix="/materials", tags=["Inventory"])


# ============================================================================
# Dependency Injection Helpers
# ============================================================================

def get_inventory_transaction_repo(db: Session = Depends(get_db)) -> InventoryTransactionRepository:
    """Dependency injection for InventoryTransactionRepository."""
    return InventoryTransactionRepository(db)


def get_inventory_repo(db: Session = Depends(get_db)) -> InventoryRepository:
    """Dependency injection for InventoryRepository."""
    return InventoryRepository(db)


def get_receive_material_use_case(db: Session = Depends(get_db)) -> ReceiveMaterialUseCase:
    """Dependency injection for ReceiveMaterialUseCase."""
    return ReceiveMaterialUseCase(db)


def get_issue_material_use_case(db: Session = Depends(get_db)) -> IssueMaterialUseCase:
    """Dependency injection for IssueMaterialUseCase."""
    return IssueMaterialUseCase(db)


def get_adjust_inventory_use_case(db: Session = Depends(get_db)) -> AdjustInventoryUseCase:
    """Dependency injection for AdjustInventoryUseCase."""
    return AdjustInventoryUseCase(db)


# ============================================================================
# Material Transaction Endpoints
# ============================================================================

@router.post("/{material_id}/receive", response_model=MaterialTransactionResponse, status_code=status.HTTP_201_CREATED)
def receive_material(
    material_id: int,
    request_data: ReceiveMaterialRequest,
    request: Request,
    use_case: ReceiveMaterialUseCase = Depends(get_receive_material_use_case),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Receive material into inventory (goods receipt).

    ## Business Flow
    1. Validates material exists and is active
    2. Validates storage location exists
    3. Creates immutable inventory transaction
    4. Updates inventory quantity (creates new batch if needed)
    5. Updates material's aggregated quantity_on_hand
    6. Triggers low stock check (if applicable)

    ## Business Rules
    - **BR-MAT-007**: Material must exist and be active
    - **BR-MAT-008**: Quantity must be positive
    - **BR-MAT-009**: Storage location must exist and be active
    - **BR-MAT-010**: Batch number is required

    ## Permissions
    - Requires: `materials.receive` permission

    ## Example
    ```json
    {
        "storage_location_id": 1,
        "quantity": 100.0,
        "batch_number": "BATCH-2024-001",
        "transaction_reference": "PO-12345",
        "unit_cost": 25.50,
        "notes": "Received from supplier XYZ"
    }
    ```
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")
        user_id = user_context.get("id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Create DTO
        dto = ReceiveMaterialDTO(
            material_id=material_id,
            storage_location_id=request_data.storage_location_id,
            quantity=request_data.quantity,
            batch_number=request_data.batch_number,
            transaction_reference=request_data.transaction_reference,
            unit_cost=request_data.unit_cost,
            transaction_date=request_data.transaction_date,
            notes=request_data.notes,
            user_id=user_id,
            organization_id=organization_id,
            plant_id=plant_id
        )

        # Execute use case
        transaction = use_case.execute(dto)

        # Build response
        return _build_transaction_response(transaction, db)

    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{material_id}/issue", response_model=MaterialTransactionResponse, status_code=status.HTTP_201_CREATED)
def issue_material(
    material_id: int,
    request_data: IssueMaterialRequest,
    request: Request,
    use_case: IssueMaterialUseCase = Depends(get_issue_material_use_case),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Issue material from inventory (goods issue to work order, sales order, etc.).

    ## Business Flow
    1. Validates material exists and is active
    2. Validates sufficient inventory available
    3. Calculates cost using organization's costing method (FIFO/LIFO/Weighted Average)
    4. Creates immutable inventory transaction
    5. Updates inventory quantity (reduces stock)
    6. Updates work order actual_material_cost (if reference is work order)
    7. Triggers low stock alert (if threshold crossed)

    ## Business Rules
    - **BR-MAT-002**: Prevents negative inventory
    - **BR-MAT-013**: Validates sufficient available quantity
    - **BR-MAT-014**: Uses organization's costing method
    - **BR-MAT-015**: Updates work order costs automatically

    ## Permissions
    - Requires: `materials.issue` permission

    ## Example
    ```json
    {
        "storage_location_id": 1,
        "quantity": 50.0,
        "batch_number": "BATCH-2024-001",
        "transaction_reference": "WO-00123",
        "reference_type": "WORK_ORDER",
        "reference_id": 456,
        "notes": "Issued for production"
    }
    ```
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")
        user_id = user_context.get("id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Create DTO
        dto = IssueMaterialDTO(
            material_id=material_id,
            storage_location_id=request_data.storage_location_id,
            quantity=request_data.quantity,
            batch_number=request_data.batch_number,
            transaction_reference=request_data.transaction_reference,
            reference_type=request_data.reference_type.value,
            reference_id=request_data.reference_id,
            transaction_date=request_data.transaction_date,
            notes=request_data.notes,
            user_id=user_id,
            organization_id=organization_id,
            plant_id=plant_id
        )

        # Execute use case
        transaction = use_case.execute(dto)

        # Build response
        return _build_transaction_response(transaction, db)

    except InsufficientInventoryException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": e.message,
                "material_code": e.material_code,
                "requested": e.requested,
                "available": e.available
            }
        )
    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except BusinessRuleViolationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{material_id}/adjust", response_model=MaterialTransactionResponse, status_code=status.HTTP_201_CREATED)
def adjust_inventory(
    material_id: int,
    request_data: AdjustInventoryRequest,
    request: Request,
    use_case: AdjustInventoryUseCase = Depends(get_adjust_inventory_use_case),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adjust inventory (physical count correction).

    ## Business Flow
    1. Validates material and storage location exist
    2. Calculates adjustment quantity (target - current)
    3. Creates immutable inventory transaction (ADJUSTMENT)
    4. Updates inventory to target quantity
    5. Updates material's aggregated quantity

    ## Business Rules
    - **BR-MAT-017**: Adjustment can be positive or negative
    - **BR-MAT-018**: Target quantity must be non-negative
    - **BR-MAT-019**: Reason code is required for audit

    ## Permissions
    - Requires: `materials.adjust` permission

    ## Example
    ```json
    {
        "storage_location_id": 1,
        "batch_number": "BATCH-2024-001",
        "target_quantity": 95.0,
        "reason": "PHYSICAL_COUNT",
        "notes": "Annual physical count - 5 units damaged"
    }
    ```
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")
        user_id = user_context.get("id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Create DTO
        dto = AdjustInventoryDTO(
            material_id=material_id,
            storage_location_id=request_data.storage_location_id,
            batch_number=request_data.batch_number,
            target_quantity=request_data.target_quantity,
            reason=request_data.reason,
            transaction_date=request_data.transaction_date,
            notes=request_data.notes,
            user_id=user_id,
            organization_id=organization_id,
            plant_id=plant_id
        )

        # Execute use case
        transaction = use_case.execute(dto)

        # Build response
        return _build_transaction_response(transaction, db)

    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{material_id}/transactions", response_model=TransactionHistoryResponse)
def get_material_transactions(
    material_id: int,
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    request: Request = None,
    repo: InventoryTransactionRepository = Depends(get_inventory_transaction_repo),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for a material.

    Returns all inventory transactions (receipts, issues, adjustments, transfers)
    for the specified material, with optional filtering by date range and type.

    ## Query Parameters
    - **start_date**: Filter by transactions >= start_date
    - **end_date**: Filter by transactions <= end_date
    - **transaction_type**: GOODS_RECEIPT, GOODS_ISSUE, ADJUSTMENT, TRANSFER_IN, TRANSFER_OUT
    - **limit**: Maximum records to return (1-1000, default: 100)

    ## Permissions
    - Requires: `materials.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Get material
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found"
            )

        # Convert date to datetime
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None

        # Get transactions
        transactions = repo.get_by_material(
            material_id=material_id,
            start_date=start_datetime,
            end_date=end_datetime,
            transaction_type=transaction_type,
            limit=limit
        )

        # Build response
        return TransactionHistoryResponse(
            material_id=material.id,
            material_code=material.material_code,
            material_description=material.description,
            total_transactions=len(transactions),
            transactions=[_build_transaction_response(t, db) for t in transactions]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{material_id}/inventory", response_model=List[InventoryBalanceResponse])
def get_material_inventory(
    material_id: int,
    request: Request,
    repo: InventoryRepository = Depends(get_inventory_repo),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get inventory balances for a material (all locations and batches).

    Returns current inventory quantities across all storage locations and batches
    for the specified material.

    ## Response Fields
    - **quantity_on_hand**: Physical quantity in location
    - **quantity_reserved**: Quantity reserved for orders/production
    - **quantity_available**: On hand - reserved (available for issue)

    ## Permissions
    - Requires: `materials.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Get material
        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material with ID {material_id} not found"
            )

        # Get inventory records
        inventory_records = repo.get_by_material(material_id)

        # Build response
        return [_build_inventory_response(inv, db) for inv in inventory_records]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================

def _build_transaction_response(transaction: InventoryTransaction, db: Session) -> MaterialTransactionResponse:
    """Build transaction response with related data."""
    material = db.query(Material).filter(Material.id == transaction.material_id).first()
    from app.models.inventory import StorageLocation
    location = db.query(StorageLocation).filter(StorageLocation.id == transaction.storage_location_id).first()
    from app.models.material import UnitOfMeasure
    uom = db.query(UnitOfMeasure).filter(UnitOfMeasure.id == transaction.unit_of_measure_id).first()

    return MaterialTransactionResponse(
        id=transaction.id,
        organization_id=transaction.organization_id,
        plant_id=transaction.plant_id,
        material_id=transaction.material_id,
        material_code=material.material_code if material else None,
        material_description=material.description if material else None,
        storage_location_id=transaction.storage_location_id,
        storage_location_code=location.location_code if location else None,
        transaction_type=transaction.transaction_type,
        transaction_reference=transaction.transaction_reference,
        batch_number=transaction.batch_number,
        quantity=transaction.quantity,
        unit_of_measure=uom.code if uom else None,
        unit_cost=transaction.unit_cost,
        total_value=transaction.total_value,
        transaction_date=transaction.transaction_date,
        posted_by_user_id=transaction.posted_by_user_id,
        notes=transaction.notes,
        created_at=transaction.created_at
    )


def _build_inventory_response(inventory, db: Session) -> InventoryBalanceResponse:
    """Build inventory response with related data."""
    material = db.query(Material).filter(Material.id == inventory.material_id).first()
    from app.models.inventory import StorageLocation
    location = db.query(StorageLocation).filter(StorageLocation.id == inventory.storage_location_id).first()
    from app.models.material import UnitOfMeasure
    uom = db.query(UnitOfMeasure).filter(UnitOfMeasure.id == inventory.unit_of_measure_id).first()

    return InventoryBalanceResponse(
        id=inventory.id,
        organization_id=inventory.organization_id,
        plant_id=inventory.plant_id,
        material_id=inventory.material_id,
        material_code=material.material_code if material else None,
        material_description=material.description if material else None,
        storage_location_id=inventory.storage_location_id,
        storage_location_code=location.location_code if location else None,
        batch_number=inventory.batch_number,
        quantity_on_hand=inventory.quantity_on_hand,
        quantity_reserved=inventory.quantity_reserved,
        quantity_available=inventory.quantity_available,
        unit_of_measure=uom.code if uom else None,
        last_movement_date=inventory.last_movement_date,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at
    )
