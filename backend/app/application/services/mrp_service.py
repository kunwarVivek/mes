"""
Application service for Material Requirements Planning (MRP).
Coordinates MRP execution, net requirements calculation, and planned order generation.
Phase 3: Production Planning Module - Component 4
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.material import Material, MRPType, ProcurementType
from app.models.inventory import Inventory
from app.models.work_order import WorkOrder, WorkOrderMaterial, OrderStatus
from app.models.bom import BOMHeader, BOMLine
from app.domain.entities.mrp_run import MRPRunDomain
from app.domain.entities.planned_order import PlannedOrderDomain
from app.domain.services.lot_sizing_service import LotSizingService
from app.domain.services.bom_service import BOMExplosionService


logger = logging.getLogger(__name__)


class BOMRepository:
    """Repository adapter for BOMExplosionService"""

    def __init__(self, session: Session):
        self.session = session

    def get_bom_header(self, bom_header_id: int) -> Optional[Dict]:
        """Get BOM header with lines"""
        bom = self.session.query(BOMHeader).filter(BOMHeader.id == bom_header_id).first()
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

    def get_bom_by_material(self, material_id: int) -> Optional[Dict]:
        """Get active BOM for material"""
        bom = self.session.query(BOMHeader).filter(
            BOMHeader.material_id == material_id,
            BOMHeader.is_active == True
        ).first()

        if not bom:
            return None

        return self.get_bom_header(bom.id)


class MRPService:
    """Service for Material Requirements Planning execution"""

    def __init__(self, session: Session):
        """
        Initialize MRP service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.lot_sizing_service = LotSizingService()
        self.bom_repository = BOMRepository(session)
        self.bom_explosion_service = BOMExplosionService(self.bom_repository)

    def run_mrp(
        self,
        organization_id: int,
        plant_id: int,
        planning_horizon_days: int = 90
    ) -> MRPRunDomain:
        """
        Execute Material Requirements Planning for all MRP materials.

        Args:
            organization_id: Organization ID
            plant_id: Plant ID
            planning_horizon_days: Planning horizon in days (default 90)

        Returns:
            MRPRun domain entity with execution results
        """
        logger.info(f"Starting MRP run for org={organization_id}, plant={plant_id}, horizon={planning_horizon_days} days")

        # Create MRP run
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=planning_horizon_days)
        run_number = f"MRP-{start_date.strftime('%Y%m%d-%H%M%S')}"

        mrp_run = MRPRunDomain(
            id=None,
            organization_id=organization_id,
            plant_id=plant_id,
            run_number=run_number,
            run_date=start_date,
            planning_horizon_start=start_date,
            planning_horizon_end=end_date,
            materials_processed=0,
            planned_orders_created=0,
            total_shortage_qty=0.0,
            status='RUNNING'
        )

        try:
            # Get all MRP materials for this plant
            mrp_materials = self.session.query(Material).filter(
                Material.organization_id == organization_id,
                Material.plant_id == plant_id,
                Material.mrp_type == MRPType.MRP,
                Material.is_active == True
            ).all()

            logger.info(f"Found {len(mrp_materials)} MRP materials to process")

            materials_processed = 0
            total_planned_orders = 0
            total_shortage = 0.0

            # Process each material
            for material in mrp_materials:
                logger.debug(f"Processing material: {material.material_number}")

                # Calculate net requirements
                net_req_result = self.calculate_net_requirements(
                    material.id,
                    start_date,
                    end_date
                )

                net_requirements = net_req_result['net_requirements']

                # Generate planned orders if shortage exists
                if net_requirements > 0:
                    planned_orders = self.generate_planned_orders(
                        material_id=material.id,
                        net_requirements=net_requirements,
                        need_date=start_date + timedelta(days=30),  # Default need date
                        lead_time_days=material.lead_time_days
                    )

                    total_planned_orders += len(planned_orders)
                    total_shortage += net_requirements
                    logger.debug(f"Generated {len(planned_orders)} planned orders for {material.material_number}")

                materials_processed += 1

            # Complete MRP run
            mrp_run.complete(
                materials_processed=materials_processed,
                planned_orders_created=total_planned_orders,
                total_shortage_qty=total_shortage
            )

            logger.info(
                f"MRP run completed: {materials_processed} materials, "
                f"{total_planned_orders} planned orders, "
                f"{total_shortage} total shortage"
            )

            return mrp_run

        except Exception as e:
            logger.error(f"MRP run failed: {str(e)}")
            mrp_run.fail()
            raise

    def calculate_net_requirements(
        self,
        material_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Calculate net material requirements for planning period.

        Formula:
        Gross Requirements = Sum of work order material requirements
        Scheduled Receipts = Open purchase orders + in-progress work orders
        Projected On Hand = Current inventory + Scheduled Receipts - Gross Requirements
        Net Requirements = max(0, -Projected On Hand)

        Args:
            material_id: Material ID
            start_date: Planning period start date
            end_date: Planning period end date

        Returns:
            Dictionary with:
            - gross_requirements: Total demand from work orders
            - scheduled_receipts: Expected receipts from open orders
            - on_hand: Current inventory
            - net_requirements: Shortage quantity
            - shortage_dates: List of dates with shortages
        """
        logger.debug(f"Calculating net requirements for material_id={material_id}")

        # Get current inventory (on-hand quantity)
        inventory_total = self.session.query(
            func.coalesce(func.sum(Inventory.quantity_on_hand), 0.0)
        ).filter(
            Inventory.material_id == material_id
        ).scalar() or 0.0

        # Get gross requirements (work order material requirements)
        gross_requirements = self.session.query(
            func.coalesce(func.sum(WorkOrderMaterial.planned_quantity - WorkOrderMaterial.actual_quantity), 0.0)
        ).join(WorkOrder).filter(
            WorkOrderMaterial.material_id == material_id,
            WorkOrder.start_date_planned >= start_date,
            WorkOrder.start_date_planned <= end_date,
            WorkOrder.order_status.in_([OrderStatus.PLANNED, OrderStatus.RELEASED, OrderStatus.IN_PROGRESS])
        ).scalar() or 0.0

        # Get scheduled receipts (in-progress work orders producing this material)
        scheduled_receipts = self.session.query(
            func.coalesce(func.sum(WorkOrder.planned_quantity - WorkOrder.actual_quantity), 0.0)
        ).filter(
            WorkOrder.material_id == material_id,
            WorkOrder.order_status.in_([OrderStatus.RELEASED, OrderStatus.IN_PROGRESS])
        ).scalar() or 0.0

        # Calculate projected on-hand
        projected_on_hand = inventory_total + scheduled_receipts - gross_requirements

        # Calculate net requirements (shortage)
        net_requirements = max(0.0, -projected_on_hand)

        # Identify shortage dates (simplified - single date if shortage exists)
        shortage_dates = []
        if net_requirements > 0:
            shortage_dates.append(start_date + timedelta(days=30))  # Default shortage date

        result = {
            'gross_requirements': float(gross_requirements),
            'scheduled_receipts': float(scheduled_receipts),
            'on_hand': float(inventory_total),
            'net_requirements': float(net_requirements),
            'shortage_dates': shortage_dates
        }

        logger.debug(f"Net requirements result: {result}")
        return result

    def generate_planned_orders(
        self,
        material_id: int,
        net_requirements: float,
        need_date: datetime,
        lead_time_days: int
    ) -> List[PlannedOrderDomain]:
        """
        Generate planned production/purchase orders to cover shortfalls.

        Args:
            material_id: Material ID
            net_requirements: Net shortage quantity
            need_date: Date when material is needed
            lead_time_days: Lead time in days

        Returns:
            List of PlannedOrder domain entities
        """
        logger.debug(f"Generating planned orders for material_id={material_id}, net_req={net_requirements}")

        # Get material details
        material = self.session.query(Material).filter(Material.id == material_id).first()
        if not material:
            raise ValueError(f"Material {material_id} not found")

        # Determine order type based on procurement type
        if material.procurement_type == ProcurementType.PURCHASE:
            order_type = 'PURCHASE'
        elif material.procurement_type == ProcurementType.MANUFACTURE:
            order_type = 'PRODUCTION'
        else:  # BOTH
            order_type = 'PURCHASE'  # Default to purchase

        # Calculate lot size using fixed lot size rule
        lot_size = self.lot_sizing_service.calculate_lot_size(
            material_id=material_id,
            net_requirement=net_requirements,
            lot_sizing_rule='FIXED_LOT_SIZE',
            fixed_lot_size=material.lot_size or 1.0
        )

        # Calculate order date (offset by lead time)
        order_date = need_date - timedelta(days=lead_time_days)

        # Create planned order
        planned_order = PlannedOrderDomain(
            id=None,
            mrp_run_id=1,  # Placeholder - would be actual MRP run ID in production
            material_id=material_id,
            order_type=order_type,
            planned_quantity=lot_size,
            unit_of_measure_id=material.base_uom_id,
            need_date=need_date,
            order_date=order_date,
            source='MRP',
            status='PLANNED'
        )

        logger.debug(f"Created planned order: type={order_type}, qty={lot_size}, order_date={order_date}")
        return [planned_order]

    def explode_requirements(self, work_order_id: int) -> List[Dict[str, Any]]:
        """
        Recursively calculate dependent requirements from work order.

        Args:
            work_order_id: Work order ID

        Returns:
            List of requirement dictionaries:
            - material_id: Component material ID
            - quantity: Required quantity
            - need_date: Date when material is needed
            - parent_work_order_id: Parent work order ID
        """
        logger.debug(f"Exploding requirements for work_order_id={work_order_id}")

        # Get work order
        work_order = self.session.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order:
            raise ValueError(f"Work order {work_order_id} not found")

        # Get BOM for work order material
        bom = self.bom_repository.get_bom_by_material(work_order.material_id)
        if not bom:
            logger.debug(f"No BOM found for material {work_order.material_id}")
            return []

        # Explode BOM
        materials_needed = self.bom_explosion_service.explode_bom(
            bom_header_id=bom['id'],
            required_quantity=work_order.planned_quantity
        )

        # Convert to requirements format
        requirements = []
        need_date = work_order.start_date_planned

        for material_id, details in materials_needed.items():
            requirement = {
                'material_id': material_id,
                'quantity': details['total_quantity'],
                'need_date': need_date,
                'parent_work_order_id': work_order_id
            }
            requirements.append(requirement)

        logger.debug(f"Exploded {len(requirements)} requirements")
        return requirements
