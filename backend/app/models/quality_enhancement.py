"""
Quality Enhancement models - Inspection Plans, SPC, and Quality Measurements
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Date, Numeric, ForeignKey, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum
from datetime import date, datetime
from typing import Optional
import math


# Enums
class PlanType(str, Enum):
    """Inspection plan type enumeration"""
    INCOMING = "INCOMING"
    IN_PROCESS = "IN_PROCESS"
    FINAL = "FINAL"
    AUDIT = "AUDIT"


class AppliesTo(str, Enum):
    """Inspection scope enumeration"""
    MATERIAL = "MATERIAL"
    WORK_ORDER = "WORK_ORDER"
    PRODUCT = "PRODUCT"
    PROCESS = "PROCESS"


class FrequencyType(str, Enum):
    """Inspection frequency enumeration"""
    EVERY_UNIT = "EVERY_UNIT"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    PERIODIC = "PERIODIC"
    ON_DEMAND = "ON_DEMAND"


class CharacteristicType(str, Enum):
    """Characteristic type enumeration"""
    VARIABLE = "VARIABLE"  # Continuous numeric measurements
    ATTRIBUTE = "ATTRIBUTE"  # Discrete or categorical data


class DataType(str, Enum):
    """Data type enumeration"""
    NUMERIC = "NUMERIC"
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"


class ControlChartType(str, Enum):
    """Control chart type enumeration"""
    XBAR_R = "XBAR_R"  # X-bar and R chart for variables
    XBAR_S = "XBAR_S"  # X-bar and S chart for variables
    I_MR = "I_MR"  # Individual and Moving Range
    P_CHART = "P_CHART"  # Proportion chart for attributes
    NP_CHART = "NP_CHART"  # Number of defectives
    C_CHART = "C_CHART"  # Count of defects
    U_CHART = "U_CHART"  # Defects per unit


class InspectionPlan(Base):
    """
    Inspection Plan model.

    Defines inspection requirements for materials, products, or processes.
    Supports:
    - Multiple inspection types (incoming, in-process, final, audit)
    - Flexible frequency scheduling
    - SPC (Statistical Process Control) configuration
    - Approval workflows
    """
    __tablename__ = 'inspection_plans'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=True, index=True)

    # Plan identification
    plan_code = Column(String(100), nullable=False)
    plan_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    plan_type = Column(String(50), nullable=False)  # INCOMING, IN_PROCESS, FINAL, AUDIT

    # Scope
    applies_to = Column(String(50), nullable=False)  # MATERIAL, WORK_ORDER, PRODUCT, PROCESS
    material_id = Column(Integer, nullable=True, index=True)
    work_center_id = Column(Integer, nullable=True)

    # Frequency and scheduling
    frequency = Column(String(50), nullable=False)  # EVERY_UNIT, HOURLY, DAILY, WEEKLY, PERIODIC, ON_DEMAND
    frequency_value = Column(Integer, nullable=True)  # e.g., every 100 units, every 4 hours
    sample_size = Column(Integer, nullable=True)

    # SPC configuration
    spc_enabled = Column(Boolean, nullable=False, default=False)
    # Structure: {
    #   "method": "3_sigma|6_sigma|custom",
    #   "ucl_multiplier": 3.0,
    #   "lcl_multiplier": 3.0,
    #   "recalculate_frequency": "monthly"
    # }
    control_limits_config = Column(JSONB, nullable=True)

    # Approval and activation
    approved_by = Column(Integer, nullable=True)
    approved_date = Column(DateTime(timezone=True), nullable=True)
    effective_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    # Instructions
    instructions = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    revision = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=False)

    # Relationships
    inspection_points = relationship("InspectionPoint", back_populates="inspection_plan", cascade="all, delete-orphan")
    measurements = relationship("InspectionMeasurement", back_populates="inspection_plan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'plan_code', name='uq_inspection_plan_code'),
        Index('idx_inspection_plans_org', 'organization_id'),
        Index('idx_inspection_plans_plant', 'plant_id'),
        Index('idx_inspection_plans_type', 'plan_type'),
        Index('idx_inspection_plans_material', 'material_id'),
        CheckConstraint(
            "plan_type IN ('INCOMING', 'IN_PROCESS', 'FINAL', 'AUDIT')",
            name='chk_plan_type_valid'
        ),
        CheckConstraint(
            "applies_to IN ('MATERIAL', 'WORK_ORDER', 'PRODUCT', 'PROCESS')",
            name='chk_applies_to_valid'
        ),
        CheckConstraint(
            "frequency IN ('EVERY_UNIT', 'HOURLY', 'DAILY', 'WEEKLY', 'PERIODIC', 'ON_DEMAND')",
            name='chk_frequency_valid'
        ),
    )

    def __repr__(self):
        return f"<InspectionPlan(id={self.id}, code='{self.plan_code}', type='{self.plan_type}')>"

    def is_effective(self) -> bool:
        """Check if plan is currently effective"""
        if not self.is_active:
            return False

        today = date.today()

        if self.effective_date and today < self.effective_date:
            return False

        if self.expiry_date and today > self.expiry_date:
            return False

        return True

    def is_approved(self) -> bool:
        """Check if plan is approved"""
        return self.approved_by is not None and self.approved_date is not None

    def requires_inspection_now(self, units_produced: Optional[int] = None, hours_elapsed: Optional[int] = None) -> bool:
        """
        Determine if inspection is required based on frequency.

        Args:
            units_produced: Number of units produced since last inspection
            hours_elapsed: Hours elapsed since last inspection

        Returns:
            True if inspection is required, False otherwise
        """
        if self.frequency == FrequencyType.ON_DEMAND.value:
            return False

        if self.frequency == FrequencyType.EVERY_UNIT.value:
            return True

        if self.frequency == FrequencyType.HOURLY.value and hours_elapsed is not None:
            return hours_elapsed >= (self.frequency_value or 1)

        if self.frequency == FrequencyType.PERIODIC.value and units_produced is not None:
            return units_produced >= (self.frequency_value or 100)

        return False


class InspectionPoint(Base):
    """
    Inspection Point model.

    Defines individual checkpoints within an inspection plan.
    Each point can have multiple characteristics to measure.
    """
    __tablename__ = 'inspection_points'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    inspection_plan_id = Column(Integer, ForeignKey('inspection_plans.id', ondelete='CASCADE'), nullable=False, index=True)

    # Point identification
    point_code = Column(String(100), nullable=False)
    point_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration
    inspection_method = Column(String(100), nullable=True)  # VISUAL, DIMENSIONAL, FUNCTIONAL, etc.
    inspection_equipment = Column(String(200), nullable=True)
    sequence = Column(Integer, nullable=False, default=0)

    # Requirements
    is_mandatory = Column(Boolean, nullable=False, default=True)
    is_critical = Column(Boolean, nullable=False, default=False)

    # Instructions
    inspection_instructions = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    inspection_plan = relationship("InspectionPlan", back_populates="inspection_points")
    characteristics = relationship("InspectionCharacteristic", back_populates="inspection_point", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('inspection_plan_id', 'point_code', name='uq_inspection_point_code'),
        Index('idx_inspection_points_org', 'organization_id'),
        Index('idx_inspection_points_plan', 'inspection_plan_id'),
        Index('idx_inspection_points_sequence', 'inspection_plan_id', 'sequence'),
    )

    def __repr__(self):
        return f"<InspectionPoint(id={self.id}, code='{self.point_code}', name='{self.point_name}')>"


class InspectionCharacteristic(Base):
    """
    Inspection Characteristic model.

    Defines measurable characteristics with specification limits and SPC configuration.
    Supports both variable (numeric) and attribute (categorical) data.
    """
    __tablename__ = 'inspection_characteristics'

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    inspection_point_id = Column(Integer, ForeignKey('inspection_points.id', ondelete='CASCADE'), nullable=False, index=True)

    # Characteristic identification
    characteristic_code = Column(String(100), nullable=False)
    characteristic_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Measurement configuration
    characteristic_type = Column(String(50), nullable=False)  # VARIABLE, ATTRIBUTE
    data_type = Column(String(50), nullable=False)  # NUMERIC, BOOLEAN, TEXT
    unit_of_measure = Column(String(50), nullable=True)

    # Specification limits (for VARIABLE characteristics)
    target_value = Column(Numeric(precision=15, scale=6), nullable=True)
    lower_spec_limit = Column(Numeric(precision=15, scale=6), nullable=True)  # LSL
    upper_spec_limit = Column(Numeric(precision=15, scale=6), nullable=True)  # USL
    lower_control_limit = Column(Numeric(precision=15, scale=6), nullable=True)  # LCL (calculated)
    upper_control_limit = Column(Numeric(precision=15, scale=6), nullable=True)  # UCL (calculated)

    # SPC configuration
    track_spc = Column(Boolean, nullable=False, default=False)
    control_chart_type = Column(String(50), nullable=True)  # XBAR_R, XBAR_S, P_CHART, C_CHART, etc.
    subgroup_size = Column(Integer, nullable=True)

    # Attribute options (for ATTRIBUTE characteristics)
    allowed_values = Column(ARRAY(String), nullable=True)

    # Tolerances
    tolerance_type = Column(String(50), nullable=True)  # BILATERAL, UNILATERAL_UPPER, UNILATERAL_LOWER
    tolerance = Column(Numeric(precision=15, scale=6), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    sequence = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    inspection_point = relationship("InspectionPoint", back_populates="characteristics")
    measurements = relationship("InspectionMeasurement", back_populates="characteristic", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        UniqueConstraint('inspection_point_id', 'characteristic_code', name='uq_inspection_characteristic_code'),
        Index('idx_inspection_characteristics_org', 'organization_id'),
        Index('idx_inspection_characteristics_point', 'inspection_point_id'),
        Index('idx_inspection_characteristics_spc', 'track_spc'),
        CheckConstraint(
            "characteristic_type IN ('VARIABLE', 'ATTRIBUTE')",
            name='chk_characteristic_type_valid'
        ),
        CheckConstraint(
            "data_type IN ('NUMERIC', 'BOOLEAN', 'TEXT')",
            name='chk_data_type_valid'
        ),
    )

    def __repr__(self):
        return f"<InspectionCharacteristic(id={self.id}, code='{self.characteristic_code}', type='{self.characteristic_type}')>"

    def is_within_spec(self, value: float) -> bool:
        """
        Check if a measured value is within specification limits.

        Args:
            value: Measured value

        Returns:
            True if within spec, False otherwise
        """
        if self.characteristic_type != CharacteristicType.VARIABLE.value:
            return True  # Attribute characteristics handled differently

        if self.lower_spec_limit is not None and value < float(self.lower_spec_limit):
            return False

        if self.upper_spec_limit is not None and value > float(self.upper_spec_limit):
            return False

        return True

    def is_within_control_limits(self, value: float) -> bool:
        """
        Check if a measured value is within control limits.

        Args:
            value: Measured value

        Returns:
            True if within control limits, False otherwise
        """
        if not self.track_spc:
            return True

        if self.lower_control_limit is not None and value < float(self.lower_control_limit):
            return False

        if self.upper_control_limit is not None and value > float(self.upper_control_limit):
            return False

        return True

    def calculate_process_capability(self, mean: float, std_dev: float) -> dict:
        """
        Calculate process capability indices (Cp, Cpk).

        Args:
            mean: Process mean
            std_dev: Process standard deviation

        Returns:
            Dictionary with Cp, Cpk, Pp, Ppk values
        """
        if self.characteristic_type != CharacteristicType.VARIABLE.value:
            return {}

        if std_dev == 0:
            return {"error": "Standard deviation is zero"}

        result = {}

        # Cp (Process Capability)
        if self.upper_spec_limit is not None and self.lower_spec_limit is not None:
            usl = float(self.upper_spec_limit)
            lsl = float(self.lower_spec_limit)
            result["Cp"] = (usl - lsl) / (6 * std_dev)

            # Cpk (Process Capability Index)
            cpu = (usl - mean) / (3 * std_dev)
            cpl = (mean - lsl) / (3 * std_dev)
            result["Cpk"] = min(cpu, cpl)
            result["CPU"] = cpu
            result["CPL"] = cpl

        # Calculate with target value if available
        if self.target_value is not None:
            target = float(self.target_value)
            result["deviation_from_target"] = abs(mean - target)

        return result

    def get_spec_range(self) -> Optional[float]:
        """Get the specification range (USL - LSL)"""
        if self.upper_spec_limit is not None and self.lower_spec_limit is not None:
            return float(self.upper_spec_limit) - float(self.lower_spec_limit)
        return None


class InspectionMeasurement(Base):
    """
    Inspection Measurement model (TimescaleDB hypertable).

    Stores individual measurement records with SPC calculations.
    Optimized for time-series queries and analytics.
    """
    __tablename__ = 'inspection_measurements'

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    characteristic_id = Column(Integer, ForeignKey('inspection_characteristics.id', ondelete='CASCADE'), nullable=False, index=True)
    inspection_plan_id = Column(Integer, ForeignKey('inspection_plans.id', ondelete='CASCADE'), nullable=False, index=True)

    # Measurement context
    work_order_id = Column(Integer, nullable=True, index=True)
    material_id = Column(Integer, nullable=True)
    lot_number = Column(String(100), nullable=True, index=True)
    serial_number = Column(String(100), nullable=True)

    # Measurement details
    measured_value = Column(Numeric(precision=15, scale=6), nullable=True)
    measured_text = Column(String(500), nullable=True)  # For attribute data
    is_conforming = Column(Boolean, nullable=True)
    deviation = Column(Numeric(precision=15, scale=6), nullable=True)  # from target

    # Sample information
    sample_number = Column(Integer, nullable=True)
    subgroup_number = Column(Integer, nullable=True)

    # SPC calculations (cached for performance)
    range_value = Column(Numeric(precision=15, scale=6), nullable=True)  # For R charts
    moving_range = Column(Numeric(precision=15, scale=6), nullable=True)  # For mR charts
    is_out_of_control = Column(Boolean, nullable=False, default=False)
    control_violation_type = Column(String(100), nullable=True)  # WESTERN_ELECTRIC_RULE_1, etc.

    # Measurement metadata
    measured_by = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    measurement_timestamp = Column(DateTime(timezone=True), nullable=False)
    inspection_equipment_id = Column(String(100), nullable=True)
    # Structure: {
    #   "temperature": 23.5,
    #   "humidity": 45.2,
    #   "operator_notes": "..."
    # }
    environmental_conditions = Column(JSONB, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    characteristic = relationship("InspectionCharacteristic", back_populates="measurements")
    inspection_plan = relationship("InspectionPlan", back_populates="measurements")

    # Table constraints
    __table_args__ = (
        Index('idx_inspection_measurements_org', 'organization_id'),
        Index('idx_inspection_measurements_char', 'characteristic_id'),
        Index('idx_inspection_measurements_plan', 'inspection_plan_id'),
        Index('idx_inspection_measurements_wo', 'work_order_id'),
        Index('idx_inspection_measurements_time', 'measurement_timestamp'),
        Index('idx_inspection_measurements_lot', 'lot_number'),
    )

    def __repr__(self):
        return f"<InspectionMeasurement(id={self.id}, char_id={self.characteristic_id}, value={self.measured_value})>"

    def calculate_deviation(self, target: Optional[float]) -> Optional[float]:
        """
        Calculate deviation from target value.

        Args:
            target: Target value

        Returns:
            Deviation amount or None
        """
        if target is None or self.measured_value is None:
            return None

        return float(self.measured_value) - target

    def check_western_electric_rules(self, previous_measurements: list) -> Optional[str]:
        """
        Check Western Electric rules for control chart violations.

        Args:
            previous_measurements: List of previous measurements for trend analysis

        Returns:
            Violation type string or None
        """
        # Rule 1: One point beyond 3 sigma
        if self.is_out_of_control:
            return "RULE_1_BEYOND_3_SIGMA"

        # Additional rules would require previous measurements context
        # Rule 2: 2 of 3 consecutive points beyond 2 sigma
        # Rule 3: 4 of 5 consecutive points beyond 1 sigma
        # Rule 4: 8 consecutive points on same side of center line

        # Simplified implementation - would need full context
        return None

    def get_measurement_age_hours(self) -> float:
        """Get age of measurement in hours"""
        if not self.measurement_timestamp:
            return 0.0

        now = datetime.now(self.measurement_timestamp.tzinfo)
        delta = now - self.measurement_timestamp
        return delta.total_seconds() / 3600.0
