"""
Application service for Production Planning operations.
Phase 3: Production Planning Module - Component 3
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.work_order import (
    WorkOrder, WorkOrderOperation, WorkOrderMaterial,
    OrderType, OrderStatus, OperationStatus
)
from app.models.bom import BOMHeader, BOMLine
from app.models.material import Material, UnitOfMeasure
from app.domain.services.bom_service import BOMExplosionService
from app.domain.services.capacity_calculator import CapacityCalculator


logger = logging.getLogger(__name__)


class ProductionPlanningService:
    """
    Application service for production planning operations.

    Provides high-level operations for:
    - Converting demand into work orders
    - Calculating material requirements
    - Generating operations from BOM routing
    - Checking capacity feasibility
    """

    def __init__(self, db_session: Session):
        """
        Initialize production planning service.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.capacity_calculator = CapacityCalculator(db_session)

    def create_work_order_from_demand(
        self,
        material_id: int,
        quantity: float,
        due_date: datetime,
        organization_id: int,
        plant_id: int,
        priority: int = 5
    ) -> WorkOrder:
        """
        Convert sales demand/forecast into production work order.

        Args:
            material_id: ID of material to produce
            quantity: Quantity to produce
            due_date: Due date for completion
            organization_id: Organization ID
            plant_id: Plant ID
            priority: Work order priority (1-10, default 5)

        Returns:
            Created WorkOrder entity

        Raises:
            ValueError: If material has no active BOM or quantity is invalid
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Get material
        material = self.db_session.query(Material).filter(
            Material.id == material_id
        ).first()

        if not material:
            raise ValueError(f"Material {material_id} not found")

        # Find active BOM for material
        now = datetime.now()
        bom_header = self.db_session.query(BOMHeader).filter(
            BOMHeader.material_id == material_id,
            BOMHeader.organization_id == organization_id,
            BOMHeader.plant_id == plant_id,
            BOMHeader.is_active == True,
            BOMHeader.effective_date_from <= now,
            BOMHeader.effective_date_to >= now
        ).first()

        if not bom_header:
            raise ValueError(f"No active BOM found for material {material_id}")

        # Generate work order number
        # Format: WO-YYYYMMDD-NNNN
        timestamp = datetime.now().strftime("%Y%m%d")
        # Get count of work orders today for sequence
        count = self.db_session.query(WorkOrder).filter(
            WorkOrder.organization_id == organization_id,
            WorkOrder.plant_id == plant_id
        ).count()
        work_order_number = f"WO-{timestamp}-{count+1:04d}"

        # Create work order
        work_order = WorkOrder(
            organization_id=organization_id,
            plant_id=plant_id,
            work_order_number=work_order_number,
            material_id=material_id,
            order_type=OrderType.PRODUCTION,
            order_status=OrderStatus.PLANNED,
            planned_quantity=quantity,
            actual_quantity=0.0,
            end_date_planned=due_date,
            priority=priority,
            created_by_user_id=1  # TODO: Get from context
        )

        self.db_session.add(work_order)
        self.db_session.flush()  # Get work_order.id

        logger.info(
            f"Created work order {work_order_number} for {quantity} units of "
            f"material {material_id}, due {due_date}"
        )

        return work_order

    def calculate_material_requirements(
        self,
        work_order_id: int
    ) -> Dict[int, Dict[str, Any]]:
        """
        Calculate all materials needed for a work order.

        Args:
            work_order_id: ID of the work order

        Returns:
            Dictionary mapping material_id to:
            {
                'required_quantity': float,
                'unit_of_measure_id': int,
                'bom_level': int
            }

        Raises:
            ValueError: If work order not found
        """
        # Get work order
        work_order = self.db_session.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if not work_order:
            raise ValueError(f"Work order {work_order_id} not found")

        # Find active BOM for the material
        now = datetime.now()
        bom_header = self.db_session.query(BOMHeader).filter(
            BOMHeader.material_id == work_order.material_id,
            BOMHeader.organization_id == work_order.organization_id,
            BOMHeader.plant_id == work_order.plant_id,
            BOMHeader.is_active == True,
            BOMHeader.effective_date_from <= now,
            BOMHeader.effective_date_to >= now
        ).first()

        if not bom_header:
            raise ValueError(f"No active BOM found for material {work_order.material_id}")

        # Create simple BOM repository adapter for explosion service
        class SimpleBOMRepository:
            def __init__(self, db_session):
                self.db_session = db_session

            def get_bom_header(self, bom_header_id):
                bom = self.db_session.query(BOMHeader).filter(
                    BOMHeader.id == bom_header_id
                ).first()
                if not bom:
                    return None
                return {
                    'id': bom.id,
                    'material_id': bom.material_id,
                    'bom_lines': [
                        {
                            'component_material_id': line.component_material_id,
                            'quantity': line.quantity,
                            'scrap_factor': line.scrap_factor,
                            'is_phantom': line.is_phantom,
                            'unit_of_measure_id': line.unit_of_measure_id
                        }
                        for line in bom.bom_lines
                    ]
                }

            def get_bom_by_material(self, material_id):
                now = datetime.now()
                bom = self.db_session.query(BOMHeader).filter(
                    BOMHeader.material_id == material_id,
                    BOMHeader.is_active == True,
                    BOMHeader.effective_date_from <= now,
                    BOMHeader.effective_date_to >= now
                ).first()
                if not bom:
                    return None
                return self.get_bom_header(bom.id)

        # Use BOM explosion service
        bom_repo = SimpleBOMRepository(self.db_session)
        explosion_service = BOMExplosionService(bom_repo)

        materials_needed = explosion_service.explode_bom(
            bom_header_id=bom_header.id,
            required_quantity=work_order.planned_quantity
        )

        # Transform to required format
        result = {}
        for material_id, details in materials_needed.items():
            result[material_id] = {
                'required_quantity': details['total_quantity'],
                'unit_of_measure_id': details['unit_of_measure_id'],
                'bom_level': details['details'][0]['level'] if details['details'] else 1
            }

        logger.info(
            f"Calculated material requirements for work order {work_order_id}: "
            f"{len(result)} materials needed"
        )

        return result

    def generate_operations_from_bom(
        self,
        work_order_id: int,
        bom_header_id: int
    ) -> List[WorkOrderOperation]:
        """
        Create work order operations from BOM routing.

        Args:
            work_order_id: ID of the work order
            bom_header_id: ID of the BOM header with routing info

        Returns:
            List of created WorkOrderOperation entities

        Raises:
            ValueError: If work order or BOM not found
        """
        # Get work order
        work_order = self.db_session.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if not work_order:
            raise ValueError(f"Work order {work_order_id} not found")

        # Get BOM header
        bom_header = self.db_session.query(BOMHeader).filter(
            BOMHeader.id == bom_header_id
        ).first()

        if not bom_header:
            raise ValueError(f"BOM header {bom_header_id} not found")

        # Get BOM lines with operation numbers (routing)
        bom_lines = self.db_session.query(BOMLine).filter(
            BOMLine.bom_header_id == bom_header_id,
            BOMLine.operation_number.isnot(None)
        ).order_by(BOMLine.operation_number).all()

        operations = []
        for bom_line in bom_lines:
            # Create operation
            # Note: In real implementation, we'd need a routing table with work centers
            # For now, we'll use a simple mapping based on operation number
            # Operation 10 -> Work Center 1 (Assembly)
            # Operation 20 -> Work Center 2 (Packaging)
            work_center_id = 1 if bom_line.operation_number == 10 else 2

            operation = WorkOrderOperation(
                organization_id=work_order.organization_id,
                plant_id=work_order.plant_id,
                work_order_id=work_order_id,
                operation_number=bom_line.operation_number,
                operation_name=f"Operation {bom_line.operation_number}",
                work_center_id=work_center_id,
                setup_time_minutes=60.0,  # Default 1 hour setup
                run_time_per_unit_minutes=3.0,  # Default 3 min per unit
                status=OperationStatus.PENDING
            )

            self.db_session.add(operation)
            operations.append(operation)

        self.db_session.flush()

        logger.info(
            f"Generated {len(operations)} operations for work order {work_order_id} "
            f"from BOM {bom_header_id}"
        )

        return operations

    def check_capacity_feasibility(
        self,
        work_order_id: int
    ) -> Dict[str, Any]:
        """
        Check if work order can be completed given work center capacity.

        Args:
            work_order_id: ID of the work order

        Returns:
            Dictionary with:
            - feasible: bool - whether order can be completed on time
            - capacity_utilization: float - percentage of capacity used
            - bottleneck_work_center: str - code of bottleneck work center (if any)
            - earliest_completion_date: datetime - earliest possible completion

        Raises:
            ValueError: If work order not found
        """
        # Get work order with operations
        work_order = self.db_session.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if not work_order:
            raise ValueError(f"Work order {work_order_id} not found")

        operations = self.db_session.query(WorkOrderOperation).filter(
            WorkOrderOperation.work_order_id == work_order_id
        ).all()

        if not operations:
            # No operations, trivially feasible
            return {
                'feasible': True,
                'capacity_utilization': 0.0,
                'bottleneck_work_center': None,
                'earliest_completion_date': work_order.end_date_planned
            }

        # Calculate total hours needed and check each work center
        max_utilization = 0.0
        bottleneck_wc_code = None
        latest_completion = datetime.now()

        for operation in operations:
            # Calculate hours needed for this operation
            hours_needed = self.capacity_calculator.calculate_operation_hours(
                setup_time_minutes=operation.setup_time_minutes,
                run_time_per_unit_minutes=operation.run_time_per_unit_minutes,
                quantity=work_order.planned_quantity
            )

            # Calculate capacity load from now until due date
            if work_order.end_date_planned:
                load_info = self.capacity_calculator.calculate_work_center_load(
                    work_center_id=operation.work_center_id,
                    start_date=datetime.now(),
                    end_date=work_order.end_date_planned
                )

                # Check if adding this operation would overload
                new_total_hours = load_info['total_hours'] + hours_needed
                new_utilization = (new_total_hours / load_info['capacity_hours'] * 100.0
                                   if load_info['capacity_hours'] > 0 else 0.0)

                if new_utilization > max_utilization:
                    max_utilization = new_utilization
                    bottleneck_wc_code = operation.work_center.work_center_code

                # If overloaded, find earliest completion
                if new_utilization > 100.0:
                    # Calculate how many extra days needed
                    extra_hours = new_total_hours - load_info['capacity_hours']
                    extra_days = int(extra_hours / 8.0) + 1
                    operation_completion = work_order.end_date_planned + timedelta(days=extra_days)

                    if operation_completion > latest_completion:
                        latest_completion = operation_completion

        # Determine feasibility
        feasible = max_utilization <= 100.0
        earliest_completion = work_order.end_date_planned if feasible else latest_completion

        logger.info(
            f"Capacity check for work order {work_order_id}: "
            f"feasible={feasible}, utilization={max_utilization:.1f}%, "
            f"bottleneck={bottleneck_wc_code}"
        )

        return {
            'feasible': feasible,
            'capacity_utilization': max_utilization,
            'bottleneck_work_center': bottleneck_wc_code,
            'earliest_completion_date': earliest_completion
        }
