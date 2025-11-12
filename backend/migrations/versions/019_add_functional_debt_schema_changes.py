"""Add functional debt schema changes - costing, dependencies, disposition

Revision ID: 019_add_functional_debt_schema_changes
Revises: 018_add_admin_audit_logs
Create Date: 2025-11-12 14:00:00.000000

Implements critical functional gaps identified in FRD review:

Schema Changes:
1. Work Order Costing Fields (FRD_WORK_ORDERS.md lines 43-77)
   - Add standard_cost, actual_material_cost, actual_labor_cost, actual_overhead_cost, total_actual_cost

2. Work Order Dependencies (FRD_WORK_ORDERS.md lines 11-35)
   - Create work_order_dependency table with DependencyType enum
   - Support FINISH_TO_START, START_TO_START, FINISH_TO_FINISH

3. Material Costing Configuration (FRD_MATERIAL_MANAGEMENT.md lines 14-17)
   - Add CostingMethod enum (FIFO, LIFO, WEIGHTED_AVERAGE)
   - Add costing_method field to organizations table

4. NCR Disposition Fields (FRD_QUALITY.md lines 15-51)
   - Add DispositionType enum (REWORK, SCRAP, USE_AS_IS, RETURN_TO_SUPPLIER)
   - Add disposition_type, disposition_date, disposition_by_user_id, rework_cost, scrap_cost
   - Add customer_affected, root_cause fields

5. Machine Utilization & Maintenance (FRD_EQUIPMENT.md)
   - Add capacity_units_per_hour, last_maintenance_date, next_maintenance_due to machine table
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '019_add_functional_debt_schema_changes'
down_revision = '018_add_admin_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add critical functional debt schema changes identified in FRD review.

    These changes enable:
    - Work order costing and variance tracking
    - Work order dependency management (Finish-to-Start, etc.)
    - Material costing method selection (FIFO/LIFO/Average)
    - NCR disposition workflow automation
    - Machine utilization and maintenance tracking
    """
    conn = op.get_bind()

    # ========================================================================
    # 1. Add CostingMethod enum type
    # ========================================================================

    conn.execute(text("""
        CREATE TYPE costingmethod AS ENUM (
            'FIFO',
            'LIFO',
            'WEIGHTED_AVERAGE'
        );

        COMMENT ON TYPE costingmethod IS
            'Material costing method: FIFO (First-In-First-Out), LIFO (Last-In-First-Out), or WEIGHTED_AVERAGE';
    """))

    # ========================================================================
    # 2. Add DependencyType enum type
    # ========================================================================

    conn.execute(text("""
        CREATE TYPE dependencytype AS ENUM (
            'FINISH_TO_START',
            'START_TO_START',
            'FINISH_TO_FINISH'
        );

        COMMENT ON TYPE dependencytype IS
            'Work order dependency type: FINISH_TO_START (predecessor completes before successor starts), START_TO_START (both start together), FINISH_TO_FINISH (both finish together)';
    """))

    # ========================================================================
    # 3. Add DispositionType enum type
    # ========================================================================

    conn.execute(text("""
        CREATE TYPE dispositiontype AS ENUM (
            'REWORK',
            'SCRAP',
            'USE_AS_IS',
            'RETURN_TO_SUPPLIER'
        );

        COMMENT ON TYPE dispositiontype IS
            'NCR disposition: REWORK (create rework WO), SCRAP (adjust inventory), USE_AS_IS (accept with deviation), RETURN_TO_SUPPLIER (return for credit)';
    """))

    # ========================================================================
    # 4. Add costing_method field to organizations table
    # ========================================================================

    conn.execute(text("""
        ALTER TABLE organizations
        ADD COLUMN costing_method costingmethod NOT NULL DEFAULT 'WEIGHTED_AVERAGE';

        COMMENT ON COLUMN organizations.costing_method IS
            'Material costing method for this organization (FIFO, LIFO, or WEIGHTED_AVERAGE)';
    """))

    # ========================================================================
    # 5. Add costing fields to work_order table
    # ========================================================================

    conn.execute(text("""
        ALTER TABLE work_order
        ADD COLUMN standard_cost FLOAT DEFAULT 0.0,
        ADD COLUMN actual_material_cost FLOAT NOT NULL DEFAULT 0.0,
        ADD COLUMN actual_labor_cost FLOAT NOT NULL DEFAULT 0.0,
        ADD COLUMN actual_overhead_cost FLOAT NOT NULL DEFAULT 0.0,
        ADD COLUMN total_actual_cost FLOAT NOT NULL DEFAULT 0.0;

        COMMENT ON COLUMN work_order.standard_cost IS
            'Standard/planned cost for this work order (for variance calculation)';
        COMMENT ON COLUMN work_order.actual_material_cost IS
            'Actual material cost accumulated during production';
        COMMENT ON COLUMN work_order.actual_labor_cost IS
            'Actual labor cost (hours × labor rate)';
        COMMENT ON COLUMN work_order.actual_overhead_cost IS
            'Actual overhead cost (labor × overhead rate)';
        COMMENT ON COLUMN work_order.total_actual_cost IS
            'Total actual cost (material + labor + overhead)';
    """))

    # ========================================================================
    # 6. Create work_order_dependency table
    # ========================================================================

    conn.execute(text("""
        CREATE TABLE work_order_dependency (
            id SERIAL PRIMARY KEY,
            organization_id INTEGER NOT NULL,
            plant_id INTEGER NOT NULL,
            work_order_id INTEGER NOT NULL REFERENCES work_order(id) ON DELETE CASCADE,
            depends_on_work_order_id INTEGER NOT NULL REFERENCES work_order(id) ON DELETE CASCADE,
            dependency_type dependencytype NOT NULL DEFAULT 'FINISH_TO_START',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,

            CONSTRAINT uq_work_order_dependency UNIQUE (work_order_id, depends_on_work_order_id),
            CONSTRAINT check_no_self_dependency CHECK (work_order_id != depends_on_work_order_id)
        );

        COMMENT ON TABLE work_order_dependency IS
            'Work order dependencies - defines Finish-to-Start, Start-to-Start, and Finish-to-Finish relationships between work orders';

        COMMENT ON COLUMN work_order_dependency.work_order_id IS
            'Work order that has the dependency (successor)';
        COMMENT ON COLUMN work_order_dependency.depends_on_work_order_id IS
            'Work order that must be satisfied first (predecessor)';
        COMMENT ON COLUMN work_order_dependency.dependency_type IS
            'Type of dependency: FINISH_TO_START (most common), START_TO_START, or FINISH_TO_FINISH';
    """))

    # ========================================================================
    # 7. Create indexes for work_order_dependency
    # ========================================================================

    conn.execute(text("""
        CREATE INDEX idx_work_order_dependency_org_plant
            ON work_order_dependency(organization_id, plant_id);

        CREATE INDEX idx_work_order_dependency_wo
            ON work_order_dependency(work_order_id);

        CREATE INDEX idx_work_order_dependency_depends_on
            ON work_order_dependency(depends_on_work_order_id);

        COMMENT ON INDEX idx_work_order_dependency_org_plant IS
            'Multi-tenant isolation index';
        COMMENT ON INDEX idx_work_order_dependency_wo IS
            'Fast lookup of all dependencies for a work order';
        COMMENT ON INDEX idx_work_order_dependency_depends_on IS
            'Fast lookup of all work orders depending on a specific work order';
    """))

    # ========================================================================
    # 8. Add disposition fields to ncr table
    # ========================================================================

    conn.execute(text("""
        ALTER TABLE ncr
        ADD COLUMN disposition_type dispositiontype,
        ADD COLUMN disposition_date TIMESTAMP WITH TIME ZONE,
        ADD COLUMN disposition_by_user_id INTEGER,
        ADD COLUMN rework_cost FLOAT DEFAULT 0.0,
        ADD COLUMN scrap_cost FLOAT DEFAULT 0.0,
        ADD COLUMN customer_affected BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN root_cause VARCHAR(1000);

        COMMENT ON COLUMN ncr.disposition_type IS
            'Disposition decision: REWORK, SCRAP, USE_AS_IS, or RETURN_TO_SUPPLIER';
        COMMENT ON COLUMN ncr.disposition_date IS
            'When disposition decision was made';
        COMMENT ON COLUMN ncr.disposition_by_user_id IS
            'User ID who made disposition decision';
        COMMENT ON COLUMN ncr.rework_cost IS
            'Cost of rework (if disposition is REWORK)';
        COMMENT ON COLUMN ncr.scrap_cost IS
            'Cost of scrapped material (if disposition is SCRAP)';
        COMMENT ON COLUMN ncr.customer_affected IS
            'Whether customer was affected (triggers notification for USE_AS_IS)';
        COMMENT ON COLUMN ncr.root_cause IS
            'Root cause analysis findings';
    """))

    # ========================================================================
    # 9. Create index for NCR disposition queries
    # ========================================================================

    conn.execute(text("""
        CREATE INDEX idx_ncr_disposition_type
            ON ncr(disposition_type)
            WHERE disposition_type IS NOT NULL;

        COMMENT ON INDEX idx_ncr_disposition_type IS
            'Fast filtering by disposition type (e.g., all REWORK dispositions)';
    """))

    # ========================================================================
    # 10. Add machine capacity and maintenance fields
    # ========================================================================

    conn.execute(text("""
        ALTER TABLE machine
        ADD COLUMN capacity_units_per_hour FLOAT,
        ADD COLUMN last_maintenance_date TIMESTAMP WITH TIME ZONE,
        ADD COLUMN next_maintenance_due TIMESTAMP WITH TIME ZONE;

        COMMENT ON COLUMN machine.capacity_units_per_hour IS
            'Machine capacity in units per hour (for utilization calculation)';
        COMMENT ON COLUMN machine.last_maintenance_date IS
            'Date of last preventive maintenance';
        COMMENT ON COLUMN machine.next_maintenance_due IS
            'Next scheduled maintenance due date (used for PM auto-generation)';
    """))

    # ========================================================================
    # 11. Create index for next_maintenance_due queries
    # ========================================================================

    conn.execute(text("""
        CREATE INDEX idx_machine_next_maintenance
            ON machine(next_maintenance_due)
            WHERE next_maintenance_due IS NOT NULL;

        COMMENT ON INDEX idx_machine_next_maintenance IS
            'Fast lookup of machines with upcoming maintenance (for PM auto-generation)';
    """))

    print("✅ CostingMethod, DependencyType, and DispositionType enums created")
    print("✅ Work order costing fields added (standard_cost, actual_material_cost, actual_labor_cost, actual_overhead_cost, total_actual_cost)")
    print("✅ Work order dependency table created with indexes")
    print("✅ Organization costing_method field added")
    print("✅ NCR disposition fields added (disposition_type, disposition_date, rework_cost, scrap_cost, customer_affected, root_cause)")
    print("✅ Machine capacity and maintenance fields added (capacity_units_per_hour, last_maintenance_date, next_maintenance_due)")
    print("✅ All indexes created for efficient querying")


def downgrade() -> None:
    """
    Remove functional debt schema changes.

    WARNING: This will drop columns and tables. Use only in development.
    """
    conn = op.get_bind()

    # Drop indexes
    conn.execute(text("DROP INDEX IF EXISTS idx_machine_next_maintenance;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_ncr_disposition_type;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_work_order_dependency_depends_on;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_work_order_dependency_wo;"))
    conn.execute(text("DROP INDEX IF EXISTS idx_work_order_dependency_org_plant;"))

    # Drop work_order_dependency table
    conn.execute(text("DROP TABLE IF EXISTS work_order_dependency CASCADE;"))

    # Remove machine fields
    conn.execute(text("""
        ALTER TABLE machine
        DROP COLUMN IF EXISTS capacity_units_per_hour,
        DROP COLUMN IF EXISTS last_maintenance_date,
        DROP COLUMN IF EXISTS next_maintenance_due;
    """))

    # Remove NCR disposition fields
    conn.execute(text("""
        ALTER TABLE ncr
        DROP COLUMN IF EXISTS disposition_type,
        DROP COLUMN IF EXISTS disposition_date,
        DROP COLUMN IF EXISTS disposition_by_user_id,
        DROP COLUMN IF EXISTS rework_cost,
        DROP COLUMN IF EXISTS scrap_cost,
        DROP COLUMN IF EXISTS customer_affected,
        DROP COLUMN IF EXISTS root_cause;
    """))

    # Remove work order costing fields
    conn.execute(text("""
        ALTER TABLE work_order
        DROP COLUMN IF EXISTS standard_cost,
        DROP COLUMN IF EXISTS actual_material_cost,
        DROP COLUMN IF EXISTS actual_labor_cost,
        DROP COLUMN IF EXISTS actual_overhead_cost,
        DROP COLUMN IF EXISTS total_actual_cost;
    """))

    # Remove organizations costing_method field
    conn.execute(text("ALTER TABLE organizations DROP COLUMN IF EXISTS costing_method;"))

    # Drop enum types
    conn.execute(text("DROP TYPE IF EXISTS dispositiontype;"))
    conn.execute(text("DROP TYPE IF EXISTS dependencytype;"))
    conn.execute(text("DROP TYPE IF EXISTS costingmethod;"))

    print("⚠️  Functional debt schema changes rolled back")
