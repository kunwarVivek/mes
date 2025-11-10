"""
Scheduling API Endpoints

Provides RESTful API for Gantt chart visualization and schedule management:
- GET /api/v1/scheduling/gantt - Get Gantt chart data
- GET /api/v1/scheduling/conflicts - Detect scheduling conflicts
- POST /api/v1/scheduling/validate - Validate schedule constraints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.infrastructure.security.dependencies import get_current_user, get_user_context, _set_rls_context
from app.application.use_cases.scheduling import (
    GetGanttChartUseCase,
    DetectConflictsUseCase,
    ValidateScheduleUseCase
)
from app.application.use_cases.scheduling.get_gantt_chart import GetGanttChartDTO
from app.application.use_cases.scheduling.detect_conflicts import DetectConflictsDTO
from app.application.use_cases.scheduling.validate_schedule import ValidateScheduleDTO
from app.presentation.schemas.scheduling import (
    GetGanttChartRequest,
    ValidateScheduleRequest,
    GanttChartResponse,
    GanttTaskResponse,
    ConflictResponse,
    ConflictsListResponse,
    ValidationResultResponse
)
from app.core.exceptions import (
    ValidationException,
    EntityNotFoundException
)
from fastapi import Request

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])


# ============================================================================
# Dependency Injection Helpers
# ============================================================================

def get_gantt_chart_use_case(db: Session = Depends(get_db)) -> GetGanttChartUseCase:
    """Dependency injection for GetGanttChartUseCase."""
    return GetGanttChartUseCase(db)


def get_detect_conflicts_use_case(db: Session = Depends(get_db)) -> DetectConflictsUseCase:
    """Dependency injection for DetectConflictsUseCase."""
    return DetectConflictsUseCase(db)


def get_validate_schedule_use_case(db: Session = Depends(get_db)) -> ValidateScheduleUseCase:
    """Dependency injection for ValidateScheduleUseCase."""
    return ValidateScheduleUseCase(db)


# ============================================================================
# Scheduling Endpoints
# ============================================================================

@router.get("/gantt", response_model=GanttChartResponse)
def get_gantt_chart(
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    lane_ids: Optional[str] = Query(None, description="Comma-separated lane IDs"),
    include_completed: bool = Query(False, description="Include completed work orders"),
    request: Request = None,
    use_case: GetGanttChartUseCase = Depends(get_gantt_chart_use_case),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Gantt chart data for visual scheduling.

    ## Business Flow
    1. Queries work orders matching filters (plant, date range, lanes, status)
    2. For each work order, generates operation schedule using domain service
    3. Aggregates all tasks into single Gantt chart
    4. Detects lane conflicts (multiple WOs on same lane at same time)
    5. Calculates critical path (longest sequence of dependent operations)

    ## Features
    - **Operation-level scheduling**: Shows individual operations within work orders
    - **Lane visualization**: Displays lane assignments for capacity planning
    - **Dependency tracking**: Shows predecessor relationships between operations
    - **Conflict detection**: Highlights overlapping lane assignments
    - **Critical path**: Identifies bottleneck operations
    - **Progress tracking**: Shows completion percentage for each task

    ## Query Parameters
    - **plant_id**: Filter by plant (optional)
    - **start_date**: Show work orders starting >= this date
    - **end_date**: Show work orders ending <= this date
    - **lane_ids**: Filter by specific lanes (comma-separated, e.g., "1,2,3")
    - **include_completed**: Include completed work orders (default: false)

    ## Response Structure
    ```json
    {
      "tasks": [
        {
          "work_order_id": 123,
          "work_order_number": "WO-00123",
          "operation_name": "Machining",
          "start_date": "2024-11-15T08:00:00Z",
          "end_date": "2024-11-15T16:00:00Z",
          "lane_code": "LINE-01",
          "dependencies": [122],
          "progress_percent": 0.0,
          "status": "PLANNED",
          "is_critical_path": false
        }
      ],
      "conflicts": [...],
      "critical_path": [123, 124],
      "total_work_orders": 15
    }
    ```

    ## Business Rules
    - Work orders filtered by RLS (organization_id from JWT)
    - Only active lanes shown unless explicitly requested
    - Critical path calculated using longest duration sequence
    - Conflicts detected for overlapping lane assignments

    ## Permissions
    - Requires: `scheduling.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id_context = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id_context)

        # Parse lane_ids if provided
        lane_ids_list = None
        if lane_ids:
            try:
                lane_ids_list = [int(lid) for lid in lane_ids.split(",")]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid lane_ids format. Use comma-separated integers (e.g., '1,2,3')"
                )

        # Create DTO
        dto = GetGanttChartDTO(
            plant_id=plant_id,
            start_date=start_date,
            end_date=end_date,
            lane_ids=lane_ids_list,
            include_completed=include_completed,
            organization_id=organization_id
        )

        # Execute use case
        result = use_case.execute(dto)

        # Build response
        return GanttChartResponse(
            tasks=[
                GanttTaskResponse(
                    work_order_id=task.work_order_id,
                    work_order_number=task.work_order_number,
                    operation_id=task.operation_id,
                    operation_name=task.operation_name,
                    operation_number=task.operation_number,
                    start_date=task.start_date,
                    end_date=task.end_date,
                    duration_hours=task.duration_hours,
                    lane_id=task.lane_id,
                    lane_code=task.lane_code,
                    dependencies=task.dependencies,
                    progress_percent=task.progress_percent,
                    status=task.status,
                    is_critical_path=task.is_critical_path,
                    scheduling_mode=task.scheduling_mode
                )
                for task in result.tasks
            ],
            conflicts=result.conflicts,
            critical_path=result.critical_path,
            start_date=result.start_date,
            end_date=result.end_date,
            total_work_orders=result.total_work_orders
        )

    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/conflicts", response_model=ConflictsListResponse)
def get_conflicts(
    plant_id: int = Query(..., description="Plant ID"),
    start_date: date = Query(..., description="Start date of period to check"),
    end_date: date = Query(..., description="End date of period to check"),
    request: Request = None,
    use_case: DetectConflictsUseCase = Depends(get_detect_conflicts_use_case),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detect scheduling conflicts for a given period.

    ## Business Flow
    1. Queries all lane assignments in the specified period
    2. Detects overlapping assignments (lane overload)
    3. Validates dependency constraints
    4. Returns list of conflicts with severity and details

    ## Conflict Types
    - **LANE_OVERLOAD**: Multiple work orders assigned to same lane at same time
    - **DEPENDENCY_VIOLATION**: Successor starts before predecessor completes
    - **CAPACITY_EXCEEDED**: Lane utilization exceeds 100%

    ## Severity Levels
    - **HIGH**: Conflicts that must be resolved (overlapping assignments)
    - **MEDIUM**: Potential issues (tight schedules)
    - **LOW**: Warnings (capacity approaching limit)

    ## Use Cases
    - **Capacity planning**: Identify overloaded lanes before releasing work orders
    - **Schedule validation**: Check for conflicts before finalizing schedule
    - **Conflict resolution**: Review and fix scheduling issues

    ## Query Parameters
    - **plant_id** (required): Plant to check
    - **start_date** (required): Start of period
    - **end_date** (required): End of period

    ## Response Structure
    ```json
    {
      "conflicts": [
        {
          "conflict_type": "LANE_OVERLOAD",
          "severity": "HIGH",
          "description": "Lane LINE-01 has overlapping assignments",
          "affected_work_orders": [123, 124],
          "affected_lanes": [5],
          "details": {
            "work_order_1": "WO-00123",
            "work_order_2": "WO-00124",
            "overlap_start": "2024-11-15T10:00:00Z",
            "overlap_end": "2024-11-15T16:00:00Z"
          }
        }
      ],
      "total_conflicts": 1
    }
    ```

    ## Permissions
    - Requires: `scheduling.view` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id_context = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id_context)

        # Create DTO
        dto = DetectConflictsDTO(
            plant_id=plant_id,
            start_date=start_date,
            end_date=end_date
        )

        # Execute use case
        conflicts = use_case.execute(dto)

        # Build response
        return ConflictsListResponse(
            conflicts=[
                ConflictResponse(
                    conflict_type=conflict.conflict_type,
                    severity=conflict.severity,
                    description=conflict.description,
                    affected_work_orders=conflict.affected_work_orders,
                    affected_lanes=conflict.affected_lanes,
                    details=conflict.details
                )
                for conflict in conflicts
            ],
            total_conflicts=len(conflicts),
            plant_id=plant_id,
            date_range_start=start_date,
            date_range_end=end_date
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate", response_model=ValidationResultResponse)
def validate_schedule(
    request_data: ValidateScheduleRequest,
    request: Request,
    use_case: ValidateScheduleUseCase = Depends(get_validate_schedule_use_case),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate scheduling constraints before assigning work order to lane.

    ## Business Flow
    1. Validates work order exists
    2. Checks lane availability (no overlapping assignments)
    3. Validates dependency constraints (predecessor completion)
    4. Checks for unreasonable durations
    5. Returns validation result with errors and warnings

    ## Business Rules
    - **BR-SCHED-001**: Lane can only have one work order at a time
    - **BR-SCHED-002**: Predecessor must complete before successor starts
    - **BR-SCHED-003**: Warning if duration > 365 days

    ## Use Cases
    - **Pre-assignment validation**: Check before creating lane assignment
    - **Drag-and-drop validation**: Validate before accepting Gantt chart changes
    - **Batch scheduling**: Validate multiple assignments before committing

    ## Request Body
    ```json
    {
      "work_order_id": 123,
      "lane_id": 5,
      "start_date": "2024-11-15T08:00:00Z",
      "end_date": "2024-11-20T17:00:00Z"
    }
    ```

    ## Response Structure
    ```json
    {
      "is_valid": false,
      "errors": [
        "Lane is not available from 2024-11-15 to 2024-11-20. Another work order is already assigned."
      ],
      "warnings": [
        "Predecessor work order WO-00122 ends after proposed start date"
      ]
    }
    ```

    ## Validation Levels
    - **Errors**: Must be fixed before assignment can proceed
    - **Warnings**: Should be reviewed but don't block assignment

    ## Permissions
    - Requires: `scheduling.validate` permission
    """
    try:
        # Get user context for RLS
        user_context = get_user_context(request)
        organization_id = user_context.get("organization_id")
        plant_id = user_context.get("plant_id")

        # Set RLS context
        _set_rls_context(db, organization_id, plant_id)

        # Create DTO
        dto = ValidateScheduleDTO(
            work_order_id=request_data.work_order_id,
            lane_id=request_data.lane_id,
            start_date=request_data.start_date,
            end_date=request_data.end_date
        )

        # Execute use case
        result = use_case.execute(dto)

        return ValidationResultResponse(
            is_valid=result.is_valid,
            errors=result.errors,
            warnings=result.warnings
        )

    except EntityNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
