"""Add traceability tables (lot_batches, serial_numbers, traceability_links, genealogy_records)

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2025-11-10 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lot_batches table
    op.create_table(
        'lot_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=True),

        # Lot identification
        sa.Column('lot_number', sa.String(length=100), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('supplier_lot_number', sa.String(length=100), nullable=True),

        # Quantity tracking
        sa.Column('initial_quantity', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('current_quantity', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('reserved_quantity', sa.Numeric(precision=15, scale=6), nullable=False, server_default='0'),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=True),

        # Source information
        sa.Column('source_type', sa.String(length=50), nullable=False),  # PURCHASED, MANUFACTURED, RETURNED, ADJUSTED
        sa.Column('source_reference_id', sa.Integer(), nullable=True),  # Work order ID or PO ID
        sa.Column('supplier_id', sa.Integer(), nullable=True),

        # Dates
        sa.Column('production_date', sa.Date(), nullable=True),
        sa.Column('received_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('retest_date', sa.Date(), nullable=True),

        # Quality status
        sa.Column('quality_status', sa.String(length=50), nullable=False, server_default='PENDING'),  # PENDING, RELEASED, QUARANTINE, REJECTED
        sa.Column('inspection_status', sa.String(length=50), nullable=True),
        sa.Column('certificate_number', sa.String(length=100), nullable=True),

        # Location
        sa.Column('warehouse_location', sa.String(length=100), nullable=True),
        sa.Column('bin_location', sa.String(length=50), nullable=True),

        # Traceability attributes
        # Structure: {
        #   "heat_number": "H12345",
        #   "melt_number": "M67890",
        #   "mill_cert": "MC-2024-001",
        #   "country_of_origin": "USA"
        # }
        sa.Column('traceability_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Custom attributes
        sa.Column('custom_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_depleted', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'lot_number', name='uq_lot_number_per_org'),
        sa.Index('idx_lot_batches_org', 'organization_id'),
        sa.Index('idx_lot_batches_plant', 'plant_id'),
        sa.Index('idx_lot_batches_material', 'material_id'),
        sa.Index('idx_lot_batches_lot_number', 'lot_number'),
        sa.Index('idx_lot_batches_quality_status', 'quality_status'),
        sa.Index('idx_lot_batches_expiry', 'expiry_date'),
        sa.CheckConstraint(
            "source_type IN ('PURCHASED', 'MANUFACTURED', 'RETURNED', 'ADJUSTED', 'TRANSFERRED')",
            name='chk_lot_source_type_valid'
        ),
        sa.CheckConstraint(
            "quality_status IN ('PENDING', 'RELEASED', 'QUARANTINE', 'REJECTED', 'EXPIRED')",
            name='chk_lot_quality_status_valid'
        ),
        sa.CheckConstraint('current_quantity >= 0', name='chk_lot_current_quantity_non_negative'),
        sa.CheckConstraint('reserved_quantity >= 0', name='chk_lot_reserved_quantity_non_negative'),
    )

    # Create serial_numbers table
    op.create_table(
        'serial_numbers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=True),

        # Serial identification
        sa.Column('serial_number', sa.String(length=100), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('lot_batch_id', sa.Integer(), nullable=True),  # Optional link to lot

        # Source information
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('production_date', sa.Date(), nullable=True),
        sa.Column('production_line', sa.String(length=100), nullable=True),

        # Status and location
        sa.Column('status', sa.String(length=50), nullable=False, server_default='IN_STOCK'),  # IN_STOCK, RESERVED, SHIPPED, INSTALLED, SCRAPPED, RETURNED
        sa.Column('quality_status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('current_location', sa.String(length=200), nullable=True),
        sa.Column('warehouse_location', sa.String(length=100), nullable=True),

        # Customer/shipment tracking
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('shipment_id', sa.Integer(), nullable=True),
        sa.Column('shipped_date', sa.Date(), nullable=True),
        sa.Column('installation_date', sa.Date(), nullable=True),
        sa.Column('installation_location', sa.String(length=200), nullable=True),

        # Warranty and service
        sa.Column('warranty_start_date', sa.Date(), nullable=True),
        sa.Column('warranty_end_date', sa.Date(), nullable=True),
        sa.Column('last_service_date', sa.Date(), nullable=True),

        # Traceability attributes
        sa.Column('traceability_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Custom attributes
        sa.Column('custom_attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Notes
        sa.Column('notes', sa.Text(), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lot_batch_id'], ['lot_batches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'serial_number', name='uq_serial_number_per_org'),
        sa.Index('idx_serial_numbers_org', 'organization_id'),
        sa.Index('idx_serial_numbers_plant', 'plant_id'),
        sa.Index('idx_serial_numbers_material', 'material_id'),
        sa.Index('idx_serial_numbers_lot', 'lot_batch_id'),
        sa.Index('idx_serial_numbers_serial', 'serial_number'),
        sa.Index('idx_serial_numbers_status', 'status'),
        sa.Index('idx_serial_numbers_customer', 'customer_id'),
        sa.CheckConstraint(
            "status IN ('IN_STOCK', 'RESERVED', 'SHIPPED', 'INSTALLED', 'SCRAPPED', 'RETURNED', 'IN_SERVICE')",
            name='chk_serial_status_valid'
        ),
        sa.CheckConstraint(
            "quality_status IN ('PENDING', 'RELEASED', 'QUARANTINE', 'REJECTED')",
            name='chk_serial_quality_status_valid'
        ),
    )

    # Create traceability_links table
    op.create_table(
        'traceability_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Parent (what was used/consumed)
        sa.Column('parent_type', sa.String(length=20), nullable=False),  # LOT, SERIAL
        sa.Column('parent_lot_id', sa.Integer(), nullable=True),
        sa.Column('parent_serial_id', sa.Integer(), nullable=True),

        # Child (what was produced/created)
        sa.Column('child_type', sa.String(length=20), nullable=False),  # LOT, SERIAL
        sa.Column('child_lot_id', sa.Integer(), nullable=True),
        sa.Column('child_serial_id', sa.Integer(), nullable=True),

        # Relationship details
        sa.Column('relationship_type', sa.String(length=50), nullable=False),  # CONSUMED_IN, ASSEMBLED_INTO, PACKAGED_WITH, DERIVED_FROM
        sa.Column('quantity_used', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('unit_of_measure', sa.String(length=50), nullable=True),

        # Context
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('operation_sequence', sa.Integer(), nullable=True),
        sa.Column('link_date', sa.DateTime(timezone=True), nullable=False),

        # Additional metadata
        # Structure: {
        #   "position": "A1",  # Assembly position
        #   "revision": "Rev B",
        #   "notes": "..."
        # }
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_lot_id'], ['lot_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_serial_id'], ['serial_numbers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['child_lot_id'], ['lot_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['child_serial_id'], ['serial_numbers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_traceability_links_org', 'organization_id'),
        sa.Index('idx_traceability_links_parent_lot', 'parent_lot_id'),
        sa.Index('idx_traceability_links_parent_serial', 'parent_serial_id'),
        sa.Index('idx_traceability_links_child_lot', 'child_lot_id'),
        sa.Index('idx_traceability_links_child_serial', 'child_serial_id'),
        sa.Index('idx_traceability_links_wo', 'work_order_id'),
        sa.Index('idx_traceability_links_date', 'link_date'),
        sa.CheckConstraint(
            "parent_type IN ('LOT', 'SERIAL')",
            name='chk_parent_type_valid'
        ),
        sa.CheckConstraint(
            "child_type IN ('LOT', 'SERIAL')",
            name='chk_child_type_valid'
        ),
        sa.CheckConstraint(
            "relationship_type IN ('CONSUMED_IN', 'ASSEMBLED_INTO', 'PACKAGED_WITH', 'DERIVED_FROM', 'SPLIT_FROM', 'MERGED_INTO')",
            name='chk_relationship_type_valid'
        ),
        sa.CheckConstraint(
            "(parent_type = 'LOT' AND parent_lot_id IS NOT NULL) OR (parent_type = 'SERIAL' AND parent_serial_id IS NOT NULL)",
            name='chk_parent_reference_valid'
        ),
        sa.CheckConstraint(
            "(child_type = 'LOT' AND child_lot_id IS NOT NULL) OR (child_type = 'SERIAL' AND child_serial_id IS NOT NULL)",
            name='chk_child_reference_valid'
        ),
    )

    # Create genealogy_records table (TimescaleDB hypertable for audit trail)
    op.create_table(
        'genealogy_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),

        # Entity being tracked
        sa.Column('entity_type', sa.String(length=20), nullable=False),  # LOT, SERIAL
        sa.Column('entity_id', sa.Integer(), nullable=False),  # ID of lot_batch or serial_number
        sa.Column('entity_identifier', sa.String(length=100), nullable=False),  # Lot number or serial number for quick lookup

        # Operation details
        sa.Column('operation_type', sa.String(length=50), nullable=False),  # CREATED, RECEIVED, INSPECTED, CONSUMED, SHIPPED, INSTALLED, etc.
        sa.Column('operation_timestamp', sa.DateTime(timezone=True), nullable=False),

        # Context
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),  # PO, SHIPMENT, INSPECTION, etc.
        sa.Column('reference_id', sa.Integer(), nullable=True),

        # Quantity changes (for lots)
        sa.Column('quantity_before', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('quantity_after', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('quantity_change', sa.Numeric(precision=15, scale=6), nullable=True),

        # Status changes
        sa.Column('status_before', sa.String(length=50), nullable=True),
        sa.Column('status_after', sa.String(length=50), nullable=True),

        # Location changes
        sa.Column('location_before', sa.String(length=200), nullable=True),
        sa.Column('location_after', sa.String(length=200), nullable=True),

        # Metadata
        # Structure: {
        #   "inspection_result": "PASS",
        #   "customer_name": "Acme Corp",
        #   "operator": "John Doe",
        #   "notes": "..."
        # }
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Audit
        sa.Column('performed_by', sa.Integer(), nullable=False),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        sa.PrimaryKeyConstraint('id', 'operation_timestamp'),  # Composite key for TimescaleDB
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_genealogy_records_org', 'organization_id'),
        sa.Index('idx_genealogy_records_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_genealogy_records_identifier', 'entity_identifier'),
        sa.Index('idx_genealogy_records_timestamp', 'operation_timestamp'),
        sa.Index('idx_genealogy_records_operation', 'operation_type'),
        sa.CheckConstraint(
            "entity_type IN ('LOT', 'SERIAL')",
            name='chk_genealogy_entity_type_valid'
        ),
    )

    # Convert genealogy_records to TimescaleDB hypertable
    op.execute("""
        SELECT create_hypertable(
            'genealogy_records',
            'operation_timestamp',
            if_not_exists => TRUE,
            chunk_time_interval => INTERVAL '3 months'
        )
    """)

    # Enable RLS on all four tables
    op.execute("ALTER TABLE lot_batches ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE serial_numbers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE traceability_links ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE genealogy_records ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY lot_batches_org_isolation ON lot_batches
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY serial_numbers_org_isolation ON serial_numbers
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY traceability_links_org_isolation ON traceability_links
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY genealogy_records_org_isolation ON genealogy_records
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS lot_batches_org_isolation ON lot_batches")
    op.execute("DROP POLICY IF EXISTS serial_numbers_org_isolation ON serial_numbers")
    op.execute("DROP POLICY IF EXISTS traceability_links_org_isolation ON traceability_links")
    op.execute("DROP POLICY IF EXISTS genealogy_records_org_isolation ON genealogy_records")

    # Drop tables
    op.drop_table('genealogy_records')
    op.drop_table('traceability_links')
    op.drop_table('serial_numbers')
    op.drop_table('lot_batches')
