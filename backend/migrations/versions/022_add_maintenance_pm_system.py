"""Add Maintenance PM System tables and fix critical schema gaps

Revision ID: 022
Revises: 021
Create Date: 2025-11-16

This migration fixes critical schema gaps identified in comprehensive audit:

CRITICAL BLOCKER:
1. Maintenance PM Tables - pg_cron job references non-existent tables
   - maintenance_schedules: PM schedule definitions (calendar/meter-based)
   - maintenance_tasks: Individual PM tasks
   - maintenance_task_checklists: Task step checklists

HIGH PRIORITY:
2. Add maintenance_task_id to work_orders (link PM work orders to tasks)
3. Add missing shift configuration columns (break_duration, days_active, targets)
4. Add plant-level RLS policies to newly added tables (migration 020)

These changes enable:
- Automated PM work order generation via pg_cron (fixes blocker)
- Multi-shift plant operations with targets
- Plant-level data isolation for multi-plant customers
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    print("🔧 Adding Maintenance PM System tables and critical fixes...")

    # ========================================================================
    # 1. CREATE maintenance_schedules TABLE (PM Schedule Definitions)
    # ========================================================================
    print("  → Creating maintenance_schedules table...")
    op.create_table(
        'maintenance_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('machine_id', sa.Integer(), nullable=True),
        sa.Column('schedule_name', sa.String(255), nullable=False),
        sa.Column('schedule_type', sa.String(50), nullable=False),  # 'calendar', 'meter_based'
        sa.Column('frequency_value', sa.Integer(), nullable=True),  # e.g., 30 for "every 30 days"
        sa.Column('frequency_unit', sa.String(50), nullable=True),  # 'days', 'weeks', 'months', 'hours'
        sa.Column('meter_threshold', sa.Integer(), nullable=True),  # For meter-based: run PM every X hours
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("schedule_type IN ('calendar', 'meter_based')", name='ck_maintenance_schedules_type'),
        sa.CheckConstraint("frequency_unit IN ('days', 'weeks', 'months', 'hours', 'cycles')",
                         name='ck_maintenance_schedules_unit')
    )

    # Indexes for maintenance_schedules
    op.create_index('idx_maintenance_schedules_org', 'maintenance_schedules', ['organization_id'])
    op.create_index('idx_maintenance_schedules_plant', 'maintenance_schedules', ['plant_id'])
    op.create_index('idx_maintenance_schedules_machine', 'maintenance_schedules', ['machine_id'])
    op.create_index('idx_maintenance_schedules_next_due', 'maintenance_schedules', ['next_due_date'],
                   postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_maintenance_schedules_active', 'maintenance_schedules', ['is_active'])

    # RLS for maintenance_schedules
    op.execute("""
        ALTER TABLE maintenance_schedules ENABLE ROW LEVEL SECURITY;

        CREATE POLICY maintenance_schedules_isolation_policy ON maintenance_schedules
            USING (organization_id = current_setting('app.current_organization_id', true)::int);

        CREATE POLICY maintenance_schedules_plant_isolation ON maintenance_schedules
            USING (plant_id = current_setting('app.current_plant_id', true)::int);
    """)

    # ========================================================================
    # 2. CREATE maintenance_tasks TABLE (Individual PM Tasks)
    # ========================================================================
    print("  → Creating maintenance_tasks table...")
    op.create_table(
        'maintenance_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('task_name', sa.String(255), nullable=False),
        sa.Column('task_type', sa.String(100), nullable=True),  # 'lubrication', 'inspection', 'calibration', 'replacement'
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_duration', sa.Interval(), nullable=True),  # Expected time to complete
        sa.Column('required_skills', sa.String(255), nullable=True),
        sa.Column('safety_notes', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='3'),  # 1=critical, 5=low
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('next_maintenance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schedule_id'], ['maintenance_schedules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('priority >= 1 AND priority <= 5', name='ck_maintenance_tasks_priority')
    )

    # Indexes for maintenance_tasks
    op.create_index('idx_maintenance_tasks_org', 'maintenance_tasks', ['organization_id'])
    op.create_index('idx_maintenance_tasks_plant', 'maintenance_tasks', ['plant_id'])
    op.create_index('idx_maintenance_tasks_schedule', 'maintenance_tasks', ['schedule_id'])
    op.create_index('idx_maintenance_tasks_next_date', 'maintenance_tasks', ['next_maintenance_date'],
                   postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_maintenance_tasks_type', 'maintenance_tasks', ['task_type'])

    # RLS for maintenance_tasks
    op.execute("""
        ALTER TABLE maintenance_tasks ENABLE ROW LEVEL SECURITY;

        CREATE POLICY maintenance_tasks_isolation_policy ON maintenance_tasks
            USING (organization_id = current_setting('app.current_organization_id', true)::int);

        CREATE POLICY maintenance_tasks_plant_isolation ON maintenance_tasks
            USING (plant_id = current_setting('app.current_plant_id', true)::int);
    """)

    # ========================================================================
    # 3. CREATE maintenance_task_checklists TABLE (Task Steps)
    # ========================================================================
    print("  → Creating maintenance_task_checklists table...")
    op.create_table(
        'maintenance_task_checklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('step_description', sa.Text(), nullable=False),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_photo', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_measurement', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('measurement_spec', sa.String(255), nullable=True),  # e.g., "Torque: 50-60 Nm"
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['maintenance_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id', 'step_number', name='uq_maintenance_checklist_task_step')
    )

    # Indexes for maintenance_task_checklists
    op.create_index('idx_maintenance_checklists_org', 'maintenance_task_checklists', ['organization_id'])
    op.create_index('idx_maintenance_checklists_task', 'maintenance_task_checklists', ['task_id'])
    op.create_index('idx_maintenance_checklists_step', 'maintenance_task_checklists', ['task_id', 'step_number'])

    # RLS for maintenance_task_checklists
    op.execute("""
        ALTER TABLE maintenance_task_checklists ENABLE ROW LEVEL SECURITY;

        CREATE POLICY maintenance_task_checklists_isolation_policy ON maintenance_task_checklists
            USING (organization_id = current_setting('app.current_organization_id', true)::int);
    """)

    # ========================================================================
    # 4. ADD maintenance_task_id COLUMN TO work_orders
    # ========================================================================
    print("  → Adding maintenance_task_id to work_orders table...")
    op.add_column('work_orders', sa.Column('maintenance_task_id', sa.Integer(), nullable=True))

    # Add foreign key
    op.create_foreign_key(
        'fk_work_orders_maintenance_task',
        'work_orders', 'maintenance_tasks',
        ['maintenance_task_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add index
    op.create_index('idx_work_orders_maintenance_task', 'work_orders', ['maintenance_task_id'],
                   postgresql_where=sa.text('maintenance_task_id IS NOT NULL'))

    # ========================================================================
    # 5. ADD MISSING COLUMNS TO shifts TABLE
    # ========================================================================
    print("  → Adding missing columns to shifts table...")
    op.add_column('shifts', sa.Column('break_duration', sa.Integer(), nullable=True, server_default='30'))  # minutes
    op.add_column('shifts', sa.Column('days_active', sa.String(50), nullable=True, server_default='Mon,Tue,Wed,Thu,Fri'))
    op.add_column('shifts', sa.Column('production_target', sa.Integer(), nullable=True))  # Target units per shift
    op.add_column('shifts', sa.Column('oee_target', sa.Numeric(5, 2), nullable=True, server_default='85.00'))  # Target OEE %

    # Add index for shifts
    op.create_index('idx_shifts_days_active', 'shifts', ['days_active'],
                   postgresql_where=sa.text('is_active = true'))

    # Add check constraint for OEE target
    op.create_check_constraint(
        'ck_shifts_oee_target',
        'shifts',
        'oee_target IS NULL OR (oee_target >= 0 AND oee_target <= 100)'
    )

    # ========================================================================
    # 6. ADD PLANT-LEVEL RLS POLICIES TO TABLES FROM MIGRATION 020
    # ========================================================================
    print("  → Adding plant-level RLS policies to migration 020 tables...")

    # Plant isolation for suppliers
    op.execute("""
        CREATE POLICY suppliers_plant_isolation ON suppliers
            USING (
                organization_id = current_setting('app.current_organization_id', true)::int
                AND (
                    current_setting('app.current_plant_id', true) IS NULL
                    OR current_setting('app.current_plant_id', true) = ''
                    OR EXISTS (
                        SELECT 1 FROM materials m
                        WHERE m.supplier_id = suppliers.id
                          AND m.plant_id = current_setting('app.current_plant_id', true)::int
                    )
                )
            );
    """)

    # Plant isolation for material_transactions
    op.execute("""
        CREATE POLICY material_transactions_plant_isolation ON material_transactions
            USING (plant_id = current_setting('app.current_plant_id', true)::int);
    """)

    # Plant isolation for ncr_photos
    op.execute("""
        CREATE POLICY ncr_photos_plant_isolation ON ncr_photos
            USING (
                EXISTS (
                    SELECT 1 FROM ncr_reports ncr
                    WHERE ncr.id = ncr_photos.ncr_id
                      AND ncr.plant_id = current_setting('app.current_plant_id', true)::int
                )
            );
    """)

    print("✅ Successfully completed migration 022:")
    print("   - Created maintenance_schedules table (PM schedule definitions)")
    print("   - Created maintenance_tasks table (individual PM tasks)")
    print("   - Created maintenance_task_checklists table (task steps)")
    print("   - Added maintenance_task_id to work_orders")
    print("   - Added 4 columns to shifts table (break_duration, days_active, targets)")
    print("   - Added plant-level RLS policies to 3 tables")
    print("")
    print("🎉 CRITICAL BLOCKER RESOLVED: pg_cron PM job can now execute!")
    print("   Job: generate_pm_work_orders (Daily 6 AM)")
    print("   References: maintenance_tasks table ✅")


def downgrade():
    """Reverse migration 022 changes"""
    print("Reversing migration 022...")

    # Remove plant-level RLS policies
    op.execute("DROP POLICY IF EXISTS suppliers_plant_isolation ON suppliers;")
    op.execute("DROP POLICY IF EXISTS material_transactions_plant_isolation ON material_transactions;")
    op.execute("DROP POLICY IF EXISTS ncr_photos_plant_isolation ON ncr_photos;")

    # Remove shifts columns
    op.drop_constraint('ck_shifts_oee_target', 'shifts', type_='check')
    op.drop_index('idx_shifts_days_active', 'shifts')
    op.drop_column('shifts', 'oee_target')
    op.drop_column('shifts', 'production_target')
    op.drop_column('shifts', 'days_active')
    op.drop_column('shifts', 'break_duration')

    # Remove work_orders maintenance_task_id
    op.drop_constraint('fk_work_orders_maintenance_task', 'work_orders', type_='foreignkey')
    op.drop_index('idx_work_orders_maintenance_task', 'work_orders')
    op.drop_column('work_orders', 'maintenance_task_id')

    # Drop maintenance tables in reverse order
    op.drop_table('maintenance_task_checklists')
    op.drop_table('maintenance_tasks')
    op.drop_table('maintenance_schedules')

    print("✅ Migration 022 reversed")
