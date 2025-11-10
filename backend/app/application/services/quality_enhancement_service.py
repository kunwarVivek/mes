"""
Quality Enhancement Service - Business logic for inspection plans, SPC, and FPY
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Integer, and_, func
from datetime import datetime, timezone
from decimal import Decimal
import math
import statistics

from app.models.quality_enhancement import (
    InspectionPlan,
    InspectionPoint,
    InspectionCharacteristic,
    InspectionMeasurement
)
from app.infrastructure.repositories.quality_enhancement_repository import (
    InspectionPlanRepository,
    InspectionPointRepository,
    InspectionCharacteristicRepository,
    InspectionMeasurementRepository,
)
from app.application.dtos.quality_enhancement_dto import (
    InspectionPlanCreateDTO,
    InspectionPlanUpdateDTO,
    InspectionPlanApprovalDTO,
    InspectionPointCreateDTO,
    InspectionPointUpdateDTO,
    InspectionCharacteristicCreateDTO,
    InspectionCharacteristicUpdateDTO,
    InspectionMeasurementCreateDTO,
    InspectionMeasurementBulkCreateDTO,
    SPCAnalysisRequest,
    SPCAnalysisResponse,
    ControlChartDataRequest,
    ControlChartDataResponse,
    ControlChartDataPoint,
    FPYCalculationRequest,
    FPYResponse,
)


class InspectionPlanService:
    """Service for Inspection Plan operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = InspectionPlanRepository(db)

    def create_plan(self, dto: InspectionPlanCreateDTO) -> InspectionPlan:
        """Create a new inspection plan"""
        # Check for duplicate plan code
        existing = self.repo.get_by_code(dto.organization_id, dto.plan_code)
        if existing:
            raise ValueError(f"Inspection plan with code '{dto.plan_code}' already exists")

        return self.repo.create(dto)

    def get_plan(self, plan_id: int) -> Optional[InspectionPlan]:
        """Get inspection plan by ID"""
        return self.repo.get_by_id(plan_id)

    def list_plans(self, organization_id: int, skip: int = 0, limit: int = 100,
                   plan_type: Optional[str] = None, plant_id: Optional[int] = None,
                   active_only: bool = True) -> List[InspectionPlan]:
        """List inspection plans"""
        return self.repo.list_by_organization(organization_id, skip, limit, plan_type, plant_id, active_only)

    def list_by_material(self, material_id: int, skip: int = 0, limit: int = 100) -> List[InspectionPlan]:
        """List inspection plans for a material"""
        return self.repo.list_by_material(material_id, skip, limit)

    def list_effective_plans(self, organization_id: int, plan_type: Optional[str] = None) -> List[InspectionPlan]:
        """List currently effective inspection plans"""
        return self.repo.list_effective_plans(organization_id, plan_type)

    def update_plan(self, plan_id: int, dto: InspectionPlanUpdateDTO) -> Optional[InspectionPlan]:
        """Update inspection plan"""
        return self.repo.update(plan_id, dto)

    def approve_plan(self, plan_id: int, dto: InspectionPlanApprovalDTO) -> Optional[InspectionPlan]:
        """Approve an inspection plan"""
        plan = self.repo.approve(plan_id, dto.approved_by)
        # TODO: Add approval comments/history if needed
        return plan

    def delete_plan(self, plan_id: int) -> bool:
        """Delete inspection plan (soft delete)"""
        return self.repo.delete(plan_id)


class InspectionPointService:
    """Service for Inspection Point operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = InspectionPointRepository(db)

    def create_point(self, dto: InspectionPointCreateDTO) -> InspectionPoint:
        """Create a new inspection point"""
        return self.repo.create(dto)

    def get_point(self, point_id: int) -> Optional[InspectionPoint]:
        """Get inspection point by ID"""
        return self.repo.get_by_id(point_id)

    def list_by_plan(self, inspection_plan_id: int, skip: int = 0, limit: int = 100,
                     active_only: bool = True) -> List[InspectionPoint]:
        """List inspection points for a plan"""
        return self.repo.list_by_plan(inspection_plan_id, skip, limit, active_only)

    def list_critical_points(self, inspection_plan_id: int) -> List[InspectionPoint]:
        """List critical inspection points"""
        return self.repo.list_critical_points(inspection_plan_id)

    def update_point(self, point_id: int, dto: InspectionPointUpdateDTO) -> Optional[InspectionPoint]:
        """Update inspection point"""
        return self.repo.update(point_id, dto)

    def delete_point(self, point_id: int) -> bool:
        """Delete inspection point (soft delete)"""
        return self.repo.delete(point_id)


class InspectionCharacteristicService:
    """Service for Inspection Characteristic operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = InspectionCharacteristicRepository(db)

    def create_characteristic(self, dto: InspectionCharacteristicCreateDTO) -> InspectionCharacteristic:
        """Create a new inspection characteristic"""
        return self.repo.create(dto)

    def get_characteristic(self, characteristic_id: int) -> Optional[InspectionCharacteristic]:
        """Get inspection characteristic by ID"""
        return self.repo.get_by_id(characteristic_id)

    def list_by_point(self, inspection_point_id: int, skip: int = 0, limit: int = 100,
                      active_only: bool = True) -> List[InspectionCharacteristic]:
        """List inspection characteristics for a point"""
        return self.repo.list_by_point(inspection_point_id, skip, limit, active_only)

    def list_spc_characteristics(self, inspection_plan_id: int) -> List[InspectionCharacteristic]:
        """List SPC-tracked characteristics"""
        return self.repo.list_spc_characteristics(inspection_plan_id)

    def update_characteristic(self, characteristic_id: int,
                             dto: InspectionCharacteristicUpdateDTO) -> Optional[InspectionCharacteristic]:
        """Update inspection characteristic"""
        return self.repo.update(characteristic_id, dto)

    def recalculate_control_limits(self, characteristic_id: int) -> Optional[InspectionCharacteristic]:
        """
        Recalculate control limits based on recent measurements.
        Uses 3-sigma method by default.
        """
        characteristic = self.repo.get_by_id(characteristic_id)
        if not characteristic or not characteristic.track_spc:
            return None

        # Get recent measurements for calculation
        measurement_repo = InspectionMeasurementRepository(self.db)
        stats = measurement_repo.get_statistics(characteristic_id)

        if stats['count'] < 30:  # Minimum sample size for reliable limits
            return characteristic

        mean = stats['mean']
        std_dev = stats['std_dev']

        if mean is None or std_dev is None:
            return characteristic

        # Calculate 3-sigma control limits
        ucl = mean + (3 * std_dev)
        lcl = mean - (3 * std_dev)

        # Update the characteristic
        return self.repo.update_control_limits(characteristic_id, ucl, lcl)

    def delete_characteristic(self, characteristic_id: int) -> bool:
        """Delete inspection characteristic (soft delete)"""
        return self.repo.delete(characteristic_id)


class InspectionMeasurementService:
    """Service for Inspection Measurement operations"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = InspectionMeasurementRepository(db)
        self.characteristic_repo = InspectionCharacteristicRepository(db)

    def record_measurement(self, dto: InspectionMeasurementCreateDTO) -> InspectionMeasurement:
        """
        Record a new inspection measurement.
        Automatically calculates conformance and control status.
        """
        # Get characteristic to check limits
        characteristic = self.characteristic_repo.get_by_id(dto.characteristic_id)
        if not characteristic:
            raise ValueError(f"Characteristic with ID {dto.characteristic_id} not found")

        # Create the measurement
        measurement = self.repo.create(dto)

        # Calculate and update conformance
        if characteristic.characteristic_type == 'VARIABLE' and measurement.measured_value is not None:
            measured_val = float(measurement.measured_value)

            # Check conformance to spec limits
            measurement.is_conforming = characteristic.is_within_spec(measured_val)

            # Calculate deviation from target
            if characteristic.target_value:
                measurement.deviation = measurement.calculate_deviation(float(characteristic.target_value))

            # Check control limits
            if characteristic.track_spc:
                measurement.is_out_of_control = not characteristic.is_within_control_limits(measured_val)

        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    def record_bulk_measurements(self, dto: InspectionMeasurementBulkCreateDTO) -> List[InspectionMeasurement]:
        """Record multiple measurements at once"""
        measurements = []
        for measurement_dto in dto.measurements:
            measurement = self.record_measurement(measurement_dto)
            measurements.append(measurement)
        return measurements

    def get_measurement(self, measurement_id: int) -> Optional[InspectionMeasurement]:
        """Get measurement by ID"""
        return self.repo.get_by_id(measurement_id)

    def list_by_characteristic(self, characteristic_id: int, skip: int = 0, limit: int = 100,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[InspectionMeasurement]:
        """List measurements for a characteristic"""
        return self.repo.list_by_characteristic(characteristic_id, skip, limit, start_date, end_date)

    def list_by_work_order(self, work_order_id: int, skip: int = 0, limit: int = 100) -> List[InspectionMeasurement]:
        """List measurements for a work order"""
        return self.repo.list_by_work_order(work_order_id, skip, limit)

    def list_by_lot(self, lot_number: str, organization_id: int, skip: int = 0, limit: int = 100) -> List[InspectionMeasurement]:
        """List measurements for a lot"""
        return self.repo.list_by_lot(lot_number, organization_id, skip, limit)

    def list_out_of_control(self, inspection_plan_id: int, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[InspectionMeasurement]:
        """List out-of-control measurements"""
        return self.repo.list_out_of_control(inspection_plan_id, start_date, end_date)


class SPCAnalysisService:
    """Service for Statistical Process Control (SPC) analysis"""

    def __init__(self, db: Session):
        self.db = db
        self.characteristic_repo = InspectionCharacteristicRepository(db)
        self.measurement_repo = InspectionMeasurementRepository(db)

    def analyze_characteristic(self, request: SPCAnalysisRequest) -> SPCAnalysisResponse:
        """
        Perform SPC analysis on a characteristic.
        Calculates Cp, Cpk, and other process capability indices.
        """
        characteristic = self.characteristic_repo.get_by_id(request.characteristic_id)
        if not characteristic:
            raise ValueError(f"Characteristic with ID {request.characteristic_id} not found")

        # Get statistics
        stats = self.measurement_repo.get_statistics(
            request.characteristic_id,
            request.start_date,
            request.end_date
        )

        if stats['count'] == 0:
            raise ValueError("No measurements found for analysis")

        # Get measurements for detailed analysis
        measurements = self.measurement_repo.list_by_characteristic(
            request.characteristic_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=10000
        )

        # Calculate process capability
        if stats['mean'] is not None and stats['std_dev'] is not None and stats['std_dev'] > 0:
            capability = characteristic.calculate_process_capability(
                stats['mean'],
                stats['std_dev']
            )
        else:
            capability = {}

        # Determine capability status
        cpk = capability.get('Cpk')
        if cpk is None:
            capability_status = "UNKNOWN"
        elif cpk >= 1.33:
            capability_status = "CAPABLE"
        elif cpk >= 1.0:
            capability_status = "MARGINAL"
        else:
            capability_status = "INCAPABLE"

        # Calculate range
        range_val = None
        if stats['max_value'] is not None and stats['min_value'] is not None:
            range_val = stats['max_value'] - stats['min_value']

        # Count non-conforming
        non_conforming_count = stats['count'] - stats['conforming_count']

        return SPCAnalysisResponse(
            characteristic_id=characteristic.id,
            characteristic_name=characteristic.characteristic_name,
            measurement_count=stats['count'],
            mean=Decimal(str(stats['mean'])) if stats['mean'] else None,
            std_dev=Decimal(str(stats['std_dev'])) if stats['std_dev'] else None,
            min_value=Decimal(str(stats['min_value'])) if stats['min_value'] else None,
            max_value=Decimal(str(stats['max_value'])) if stats['max_value'] else None,
            range=Decimal(str(range_val)) if range_val else None,
            ucl=characteristic.upper_control_limit,
            lcl=characteristic.lower_control_limit,
            usl=characteristic.upper_spec_limit,
            lsl=characteristic.lower_spec_limit,
            target=characteristic.target_value,
            cp=Decimal(str(capability.get('Cp'))) if capability.get('Cp') else None,
            cpk=Decimal(str(capability.get('Cpk'))) if capability.get('Cpk') else None,
            out_of_control_count=stats['out_of_control_count'],
            conforming_count=stats['conforming_count'],
            non_conforming_count=non_conforming_count,
            capability_status=capability_status,
        )

    def get_control_chart_data(self, request: ControlChartDataRequest) -> ControlChartDataResponse:
        """
        Get control chart data for visualization.
        Returns data points with control limits.
        """
        characteristic = self.characteristic_repo.get_by_id(request.characteristic_id)
        if not characteristic:
            raise ValueError(f"Characteristic with ID {request.characteristic_id} not found")

        # Get measurements
        measurements = self.measurement_repo.list_by_characteristic(
            request.characteristic_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit
        )

        if not measurements:
            raise ValueError("No measurements found")

        # Calculate center line (mean)
        values = [float(m.measured_value) for m in measurements if m.measured_value is not None]
        if not values:
            raise ValueError("No valid measurements found")

        center_line = Decimal(str(statistics.mean(values)))

        # Build data points
        data_points = []
        for measurement in reversed(measurements):  # Chronological order
            if measurement.measured_value is None:
                continue

            data_points.append(ControlChartDataPoint(
                timestamp=measurement.measurement_timestamp,
                value=measurement.measured_value,
                ucl=characteristic.upper_control_limit,
                lcl=characteristic.lower_control_limit,
                center_line=center_line,
                is_out_of_control=measurement.is_out_of_control,
                violation_type=measurement.control_violation_type,
            ))

        return ControlChartDataResponse(
            characteristic_id=characteristic.id,
            characteristic_name=characteristic.characteristic_name,
            chart_type=request.chart_type,
            data_points=data_points,
            ucl=characteristic.upper_control_limit,
            lcl=characteristic.lower_control_limit,
            center_line=center_line,
            usl=characteristic.upper_spec_limit,
            lsl=characteristic.lower_spec_limit,
        )


class FPYCalculationService:
    """Service for First Pass Yield (FPY) calculations"""

    def __init__(self, db: Session):
        self.db = db
        self.measurement_repo = InspectionMeasurementRepository(db)

    def calculate_fpy(self, request: FPYCalculationRequest) -> FPYResponse:
        """
        Calculate First Pass Yield for a given period and filters.
        FPY = (Total Passed / Total Inspected) * 100
        """
        # Build query filters
        filters = [
            InspectionMeasurement.measurement_timestamp >= request.start_date,
            InspectionMeasurement.measurement_timestamp <= request.end_date,
        ]

        if request.plant_id:
            # Would need to join with inspection_plans to filter by plant
            pass  # TODO: Implement plant filter

        if request.material_id:
            filters.append(InspectionMeasurement.material_id == request.material_id)

        if request.work_order_id:
            filters.append(InspectionMeasurement.work_order_id == request.work_order_id)

        # Query measurements
        query = self.db.query(
            func.count(InspectionMeasurement.id).label('total_inspected'),
            func.sum(InspectionMeasurement.is_conforming.cast(Integer)).label('total_passed'),
        ).filter(and_(*filters))

        result = query.first()

        total_inspected = result.total_inspected or 0
        total_passed = result.total_passed or 0
        total_failed = total_inspected - total_passed

        if total_inspected == 0:
            fpy_percentage = Decimal('0')
            defect_rate = Decimal('0')
        else:
            fpy_percentage = Decimal(str((total_passed / total_inspected) * 100))
            defect_rate = Decimal(str((total_failed / total_inspected) * 100))

        return FPYResponse(
            total_inspected=total_inspected,
            total_passed=total_passed,
            total_failed=total_failed,
            fpy_percentage=fpy_percentage,
            defect_rate=defect_rate,
            period_start=request.start_date,
            period_end=request.end_date,
            breakdown_by_plan=None,  # TODO: Implement breakdowns
            breakdown_by_material=None,
        )
