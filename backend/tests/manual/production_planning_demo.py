"""
Manual demonstration of Production Planning Service business logic.
Phase 3: Production Planning Module - Component 3

This script demonstrates:
1. Creating work orders from demand
2. Calculating material requirements (BOM explosion)
3. Generating operations from BOM routing
4. Checking capacity feasibility
"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.application.services.production_planning_service import ProductionPlanningService
from app.domain.services.capacity_calculator import CapacityCalculator
from app.domain.entities.production_plan import ProductionPlan, PlanType, PlanStatus
from app.models.work_order import WorkCenter, WorkCenterType, WorkOrder, OrderStatus, OrderType, OperationStatus
from app.models.bom import BOMHeader, BOMLine, BOMType
from app.models.material import Material, UnitOfMeasure, MaterialCategory, ProcurementType, MRPType, DimensionType


def setup_demo_data(session):
    """Setup demo data for production planning"""
    print("Setting up demo data...")

    # Create UOMs
    uom_ea = UnitOfMeasure(
        id=1, uom_code="EA", uom_name="Each",
        dimension=DimensionType.QUANTITY, is_base_unit=True, conversion_factor=1.0
    )
    uom_kg = UnitOfMeasure(
        id=2, uom_code="KG", uom_name="Kilogram",
        dimension=DimensionType.MASS, is_base_unit=True, conversion_factor=1.0
    )
    session.add_all([uom_ea, uom_kg])

    # Create category
    category = MaterialCategory(
        id=1, organization_id=1, category_code="PROD",
        category_name="Products", is_active=True
    )
    session.add(category)

    # Create materials
    finished_good = Material(
        id=1, organization_id=1, plant_id=1,
        material_number="FG001", material_name="Bike Frame Assembly",
        description="Complete bicycle frame", material_category_id=1,
        base_uom_id=1, procurement_type=ProcurementType.MANUFACTURE,
        mrp_type=MRPType.MRP, safety_stock=10.0, reorder_point=20.0,
        lot_size=1.0, lead_time_days=5, is_active=True
    )
    component_1 = Material(
        id=2, organization_id=1, plant_id=1,
        material_number="RM001", material_name="Steel Tubing",
        description="Frame tubes", material_category_id=1,
        base_uom_id=2, procurement_type=ProcurementType.PURCHASE,
        mrp_type=MRPType.MRP, safety_stock=50.0, reorder_point=100.0,
        lot_size=1.0, lead_time_days=3, is_active=True
    )
    component_2 = Material(
        id=3, organization_id=1, plant_id=1,
        material_number="RM002", material_name="Welds & Fasteners",
        description="Welding materials", material_category_id=1,
        base_uom_id=1, procurement_type=ProcurementType.PURCHASE,
        mrp_type=MRPType.MRP, safety_stock=30.0, reorder_point=60.0,
        lot_size=1.0, lead_time_days=2, is_active=True
    )
    session.add_all([finished_good, component_1, component_2])

    # Create work centers
    wc_welding = WorkCenter(
        id=1, organization_id=1, plant_id=1,
        work_center_code="WELD-01", work_center_name="Welding Station 1",
        work_center_type=WorkCenterType.ASSEMBLY,
        capacity_per_hour=10.0, cost_per_hour=50.0, is_active=True
    )
    wc_finishing = WorkCenter(
        id=2, organization_id=1, plant_id=1,
        work_center_code="FINISH-01", work_center_name="Finishing Station 1",
        work_center_type=WorkCenterType.ASSEMBLY,
        capacity_per_hour=15.0, cost_per_hour=40.0, is_active=True
    )
    session.add_all([wc_welding, wc_finishing])

    # Create BOM
    bom_header = BOMHeader(
        id=1, organization_id=1, plant_id=1,
        bom_number="BOM-FG001-V1", material_id=1, bom_version=1,
        bom_name="BOM for Bike Frame", bom_type=BOMType.PRODUCTION,
        base_quantity=1.0, unit_of_measure_id=1,
        effective_date_from=datetime(2025, 1, 1),
        effective_date_to=datetime(2026, 12, 31),
        is_active=True, created_by_user_id=1
    )
    session.add(bom_header)

    # BOM lines with routing
    bom_line_1 = BOMLine(
        id=1, bom_header_id=1, line_number=10,
        component_material_id=2, quantity=5.5,  # 5.5 KG steel per frame
        unit_of_measure_id=2, scrap_factor=10.0,  # 10% scrap
        operation_number=10, is_phantom=False, backflush=True
    )
    bom_line_2 = BOMLine(
        id=2, bom_header_id=1, line_number=20,
        component_material_id=3, quantity=12.0,  # 12 welds per frame
        unit_of_measure_id=1, scrap_factor=5.0,  # 5% scrap
        operation_number=20, is_phantom=False, backflush=False
    )
    session.add_all([bom_line_1, bom_line_2])

    session.commit()
    print("Demo data setup complete!\n")


def demo_production_planning(session):
    """Demonstrate production planning workflow"""
    print("=" * 70)
    print("PRODUCTION PLANNING DEMONSTRATION")
    print("=" * 70)

    service = ProductionPlanningService(session)

    # Example 1: Create work order from demand
    print("\n1. CREATE WORK ORDER FROM DEMAND")
    print("-" * 70)
    print("Scenario: Sales demands 50 Bike Frame Assemblies by Dec 31, 2025")

    work_order = service.create_work_order_from_demand(
        material_id=1,  # Bike Frame Assembly
        quantity=50.0,
        due_date=datetime(2025, 12, 31),
        organization_id=1,
        plant_id=1
    )

    print(f"Created Work Order: {work_order.work_order_number}")
    print(f"  Material: {work_order.material.material_name}")
    print(f"  Quantity: {work_order.planned_quantity} units")
    print(f"  Status: {work_order.order_status.value}")
    print(f"  Due Date: {work_order.end_date_planned.strftime('%Y-%m-%d')}")

    # Example 2: Calculate material requirements
    print("\n2. CALCULATE MATERIAL REQUIREMENTS")
    print("-" * 70)
    print("BOM Explosion for 50 bike frames:")

    requirements = service.calculate_material_requirements(work_order.id)

    for material_id, req in requirements.items():
        material = session.query(Material).get(material_id)
        uom = session.query(UnitOfMeasure).get(req['unit_of_measure_id'])
        print(f"  {material.material_name}:")
        print(f"    Required: {req['required_quantity']:.2f} {uom.uom_code}")
        print(f"    BOM Level: {req['bom_level']}")

    # Example 3: Generate operations
    print("\n3. GENERATE OPERATIONS FROM BOM ROUTING")
    print("-" * 70)

    operations = service.generate_operations_from_bom(work_order.id, 1)

    print(f"Generated {len(operations)} operations:")
    for op in operations:
        wc = session.query(WorkCenter).get(op.work_center_id)
        print(f"  Operation {op.operation_number}: {op.operation_name}")
        print(f"    Work Center: {wc.work_center_name}")
        print(f"    Setup Time: {op.setup_time_minutes} minutes")
        print(f"    Run Time: {op.run_time_per_unit_minutes} min/unit")

    # Example 4: Check capacity feasibility
    print("\n4. CHECK CAPACITY FEASIBILITY")
    print("-" * 70)

    feasibility = service.check_capacity_feasibility(work_order.id)

    print(f"Feasibility Analysis:")
    print(f"  Can complete on time: {'Yes' if feasibility['feasible'] else 'No'}")
    print(f"  Capacity utilization: {feasibility['capacity_utilization']:.1f}%")
    if feasibility['bottleneck_work_center']:
        print(f"  Bottleneck: {feasibility['bottleneck_work_center']}")
    print(f"  Earliest completion: {feasibility['earliest_completion_date'].strftime('%Y-%m-%d')}")

    # Example 5: Create production plan
    print("\n5. CREATE PRODUCTION PLAN")
    print("-" * 70)

    plan = ProductionPlan(
        organization_id=1,
        plant_id=1,
        plan_number="PLAN-2025-12",
        plan_name="December Production Plan",
        plan_type=PlanType.MONTHLY,
        plan_period_start=datetime(2025, 12, 1),
        plan_period_end=datetime(2025, 12, 31),
        status=PlanStatus.DRAFT,
        created_by_user_id=1
    )

    print(f"Created Production Plan: {plan.plan_number}")
    print(f"  Name: {plan.plan_name}")
    print(f"  Type: {plan.plan_type.value}")
    print(f"  Status: {plan.status.value}")
    print(f"  Period: {plan.plan_period_start.strftime('%Y-%m-%d')} to {plan.plan_period_end.strftime('%Y-%m-%d')}")

    plan.approve()
    print(f"  Status after approval: {plan.status.value}")

    plan.execute()
    print(f"  Status after execution: {plan.status.value}")

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)


def main():
    """Main demo entry point"""
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        setup_demo_data(session)
        demo_production_planning(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
