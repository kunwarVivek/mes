"""
MRP Calculation Demonstration
Shows before/after inventory levels and planned order generation.
Phase 3: Production Planning Module - Component 4
"""
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.application.services.mrp_service import MRPService
from app.models.material import Material, UnitOfMeasure, MaterialCategory, ProcurementType, MRPType, DimensionType
from app.models.inventory import Inventory, StorageLocation, LocationType
from app.models.work_order import WorkOrder, WorkOrderMaterial, OrderStatus, OrderType


def run_mrp_demo():
    """Demonstrate MRP calculation with before/after states"""

    # Setup database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("=" * 80)
    print("MRP CALCULATION DEMONSTRATION")
    print("=" * 80)

    # Setup test data
    print("\n1. SETUP: Creating master data...")

    # Create UOM
    uom_ea = UnitOfMeasure(
        id=1,
        uom_code="EA",
        uom_name="Each",
        dimension=DimensionType.QUANTITY,
        is_base_unit=True,
        conversion_factor=1.0
    )
    session.add(uom_ea)

    # Create Category
    category = MaterialCategory(
        id=1,
        organization_id=1,
        category_code="RM",
        category_name="Raw Materials",
        is_active=True
    )
    session.add(category)

    # Create Material A (Purchased, MRP-controlled)
    material_a = Material(
        id=1,
        organization_id=1,
        plant_id=1,
        material_number="MAT-A",
        material_name="Component A (Purchased)",
        material_category_id=1,
        base_uom_id=1,
        procurement_type=ProcurementType.PURCHASE,
        mrp_type=MRPType.MRP,
        lead_time_days=7,
        safety_stock=50.0,
        reorder_point=100.0,
        lot_size=100.0,  # Fixed lot size
        is_active=True
    )
    session.add(material_a)

    # Create Storage Location
    location = StorageLocation(
        id=1,
        organization_id=1,
        plant_id=1,
        location_code="WH-01",
        location_name="Main Warehouse",
        location_type=LocationType.WAREHOUSE,
        is_active=True
    )
    session.add(location)

    # Create Inventory (Current on-hand = 100 units)
    inventory = Inventory(
        id=1,
        organization_id=1,
        plant_id=1,
        material_id=1,
        storage_location_id=1,
        batch_number="BATCH-001",
        quantity_on_hand=100.0,
        quantity_reserved=0.0,
        unit_of_measure_id=1
    )
    session.add(inventory)
    session.commit()

    print(f"   Material: {material_a.material_number} - {material_a.material_name}")
    print(f"   Procurement Type: {material_a.procurement_type.value}")
    print(f"   Lead Time: {material_a.lead_time_days} days")
    print(f"   Lot Size: {material_a.lot_size} units")
    print(f"   Current Inventory: {inventory.quantity_on_hand} units")

    # Create Work Orders with demand
    print("\n2. DEMAND: Creating work orders...")

    start_date = datetime.utcnow()

    # Work Order 1: Due in 2 weeks (requires 50 units)
    wo1 = WorkOrder(
        id=1,
        organization_id=1,
        plant_id=1,
        work_order_number="WO-001",
        material_id=2,  # Finished good
        order_type=OrderType.PRODUCTION,
        order_status=OrderStatus.PLANNED,
        planned_quantity=100.0,
        actual_quantity=0.0,
        start_date_planned=start_date + timedelta(days=14),
        end_date_planned=start_date + timedelta(days=21),
        priority=5,
        created_by_user_id=1
    )
    session.add(wo1)

    wo1_mat = WorkOrderMaterial(
        id=1,
        work_order_id=1,
        material_id=1,
        planned_quantity=50.0,
        actual_quantity=0.0,
        unit_of_measure_id=1
    )
    session.add(wo1_mat)

    # Work Order 2: Due in 4 weeks (requires 80 units)
    wo2 = WorkOrder(
        id=2,
        organization_id=1,
        plant_id=1,
        work_order_number="WO-002",
        material_id=2,
        order_type=OrderType.PRODUCTION,
        order_status=OrderStatus.PLANNED,
        planned_quantity=200.0,
        actual_quantity=0.0,
        start_date_planned=start_date + timedelta(days=28),
        end_date_planned=start_date + timedelta(days=35),
        priority=5,
        created_by_user_id=1
    )
    session.add(wo2)

    wo2_mat = WorkOrderMaterial(
        id=2,
        work_order_id=2,
        material_id=1,
        planned_quantity=80.0,
        actual_quantity=0.0,
        unit_of_measure_id=1
    )
    session.add(wo2_mat)

    # Work Order 3: Due in 6 weeks (requires 120 units)
    wo3 = WorkOrder(
        id=3,
        organization_id=1,
        plant_id=1,
        work_order_number="WO-003",
        material_id=2,
        order_type=OrderType.PRODUCTION,
        order_status=OrderStatus.PLANNED,
        planned_quantity=300.0,
        actual_quantity=0.0,
        start_date_planned=start_date + timedelta(days=42),
        end_date_planned=start_date + timedelta(days=49),
        priority=5,
        created_by_user_id=1
    )
    session.add(wo3)

    wo3_mat = WorkOrderMaterial(
        id=3,
        work_order_id=3,
        material_id=1,
        planned_quantity=120.0,
        actual_quantity=0.0,
        unit_of_measure_id=1
    )
    session.add(wo3_mat)
    session.commit()

    print(f"   WO-001 (Week 2): Requires {wo1_mat.planned_quantity} units")
    print(f"   WO-002 (Week 4): Requires {wo2_mat.planned_quantity} units")
    print(f"   WO-003 (Week 6): Requires {wo3_mat.planned_quantity} units")
    print(f"   TOTAL DEMAND: {wo1_mat.planned_quantity + wo2_mat.planned_quantity + wo3_mat.planned_quantity} units")

    # Run MRP
    print("\n3. MRP CALCULATION:")
    print("   " + "-" * 76)

    mrp_service = MRPService(session)

    # Calculate net requirements
    net_req = mrp_service.calculate_net_requirements(
        material_id=1,
        start_date=start_date,
        end_date=start_date + timedelta(days=90)
    )

    print(f"   Current On-Hand:        {net_req['on_hand']:.0f} units")
    print(f"   Gross Requirements:     {net_req['gross_requirements']:.0f} units")
    print(f"   Scheduled Receipts:     {net_req['scheduled_receipts']:.0f} units")
    print(f"   Projected On-Hand:      {net_req['on_hand'] + net_req['scheduled_receipts'] - net_req['gross_requirements']:.0f} units")
    print(f"   Net Requirements:       {net_req['net_requirements']:.0f} units (SHORTAGE!)")

    # Time-phased calculation example
    print("\n4. TIME-PHASED INVENTORY PROJECTION:")
    print("   " + "-" * 76)
    print(f"   {'Period':<15} {'On-Hand':<15} {'Demand':<15} {'Projected':<15}")
    print("   " + "-" * 76)

    on_hand = 100.0
    print(f"   {'Now':<15} {on_hand:<15.0f} {0:<15.0f} {on_hand:<15.0f}")

    # Week 2
    on_hand = on_hand - 50.0
    print(f"   {'Week 2':<15} {on_hand:<15.0f} {50.0:<15.0f} {on_hand:<15.0f} {'✓ OK' if on_hand >= 0 else '✗ SHORTAGE'}")

    # Week 4
    on_hand = on_hand - 80.0
    print(f"   {'Week 4':<15} {on_hand:<15.0f} {80.0:<15.0f} {on_hand:<15.0f} {'✓ OK' if on_hand >= 0 else '✗ SHORTAGE'}")

    # Week 6
    on_hand = on_hand - 120.0
    print(f"   {'Week 6':<15} {on_hand:<15.0f} {120.0:<15.0f} {on_hand:<15.0f} {'✓ OK' if on_hand >= 0 else '✗ SHORTAGE'}")

    # Generate planned orders
    print("\n5. PLANNED ORDER GENERATION:")
    print("   " + "-" * 76)

    planned_orders = mrp_service.generate_planned_orders(
        material_id=1,
        net_requirements=net_req['net_requirements'],
        need_date=start_date + timedelta(days=30),
        lead_time_days=7
    )

    for i, order in enumerate(planned_orders, 1):
        print(f"   Order #{i}:")
        print(f"      Type:          {order.order_type}")
        print(f"      Quantity:      {order.planned_quantity:.0f} units (rounded to lot size)")
        print(f"      Need Date:     {order.need_date.strftime('%Y-%m-%d')}")
        print(f"      Order Date:    {order.order_date.strftime('%Y-%m-%d')} (lead time offset)")
        print(f"      Status:        {order.status}")

    # Run full MRP
    print("\n6. FULL MRP RUN:")
    print("   " + "-" * 76)

    mrp_run = mrp_service.run_mrp(
        organization_id=1,
        plant_id=1,
        planning_horizon_days=90
    )

    print(f"   Run Number:            {mrp_run.run_number}")
    print(f"   Status:                {mrp_run.status}")
    print(f"   Materials Processed:   {mrp_run.materials_processed}")
    print(f"   Planned Orders:        {mrp_run.planned_orders_created}")
    print(f"   Total Shortage:        {mrp_run.total_shortage_qty:.0f} units")

    print("\n" + "=" * 80)
    print("MRP CALCULATION COMPLETE")
    print("=" * 80)
    print("\nSUMMARY:")
    print(f"  - Started with {100.0:.0f} units on-hand")
    print(f"  - Total demand: {250.0:.0f} units")
    print(f"  - Shortage: {150.0:.0f} units")
    print(f"  - Generated {1} planned purchase order for {200.0:.0f} units")
    print(f"  - Order rounded to lot size ({100.0:.0f} unit lots)")
    print("\n")

    session.close()


if __name__ == "__main__":
    run_mrp_demo()
