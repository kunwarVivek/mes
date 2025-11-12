"""
MachineRepository - Infrastructure layer repository for Machine entities.

Handles database operations for Machine and MachineStatusHistory with:
- CRUD operations with domain validation
- RLS-aware queries (context set automatically by get_db())
- Status change tracking with history
- OEE calculation support via status history queries
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, func
from datetime import datetime
import logging

from app.models.machine import Machine, MachineStatusHistory
from app.domain.entities.machine import MachineDomain, MachineStatusHistoryDomain, MachineStatus

logger = logging.getLogger(__name__)


class MachineRepository:
    """
    Repository for Machine entity persistence.

    Provides CRUD operations and status tracking functionality.
    RLS context is automatically applied from database session.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session with RLS context
        """
        self._db = db

    def create(self, machine_data: dict) -> Machine:
        """
        Create new machine with domain validation.

        Args:
            machine_data: Dictionary with machine attributes

        Returns:
            Created Machine entity

        Raises:
            ValueError: If validation fails or machine code exists
        """
        # Domain validation
        domain_machine = MachineDomain(
            id=None,
            organization_id=machine_data["organization_id"],
            plant_id=machine_data["plant_id"],
            machine_code=machine_data["machine_code"],
            machine_name=machine_data["machine_name"],
            description=machine_data.get("description", ""),
            work_center_id=machine_data["work_center_id"],
            status=MachineStatus(machine_data.get("status", "AVAILABLE")),
            is_active=machine_data.get("is_active", True)
        )

        # Create database model
        db_machine = Machine(
            organization_id=machine_data["organization_id"],
            plant_id=machine_data["plant_id"],
            machine_code=domain_machine.machine_code,
            machine_name=machine_data["machine_name"],
            description=machine_data.get("description"),
            work_center_id=machine_data["work_center_id"],
            status=MachineStatus(machine_data.get("status", "AVAILABLE")),
            is_active=machine_data.get("is_active", True)
        )

        try:
            self._db.add(db_machine)
            self._db.commit()
            self._db.refresh(db_machine)
            logger.info(f"Created machine: {db_machine.machine_code}")
            return db_machine
        except IntegrityError as e:
            self._db.rollback()
            logger.error(f"Failed to create machine: {e}")
            raise ValueError(f"Machine code {domain_machine.machine_code} already exists")

    def get_by_id(self, machine_id: int) -> Optional[Machine]:
        """
        Retrieve machine by ID.

        RLS filtering is automatic from session context.

        Args:
            machine_id: Machine ID

        Returns:
            Machine entity or None if not found
        """
        return self._db.query(Machine).filter(Machine.id == machine_id).first()

    def get_by_machine_code(
        self, org_id: int, plant_id: int, machine_code: str
    ) -> Optional[Machine]:
        """
        Retrieve machine by unique machine code within org/plant.

        Args:
            org_id: Organization ID
            plant_id: Plant ID
            machine_code: Machine code (unique)

        Returns:
            Machine entity or None if not found
        """
        return (
            self._db.query(Machine)
            .filter(Machine.organization_id == org_id)
            .filter(Machine.plant_id == plant_id)
            .filter(Machine.machine_code == machine_code)
            .first()
        )

    def update(self, machine_id: int, updates: dict) -> Machine:
        """
        Update machine with validation.

        Args:
            machine_id: Machine ID to update
            updates: Dictionary with fields to update

        Returns:
            Updated Machine entity

        Raises:
            ValueError: If machine not found or validation fails
        """
        db_machine = self._db.query(Machine).filter(Machine.id == machine_id).first()
        if not db_machine:
            raise ValueError(f"Machine with id {machine_id} not found")

        # Update allowed fields
        updatable_fields = [
            "machine_name",
            "description",
            "work_center_id",
            "status",
            "is_active",
        ]

        for field, value in updates.items():
            if field in updatable_fields:
                if field == "status":
                    setattr(db_machine, field, MachineStatus(value))
                else:
                    setattr(db_machine, field, value)

        self._db.commit()
        self._db.refresh(db_machine)
        logger.info(f"Updated machine: {db_machine.machine_code}")
        return db_machine

    def delete(self, machine_id: int) -> bool:
        """
        Soft delete machine (set is_active=False).

        Args:
            machine_id: Machine ID to delete

        Returns:
            True if deleted, False if not found
        """
        db_machine = self._db.query(Machine).filter(Machine.id == machine_id).first()
        if not db_machine:
            return False

        db_machine.is_active = False
        self._db.commit()
        logger.info(f"Soft deleted machine: {db_machine.machine_code}")
        return True

    def list_by_organization(
        self,
        org_id: int,
        plant_id: Optional[int] = None,
        filters: Optional[dict] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """
        List machines with pagination and filtering.

        Args:
            org_id: Organization ID
            plant_id: Optional plant ID filter
            filters: Optional filters (status, work_center_id, is_active)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with items, total, page, page_size, total_pages
        """
        query = self._db.query(Machine).filter(Machine.organization_id == org_id)

        if plant_id is not None:
            query = query.filter(Machine.plant_id == plant_id)

        # Apply filters
        if filters:
            if "status" in filters:
                query = query.filter(Machine.status == MachineStatus(filters["status"]))
            if "work_center_id" in filters:
                query = query.filter(Machine.work_center_id == filters["work_center_id"])
            if "is_active" in filters:
                query = query.filter(Machine.is_active == filters["is_active"])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def change_status(
        self, machine_id: int, new_status: MachineStatus, notes: Optional[str] = None
    ) -> tuple[Machine, MachineStatusHistory]:
        """
        Change machine status and create history record.

        This method:
        1. Ends the current status period (if exists)
        2. Updates machine status
        3. Creates new status history record

        Args:
            machine_id: Machine ID
            new_status: New status to set
            notes: Optional notes about status change

        Returns:
            Tuple of (updated_machine, new_status_history)

        Raises:
            ValueError: If machine not found
        """
        db_machine = self._db.query(Machine).filter(Machine.id == machine_id).first()
        if not db_machine:
            raise ValueError(f"Machine with id {machine_id} not found")

        # End current status period if exists
        current_status = (
            self._db.query(MachineStatusHistory)
            .filter(MachineStatusHistory.machine_id == machine_id)
            .filter(MachineStatusHistory.ended_at.is_(None))
            .first()
        )

        now = datetime.utcnow()

        if current_status:
            current_status.ended_at = now
            logger.info(f"Ended status period for machine {machine_id}: {current_status.status}")

        # Update machine status
        db_machine.status = new_status

        # Create new status history record
        status_history = MachineStatusHistory(
            machine_id=machine_id,
            status=new_status,
            started_at=now,
            ended_at=None,
            notes=notes
        )

        self._db.add(status_history)
        self._db.commit()
        self._db.refresh(db_machine)
        self._db.refresh(status_history)

        logger.info(f"Changed machine {db_machine.machine_code} status to {new_status}")
        return db_machine, status_history

    def get_status_history(
        self,
        machine_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MachineStatusHistory]:
        """
        Get status history for a machine within a time period.

        Args:
            machine_id: Machine ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum records to return

        Returns:
            List of MachineStatusHistory records ordered by started_at desc
        """
        query = (
            self._db.query(MachineStatusHistory)
            .filter(MachineStatusHistory.machine_id == machine_id)
        )

        if start_date:
            query = query.filter(MachineStatusHistory.started_at >= start_date)
        if end_date:
            query = query.filter(MachineStatusHistory.started_at <= end_date)

        return query.order_by(MachineStatusHistory.started_at.desc()).limit(limit).all()

    def calculate_downtime(
        self,
        machine_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calculate total downtime (DOWN + MAINTENANCE) in minutes for a time period.

        Args:
            machine_id: Machine ID
            start_date: Start of time period
            end_date: End of time period

        Returns:
            Total downtime in minutes
        """
        downtime_statuses = [MachineStatus.DOWN, MachineStatus.MAINTENANCE]

        history_records = (
            self._db.query(MachineStatusHistory)
            .filter(MachineStatusHistory.machine_id == machine_id)
            .filter(
                and_(
                    MachineStatusHistory.started_at < end_date,
                    func.coalesce(MachineStatusHistory.ended_at, end_date) > start_date
                )
            )
            .filter(MachineStatusHistory.status.in_(downtime_statuses))
            .all()
        )

        total_downtime_minutes = 0.0

        for record in history_records:
            # Calculate overlap with requested time period
            period_start = max(record.started_at, start_date)
            period_end = min(record.ended_at or end_date, end_date)

            if period_end > period_start:
                duration = (period_end - period_start).total_seconds() / 60.0
                total_downtime_minutes += duration

        return total_downtime_minutes

    def calculate_utilization(
        self,
        machine_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Calculate machine utilization metrics for a time period.

        Calculates:
        - Total running hours (RUNNING status)
        - Total downtime hours (DOWN + MAINTENANCE)
        - Utilization percentage
        - OEE Availability

        Args:
            machine_id: Machine ID
            start_date: Start of time period
            end_date: End of time period

        Returns:
            Dictionary with utilization metrics
        """
        logger.info(f"Calculating utilization for machine {machine_id} from {start_date} to {end_date}")

        # Get all status history records that overlap with the time period
        history_records = (
            self._db.query(MachineStatusHistory)
            .filter(MachineStatusHistory.machine_id == machine_id)
            .filter(
                and_(
                    MachineStatusHistory.started_at < end_date,
                    func.coalesce(MachineStatusHistory.ended_at, end_date) > start_date
                )
            )
            .all()
        )

        # Calculate total time in each status
        total_running_seconds = 0.0
        total_downtime_seconds = 0.0
        total_maintenance_seconds = 0.0

        for record in history_records:
            # Calculate overlap with requested time period
            period_start = max(record.started_at, start_date)
            period_end = min(record.ended_at or end_date, end_date)

            if period_end > period_start:
                duration_seconds = (period_end - period_start).total_seconds()

                if record.status == MachineStatus.RUNNING:
                    total_running_seconds += duration_seconds
                elif record.status == MachineStatus.DOWN:
                    total_downtime_seconds += duration_seconds
                elif record.status == MachineStatus.MAINTENANCE:
                    total_maintenance_seconds += duration_seconds

        # Calculate total period in seconds
        total_period_seconds = (end_date - start_date).total_seconds()

        # Convert to hours
        total_period_hours = total_period_seconds / 3600.0
        total_running_hours = total_running_seconds / 3600.0
        total_downtime_hours = (total_downtime_seconds + total_maintenance_seconds) / 3600.0

        # Calculate utilization percentage
        utilization_percent = (total_running_hours / total_period_hours * 100.0) if total_period_hours > 0 else 0.0

        # Calculate OEE Availability
        # OEE Availability = (Planned Production Time - Unplanned Downtime) / Planned Production Time × 100
        # For simplicity, we consider:
        # - Planned production time = total period - scheduled maintenance
        # - Unplanned downtime = time in DOWN status
        planned_production_time_hours = total_period_hours - (total_maintenance_seconds / 3600.0)
        unplanned_downtime_hours = total_downtime_seconds / 3600.0

        if planned_production_time_hours > 0:
            oee_availability = ((planned_production_time_hours - unplanned_downtime_hours) / planned_production_time_hours) * 100.0
            # Ensure it's within 0-100 range
            oee_availability = max(0.0, min(100.0, oee_availability))
        else:
            oee_availability = 0.0

        logger.info(
            f"Utilization calculated - Running: {total_running_hours:.2f}h, "
            f"Downtime: {total_downtime_hours:.2f}h, "
            f"Utilization: {utilization_percent:.2f}%, "
            f"OEE Availability: {oee_availability:.2f}%"
        )

        return {
            "total_available_hours": total_period_hours,
            "total_running_hours": total_running_hours,
            "total_downtime_hours": total_downtime_hours,
            "utilization_percent": utilization_percent,
            "oee_availability": oee_availability
        }
