"""Add critical missing tables for functional debt resolution

Revision ID: 020
Revises: 019
Create Date: 2025-11-12

This migration adds critical tables identified in functional debt audit:
- suppliers: Material procurement
- material_transactions: FIFO/LIFO/Weighted Average costing
- ncr_photos: Mobile NCR photo attachments
- quality_inspections: In-process quality checks
- quality_checkpoints: Individual checkpoint results
- manpower_allocation: Worker assignments to work orders
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    # 1. CREATE suppliers TABLE
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('payment_terms', sa.String(100), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),  # 1-5
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'supplier_code', name='uq_suppliers_org_code'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_suppliers_rating')
    )

    # Create indexes for suppliers
    op.create_index('idx_suppliers_org', 'suppliers', ['organization_id'])
    op.create_index('idx_suppliers_code', 'suppliers', ['supplier_code'])
    op.create_index('idx_suppliers_active', 'suppliers', ['is_active'], postgresql_where=sa.text('is_active = true'))

    # Enable RLS for suppliers
    op.execute("""
        ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;

        CREATE POLICY suppliers_isolation_policy ON suppliers
            USING (organization_id = current_setting('app.current_organization_id', true)::int);
    """)

    # 2. CREATE material_transactions TABLE (TimescaleDB hypertable for FIFO/LIFO costing)
    op.create_table(
        'material_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),  # 'receipt', 'issue', 'adjustment', 'transfer'
        sa.Column('quantity', sa.Numeric(15, 4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(15, 4), nullable=True),  # Cost at time of transaction
        sa.Column('total_cost', sa.Numeric(15, 2), nullable=True),  # quantity * unit_cost
        sa.Column('reference_type', sa.String(50), nullable=True),  # 'work_order', 'purchase_order', 'adjustment'
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('batch_number', sa.String(100), nullable=True),
        sa.Column('lot_number', sa.String(100), nullable=True),
        sa.Column('storage_location_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=True),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['storage_location_id'], ['storage_locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity != 0', name='ck_material_transactions_qty'),
        sa.CheckConstraint("transaction_type IN ('receipt', 'issue', 'adjustment', 'transfer_in', 'transfer_out')",
                         name='ck_material_transactions_type')
    )

    # Create indexes for material_transactions
    op.create_index('idx_material_transactions_org', 'material_transactions', ['organization_id'])
    op.create_index('idx_material_transactions_material', 'material_transactions', ['material_id', 'transaction_date'])
    op.create_index('idx_material_transactions_plant', 'material_transactions', ['plant_id', 'transaction_date'])
    op.create_index('idx_material_transactions_date', 'material_transactions', ['transaction_date'])
    op.create_index('idx_material_transactions_type', 'material_transactions', ['transaction_type'])
    op.create_index('idx_material_transactions_reference', 'material_transactions', ['reference_type', 'reference_id'])

    # Enable RLS for material_transactions
    op.execute("""
        ALTER TABLE material_transactions ENABLE ROW LEVEL SECURITY;

        CREATE POLICY material_transactions_isolation_policy ON material_transactions
            USING (organization_id = current_setting('app.current_organization_id', true)::int);
    """)

    # Convert to TimescaleDB hypertable (1 month chunks for better performance)
    op.execute("""
        SELECT create_hypertable('material_transactions', 'transaction_date',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE);

        -- Add compression policy (compress data older than 7 days)
        SELECT add_compression_policy('material_transactions', INTERVAL '7 days', if_not_exists => TRUE);

        -- Add retention policy (keep 3 years of data)
        SELECT add_retention_policy('material_transactions', INTERVAL '3 years', if_not_exists => TRUE);
    """)

    # 3. CREATE ncr_photos TABLE
    op.create_table(
        'ncr_photos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('ncr_id', sa.Integer(), nullable=False),
        sa.Column('photo_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),  # MinIO path
        sa.Column('file_size', sa.Integer(), nullable=True),  # bytes
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ncr_id'], ['ncr_reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for ncr_photos
    op.create_index('idx_ncr_photos_org', 'ncr_photos', ['organization_id'])
    op.create_index('idx_ncr_photos_ncr', 'ncr_photos', ['ncr_id'])
    op.create_index('idx_ncr_photos_uploaded_at', 'ncr_photos', ['uploaded_at'])

    # Enable RLS for ncr_photos
    op.execute("""
        ALTER TABLE ncr_photos ENABLE ROW LEVEL SECURITY;

        CREATE POLICY ncr_photos_isolation_policy ON ncr_photos
            USING (organization_id = current_setting('app.current_organization_id', true)::int);
    """)

    # 4. CREATE quality_inspections TABLE
    op.create_table(
        'quality_inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('inspection_type', sa.String(50), nullable=False),  # 'in_process', 'final', 'incoming'
        sa.Column('inspection_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('inspector_id', sa.Integer(), nullable=True),
        sa.Column('result', sa.String(50), nullable=False),  # 'passed', 'failed', 'conditional'
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspector_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("inspection_type IN ('in_process', 'final', 'incoming', 'first_article')",
                         name='ck_quality_inspections_type'),
        sa.CheckConstraint("result IN ('passed', 'failed', 'conditional', 'pending')",
                         name='ck_quality_inspections_result')
    )

    # Create indexes for quality_inspections
    op.create_index('idx_quality_inspections_org', 'quality_inspections', ['organization_id'])
    op.create_index('idx_quality_inspections_plant', 'quality_inspections', ['plant_id'])
    op.create_index('idx_quality_inspections_wo', 'quality_inspections', ['work_order_id'])
    op.create_index('idx_quality_inspections_material', 'quality_inspections', ['material_id'])
    op.create_index('idx_quality_inspections_date', 'quality_inspections', ['inspection_date'])
    op.create_index('idx_quality_inspections_result', 'quality_inspections', ['result'])

    # Enable RLS for quality_inspections
    op.execute("""
        ALTER TABLE quality_inspections ENABLE ROW LEVEL SECURITY;

        CREATE POLICY quality_inspections_isolation_policy ON quality_inspections
            USING (organization_id = current_setting('app.current_organization_id', true)::int);
    """)

    # 5. CREATE quality_checkpoints TABLE
    op.create_table(
        'quality_checkpoints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('inspection_id', sa.Integer(), nullable=False),
        sa.Column('checkpoint_name', sa.String(255), nullable=False),
        sa.Column('characteristic', sa.String(255), nullable=True),  # e.g., "Length", "Diameter"
        sa.Column('specification', sa.String(255), nullable=True),  # e.g., "100mm ± 0.5mm"
        sa.Column('expected_value', sa.String(100), nullable=True),
        sa.Column('actual_value', sa.String(100), nullable=True),
        sa.Column('uom', sa.String(50), nullable=True),  # Unit of measure
        sa.Column('result', sa.String(50), nullable=False),  # 'passed', 'failed', 'within_tolerance', 'out_of_spec'
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('measured_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspection_id'], ['quality_inspections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("result IN ('passed', 'failed', 'within_tolerance', 'out_of_spec', 'not_measured')",
                         name='ck_quality_checkpoints_result')
    )

    # Create indexes for quality_checkpoints
    op.create_index('idx_quality_checkpoints_org', 'quality_checkpoints', ['organization_id'])
    op.create_index('idx_quality_checkpoints_inspection', 'quality_checkpoints', ['inspection_id'])
    op.create_index('idx_quality_checkpoints_result', 'quality_checkpoints', ['result'])

    # Enable RLS for quality_checkpoints
    op.execute("""
        ALTER TABLE quality_checkpoints ENABLE ROW LEVEL SECURITY;

        CREATE POLICY quality_checkpoints_isolation_policy ON quality_checkpoints
            USING (organization_id = current_setting('app.current_organization_id', true)::int);
    """)

    # 6. CREATE manpower_allocation TABLE
    op.create_table(
        'manpower_allocation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('work_order_id', sa.Integer(), nullable=False),
        sa.Column('operation_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(100), nullable=True),  # 'operator', 'supervisor', 'technician'
        sa.Column('allocated_hours', sa.Numeric(10, 2), nullable=True),
        sa.Column('actual_hours', sa.Numeric(10, 2), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=True),
        sa.Column('allocated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('allocated_by', sa.Integer(), nullable=True),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['operation_id'], ['work_order_operations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['allocated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for manpower_allocation
    op.create_index('idx_manpower_allocation_org', 'manpower_allocation', ['organization_id'])
    op.create_index('idx_manpower_allocation_wo', 'manpower_allocation', ['work_order_id'])
    op.create_index('idx_manpower_allocation_user', 'manpower_allocation', ['user_id'])
    op.create_index('idx_manpower_allocation_operation', 'manpower_allocation', ['operation_id'])
    op.create_index('idx_manpower_allocation_date', 'manpower_allocation', ['allocated_at'])

    # Enable RLS for manpower_allocation
    op.execute("""
        ALTER TABLE manpower_allocation ENABLE ROW LEVEL SECURITY;

        CREATE POLICY manpower_allocation_isolation_policy ON manpower_allocation
            USING (organization_id = current_setting('app.current_organization_id', true)::int);
    """)

    print("✅ Successfully created 6 critical tables:")
    print("   - suppliers")
    print("   - material_transactions (TimescaleDB hypertable)")
    print("   - ncr_photos")
    print("   - quality_inspections")
    print("   - quality_checkpoints")
    print("   - manpower_allocation")


def downgrade():
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('manpower_allocation')
    op.drop_table('quality_checkpoints')
    op.drop_table('quality_inspections')
    op.drop_table('ncr_photos')
    op.drop_table('material_transactions')
    op.drop_table('suppliers')
