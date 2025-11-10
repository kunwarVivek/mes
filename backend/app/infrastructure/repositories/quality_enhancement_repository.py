"""
Repository for Quality Enhancement (Inspection Plans, SPC, Quality Measurements)
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, asc, Integer
from datetime import datetime, timezone

from app.models.quality_enhancement import (
    InspectionPlan,
    InspectionPoint,
    InspectionCharacteristic,
    InspectionMeasurement
)
from app.application.dtos.quality_enhancement_dto import (
    InspectionPlanCreateDTO,
    InspectionPlanUpdateDTO,
    InspectionPointCreateDTO,
    InspectionPointUpdateDTO,
    InspectionCharacteristicCreateDTO,
    InspectionCharacteristicUpdateDTO,
    InspectionMeasurementCreateDTO,
)


class InspectionPlanRepository:
    """Repository for InspectionPlan operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: InspectionPlanCreateDTO) -> InspectionPlan:
        """Create a new inspection plan"""
        plan = InspectionPlan(
            organization_id=dto.organization_id,
            plant_id=dto.plant_id,
            plan_code=dto.plan_code,
            plan_name=dto.plan_name,
            description=dto.description,
            plan_type=dto.plan_type,
            applies_to=dto.applies_to,
            material_id=dto.material_id,
            work_center_id=dto.work_center_id,
            frequency=dto.frequency,
            frequency_value=dto.frequency_value,
            sample_size=dto.sample_size,
            spc_enabled=dto.spc_enabled,
            control_limits_config=dto.control_limits_config,
            effective_date=dto.effective_date,
            expiry_date=dto.expiry_date,
            instructions=dto.instructions,
            acceptance_criteria=dto.acceptance_criteria,
            created_by=dto.created_by,
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_by_id(self, plan_id: int) -> Optional[InspectionPlan]:
        """Get inspection plan by ID"""
        return self.db.query(InspectionPlan).filter(InspectionPlan.id == plan_id).first()

    def get_by_code(self, organization_id: int, plan_code: str) -> Optional[InspectionPlan]:
        """Get inspection plan by code"""
        return self.db.query(InspectionPlan).filter(
            and_(
                InspectionPlan.organization_id == organization_id,
                InspectionPlan.plan_code == plan_code
            )
        ).first()

    def list_by_organization(self, organization_id: int, skip: int = 0, limit: int = 100,
                            plan_type: Optional[str] = None, plant_id: Optional[int] = None,
                            active_only: bool = True) -> List[InspectionPlan]:
        """List inspection plans for an organization"""
        query = self.db.query(InspectionPlan).filter(
            InspectionPlan.organization_id == organization_id
        )

        if active_only:
            query = query.filter(InspectionPlan.is_active == True)

        if plan_type:
            query = query.filter(InspectionPlan.plan_type == plan_type)

        if plant_id:
            query = query.filter(InspectionPlan.plant_id == plant_id)

        return query.order_by(desc(InspectionPlan.created_at)).offset(skip).limit(limit).all()

    def list_by_material(self, material_id: int, skip: int = 0, limit: int = 100) -> List[InspectionPlan]:
        """List inspection plans for a specific material"""
        return self.db.query(InspectionPlan).filter(
            and_(
                InspectionPlan.material_id == material_id,
                InspectionPlan.is_active == True
            )
        ).order_by(InspectionPlan.plan_name).offset(skip).limit(limit).all()

    def list_effective_plans(self, organization_id: int, plan_type: Optional[str] = None) -> List[InspectionPlan]:
        """List currently effective inspection plans"""
        today = datetime.now(timezone.utc).date()

        query = self.db.query(InspectionPlan).filter(
            and_(
                InspectionPlan.organization_id == organization_id,
                InspectionPlan.is_active == True,
                or_(
                    InspectionPlan.effective_date.is_(None),
                    InspectionPlan.effective_date <= today
                ),
                or_(
                    InspectionPlan.expiry_date.is_(None),
                    InspectionPlan.expiry_date >= today
                )
            )
        )

        if plan_type:
            query = query.filter(InspectionPlan.plan_type == plan_type)

        return query.all()

    def update(self, plan_id: int, dto: InspectionPlanUpdateDTO) -> Optional[InspectionPlan]:
        """Update inspection plan"""
        plan = self.get_by_id(plan_id)
        if not plan:
            return None

        if dto.plan_name:
            plan.plan_name = dto.plan_name
        if dto.description is not None:
            plan.description = dto.description
        if dto.material_id is not None:
            plan.material_id = dto.material_id
        if dto.work_center_id is not None:
            plan.work_center_id = dto.work_center_id
        if dto.frequency:
            plan.frequency = dto.frequency
        if dto.frequency_value is not None:
            plan.frequency_value = dto.frequency_value
        if dto.sample_size is not None:
            plan.sample_size = dto.sample_size
        if dto.spc_enabled is not None:
            plan.spc_enabled = dto.spc_enabled
        if dto.control_limits_config is not None:
            plan.control_limits_config = dto.control_limits_config
        if dto.effective_date is not None:
            plan.effective_date = dto.effective_date
        if dto.expiry_date is not None:
            plan.expiry_date = dto.expiry_date
        if dto.instructions is not None:
            plan.instructions = dto.instructions
        if dto.acceptance_criteria is not None:
            plan.acceptance_criteria = dto.acceptance_criteria
        if dto.is_active is not None:
            plan.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def approve(self, plan_id: int, approved_by: int) -> Optional[InspectionPlan]:
        """Approve an inspection plan"""
        plan = self.get_by_id(plan_id)
        if not plan:
            return None

        plan.approved_by = approved_by
        plan.approved_date = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def delete(self, plan_id: int) -> bool:
        """Delete inspection plan (soft delete)"""
        plan = self.get_by_id(plan_id)
        if not plan:
            return False

        plan.is_active = False
        self.db.commit()
        return True


class InspectionPointRepository:
    """Repository for InspectionPoint operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: InspectionPointCreateDTO) -> InspectionPoint:
        """Create a new inspection point"""
        point = InspectionPoint(
            organization_id=dto.organization_id,
            inspection_plan_id=dto.inspection_plan_id,
            point_code=dto.point_code,
            point_name=dto.point_name,
            description=dto.description,
            inspection_method=dto.inspection_method,
            inspection_equipment=dto.inspection_equipment,
            sequence=dto.sequence,
            is_mandatory=dto.is_mandatory,
            is_critical=dto.is_critical,
            inspection_instructions=dto.inspection_instructions,
            acceptance_criteria=dto.acceptance_criteria,
        )
        self.db.add(point)
        self.db.commit()
        self.db.refresh(point)
        return point

    def get_by_id(self, point_id: int) -> Optional[InspectionPoint]:
        """Get inspection point by ID"""
        return self.db.query(InspectionPoint).filter(InspectionPoint.id == point_id).first()

    def list_by_plan(self, inspection_plan_id: int, skip: int = 0, limit: int = 100,
                    active_only: bool = True) -> List[InspectionPoint]:
        """List inspection points for a plan"""
        query = self.db.query(InspectionPoint).filter(
            InspectionPoint.inspection_plan_id == inspection_plan_id
        )

        if active_only:
            query = query.filter(InspectionPoint.is_active == True)

        return query.order_by(asc(InspectionPoint.sequence), asc(InspectionPoint.point_code)).offset(skip).limit(limit).all()

    def list_critical_points(self, inspection_plan_id: int) -> List[InspectionPoint]:
        """List critical inspection points for a plan"""
        return self.db.query(InspectionPoint).filter(
            and_(
                InspectionPoint.inspection_plan_id == inspection_plan_id,
                InspectionPoint.is_critical == True,
                InspectionPoint.is_active == True
            )
        ).order_by(asc(InspectionPoint.sequence)).all()

    def update(self, point_id: int, dto: InspectionPointUpdateDTO) -> Optional[InspectionPoint]:
        """Update inspection point"""
        point = self.get_by_id(point_id)
        if not point:
            return None

        if dto.point_name:
            point.point_name = dto.point_name
        if dto.description is not None:
            point.description = dto.description
        if dto.inspection_method is not None:
            point.inspection_method = dto.inspection_method
        if dto.inspection_equipment is not None:
            point.inspection_equipment = dto.inspection_equipment
        if dto.sequence is not None:
            point.sequence = dto.sequence
        if dto.is_mandatory is not None:
            point.is_mandatory = dto.is_mandatory
        if dto.is_critical is not None:
            point.is_critical = dto.is_critical
        if dto.inspection_instructions is not None:
            point.inspection_instructions = dto.inspection_instructions
        if dto.acceptance_criteria is not None:
            point.acceptance_criteria = dto.acceptance_criteria
        if dto.is_active is not None:
            point.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(point)
        return point

    def delete(self, point_id: int) -> bool:
        """Delete inspection point (soft delete)"""
        point = self.get_by_id(point_id)
        if not point:
            return False

        point.is_active = False
        self.db.commit()
        return True


class InspectionCharacteristicRepository:
    """Repository for InspectionCharacteristic operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: InspectionCharacteristicCreateDTO) -> InspectionCharacteristic:
        """Create a new inspection characteristic"""
        characteristic = InspectionCharacteristic(
            organization_id=dto.organization_id,
            inspection_point_id=dto.inspection_point_id,
            characteristic_code=dto.characteristic_code,
            characteristic_name=dto.characteristic_name,
            description=dto.description,
            characteristic_type=dto.characteristic_type,
            data_type=dto.data_type,
            unit_of_measure=dto.unit_of_measure,
            target_value=dto.target_value,
            lower_spec_limit=dto.lower_spec_limit,
            upper_spec_limit=dto.upper_spec_limit,
            lower_control_limit=dto.lower_control_limit,
            upper_control_limit=dto.upper_control_limit,
            track_spc=dto.track_spc,
            control_chart_type=dto.control_chart_type,
            subgroup_size=dto.subgroup_size,
            allowed_values=dto.allowed_values,
            tolerance_type=dto.tolerance_type,
            tolerance=dto.tolerance,
            sequence=dto.sequence,
        )
        self.db.add(characteristic)
        self.db.commit()
        self.db.refresh(characteristic)
        return characteristic

    def get_by_id(self, characteristic_id: int) -> Optional[InspectionCharacteristic]:
        """Get inspection characteristic by ID"""
        return self.db.query(InspectionCharacteristic).filter(
            InspectionCharacteristic.id == characteristic_id
        ).first()

    def list_by_point(self, inspection_point_id: int, skip: int = 0, limit: int = 100,
                     active_only: bool = True) -> List[InspectionCharacteristic]:
        """List inspection characteristics for a point"""
        query = self.db.query(InspectionCharacteristic).filter(
            InspectionCharacteristic.inspection_point_id == inspection_point_id
        )

        if active_only:
            query = query.filter(InspectionCharacteristic.is_active == True)

        return query.order_by(asc(InspectionCharacteristic.sequence), asc(InspectionCharacteristic.characteristic_code)).offset(skip).limit(limit).all()

    def list_spc_characteristics(self, inspection_plan_id: int) -> List[InspectionCharacteristic]:
        """List all SPC-tracked characteristics for a plan"""
        return self.db.query(InspectionCharacteristic).join(
            InspectionPoint,
            InspectionCharacteristic.inspection_point_id == InspectionPoint.id
        ).filter(
            and_(
                InspectionPoint.inspection_plan_id == inspection_plan_id,
                InspectionCharacteristic.track_spc == True,
                InspectionCharacteristic.is_active == True
            )
        ).all()

    def update(self, characteristic_id: int, dto: InspectionCharacteristicUpdateDTO) -> Optional[InspectionCharacteristic]:
        """Update inspection characteristic"""
        characteristic = self.get_by_id(characteristic_id)
        if not characteristic:
            return None

        if dto.characteristic_name:
            characteristic.characteristic_name = dto.characteristic_name
        if dto.description is not None:
            characteristic.description = dto.description
        if dto.unit_of_measure is not None:
            characteristic.unit_of_measure = dto.unit_of_measure
        if dto.target_value is not None:
            characteristic.target_value = dto.target_value
        if dto.lower_spec_limit is not None:
            characteristic.lower_spec_limit = dto.lower_spec_limit
        if dto.upper_spec_limit is not None:
            characteristic.upper_spec_limit = dto.upper_spec_limit
        if dto.lower_control_limit is not None:
            characteristic.lower_control_limit = dto.lower_control_limit
        if dto.upper_control_limit is not None:
            characteristic.upper_control_limit = dto.upper_control_limit
        if dto.track_spc is not None:
            characteristic.track_spc = dto.track_spc
        if dto.control_chart_type is not None:
            characteristic.control_chart_type = dto.control_chart_type
        if dto.subgroup_size is not None:
            characteristic.subgroup_size = dto.subgroup_size
        if dto.allowed_values is not None:
            characteristic.allowed_values = dto.allowed_values
        if dto.tolerance_type is not None:
            characteristic.tolerance_type = dto.tolerance_type
        if dto.tolerance is not None:
            characteristic.tolerance = dto.tolerance
        if dto.sequence is not None:
            characteristic.sequence = dto.sequence
        if dto.is_active is not None:
            characteristic.is_active = dto.is_active

        self.db.commit()
        self.db.refresh(characteristic)
        return characteristic

    def update_control_limits(self, characteristic_id: int, ucl: float, lcl: float) -> Optional[InspectionCharacteristic]:
        """Update control limits for a characteristic"""
        characteristic = self.get_by_id(characteristic_id)
        if not characteristic:
            return None

        characteristic.upper_control_limit = ucl
        characteristic.lower_control_limit = lcl

        self.db.commit()
        self.db.refresh(characteristic)
        return characteristic

    def delete(self, characteristic_id: int) -> bool:
        """Delete inspection characteristic (soft delete)"""
        characteristic = self.get_by_id(characteristic_id)
        if not characteristic:
            return False

        characteristic.is_active = False
        self.db.commit()
        return True


class InspectionMeasurementRepository:
    """Repository for InspectionMeasurement operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, dto: InspectionMeasurementCreateDTO) -> InspectionMeasurement:
        """Create a new inspection measurement"""
        measurement = InspectionMeasurement(
            organization_id=dto.organization_id,
            characteristic_id=dto.characteristic_id,
            inspection_plan_id=dto.inspection_plan_id,
            work_order_id=dto.work_order_id,
            material_id=dto.material_id,
            lot_number=dto.lot_number,
            serial_number=dto.serial_number,
            measured_value=dto.measured_value,
            measured_text=dto.measured_text,
            sample_number=dto.sample_number,
            subgroup_number=dto.subgroup_number,
            measured_by=dto.measured_by,
            measurement_timestamp=dto.measurement_timestamp,
            inspection_equipment_id=dto.inspection_equipment_id,
            environmental_conditions=dto.environmental_conditions,
            notes=dto.notes,
        )
        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    def create_bulk(self, measurements: List[InspectionMeasurementCreateDTO]) -> List[InspectionMeasurement]:
        """Create multiple measurements at once"""
        measurement_objects = [
            InspectionMeasurement(
                organization_id=dto.organization_id,
                characteristic_id=dto.characteristic_id,
                inspection_plan_id=dto.inspection_plan_id,
                work_order_id=dto.work_order_id,
                material_id=dto.material_id,
                lot_number=dto.lot_number,
                serial_number=dto.serial_number,
                measured_value=dto.measured_value,
                measured_text=dto.measured_text,
                sample_number=dto.sample_number,
                subgroup_number=dto.subgroup_number,
                measured_by=dto.measured_by,
                measurement_timestamp=dto.measurement_timestamp,
                inspection_equipment_id=dto.inspection_equipment_id,
                environmental_conditions=dto.environmental_conditions,
                notes=dto.notes,
            )
            for dto in measurements
        ]

        self.db.bulk_save_objects(measurement_objects)
        self.db.commit()
        return measurement_objects

    def get_by_id(self, measurement_id: int) -> Optional[InspectionMeasurement]:
        """Get inspection measurement by ID"""
        return self.db.query(InspectionMeasurement).filter(
            InspectionMeasurement.id == measurement_id
        ).first()

    def list_by_characteristic(self, characteristic_id: int, skip: int = 0, limit: int = 100,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[InspectionMeasurement]:
        """List measurements for a characteristic"""
        query = self.db.query(InspectionMeasurement).filter(
            InspectionMeasurement.characteristic_id == characteristic_id
        )

        if start_date:
            query = query.filter(InspectionMeasurement.measurement_timestamp >= start_date)
        if end_date:
            query = query.filter(InspectionMeasurement.measurement_timestamp <= end_date)

        return query.order_by(desc(InspectionMeasurement.measurement_timestamp)).offset(skip).limit(limit).all()

    def list_by_work_order(self, work_order_id: int, skip: int = 0, limit: int = 100) -> List[InspectionMeasurement]:
        """List measurements for a work order"""
        return self.db.query(InspectionMeasurement).filter(
            InspectionMeasurement.work_order_id == work_order_id
        ).order_by(desc(InspectionMeasurement.measurement_timestamp)).offset(skip).limit(limit).all()

    def list_by_lot(self, lot_number: str, organization_id: int, skip: int = 0, limit: int = 100) -> List[InspectionMeasurement]:
        """List measurements for a lot"""
        return self.db.query(InspectionMeasurement).filter(
            and_(
                InspectionMeasurement.lot_number == lot_number,
                InspectionMeasurement.organization_id == organization_id
            )
        ).order_by(desc(InspectionMeasurement.measurement_timestamp)).offset(skip).limit(limit).all()

    def list_out_of_control(self, inspection_plan_id: int, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[InspectionMeasurement]:
        """List out-of-control measurements for a plan"""
        query = self.db.query(InspectionMeasurement).filter(
            and_(
                InspectionMeasurement.inspection_plan_id == inspection_plan_id,
                InspectionMeasurement.is_out_of_control == True
            )
        )

        if start_date:
            query = query.filter(InspectionMeasurement.measurement_timestamp >= start_date)
        if end_date:
            query = query.filter(InspectionMeasurement.measurement_timestamp <= end_date)

        return query.order_by(desc(InspectionMeasurement.measurement_timestamp)).all()

    def get_statistics(self, characteristic_id: int, start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> dict:
        """Get statistical summary for a characteristic"""
        query = self.db.query(
            func.count(InspectionMeasurement.id).label('count'),
            func.avg(InspectionMeasurement.measured_value).label('mean'),
            func.stddev(InspectionMeasurement.measured_value).label('std_dev'),
            func.min(InspectionMeasurement.measured_value).label('min_value'),
            func.max(InspectionMeasurement.measured_value).label('max_value'),
            func.sum(InspectionMeasurement.is_conforming.cast(Integer)).label('conforming_count'),
            func.sum(InspectionMeasurement.is_out_of_control.cast(Integer)).label('out_of_control_count'),
        ).filter(
            InspectionMeasurement.characteristic_id == characteristic_id
        )

        if start_date:
            query = query.filter(InspectionMeasurement.measurement_timestamp >= start_date)
        if end_date:
            query = query.filter(InspectionMeasurement.measurement_timestamp <= end_date)

        result = query.first()

        return {
            'count': result.count or 0,
            'mean': float(result.mean) if result.mean else None,
            'std_dev': float(result.std_dev) if result.std_dev else None,
            'min_value': float(result.min_value) if result.min_value else None,
            'max_value': float(result.max_value) if result.max_value else None,
            'conforming_count': result.conforming_count or 0,
            'out_of_control_count': result.out_of_control_count or 0,
        }
