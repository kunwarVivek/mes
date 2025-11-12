"""
SQLAlchemy models for Work Order Production Planning domain.
Phase 3: Production Planning Module
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, UniqueConstraint, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class OrderType(str, enum.Enum):
    """Enum for work order types"""
    PRODUCTION = "PRODUCTION"
    REWORK = "REWORK"
    ASSEMBLY = "ASSEMBLY"


class OrderStatus(str, enum.Enum):
    """Enum for work order status"""
    PLANNED = "PLANNED"
    RELEASED = "RELEASED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OperationStatus(str, enum.Enum):
    """Enum for work order operation status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class WorkCenterType(str, enum.Enum):
    """Enum for work center types"""
    MACHINE = "MACHINE"
    ASSEMBLY = "ASSEMBLY"
    PACKAGING = "PACKAGING"
    QUALITY_CHECK = "QUALITY_CHECK"


class SchedulingMode(str, enum.Enum):
    """Enum for operation scheduling modes"""
    SEQUENTIAL = "SEQUENTIAL"  # Operation starts only after predecessor completes
    OVERLAP = "OVERLAP"  # Operation can start during predecessor execution
    PARALLEL = "PARALLEL"  # Operations run simultaneously


class WorkCenter(Base):
    """
    Work Center entity - production resources and stations.

    Represents physical or logical work centers where operations are performed.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    """
    __tablename__ = "work_center"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    work_center_code = Column(String(20), nullable=False, index=True)
    work_center_name = Column(String(100), nullable=False)
    work_center_type = Column(Enum(WorkCenterType), nullable=False)
    capacity_per_hour = Column(Float, nullable=False)
    cost_per_hour = Column(Float, nullable=False, default=0.0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    operations = relationship("WorkOrderOperation", back_populates="work_center")

    # Unique constraint: work_center_code per organization and plant
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'work_center_code',
                         name='uq_work_center_code_per_plant'),
        Index('idx_work_center_org_plant', 'organization_id', 'plant_id'),
        CheckConstraint('capacity_per_hour > 0', name='check_capacity_positive'),
        CheckConstraint('cost_per_hour >= 0', name='check_cost_non_negative'),
    )

    def __repr__(self):
        return f"<WorkCenter(code='{self.work_center_code}', name='{self.work_center_name}', type='{self.work_center_type}')>"


class ReworkMode(str, enum.Enum):
    """Enum for rework operation modes"""
    CONSUME_ADDITIONAL_MATERIALS = "CONSUME_ADDITIONAL_MATERIALS"
    REPROCESS_EXISTING_WIP = "REPROCESS_EXISTING_WIP"
    HYBRID = "HYBRID"


class WorkOrder(Base):
    """
    Work Order entity - production orders for manufacturing.

    Represents a production order to manufacture a specific quantity of a material.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    Links to Material entity for the finished good being produced.
    Extended to support rework operations.
    """
    __tablename__ = "work_order"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    work_order_number = Column(String(50), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    order_type = Column(Enum(OrderType), nullable=False)
    order_status = Column(Enum(OrderStatus), nullable=False, index=True)
    planned_quantity = Column(Float, nullable=False)
    actual_quantity = Column(Float, nullable=False, default=0.0)
    start_date_planned = Column(DateTime(timezone=True), nullable=True)
    start_date_actual = Column(DateTime(timezone=True), nullable=True)
    end_date_planned = Column(DateTime(timezone=True), nullable=True)
    end_date_actual = Column(DateTime(timezone=True), nullable=True)
    priority = Column(Integer, nullable=False, default=5)
    created_by_user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Rework-specific fields
    is_rework_order = Column(Boolean, default=False, nullable=False)
    parent_work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=True, index=True)
    rework_reason_code = Column(String(50), nullable=True)
    rework_mode = Column(Enum(ReworkMode), nullable=True)

    # Costing fields (FRD_WORK_ORDERS.md lines 43-77)
    standard_cost = Column(Float, nullable=True, default=0.0)
    actual_material_cost = Column(Float, nullable=False, default=0.0)
    actual_labor_cost = Column(Float, nullable=False, default=0.0)
    actual_overhead_cost = Column(Float, nullable=False, default=0.0)
    total_actual_cost = Column(Float, nullable=False, default=0.0)

    # Relationships
    material = relationship("Material", backref="work_orders")
    operations = relationship("WorkOrderOperation", back_populates="work_order", cascade="all, delete-orphan")
    materials = relationship("WorkOrderMaterial", back_populates="work_order", cascade="all, delete-orphan")
    parent_work_order = relationship("WorkOrder", remote_side=[id], backref="rework_orders")
    dependencies = relationship("WorkOrderDependency", foreign_keys="WorkOrderDependency.work_order_id", back_populates="work_order", cascade="all, delete-orphan")
    dependent_on = relationship("WorkOrderDependency", foreign_keys="WorkOrderDependency.depends_on_work_order_id", back_populates="depends_on_work_order", cascade="all, delete-orphan")

    # Unique constraint: work_order_number per organization and plant
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id', 'work_order_number',
                         name='uq_work_order_number_per_plant'),
        Index('idx_work_order_org_plant', 'organization_id', 'plant_id'),
        Index('idx_work_order_status', 'order_status'),
        Index('idx_work_order_material', 'material_id'),
        CheckConstraint('planned_quantity > 0', name='check_planned_quantity_positive'),
        CheckConstraint('actual_quantity >= 0', name='check_actual_quantity_non_negative'),
        CheckConstraint('actual_quantity <= planned_quantity', name='check_actual_not_exceed_planned'),
        CheckConstraint('priority >= 1 AND priority <= 10', name='check_priority_range'),
    )

    def __repr__(self):
        return f"<WorkOrder(number='{self.work_order_number}', status='{self.order_status}', org={self.organization_id})>"


class WorkOrderOperation(Base):
    """
    Work Order Operation entity - sequential operations within a work order.

    Represents individual operations that must be performed to complete a work order.
    Operations are executed in sequence order (operation_number).
    Links to WorkCenter for resource allocation.
    """
    __tablename__ = "work_order_operation"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False, index=True)
    operation_number = Column(Integer, nullable=False)
    operation_name = Column(String(100), nullable=False)
    work_center_id = Column(Integer, ForeignKey('work_center.id', ondelete='CASCADE'), nullable=False)
    setup_time_minutes = Column(Float, nullable=False, default=0.0)
    run_time_per_unit_minutes = Column(Float, nullable=False, default=0.0)
    status = Column(Enum(OperationStatus), nullable=False, default=OperationStatus.PENDING)
    actual_setup_time = Column(Float, nullable=True)
    actual_run_time = Column(Float, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # Operation scheduling fields
    scheduling_mode = Column(Enum(SchedulingMode), nullable=False, default=SchedulingMode.SEQUENTIAL)
    overlap_percentage = Column(Float, nullable=False, default=0.0)
    predecessor_operation_id = Column(Integer, ForeignKey('work_order_operation.id', ondelete='SET NULL'), nullable=True)
    can_start_at_percentage = Column(Float, nullable=False, default=100.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    work_order = relationship("WorkOrder", back_populates="operations")
    work_center = relationship("WorkCenter", back_populates="operations")

    # Unique constraint: operation_number per work_order
    __table_args__ = (
        UniqueConstraint('work_order_id', 'operation_number',
                         name='uq_operation_number_per_work_order'),
        Index('idx_work_order_operation_org_plant', 'organization_id', 'plant_id'),
        Index('idx_operation_work_order', 'work_order_id'),
        CheckConstraint('operation_number > 0', name='check_operation_number_positive'),
        CheckConstraint('setup_time_minutes >= 0', name='check_setup_time_non_negative'),
        CheckConstraint('run_time_per_unit_minutes >= 0', name='check_run_time_non_negative'),
        CheckConstraint('overlap_percentage >= 0 AND overlap_percentage <= 100', name='check_overlap_percentage_range'),
        CheckConstraint('can_start_at_percentage >= 0 AND can_start_at_percentage <= 100', name='check_can_start_percentage_range'),
    )

    def __repr__(self):
        return f"<WorkOrderOperation(wo_id={self.work_order_id}, op_num={self.operation_number}, name='{self.operation_name}')>"


class WorkOrderMaterial(Base):
    """
    Work Order Material entity - material consumption tracking for production.

    Represents materials consumed during production (linked to BOM).
    Supports backflush (auto-consumption) and manual consumption tracking.
    Links to Material entity for the input material and UnitOfMeasure for quantity.
    """
    __tablename__ = "work_order_material"

    id = Column(Integer, primary_key=True)
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey('material.id', ondelete='CASCADE'), nullable=False, index=True)
    planned_quantity = Column(Float, nullable=False)
    actual_quantity = Column(Float, nullable=False, default=0.0)
    unit_of_measure_id = Column(Integer, ForeignKey('unit_of_measure.id', ondelete='CASCADE'), nullable=False)
    backflush = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    work_order = relationship("WorkOrder", back_populates="materials")
    material = relationship("Material")
    unit_of_measure = relationship("UnitOfMeasure")

    # Constraints
    __table_args__ = (
        Index('idx_work_order_material_wo', 'work_order_id'),
        Index('idx_work_order_material_mat', 'material_id'),
        CheckConstraint('planned_quantity > 0', name='check_wom_planned_quantity_positive'),
        CheckConstraint('actual_quantity >= 0', name='check_wom_actual_quantity_non_negative'),
    )

    def __repr__(self):
        return f"<WorkOrderMaterial(wo_id={self.work_order_id}, mat_id={self.material_id}, planned={self.planned_quantity})>"


class DependencyType(str, enum.Enum):
    """Enum for work order dependency types (FRD_WORK_ORDERS.md)"""
    FINISH_TO_START = "FINISH_TO_START"  # Most common: predecessor must finish before successor starts
    START_TO_START = "START_TO_START"    # Successor can start when predecessor starts
    FINISH_TO_FINISH = "FINISH_TO_FINISH"  # Both must finish together


class WorkOrderDependency(Base):
    """
    Work Order Dependency entity - defines dependencies between work orders.

    Implements Finish-to-Start, Start-to-Start, and Finish-to-Finish dependency logic.
    Prevents work orders from starting until dependencies are satisfied.
    Per FRD_WORK_ORDERS.md lines 11-35.
    """
    __tablename__ = "work_order_dependency"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False, index=True)
    depends_on_work_order_id = Column(Integer, ForeignKey('work_order.id', ondelete='CASCADE'), nullable=False, index=True)
    dependency_type = Column(Enum(DependencyType), nullable=False, default=DependencyType.FINISH_TO_START)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    work_order = relationship("WorkOrder", foreign_keys=[work_order_id], back_populates="dependencies")
    depends_on_work_order = relationship("WorkOrder", foreign_keys=[depends_on_work_order_id], back_populates="dependent_on")

    # Constraints
    __table_args__ = (
        UniqueConstraint('work_order_id', 'depends_on_work_order_id',
                         name='uq_work_order_dependency'),
        Index('idx_work_order_dependency_org_plant', 'organization_id', 'plant_id'),
        Index('idx_work_order_dependency_wo', 'work_order_id'),
        Index('idx_work_order_dependency_depends_on', 'depends_on_work_order_id'),
        CheckConstraint('work_order_id != depends_on_work_order_id', name='check_no_self_dependency'),
    )

    def __repr__(self):
        return f"<WorkOrderDependency(wo={self.work_order_id}, depends_on={self.depends_on_work_order_id}, type='{self.dependency_type}')>"


class ReworkConfig(Base):
    """
    Rework Configuration entity - organization/plant-level rework settings.

    Defines default rework behavior and constraints per organization and plant.
    Supports multi-tenant isolation via organization_id and plant_id (RLS).
    """
    __tablename__ = "rework_config"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, nullable=False, index=True)
    plant_id = Column(Integer, nullable=False, index=True)
    default_rework_mode = Column(Enum(ReworkMode), nullable=False, default=ReworkMode.CONSUME_ADDITIONAL_MATERIALS)
    require_reason_code = Column(Boolean, default=True, nullable=False)
    allow_multiple_rework_cycles = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Unique constraint: one config per organization and plant
    __table_args__ = (
        UniqueConstraint('organization_id', 'plant_id',
                         name='uq_rework_config_per_plant'),
        Index('idx_rework_config_org_plant', 'organization_id', 'plant_id'),
    )

    def __repr__(self):
        return f"<ReworkConfig(org={self.organization_id}, plant={self.plant_id}, mode='{self.default_rework_mode}')>"
