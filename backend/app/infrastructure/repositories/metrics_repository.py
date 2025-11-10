"""
Metrics Repository

Data access layer for KPI calculations (OEE, OTD, FPY).
Aggregates data from production_logs, machine_status_history, work_orders, inspection_logs.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from app.models.production_log import ProductionLog
from app.models.machine import Machine, MachineStatusHistory, MachineStatus
from app.models.work_order import WorkOrder, OrderStatus
from app.models.inspection import InspectionLog


class MetricsRepository:
    """
    Repository for aggregating KPI metrics.

    Provides optimized queries for:
    - OEE (Overall Equipment Effectiveness)
    - OTD (On-Time Delivery)
    - FPY (First Pass Yield)
    """

    def __init__(self, db: Session):
        self.db = db

    # ============================================================================
    # OEE (Overall Equipment Effectiveness) Queries
    # ============================================================================

    def get_oee_data(
        self,
        plant_id: Optional[int] = None,
        machine_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None
    ) -> Dict:
        """
        Aggregate OEE data for machines.

        OEE = Availability × Performance × Quality

        - Availability: (Total Time - Downtime) / Total Time
        - Performance: (Ideal Cycle Time × Total Pieces) / Operating Time
        - Quality: Good Pieces / Total Pieces

        Args:
            plant_id: Filter by plant (optional)
            machine_id: Filter by specific machine (optional)
            start_date: Start of period (optional)
            end_date: End of period (optional)
            organization_id: Organization ID for RLS

        Returns:
            Dict with OEE components:
            {
                "total_time_minutes": float,
                "downtime_minutes": float,
                "total_pieces": int,
                "good_pieces": int,
                "defect_pieces": int,
                "availability": float,
                "performance": float,
                "quality": float,
                "oee": float
            }
        """
        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Calculate total time in minutes
        total_time_minutes = (end_date - start_date).total_seconds() / 60.0

        # Calculate downtime from machine status history
        downtime_query = self.db.query(
            func.sum(
                func.extract('epoch',
                    func.coalesce(
                        MachineStatusHistory.ended_at,
                        func.now()
                    ) - MachineStatusHistory.started_at
                ) / 60.0
            )
        ).join(Machine).filter(
            MachineStatusHistory.started_at >= start_date,
            MachineStatusHistory.started_at <= end_date,
            MachineStatusHistory.status.in_([
                MachineStatus.DOWN,
                MachineStatus.MAINTENANCE
            ])
        )

        # Apply filters
        if organization_id:
            downtime_query = downtime_query.filter(Machine.organization_id == organization_id)
        if plant_id:
            downtime_query = downtime_query.filter(Machine.plant_id == plant_id)
        if machine_id:
            downtime_query = downtime_query.filter(MachineStatusHistory.machine_id == machine_id)

        downtime_minutes = downtime_query.scalar() or 0.0

        # Calculate production metrics from production logs
        production_query = self.db.query(
            func.sum(ProductionLog.quantity_produced).label('total_pieces'),
            func.sum(ProductionLog.quantity_scrapped).label('scrapped_pieces'),
            func.sum(ProductionLog.quantity_reworked).label('reworked_pieces')
        ).filter(
            ProductionLog.timestamp >= start_date,
            ProductionLog.timestamp <= end_date
        )

        # Apply filters
        if organization_id:
            production_query = production_query.filter(ProductionLog.organization_id == organization_id)
        if plant_id:
            production_query = production_query.filter(ProductionLog.plant_id == plant_id)
        if machine_id:
            production_query = production_query.filter(ProductionLog.machine_id == machine_id)

        production_result = production_query.first()
        total_pieces = int(production_result.total_pieces or 0)
        scrapped_pieces = int(production_result.scrapped_pieces or 0)
        reworked_pieces = int(production_result.reworked_pieces or 0)

        # Good pieces = Total - Scrapped (reworked pieces are still good after rework)
        good_pieces = total_pieces - scrapped_pieces
        defect_pieces = scrapped_pieces + reworked_pieces

        # Calculate OEE components
        operating_time = total_time_minutes - downtime_minutes
        availability = operating_time / total_time_minutes if total_time_minutes > 0 else 0.0

        # Performance: For simplification, assume 100% if pieces were produced
        # In reality, would need ideal_cycle_time from machine specifications
        performance = 1.0 if total_pieces > 0 else 0.0

        # Quality
        quality = good_pieces / total_pieces if total_pieces > 0 else 0.0

        # OEE
        oee = availability * performance * quality

        return {
            "total_time_minutes": total_time_minutes,
            "downtime_minutes": downtime_minutes,
            "operating_time_minutes": operating_time,
            "total_pieces": total_pieces,
            "good_pieces": good_pieces,
            "defect_pieces": defect_pieces,
            "scrapped_pieces": scrapped_pieces,
            "reworked_pieces": reworked_pieces,
            "availability": round(availability * 100, 2),  # Convert to percentage
            "performance": round(performance * 100, 2),  # Convert to percentage
            "quality": round(quality * 100, 2),  # Convert to percentage
            "oee": round(oee * 100, 2)  # Convert to percentage
        }

    def get_oee_by_machine(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Get OEE breakdown by individual machines.

        Args:
            plant_id: Filter by plant (optional)
            start_date: Start of period (optional)
            end_date: End of period (optional)
            organization_id: Organization ID for RLS

        Returns:
            List of dicts with machine-level OEE data
        """
        # Get all machines
        machines_query = self.db.query(Machine).filter(Machine.is_active == True)

        if organization_id:
            machines_query = machines_query.filter(Machine.organization_id == organization_id)
        if plant_id:
            machines_query = machines_query.filter(Machine.plant_id == plant_id)

        machines = machines_query.all()

        results = []
        for machine in machines:
            oee_data = self.get_oee_data(
                machine_id=machine.id,
                plant_id=plant_id,
                start_date=start_date,
                end_date=end_date,
                organization_id=organization_id
            )
            results.append({
                "machine_id": machine.id,
                "machine_code": machine.machine_code,
                "machine_name": machine.machine_name,
                **oee_data
            })

        return results

    # ============================================================================
    # OTD (On-Time Delivery) Queries
    # ============================================================================

    def get_otd_data(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None
    ) -> Dict:
        """
        Calculate On-Time Delivery (OTD) metrics.

        OTD = (Work Orders Completed On-Time / Total Completed Work Orders) × 100%

        A work order is on-time if:
        - end_date_actual <= end_date_planned
        - OR end_date_actual is NULL and status is COMPLETED

        Args:
            plant_id: Filter by plant (optional)
            start_date: Filter work orders completed >= this date (optional)
            end_date: Filter work orders completed <= this date (optional)
            organization_id: Organization ID for RLS

        Returns:
            Dict with OTD metrics:
            {
                "total_completed": int,
                "on_time": int,
                "late": int,
                "otd_percentage": float,
                "average_delay_days": float
            }
        """
        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Query completed work orders
        query = self.db.query(
            func.count(WorkOrder.id).label('total'),
            func.sum(
                case(
                    (
                        or_(
                            WorkOrder.end_date_actual <= WorkOrder.end_date_planned,
                            and_(
                                WorkOrder.end_date_actual.is_(None),
                                WorkOrder.order_status == OrderStatus.COMPLETED
                            )
                        ),
                        1
                    ),
                    else_=0
                )
            ).label('on_time'),
            func.avg(
                func.extract('epoch',
                    WorkOrder.end_date_actual - WorkOrder.end_date_planned
                ) / 86400.0  # Convert to days
            ).label('avg_delay_days')
        ).filter(
            WorkOrder.order_status == OrderStatus.COMPLETED,
            or_(
                WorkOrder.end_date_actual >= start_date,
                and_(
                    WorkOrder.end_date_actual.is_(None),
                    WorkOrder.end_date_planned >= start_date
                )
            ),
            or_(
                WorkOrder.end_date_actual <= end_date,
                and_(
                    WorkOrder.end_date_actual.is_(None),
                    WorkOrder.end_date_planned <= end_date
                )
            )
        )

        # Apply filters
        if organization_id:
            query = query.filter(WorkOrder.organization_id == organization_id)
        if plant_id:
            query = query.filter(WorkOrder.plant_id == plant_id)

        result = query.first()
        total_completed = int(result.total or 0)
        on_time = int(result.on_time or 0)
        late = total_completed - on_time
        avg_delay_days = float(result.avg_delay_days or 0.0)

        otd_percentage = (on_time / total_completed * 100) if total_completed > 0 else 0.0

        return {
            "total_completed": total_completed,
            "on_time": on_time,
            "late": late,
            "otd_percentage": round(otd_percentage, 2),
            "average_delay_days": round(avg_delay_days, 2)
        }

    # ============================================================================
    # FPY (First Pass Yield) Queries
    # ============================================================================

    def get_fpy_data(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None
    ) -> Dict:
        """
        Calculate First Pass Yield (FPY) metrics.

        FPY = (Passed Quantity / Inspected Quantity) × 100%

        Aggregates inspection logs to calculate quality metrics.

        Args:
            plant_id: Filter by plant (optional)
            start_date: Filter inspections >= this date (optional)
            end_date: Filter inspections <= this date (optional)
            organization_id: Organization ID for RLS

        Returns:
            Dict with FPY metrics:
            {
                "total_inspected": int,
                "total_passed": int,
                "total_failed": int,
                "fpy_percentage": float,
                "defect_rate": float
            }
        """
        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Query inspection logs
        query = self.db.query(
            func.sum(InspectionLog.inspected_quantity).label('total_inspected'),
            func.sum(InspectionLog.passed_quantity).label('total_passed'),
            func.sum(InspectionLog.failed_quantity).label('total_failed')
        ).filter(
            InspectionLog.inspected_at >= start_date,
            InspectionLog.inspected_at <= end_date
        )

        # Apply filters
        if organization_id:
            query = query.filter(InspectionLog.organization_id == organization_id)
        if plant_id:
            query = query.filter(InspectionLog.plant_id == plant_id)

        result = query.first()
        total_inspected = int(result.total_inspected or 0)
        total_passed = int(result.total_passed or 0)
        total_failed = int(result.total_failed or 0)

        fpy_percentage = (total_passed / total_inspected * 100) if total_inspected > 0 else 0.0
        defect_rate = (total_failed / total_inspected * 100) if total_inspected > 0 else 0.0

        return {
            "total_inspected": total_inspected,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "fpy_percentage": round(fpy_percentage, 2),
            "defect_rate": round(defect_rate, 2)
        }

    def get_fpy_by_work_order(
        self,
        plant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        organization_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get FPY breakdown by work order (top worst performers).

        Args:
            plant_id: Filter by plant (optional)
            start_date: Filter inspections >= this date (optional)
            end_date: Filter inspections <= this date (optional)
            organization_id: Organization ID for RLS
            limit: Number of work orders to return (default 10)

        Returns:
            List of dicts with work order FPY data
        """
        # Default to last 30 days if no date range provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Query inspection logs grouped by work order
        query = self.db.query(
            InspectionLog.work_order_id,
            WorkOrder.work_order_number,
            func.sum(InspectionLog.inspected_quantity).label('inspected'),
            func.sum(InspectionLog.passed_quantity).label('passed'),
            func.sum(InspectionLog.failed_quantity).label('failed')
        ).join(WorkOrder).filter(
            InspectionLog.inspected_at >= start_date,
            InspectionLog.inspected_at <= end_date
        ).group_by(
            InspectionLog.work_order_id,
            WorkOrder.work_order_number
        )

        # Apply filters
        if organization_id:
            query = query.filter(InspectionLog.organization_id == organization_id)
        if plant_id:
            query = query.filter(InspectionLog.plant_id == plant_id)

        # Order by worst FPY (highest failure rate)
        query = query.order_by(
            (func.sum(InspectionLog.failed_quantity) /
             func.sum(InspectionLog.inspected_quantity)).desc()
        ).limit(limit)

        results = []
        for row in query.all():
            inspected = int(row.inspected)
            passed = int(row.passed)
            failed = int(row.failed)
            fpy = (passed / inspected * 100) if inspected > 0 else 0.0

            results.append({
                "work_order_id": row.work_order_id,
                "work_order_number": row.work_order_number,
                "total_inspected": inspected,
                "total_passed": passed,
                "total_failed": failed,
                "fpy_percentage": round(fpy, 2)
            })

        return results
