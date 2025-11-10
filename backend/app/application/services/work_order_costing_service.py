"""
Work Order Costing Service

Automatically calculates and updates work order costs:
- Material Cost (from Phase 2: FIFO/LIFO costing on material issue)
- Labor Cost (from production logs: hours × hourly rates)
- Overhead Cost (configurable percentage of material + labor)

Total Cost = Material Cost + Labor Cost + Overhead Cost
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.work_order import WorkOrder
from app.models.production_log import ProductionLog
from app.models.inventory import InventoryTransaction
from app.core.exceptions import EntityNotFoundException


class WorkOrderCostingService:
    """
    Service for calculating and updating work order costs.

    Business Rules:
    - BR-COST-001: Material cost accumulated via InventoryTransaction (type=ISSUE)
    - BR-COST-002: Labor cost = Sum(production hours) × hourly rate
    - BR-COST-003: Overhead = (Material + Labor) × overhead_percentage
    - BR-COST-004: Total cost = Material + Labor + Overhead
    - BR-COST-005: Costs updated in real-time (on material issue, production log)
    """

    def __init__(self, db: Session, overhead_percentage: float = 0.15):
        """
        Initialize costing service.

        Args:
            db: Database session
            overhead_percentage: Overhead rate as decimal (0.15 = 15%)
                Default: 15% (configurable per organization)
        """
        self.db = db
        self.overhead_percentage = Decimal(str(overhead_percentage))

    def update_material_cost(self, work_order_id: int) -> Dict:
        """
        Update material cost from inventory transactions.

        This is called when material is issued to a work order.
        Material cost is already calculated by FIFO/LIFO service (Phase 2).

        Args:
            work_order_id: Work order ID

        Returns:
            Dict with updated costs

        Raises:
            EntityNotFoundException: If work order not found
        """
        work_order = self.db.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if not work_order:
            raise EntityNotFoundException(
                entity_type="WorkOrder",
                entity_id=work_order_id
            )

        # Sum all ISSUE transactions for this work order
        material_cost_result = self.db.query(
            func.sum(InventoryTransaction.total_cost)
        ).filter(
            InventoryTransaction.reference_type == "WORK_ORDER",
            InventoryTransaction.reference_id == work_order_id,
            InventoryTransaction.transaction_type == "ISSUE"
        ).scalar()

        material_cost = Decimal(str(material_cost_result or 0))

        # Update work order
        work_order.actual_material_cost = float(material_cost)

        # Recalculate overhead and total cost
        self._recalculate_total_cost(work_order)

        self.db.commit()
        self.db.refresh(work_order)

        return self._get_cost_breakdown(work_order)

    def update_labor_cost(self, work_order_id: int, hourly_rate: Optional[float] = None) -> Dict:
        """
        Update labor cost from production logs.

        Labor Cost = Sum(production hours) × hourly rate

        Args:
            work_order_id: Work order ID
            hourly_rate: Hourly labor rate (default: $25/hour if not specified)

        Returns:
            Dict with updated costs

        Raises:
            EntityNotFoundException: If work order not found
        """
        work_order = self.db.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if not work_order:
            raise EntityNotFoundException(
                entity_type="WorkOrder",
                entity_id=work_order_id
            )

        # Default hourly rate (should come from organization settings or user role)
        rate = Decimal(str(hourly_rate or 25.0))

        # Get total production time from production logs
        # Note: production_logs may need a duration_hours field
        # For now, we'll estimate based on quantity and standard time
        production_result = self.db.query(
            func.sum(ProductionLog.quantity_produced)
        ).filter(
            ProductionLog.work_order_id == work_order_id
        ).scalar()

        total_produced = Decimal(str(production_result or 0))

        # Estimate hours (simplified - should use operation.standard_time_per_unit)
        # Assuming 0.5 hours per unit as default
        estimated_hours = total_produced * Decimal("0.5")

        labor_cost = estimated_hours * rate

        # Update work order
        work_order.actual_labor_cost = float(labor_cost)

        # Recalculate overhead and total cost
        self._recalculate_total_cost(work_order)

        self.db.commit()
        self.db.refresh(work_order)

        return self._get_cost_breakdown(work_order)

    def update_all_costs(self, work_order_id: int, hourly_rate: Optional[float] = None) -> Dict:
        """
        Update all costs for a work order (material, labor, overhead).

        This is called:
        - When work order is completed
        - On-demand via cost breakdown endpoint
        - By scheduled job (daily cost reconciliation)

        Args:
            work_order_id: Work order ID
            hourly_rate: Hourly labor rate (optional)

        Returns:
            Dict with complete cost breakdown
        """
        # Update material cost
        self.update_material_cost(work_order_id)

        # Update labor cost
        return self.update_labor_cost(work_order_id, hourly_rate)

    def calculate_variance(self, work_order_id: int) -> Dict:
        """
        Calculate cost variance (Actual vs Standard/Estimated).

        Variance = Actual Cost - Standard Cost

        Args:
            work_order_id: Work order ID

        Returns:
            Dict with variance analysis
        """
        work_order = self.db.query(WorkOrder).filter(
            WorkOrder.id == work_order_id
        ).first()

        if not work_order:
            raise EntityNotFoundException(
                entity_type="WorkOrder",
                entity_id=work_order_id
            )

        # Get actual costs
        actual_material = Decimal(str(work_order.actual_material_cost or 0))
        actual_labor = Decimal(str(work_order.actual_labor_cost or 0))
        actual_overhead = Decimal(str(work_order.actual_overhead_cost or 0))
        actual_total = actual_material + actual_labor + actual_overhead

        # Get standard/estimated costs (if available)
        # Note: These fields may need to be added to WorkOrder model
        standard_material = Decimal(str(getattr(work_order, 'standard_material_cost', 0) or 0))
        standard_labor = Decimal(str(getattr(work_order, 'standard_labor_cost', 0) or 0))
        standard_overhead = standard_material + standard_labor * self.overhead_percentage
        standard_total = standard_material + standard_labor + standard_overhead

        return {
            "work_order_id": work_order_id,
            "work_order_number": work_order.work_order_number,
            "actual_costs": {
                "material": float(actual_material),
                "labor": float(actual_labor),
                "overhead": float(actual_overhead),
                "total": float(actual_total)
            },
            "standard_costs": {
                "material": float(standard_material),
                "labor": float(standard_labor),
                "overhead": float(standard_overhead),
                "total": float(standard_total)
            },
            "variance": {
                "material": float(actual_material - standard_material),
                "labor": float(actual_labor - standard_labor),
                "overhead": float(actual_overhead - standard_overhead),
                "total": float(actual_total - standard_total)
            },
            "variance_percentage": {
                "material": float((actual_material - standard_material) / standard_material * 100) if standard_material > 0 else 0,
                "labor": float((actual_labor - standard_labor) / standard_labor * 100) if standard_labor > 0 else 0,
                "total": float((actual_total - standard_total) / standard_total * 100) if standard_total > 0 else 0
            }
        }

    def _recalculate_total_cost(self, work_order: WorkOrder):
        """
        Recalculate overhead and total cost.

        BR-COST-003: Overhead = (Material + Labor) × overhead_percentage
        BR-COST-004: Total = Material + Labor + Overhead
        """
        material = Decimal(str(work_order.actual_material_cost or 0))
        labor = Decimal(str(work_order.actual_labor_cost or 0))

        # Calculate overhead
        overhead = (material + labor) * self.overhead_percentage

        # Update work order
        work_order.actual_overhead_cost = float(overhead)

        # Note: total_actual_cost field may need to be added
        total_cost = material + labor + overhead
        if hasattr(work_order, 'total_actual_cost'):
            work_order.total_actual_cost = float(total_cost)

    def _get_cost_breakdown(self, work_order: WorkOrder) -> Dict:
        """Get cost breakdown for a work order."""
        material = Decimal(str(work_order.actual_material_cost or 0))
        labor = Decimal(str(work_order.actual_labor_cost or 0))
        overhead = Decimal(str(work_order.actual_overhead_cost or 0))
        total = material + labor + overhead

        return {
            "work_order_id": work_order.id,
            "work_order_number": work_order.work_order_number,
            "quantity_ordered": work_order.quantity_ordered,
            "quantity_completed": work_order.quantity_completed,
            "costs": {
                "material": float(material),
                "labor": float(labor),
                "overhead": float(overhead),
                "total": float(total)
            },
            "cost_per_unit": {
                "material": float(material / work_order.quantity_completed) if work_order.quantity_completed > 0 else 0,
                "labor": float(labor / work_order.quantity_completed) if work_order.quantity_completed > 0 else 0,
                "overhead": float(overhead / work_order.quantity_completed) if work_order.quantity_completed > 0 else 0,
                "total": float(total / work_order.quantity_completed) if work_order.quantity_completed > 0 else 0
            },
            "overhead_rate": float(self.overhead_percentage * 100),  # Convert to percentage
            "updated_at": work_order.updated_at.isoformat() if work_order.updated_at else None
        }
