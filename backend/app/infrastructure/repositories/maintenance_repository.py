"""
Repository for Maintenance Management domain.
Implements data access layer for PM schedules, PM work orders, and downtime events.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from app.models.maintenance import PMSchedule, PMWorkOrder, DowntimeEvent
from app.domain.entities.maintenance import (
    PMScheduleDomain, PMWorkOrderDomain, DowntimeEventDomain,
    TriggerType, PMStatus, DowntimeCategory, MTBFMTTRCalculator, MTBFMTTRMetrics
)


class MaintenanceRepository:
    """Repository for maintenance operations"""

    def __init__(self, db: Session):
        self.db = db

    # PM Schedule operations
    def create_pm_schedule(
        self,
        organization_id: int,
        plant_id: int,
        schedule_domain: PMScheduleDomain
    ) -> PMSchedule:
        """Create a new PM schedule"""
        pm_schedule = PMSchedule(
            organization_id=organization_id,
            plant_id=plant_id,
            schedule_code=schedule_domain.schedule_code,
            schedule_name=schedule_domain.schedule_name,
            machine_id=schedule_domain.machine_id,
            trigger_type=schedule_domain.trigger_type,
            frequency_days=schedule_domain.frequency_days,
            meter_threshold=schedule_domain.meter_threshold,
            is_active=schedule_domain.is_active
        )
        self.db.add(pm_schedule)
        self.db.commit()
        self.db.refresh(pm_schedule)
        return pm_schedule

    def get_pm_schedule_by_id(
        self,
        schedule_id: int,
        organization_id: int,
        plant_id: int
    ) -> Optional[PMSchedule]:
        """Get PM schedule by ID with RLS"""
        return self.db.query(PMSchedule).filter(
            and_(
                PMSchedule.id == schedule_id,
                PMSchedule.organization_id == organization_id,
                PMSchedule.plant_id == plant_id
            )
        ).first()

    def get_pm_schedules(
        self,
        organization_id: int,
        plant_id: int,
        machine_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[PMSchedule]:
        """Get PM schedules with filters"""
        query = self.db.query(PMSchedule).filter(
            and_(
                PMSchedule.organization_id == organization_id,
                PMSchedule.plant_id == plant_id
            )
        )

        if machine_id is not None:
            query = query.filter(PMSchedule.machine_id == machine_id)

        if is_active is not None:
            query = query.filter(PMSchedule.is_active == is_active)

        return query.all()

    def update_pm_schedule(
        self,
        schedule_id: int,
        organization_id: int,
        plant_id: int,
        **updates
    ) -> Optional[PMSchedule]:
        """Update PM schedule"""
        pm_schedule = self.get_pm_schedule_by_id(schedule_id, organization_id, plant_id)
        if not pm_schedule:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(pm_schedule, key):
                setattr(pm_schedule, key, value)

        self.db.commit()
        self.db.refresh(pm_schedule)
        return pm_schedule

    def delete_pm_schedule(
        self,
        schedule_id: int,
        organization_id: int,
        plant_id: int
    ) -> bool:
        """Delete PM schedule"""
        pm_schedule = self.get_pm_schedule_by_id(schedule_id, organization_id, plant_id)
        if not pm_schedule:
            return False

        self.db.delete(pm_schedule)
        self.db.commit()
        return True

    # PM Work Order operations
    def create_pm_work_order(
        self,
        organization_id: int,
        plant_id: int,
        work_order_domain: PMWorkOrderDomain
    ) -> PMWorkOrder:
        """Create a new PM work order"""
        pm_work_order = PMWorkOrder(
            organization_id=organization_id,
            plant_id=plant_id,
            pm_schedule_id=work_order_domain.pm_schedule_id,
            machine_id=work_order_domain.machine_id,
            pm_number=work_order_domain.pm_number,
            status=work_order_domain.status,
            scheduled_date=work_order_domain.scheduled_date,
            due_date=work_order_domain.due_date,
            started_at=work_order_domain.started_at,
            completed_at=work_order_domain.completed_at
        )
        self.db.add(pm_work_order)
        self.db.commit()
        self.db.refresh(pm_work_order)
        return pm_work_order

    def get_pm_work_order_by_id(
        self,
        work_order_id: int,
        organization_id: int,
        plant_id: int
    ) -> Optional[PMWorkOrder]:
        """Get PM work order by ID with RLS"""
        return self.db.query(PMWorkOrder).filter(
            and_(
                PMWorkOrder.id == work_order_id,
                PMWorkOrder.organization_id == organization_id,
                PMWorkOrder.plant_id == plant_id
            )
        ).first()

    def get_pm_work_orders(
        self,
        organization_id: int,
        plant_id: int,
        machine_id: Optional[int] = None,
        status: Optional[PMStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PMWorkOrder]:
        """Get PM work orders with filters"""
        query = self.db.query(PMWorkOrder).filter(
            and_(
                PMWorkOrder.organization_id == organization_id,
                PMWorkOrder.plant_id == plant_id
            )
        )

        if machine_id is not None:
            query = query.filter(PMWorkOrder.machine_id == machine_id)

        if status is not None:
            query = query.filter(PMWorkOrder.status == status)

        if start_date is not None:
            query = query.filter(PMWorkOrder.scheduled_date >= start_date)

        if end_date is not None:
            query = query.filter(PMWorkOrder.scheduled_date <= end_date)

        return query.order_by(PMWorkOrder.scheduled_date).all()

    def update_pm_work_order(
        self,
        work_order_id: int,
        organization_id: int,
        plant_id: int,
        **updates
    ) -> Optional[PMWorkOrder]:
        """Update PM work order"""
        pm_work_order = self.get_pm_work_order_by_id(work_order_id, organization_id, plant_id)
        if not pm_work_order:
            return None

        for key, value in updates.items():
            if value is not None and hasattr(pm_work_order, key):
                setattr(pm_work_order, key, value)

        self.db.commit()
        self.db.refresh(pm_work_order)
        return pm_work_order

    # Downtime Event operations
    def create_downtime_event(
        self,
        organization_id: int,
        plant_id: int,
        event_domain: DowntimeEventDomain
    ) -> DowntimeEvent:
        """Create a new downtime event"""
        downtime_event = DowntimeEvent(
            organization_id=organization_id,
            plant_id=plant_id,
            machine_id=event_domain.machine_id,
            category=event_domain.category,
            reason=event_domain.reason,
            started_at=event_domain.started_at,
            ended_at=event_domain.ended_at
        )
        self.db.add(downtime_event)
        self.db.commit()
        self.db.refresh(downtime_event)
        return downtime_event

    def get_downtime_event_by_id(
        self,
        event_id: int,
        organization_id: int,
        plant_id: int
    ) -> Optional[DowntimeEvent]:
        """Get downtime event by ID with RLS"""
        return self.db.query(DowntimeEvent).filter(
            and_(
                DowntimeEvent.id == event_id,
                DowntimeEvent.organization_id == organization_id,
                DowntimeEvent.plant_id == plant_id
            )
        ).first()

    def get_downtime_events(
        self,
        organization_id: int,
        plant_id: int,
        machine_id: Optional[int] = None,
        category: Optional[DowntimeCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[DowntimeEvent]:
        """Get downtime events with filters"""
        query = self.db.query(DowntimeEvent).filter(
            and_(
                DowntimeEvent.organization_id == organization_id,
                DowntimeEvent.plant_id == plant_id
            )
        )

        if machine_id is not None:
            query = query.filter(DowntimeEvent.machine_id == machine_id)

        if category is not None:
            query = query.filter(DowntimeEvent.category == category)

        if start_date is not None:
            query = query.filter(DowntimeEvent.started_at >= start_date)

        if end_date is not None:
            query = query.filter(
                or_(
                    DowntimeEvent.ended_at <= end_date,
                    DowntimeEvent.ended_at.is_(None)  # Include ongoing events
                )
            )

        return query.order_by(DowntimeEvent.started_at.desc()).all()

    def update_downtime_event(
        self,
        event_id: int,
        organization_id: int,
        plant_id: int,
        **updates
    ) -> Optional[DowntimeEvent]:
        """Update downtime event"""
        downtime_event = self.get_downtime_event_by_id(event_id, organization_id, plant_id)
        if not downtime_event:
            return None

        for key, value in updates.items():
            if hasattr(downtime_event, key):
                setattr(downtime_event, key, value)

        self.db.commit()
        self.db.refresh(downtime_event)
        return downtime_event

    # MTBF/MTTR Calculations
    def calculate_mtbf_mttr(
        self,
        organization_id: int,
        plant_id: int,
        machine_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> MTBFMTTRMetrics:
        """
        Calculate MTBF/MTTR metrics for a machine within a date range.

        Uses breakdown downtime events for failure counting and repair time.
        Operating time = total time - all downtime.
        """
        # Get all breakdown events in the period
        breakdown_events = self.db.query(DowntimeEvent).filter(
            and_(
                DowntimeEvent.organization_id == organization_id,
                DowntimeEvent.plant_id == plant_id,
                DowntimeEvent.machine_id == machine_id,
                DowntimeEvent.category == DowntimeCategory.BREAKDOWN,
                DowntimeEvent.started_at >= start_date,
                DowntimeEvent.started_at <= end_date,
                DowntimeEvent.ended_at.isnot(None)  # Only completed events
            )
        ).all()

        # Calculate total repair time and number of failures
        number_of_failures = len(breakdown_events)
        total_repair_time = 0.0

        for event in breakdown_events:
            if event.ended_at:
                duration = (event.ended_at - event.started_at).total_seconds() / 60.0
                total_repair_time += duration

        # Calculate total time in period (minutes)
        total_time_in_period = (end_date - start_date).total_seconds() / 60.0

        # Get all downtime (all categories) to calculate operating time
        all_downtime_events = self.db.query(DowntimeEvent).filter(
            and_(
                DowntimeEvent.organization_id == organization_id,
                DowntimeEvent.plant_id == plant_id,
                DowntimeEvent.machine_id == machine_id,
                DowntimeEvent.started_at >= start_date,
                DowntimeEvent.started_at <= end_date,
                DowntimeEvent.ended_at.isnot(None)
            )
        ).all()

        total_downtime = 0.0
        for event in all_downtime_events:
            if event.ended_at:
                duration = (event.ended_at - event.started_at).total_seconds() / 60.0
                total_downtime += duration

        # Operating time = total time - downtime
        total_operating_time = max(0.0, total_time_in_period - total_downtime)

        # Calculate MTBF/MTTR metrics using domain service
        return MTBFMTTRCalculator.calculate_metrics(
            total_operating_time=total_operating_time,
            total_repair_time=total_repair_time,
            number_of_failures=number_of_failures
        )

    def calculate_comprehensive_maintenance_metrics(
        self,
        organization_id: int,
        plant_id: int,
        start_date: datetime,
        end_date: datetime,
        machine_id: Optional[int] = None
    ) -> dict:
        """
        Calculate comprehensive maintenance metrics including MTBF, MTTR, availability,
        and PM compliance for machines within a date range.

        Args:
            organization_id: Organization ID for RLS
            plant_id: Plant ID for RLS
            start_date: Start of metrics period
            end_date: End of metrics period
            machine_id: Optional specific machine ID (if None, calculates for all machines)

        Returns:
            Dict with machine_metrics list and plant_aggregate dict
        """
        from app.models.machine import Machine, MachineStatusHistory, MachineStatus

        # Build query for machines
        machines_query = self.db.query(Machine).filter(
            and_(
                Machine.organization_id == organization_id,
                Machine.plant_id == plant_id,
                Machine.is_active == True
            )
        )

        if machine_id is not None:
            machines_query = machines_query.filter(Machine.id == machine_id)

        machines = machines_query.all()

        if not machines:
            return {
                "machine_metrics": [],
                "plant_aggregate": {
                    "avg_mtbf_hours": 0.0,
                    "avg_mttr_hours": 0.0,
                    "total_failures": 0,
                    "total_downtime_hours": 0.0,
                    "avg_availability_percent": 0.0,
                    "avg_pm_compliance_percent": 0.0
                }
            }

        # Calculate total time period in hours
        total_time_hours = (end_date - start_date).total_seconds() / 3600.0

        machine_metrics = []
        total_failures_sum = 0
        total_downtime_sum = 0.0
        mtbf_sum = 0.0
        mttr_sum = 0.0
        availability_sum = 0.0
        pm_compliance_sum = 0.0
        machines_with_metrics = 0

        for machine in machines:
            # Calculate downtime from downtime events (all categories)
            all_downtime_events = self.db.query(DowntimeEvent).filter(
                and_(
                    DowntimeEvent.organization_id == organization_id,
                    DowntimeEvent.plant_id == plant_id,
                    DowntimeEvent.machine_id == machine.id,
                    DowntimeEvent.started_at >= start_date,
                    DowntimeEvent.started_at <= end_date,
                    DowntimeEvent.ended_at.isnot(None)
                )
            ).all()

            total_downtime_minutes = 0.0
            for event in all_downtime_events:
                if event.ended_at:
                    duration = (event.ended_at - event.started_at).total_seconds() / 60.0
                    total_downtime_minutes += duration

            total_downtime_hours_machine = total_downtime_minutes / 60.0

            # Calculate breakdown-specific metrics (failures and repair time)
            breakdown_events = self.db.query(DowntimeEvent).filter(
                and_(
                    DowntimeEvent.organization_id == organization_id,
                    DowntimeEvent.plant_id == plant_id,
                    DowntimeEvent.machine_id == machine.id,
                    DowntimeEvent.category == DowntimeCategory.BREAKDOWN,
                    DowntimeEvent.started_at >= start_date,
                    DowntimeEvent.started_at <= end_date,
                    DowntimeEvent.ended_at.isnot(None)
                )
            ).all()

            number_of_failures = len(breakdown_events)
            total_repair_minutes = 0.0

            for event in breakdown_events:
                if event.ended_at:
                    duration = (event.ended_at - event.started_at).total_seconds() / 60.0
                    total_repair_minutes += duration

            total_repair_hours = total_repair_minutes / 60.0

            # Calculate operating time
            total_operating_hours = max(0.0, total_time_hours - total_downtime_hours_machine)

            # Calculate MTBF and MTTR (in hours)
            if number_of_failures > 0:
                mtbf_hours = total_operating_hours / number_of_failures
                mttr_hours = total_repair_hours / number_of_failures
            else:
                mtbf_hours = float('inf')
                mttr_hours = 0.0

            # Calculate availability (using formula: (Total Time - Downtime) / Total Time × 100)
            if total_time_hours > 0:
                availability_percent = ((total_time_hours - total_downtime_hours_machine) / total_time_hours) * 100
            else:
                availability_percent = 0.0

            # Calculate PM compliance
            scheduled_pms = self.db.query(PMWorkOrder).filter(
                and_(
                    PMWorkOrder.organization_id == organization_id,
                    PMWorkOrder.plant_id == plant_id,
                    PMWorkOrder.machine_id == machine.id,
                    PMWorkOrder.scheduled_date >= start_date,
                    PMWorkOrder.scheduled_date <= end_date
                )
            ).all()

            scheduled_pm_count = len(scheduled_pms)
            completed_pm_count = len([pm for pm in scheduled_pms if pm.status == PMStatus.COMPLETED])

            if scheduled_pm_count > 0:
                pm_compliance_percent = (completed_pm_count / scheduled_pm_count) * 100
            else:
                pm_compliance_percent = 0.0

            # Add to machine metrics
            machine_metrics.append({
                "machine_id": machine.id,
                "machine_code": machine.machine_code,
                "machine_name": machine.machine_name,
                "mtbf_hours": round(mtbf_hours, 2) if mtbf_hours != float('inf') else 0.0,
                "mttr_hours": round(mttr_hours, 2),
                "total_failures": number_of_failures,
                "total_downtime_hours": round(total_downtime_hours_machine, 2),
                "total_repair_hours": round(total_repair_hours, 2),
                "total_operating_hours": round(total_operating_hours, 2),
                "availability_percent": round(availability_percent, 2),
                "pm_compliance_percent": round(pm_compliance_percent, 2),
                "scheduled_pm_count": scheduled_pm_count,
                "completed_pm_count": completed_pm_count
            })

            # Aggregate for plant-level metrics
            total_failures_sum += number_of_failures
            total_downtime_sum += total_downtime_hours_machine

            # Only include machines with finite MTBF in averages
            if mtbf_hours != float('inf'):
                mtbf_sum += mtbf_hours
                machines_with_metrics += 1

            mttr_sum += mttr_hours
            availability_sum += availability_percent
            pm_compliance_sum += pm_compliance_percent

        # Calculate plant aggregate metrics
        machine_count = len(machines)
        if machine_count > 0:
            # Use machines_with_metrics for MTBF average to avoid division issues
            avg_mtbf = mtbf_sum / machines_with_metrics if machines_with_metrics > 0 else 0.0
            avg_mttr = mttr_sum / machine_count
            avg_availability = availability_sum / machine_count
            avg_pm_compliance = pm_compliance_sum / machine_count
        else:
            avg_mtbf = 0.0
            avg_mttr = 0.0
            avg_availability = 0.0
            avg_pm_compliance = 0.0

        plant_aggregate = {
            "avg_mtbf_hours": round(avg_mtbf, 2),
            "avg_mttr_hours": round(avg_mttr, 2),
            "total_failures": total_failures_sum,
            "total_downtime_hours": round(total_downtime_sum, 2),
            "avg_availability_percent": round(avg_availability, 2),
            "avg_pm_compliance_percent": round(avg_pm_compliance, 2)
        }

        return {
            "machine_metrics": machine_metrics,
            "plant_aggregate": plant_aggregate
        }
