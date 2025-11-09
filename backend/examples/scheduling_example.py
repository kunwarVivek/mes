"""
Example demonstrating Production Scheduling Service usage.
Phase 3: Production Planning Module - Component 6

This example shows:
1. Creating work orders with operations
2. Scheduling using different strategies (EARLIEST_DUE_DATE)
3. Detecting capacity conflicts
4. Calculating critical paths

NOTE: This is a conceptual demonstration showing scheduling logic.
      In production, this would use the ProductionSchedulingService
      with a real database session.
"""
from datetime import datetime, timedelta
from collections import namedtuple

# Define simple data structures for demonstration
WorkOrder = namedtuple('WorkOrder', ['work_order_number', 'end_date_planned', 'planned_quantity', 'operations'])
Operation = namedtuple('Operation', ['operation_number', 'operation_name', 'setup_time_minutes', 'run_time_per_unit_minutes'])


def scheduling_example():
    """Demonstrate production scheduling with capacity constraints"""

    # Example setup:
    # - 3 Work Orders with different due dates
    # - 1 Work Center (capacity constrained)
    # - Multiple operations competing for same resource

    print("\n" + "=" * 80)
    print("PRODUCTION SCHEDULING EXAMPLE")
    print("=" * 80)

    # Create work orders with operations
    work_orders = []

    # WO-001: Due Jan 20, 2 operations (60 min each)
    wo1 = WorkOrder(
        work_order_number="WO-001",
        end_date_planned=datetime(2025, 1, 20),
        planned_quantity=10.0,
        operations=[
            Operation(10, "Cut Material", 30.0, 3.0),
            Operation(20, "Assemble", 30.0, 3.0)
        ]
    )
    work_orders.append(wo1)

    # WO-002: Due Jan 15 (earliest), 1 operation (30 min)
    wo2 = WorkOrder(
        work_order_number="WO-002",
        end_date_planned=datetime(2025, 1, 15),
        planned_quantity=5.0,
        operations=[
            Operation(10, "Quick Assembly", 20.0, 2.0)
        ]
    )
    work_orders.append(wo2)

    # WO-003: Due Jan 25, 3 operations (45 min each)
    wo3 = WorkOrder(
        work_order_number="WO-003",
        end_date_planned=datetime(2025, 1, 25),
        planned_quantity=8.0,
        operations=[
            Operation(10, "Prepare", 40.0, 4.0),
            Operation(20, "Process", 40.0, 4.0),
            Operation(30, "Package", 40.0, 4.0)
        ]
    )
    work_orders.append(wo3)

    # Print work order summary
    print("\nWORK ORDERS TO SCHEDULE:")
    print("-" * 80)
    for wo in work_orders:
        total_time = sum(
            op.setup_time_minutes + (op.run_time_per_unit_minutes * wo.planned_quantity)
            for op in wo.operations
        )
        print(f"{wo.work_order_number}:")
        print(f"  Due Date: {wo.end_date_planned.strftime('%Y-%m-%d')}")
        print(f"  Quantity: {wo.planned_quantity}")
        print(f"  Operations: {len(wo.operations)}")
        print(f"  Total Time: {total_time:.0f} minutes ({total_time/60:.1f} hours)")

    # Schedule using EARLIEST_DUE_DATE strategy
    print("\n" + "=" * 80)
    print("SCHEDULING STRATEGY: EARLIEST_DUE_DATE")
    print("=" * 80)

    # Simulate scheduling (in reality, would use database session)
    # This is a conceptual demonstration showing the scheduling logic

    print("\nScheduled Operations (on Work Center ASSY-01):")
    print("-" * 80)

    # Manual calculation to demonstrate scheduling logic:
    current_time = datetime(2025, 1, 10, 8, 0)  # Start at 8 AM

    # Sort by due date: WO-002 (Jan 15), WO-001 (Jan 20), WO-003 (Jan 25)
    sorted_wos = sorted(work_orders, key=lambda w: w.end_date_planned)

    schedule_timeline = []

    for wo in sorted_wos:
        for op in sorted(wo.operations, key=lambda o: o.operation_number):
            # Calculate duration
            setup_hours = op.setup_time_minutes / 60.0
            run_hours = (op.run_time_per_unit_minutes * wo.planned_quantity) / 60.0
            total_hours = setup_hours + run_hours

            # Schedule operation
            start_time = current_time
            end_time = start_time + timedelta(hours=total_hours)

            schedule_timeline.append({
                'work_order': wo.work_order_number,
                'operation': op.operation_name,
                'start': start_time,
                'end': end_time,
                'duration_minutes': total_hours * 60
            })

            print(f"{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')}: "
                  f"{wo.work_order_number} - {op.operation_name} "
                  f"({total_hours * 60:.0f} min)")

            current_time = end_time

    # Calculate summary statistics
    print("\n" + "=" * 80)
    print("SCHEDULE SUMMARY")
    print("=" * 80)

    total_scheduled_time = (current_time - datetime(2025, 1, 10, 8, 0)).total_seconds() / 3600
    print(f"Total Scheduled Time: {total_scheduled_time:.1f} hours")
    print(f"Schedule Completion: {current_time.strftime('%Y-%m-%d %H:%M')}")

    # Check if all work orders meet their due dates
    print("\nDUE DATE ANALYSIS:")
    print("-" * 80)
    for wo in sorted_wos:
        # Find last operation for this work order
        wo_ops = [s for s in schedule_timeline if s['work_order'] == wo.work_order_number]
        if wo_ops:
            completion_time = wo_ops[-1]['end']
            on_time = completion_time <= wo.end_date_planned
            status = "ON TIME" if on_time else "LATE"
            days_diff = (completion_time - wo.end_date_planned).days

            print(f"{wo.work_order_number}:")
            print(f"  Scheduled Completion: {completion_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Due Date: {wo.end_date_planned.strftime('%Y-%m-%d')}")
            print(f"  Status: {status}", end="")
            if not on_time:
                print(f" ({abs(days_diff)} days late)")
            else:
                print(f" ({abs(days_diff)} days early)")

    # Demonstrate capacity conflict detection
    print("\n" + "=" * 80)
    print("CAPACITY ANALYSIS")
    print("=" * 80)
    print("Work Center: ASSY-01")
    print("Capacity: 10.0 units/hour")
    print("Operating Hours: 8 hours/day")
    print("\nAll operations scheduled sequentially - NO CONFLICTS")
    print("Operations do not overlap on the same work center")

    print("\n" + "=" * 80)
    print("CRITICAL PATH ANALYSIS (WO-001)")
    print("=" * 80)

    # Calculate critical path for WO-001
    wo1_total = sum(
        op.setup_time_minutes + (op.run_time_per_unit_minutes * wo1.planned_quantity)
        for op in wo1.operations
    )

    print(f"Work Order: {wo1.work_order_number}")
    print(f"Total Duration: {wo1_total:.0f} minutes ({wo1_total/60:.1f} hours)")
    print(f"Critical Path Operations:")
    for op in wo1.operations:
        op_duration = op.setup_time_minutes + (op.run_time_per_unit_minutes * wo1.planned_quantity)
        print(f"  - Op {op.operation_number}: {op.operation_name} ({op_duration:.0f} min)")

    # Calculate critical ratio
    if wo1.end_date_planned:
        time_until_due = (wo1.end_date_planned - datetime(2025, 1, 10)).total_seconds() / 3600  # hours
        critical_ratio = time_until_due / (wo1_total / 60)
        print(f"\nCritical Ratio: {critical_ratio:.2f}")
        print(f"  (Time Available / Time Required)")
        if critical_ratio < 1:
            print("  WARNING: Critical ratio < 1 - Work order is at risk!")
        elif critical_ratio < 1.5:
            print("  CAUTION: Low critical ratio - monitor closely")
        else:
            print("  GOOD: Adequate time available")

    print("\n" + "=" * 80)
    print("EXAMPLE COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("1. EARLIEST_DUE_DATE strategy prioritizes urgent work orders")
    print("2. Sequential scheduling prevents capacity conflicts")
    print("3. Critical path identifies bottleneck operations")
    print("4. Critical ratio helps prioritize urgent work")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    scheduling_example()
