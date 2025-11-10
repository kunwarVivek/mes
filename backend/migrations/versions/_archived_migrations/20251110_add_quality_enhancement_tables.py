"""Add quality enhancement tables (inspection_plans, inspection_points, inspection_characteristics, inspection_measurements)

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-11-10 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create inspection_plans table
    op.create_table(
        'inspection_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=True),

        # Plan identification
        sa.Column('plan_code', sa.String(length=100), nullable=False),
        sa.Column('plan_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plan_type', sa.String(length=50), nullable=False),  # INCOMING, IN_PROCESS, FINAL, AUDIT

        # Scope
        sa.Column('applies_to', sa.String(length=50), nullable=False),  # MATERIAL, WORK_ORDER, PRODUCT, PROCESS
        sa.Column('material_id', sa.Integer(), nullable=True),  # If applies to specific material
        sa.Column('work_center_id', sa.Integer(), nullable=True),  # If applies to specific work center

        # Frequency and scheduling
        sa.Column('frequency', sa.String(length=50), nullable=False),  # EVERY_UNIT, HOURLY, DAILY, WEEKLY, PERIODIC
        sa.Column('frequency_value', sa.Integer(), nullable=True),  # e.g., every 100 units, every 4 hours
        sa.Column('sample_size', sa.Integer(), nullable=True),

        # SPC configuration
        sa.Column('spc_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('control_limits_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Structure: {
        #   "method": "3_sigma|6_sigma|custom",
        #   "ucl_multiplier": 3.0,
        #   "lcl_multiplier": 3.0,
        #   "recalculate_frequency": "monthly"
        # }

        # Approval and activation
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),

        # Instructions
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('acceptance_criteria', sa.Text(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('revision', sa.Integer(), nullable=False, server_default='1'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'plan_code', name='uq_inspection_plan_code'),
        sa.Index('idx_inspection_plans_org', 'organization_id'),
        sa.Index('idx_inspection_plans_plant', 'plant_id'),
        sa.Index('idx_inspection_plans_type', 'plan_type'),
        sa.Index('idx_inspection_plans_material', 'material_id'),
        sa.CheckConstraint(
            "plan_type IN ('INCOMING', 'IN_PROCESS', 'FINAL', 'AUDIT')",
            name='chk_plan_type_valid'
        ),
        sa.CheckConstraint(
            "applies_to IN ('MATERIAL', 'WORK_ORDER', 'PRODUCT', 'PROCESS')",
            name='chk_applies_to_valid'
        ),
        sa.CheckConstraint(
            "frequency IN ('EVERY_UNIT', 'HOURLY', 'DAILY', 'WEEKLY', 'PERIODIC', 'ON_DEMAND')",
            name='chk_frequency_valid'
        ),
    )

    # Create inspection_points table
    op.create_table(
        'inspection_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('inspection_plan_id', sa.Integer(), nullable=False),

        # Point identification
        sa.Column('point_code', sa.String(length=100), nullable=False),
        sa.Column('point_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Configuration
        sa.Column('inspection_method', sa.String(length=100), nullable=True),  # VISUAL, DIMENSIONAL, FUNCTIONAL, etc.
        sa.Column('inspection_equipment', sa.String(length=200), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),

        # Requirements
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_critical', sa.Boolean(), nullable=False, server_default='false'),

        # Instructions
        sa.Column('inspection_instructions', sa.Text(), nullable=True),
        sa.Column('acceptance_criteria', sa.Text(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspection_plan_id'], ['inspection_plans.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('inspection_plan_id', 'point_code', name='uq_inspection_point_code'),
        sa.Index('idx_inspection_points_org', 'organization_id'),
        sa.Index('idx_inspection_points_plan', 'inspection_plan_id'),
        sa.Index('idx_inspection_points_sequence', 'inspection_plan_id', 'sequence'),
    )

    # Create inspection_characteristics table
    op.create_table(
        'inspection_characteristics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('inspection_point_id', sa.Integer(), nullable=False),

        # Characteristic identification
        sa.Column('characteristic_code', sa.String(length=100), nullable=False),
        sa.Column('characteristic_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Measurement configuration
        sa.Column('characteristic_type', sa.String(length=50), nullable=False),  # VARIABLE, ATTRIBUTE
        sa.Column('data_type', sa.String(length=50), nullable=False),  # NUMERIC, BOOLEAN, TEXT
        sa.Column('unit_of_measure', sa.String(length=50), nullable=True),

        # Specification limits (for VARIABLE characteristics)
        sa.Column('target_value', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('lower_spec_limit', sa.Numeric(precision=15, scale=6), nullable=True),  # LSL
        sa.Column('upper_spec_limit', sa.Numeric(precision=15, scale=6), nullable=True),  # USL
        sa.Column('lower_control_limit', sa.Numeric(precision=15, scale=6), nullable=True),  # LCL (calculated)
        sa.Column('upper_control_limit', sa.Numeric(precision=15, scale=6), nullable=True),  # UCL (calculated)

        # SPC configuration
        sa.Column('track_spc', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('control_chart_type', sa.String(length=50), nullable=True),  # XBAR_R, XBAR_S, P_CHART, C_CHART, etc.
        sa.Column('subgroup_size', sa.Integer(), nullable=True),

        # Attribute options (for ATTRIBUTE characteristics)
        sa.Column('allowed_values', postgresql.ARRAY(sa.String()), nullable=True),

        # Tolerances
        sa.Column('tolerance_type', sa.String(length=50), nullable=True),  # BILATERAL, UNILATERAL_UPPER, UNILATERAL_LOWER
        sa.Column('tolerance', sa.Numeric(precision=15, scale=6), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspection_point_id'], ['inspection_points.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('inspection_point_id', 'characteristic_code', name='uq_inspection_characteristic_code'),
        sa.Index('idx_inspection_characteristics_org', 'organization_id'),
        sa.Index('idx_inspection_characteristics_point', 'inspection_point_id'),
        sa.Index('idx_inspection_characteristics_spc', 'track_spc'),
        sa.CheckConstraint(
            "characteristic_type IN ('VARIABLE', 'ATTRIBUTE')",
            name='chk_characteristic_type_valid'
        ),
        sa.CheckConstraint(
            "data_type IN ('NUMERIC', 'BOOLEAN', 'TEXT')",
            name='chk_data_type_valid'
        ),
    )

    # Create inspection_measurements table (timescaledb hypertable)
    op.create_table(
        'inspection_measurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('characteristic_id', sa.Integer(), nullable=False),
        sa.Column('inspection_plan_id', sa.Integer(), nullable=False),

        # Measurement context
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('lot_number', sa.String(length=100), nullable=True),
        sa.Column('serial_number', sa.String(length=100), nullable=True),

        # Measurement details
        sa.Column('measured_value', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('measured_text', sa.String(length=500), nullable=True),  # For attribute data
        sa.Column('is_conforming', sa.Boolean(), nullable=True),
        sa.Column('deviation', sa.Numeric(precision=15, scale=6), nullable=True),  # from target

        # Sample information
        sa.Column('sample_number', sa.Integer(), nullable=True),
        sa.Column('subgroup_number', sa.Integer(), nullable=True),

        # SPC calculations (cached for performance)
        sa.Column('range_value', sa.Numeric(precision=15, scale=6), nullable=True),  # For R charts
        sa.Column('moving_range', sa.Numeric(precision=15, scale=6), nullable=True),  # For mR charts
        sa.Column('is_out_of_control', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('control_violation_type', sa.String(length=100), nullable=True),  # WESTERN_ELECTRIC_RULE_1, etc.

        # Measurement metadata
        sa.Column('measured_by', sa.Integer(), nullable=False),
        sa.Column('measurement_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('inspection_equipment_id', sa.String(length=100), nullable=True),
        sa.Column('environmental_conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id', 'measurement_timestamp'),  # Composite key for timescaledb
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['characteristic_id'], ['inspection_characteristics.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspection_plan_id'], ['inspection_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['measured_by'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_inspection_measurements_org', 'organization_id'),
        sa.Index('idx_inspection_measurements_char', 'characteristic_id'),
        sa.Index('idx_inspection_measurements_plan', 'inspection_plan_id'),
        sa.Index('idx_inspection_measurements_wo', 'work_order_id'),
        sa.Index('idx_inspection_measurements_time', 'measurement_timestamp'),
        sa.Index('idx_inspection_measurements_lot', 'lot_number'),
    )

    # Convert to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable(
            'inspection_measurements',
            'measurement_timestamp',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '1 month'
        )
    """)

    # Enable RLS on all four tables
    op.execute("ALTER TABLE inspection_plans ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inspection_points ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inspection_characteristics ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE inspection_measurements ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY inspection_plans_org_isolation ON inspection_plans
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY inspection_points_org_isolation ON inspection_points
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY inspection_characteristics_org_isolation ON inspection_characteristics
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY inspection_measurements_org_isolation ON inspection_measurements
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS inspection_plans_org_isolation ON inspection_plans")
    op.execute("DROP POLICY IF EXISTS inspection_points_org_isolation ON inspection_points")
    op.execute("DROP POLICY IF EXISTS inspection_characteristics_org_isolation ON inspection_characteristics")
    op.execute("DROP POLICY IF EXISTS inspection_measurements_org_isolation ON inspection_measurements")

    # Drop tables
    op.drop_table('inspection_measurements')
    op.drop_table('inspection_characteristics')
    op.drop_table('inspection_points')
    op.drop_table('inspection_plans')
