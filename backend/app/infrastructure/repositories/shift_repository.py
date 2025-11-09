"""
Repository for Shift and ShiftHandover entities.
Handles database operations with RLS enforcement.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, Dict, Any, List
from datetime import datetime
import math

from app.models.shift import Shift, ShiftHandover, ShiftPerformance
from app.domain.entities.shift import ShiftDomain, ShiftHandoverDomain


class ShiftRepository:
    """Repository for Shift entity operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, shift_data: Dict[str, Any]) -> Shift:
        """Create a new shift"""
        # Validate using domain entity
        domain_shift = ShiftDomain(
            id=None,
            organization_id=shift_data["organization_id"],
            plant_id=shift_data["plant_id"],
            shift_name=shift_data["shift_name"],
            shift_code=shift_data["shift_code"],
            start_time=shift_data["start_time"],
            end_time=shift_data["end_time"],
            production_target=shift_data.get("production_target", 0.0),
            is_active=shift_data.get("is_active", True),
        )

        # Check for duplicate shift code
        existing = self.db.query(Shift).filter(
            and_(
                Shift.organization_id == shift_data["organization_id"],
                Shift.plant_id == shift_data["plant_id"],
                Shift.shift_code == domain_shift.shift_code
            )
        ).first()

        if existing:
            raise ValueError(f"Shift code {domain_shift.shift_code} already exists for this organization and plant")

        # Create database entity
        db_shift = Shift(
            organization_id=shift_data["organization_id"],
            plant_id=shift_data["plant_id"],
            shift_name=domain_shift.shift_name,
            shift_code=domain_shift.shift_code,
            start_time=domain_shift.start_time,
            end_time=domain_shift.end_time,
            production_target=domain_shift.production_target,
            is_active=domain_shift.is_active,
        )

        self.db.add(db_shift)
        self.db.commit()
        self.db.refresh(db_shift)
        return db_shift

    def get_by_id(self, shift_id: int) -> Optional[Shift]:
        """Get shift by ID (RLS filtering applied automatically)"""
        return self.db.query(Shift).filter(Shift.id == shift_id).first()

    def get_by_code(self, organization_id: int, plant_id: int, shift_code: str) -> Optional[Shift]:
        """Get shift by code"""
        return self.db.query(Shift).filter(
            and_(
                Shift.organization_id == organization_id,
                Shift.plant_id == plant_id,
                Shift.shift_code == shift_code.upper()
            )
        ).first()

    def list_by_organization(
        self,
        org_id: int,
        plant_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List shifts with pagination and filters"""
        query = self.db.query(Shift).filter(Shift.organization_id == org_id)

        if plant_id is not None:
            query = query.filter(Shift.plant_id == plant_id)

        # Apply filters
        if filters:
            if "is_active" in filters:
                query = query.filter(Shift.is_active == filters["is_active"])
            if "shift_code" in filters:
                query = query.filter(Shift.shift_code == filters["shift_code"].upper())

        # Get total count
        total = query.count()

        # Apply pagination
        query = query.order_by(Shift.shift_code).offset((page - 1) * page_size).limit(page_size)

        items = query.all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }

    def update(self, shift_id: int, update_data: Dict[str, Any]) -> Shift:
        """Update shift by ID"""
        db_shift = self.get_by_id(shift_id)
        if not db_shift:
            raise ValueError(f"Shift with ID {shift_id} not found")

        # Update allowed fields
        allowed_fields = ["shift_name", "start_time", "end_time", "production_target", "is_active"]
        for field in allowed_fields:
            if field in update_data:
                setattr(db_shift, field, update_data[field])

        self.db.commit()
        self.db.refresh(db_shift)
        return db_shift

    def delete(self, shift_id: int) -> bool:
        """Delete shift by ID (hard delete)"""
        db_shift = self.get_by_id(shift_id)
        if not db_shift:
            return False

        self.db.delete(db_shift)
        self.db.commit()
        return True

    def activate(self, shift_id: int) -> Shift:
        """Activate shift"""
        db_shift = self.get_by_id(shift_id)
        if not db_shift:
            raise ValueError(f"Shift with ID {shift_id} not found")

        db_shift.is_active = True
        self.db.commit()
        self.db.refresh(db_shift)
        return db_shift

    def deactivate(self, shift_id: int) -> Shift:
        """Deactivate shift"""
        db_shift = self.get_by_id(shift_id)
        if not db_shift:
            raise ValueError(f"Shift with ID {shift_id} not found")

        db_shift.is_active = False
        self.db.commit()
        self.db.refresh(db_shift)
        return db_shift


class ShiftHandoverRepository:
    """Repository for ShiftHandover entity operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, handover_data: Dict[str, Any]) -> ShiftHandover:
        """Create a new shift handover"""
        # Validate using domain entity
        domain_handover = ShiftHandoverDomain(
            id=None,
            organization_id=handover_data["organization_id"],
            plant_id=handover_data["plant_id"],
            from_shift_id=handover_data["from_shift_id"],
            to_shift_id=handover_data["to_shift_id"],
            handover_date=handover_data["handover_date"],
            wip_quantity=handover_data.get("wip_quantity", 0.0),
            production_summary=handover_data["production_summary"],
            quality_issues=handover_data.get("quality_issues"),
            machine_status=handover_data.get("machine_status"),
            material_status=handover_data.get("material_status"),
            safety_incidents=handover_data.get("safety_incidents"),
            handover_by_user_id=handover_data["handover_by_user_id"],
        )

        # Verify shifts exist
        from_shift = self.db.query(Shift).filter(Shift.id == handover_data["from_shift_id"]).first()
        to_shift = self.db.query(Shift).filter(Shift.id == handover_data["to_shift_id"]).first()

        if not from_shift:
            raise ValueError(f"From shift with ID {handover_data['from_shift_id']} not found")
        if not to_shift:
            raise ValueError(f"To shift with ID {handover_data['to_shift_id']} not found")

        # Create database entity
        db_handover = ShiftHandover(
            organization_id=handover_data["organization_id"],
            plant_id=handover_data["plant_id"],
            from_shift_id=domain_handover.from_shift_id,
            to_shift_id=domain_handover.to_shift_id,
            handover_date=domain_handover.handover_date,
            wip_quantity=domain_handover.wip_quantity,
            production_summary=domain_handover.production_summary,
            quality_issues=domain_handover.quality_issues,
            machine_status=domain_handover.machine_status,
            material_status=domain_handover.material_status,
            safety_incidents=domain_handover.safety_incidents,
            handover_by_user_id=domain_handover.handover_by_user_id,
        )

        self.db.add(db_handover)
        self.db.commit()
        self.db.refresh(db_handover)
        return db_handover

    def get_by_id(self, handover_id: int) -> Optional[ShiftHandover]:
        """Get shift handover by ID (RLS filtering applied automatically)"""
        return self.db.query(ShiftHandover).filter(ShiftHandover.id == handover_id).first()

    def list_by_organization(
        self,
        org_id: int,
        plant_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List shift handovers with pagination and filters"""
        query = self.db.query(ShiftHandover).filter(ShiftHandover.organization_id == org_id)

        if plant_id is not None:
            query = query.filter(ShiftHandover.plant_id == plant_id)

        # Apply filters
        if filters:
            if "from_shift_id" in filters:
                query = query.filter(ShiftHandover.from_shift_id == filters["from_shift_id"])
            if "to_shift_id" in filters:
                query = query.filter(ShiftHandover.to_shift_id == filters["to_shift_id"])
            if "acknowledged" in filters:
                if filters["acknowledged"]:
                    query = query.filter(ShiftHandover.acknowledged_by_user_id.isnot(None))
                else:
                    query = query.filter(ShiftHandover.acknowledged_by_user_id.is_(None))

        # Get total count
        total = query.count()

        # Apply pagination (most recent first)
        query = query.order_by(desc(ShiftHandover.handover_date)).offset((page - 1) * page_size).limit(page_size)

        items = query.all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }

    def acknowledge(self, handover_id: int, user_id: int) -> ShiftHandover:
        """Acknowledge a shift handover"""
        db_handover = self.get_by_id(handover_id)
        if not db_handover:
            raise ValueError(f"Shift handover with ID {handover_id} not found")

        if db_handover.acknowledged_by_user_id is not None:
            raise ValueError("Handover already acknowledged")

        db_handover.acknowledged_by_user_id = user_id
        db_handover.acknowledged_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_handover)
        return db_handover


class ShiftPerformanceRepository:
    """Repository for ShiftPerformance entity operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_shift_and_date(
        self, shift_id: int, performance_date: datetime
    ) -> Optional[ShiftPerformance]:
        """Get shift performance for a specific shift and date"""
        return self.db.query(ShiftPerformance).filter(
            and_(
                ShiftPerformance.shift_id == shift_id,
                ShiftPerformance.performance_date == performance_date
            )
        ).first()

    def list_by_shift(
        self,
        shift_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List shift performance records with pagination"""
        query = self.db.query(ShiftPerformance).filter(ShiftPerformance.shift_id == shift_id)

        if start_date:
            query = query.filter(ShiftPerformance.performance_date >= start_date)
        if end_date:
            query = query.filter(ShiftPerformance.performance_date <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination (most recent first)
        query = query.order_by(desc(ShiftPerformance.performance_date)).offset((page - 1) * page_size).limit(page_size)

        items = query.all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }
