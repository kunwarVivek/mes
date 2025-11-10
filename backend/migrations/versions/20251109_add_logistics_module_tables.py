"""Add Logistics Module tables (shipments, barcode_labels, qr_code_scans)

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2025-11-09 20:00:00.000000

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
    # Create shipments table
    op.create_table(
        'shipments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('shipment_number', sa.String(length=50), nullable=False),
        sa.Column('shipment_type', sa.String(length=50), nullable=False),  # outbound, inbound, inter_plant
        sa.Column('status', sa.String(length=50), nullable=False),  # draft, packed, shipped, in_transit, delivered, cancelled

        # Customer/Vendor information
        sa.Column('customer_name', sa.String(length=200), nullable=True),
        sa.Column('customer_code', sa.String(length=50), nullable=True),
        sa.Column('vendor_name', sa.String(length=200), nullable=True),
        sa.Column('vendor_code', sa.String(length=50), nullable=True),

        # Destination (for inter-plant transfers)
        sa.Column('destination_plant_id', sa.Integer(), nullable=True),

        # Shipping details
        sa.Column('carrier_name', sa.String(length=100), nullable=True),
        sa.Column('tracking_number', sa.String(length=100), nullable=True),
        sa.Column('shipping_method', sa.String(length=50), nullable=True),  # ground, air, sea, courier

        # Address
        sa.Column('shipping_address', sa.Text(), nullable=True),
        sa.Column('delivery_address', sa.Text(), nullable=True),

        # Dates
        sa.Column('planned_ship_date', sa.Date(), nullable=True),
        sa.Column('actual_ship_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_delivery_date', sa.Date(), nullable=True),
        sa.Column('actual_delivery_date', sa.DateTime(timezone=True), nullable=True),

        # Dimensions and weight
        sa.Column('total_packages', sa.Integer(), nullable=True),
        sa.Column('total_weight', sa.Float(), nullable=True),
        sa.Column('weight_uom', sa.String(length=10), nullable=True),  # kg, lb
        sa.Column('total_volume', sa.Float(), nullable=True),
        sa.Column('volume_uom', sa.String(length=10), nullable=True),  # m3, ft3

        # Additional info
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('special_instructions', sa.Text(), nullable=True),

        # Metadata (JSONB)
        # {
        #   "documents": [...],
        #   "customs_info": {...},
        #   "insurance": {...},
        #   "cost": {...}
        # }
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('packed_by', sa.Integer(), nullable=True),
        sa.Column('shipped_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['destination_plant_id'], ['plants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['packed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['shipped_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'plant_id', 'shipment_number',
                           name='uq_shipment_number_per_plant'),
        sa.Index('idx_shipments_org', 'organization_id'),
        sa.Index('idx_shipments_plant', 'plant_id'),
        sa.Index('idx_shipments_status', 'status'),
        sa.Index('idx_shipments_type', 'shipment_type'),
        sa.Index('idx_shipments_tracking', 'tracking_number'),
        sa.Index('idx_shipments_dates', 'planned_ship_date', 'actual_ship_date'),
        sa.CheckConstraint(
            "shipment_type IN ('outbound', 'inbound', 'inter_plant')",
            name='chk_shipment_type_valid'
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'packed', 'shipped', 'in_transit', 'delivered', 'cancelled')",
            name='chk_shipment_status_valid'
        ),
    )

    # Create shipment_items table
    op.create_table(
        'shipment_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('shipment_id', sa.Integer(), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),

        # Item details
        sa.Column('material_id', sa.Integer(), nullable=True),
        sa.Column('work_order_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('item_description', sa.String(length=200), nullable=False),

        # Quantity
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('uom', sa.String(length=20), nullable=False),

        # Packaging
        sa.Column('package_number', sa.String(length=50), nullable=True),
        sa.Column('package_type', sa.String(length=50), nullable=True),  # box, pallet, crate, container
        sa.Column('package_weight', sa.Float(), nullable=True),
        sa.Column('package_dimensions', sa.String(length=50), nullable=True),  # LxWxH

        # Lot/Serial tracking
        sa.Column('lot_number', sa.String(length=50), nullable=True),
        sa.Column('serial_numbers', postgresql.ARRAY(sa.String()), nullable=True),

        # QR/Barcode
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('qr_code', sa.String(length=200), nullable=True),

        # Status
        sa.Column('is_packed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('packed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('packed_by', sa.Integer(), nullable=True),

        # Metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['material.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_order.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['packed_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('shipment_id', 'line_number', name='uq_line_number_per_shipment'),
        sa.Index('idx_shipment_items_org', 'organization_id'),
        sa.Index('idx_shipment_items_shipment', 'shipment_id'),
        sa.Index('idx_shipment_items_material', 'material_id'),
        sa.Index('idx_shipment_items_barcode', 'barcode'),
        sa.Index('idx_shipment_items_lot', 'lot_number'),
    )

    # Create barcode_labels table
    op.create_table(
        'barcode_labels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),

        # Entity reference
        sa.Column('entity_type', sa.String(length=50), nullable=False),  # material, work_order, shipment, package
        sa.Column('entity_id', sa.Integer(), nullable=False),

        # Barcode details
        sa.Column('barcode_type', sa.String(length=50), nullable=False),  # code128, qr_code, ean13, datamatrix
        sa.Column('barcode_value', sa.String(length=200), nullable=False),
        sa.Column('barcode_data', sa.Text(), nullable=True),  # Base64 encoded image

        # Label info
        sa.Column('label_format', sa.String(length=50), nullable=True),  # 4x6, 2x1, custom
        sa.Column('label_template', sa.String(length=100), nullable=True),

        # Status
        sa.Column('is_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_printed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('printed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('printed_by', sa.Integer(), nullable=True),
        sa.Column('print_count', sa.Integer(), nullable=False, server_default='0'),

        # Storage
        sa.Column('file_path', sa.String(length=500), nullable=True),  # MinIO path
        sa.Column('file_url', sa.String(length=500), nullable=True),  # Presigned URL

        # Metadata
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['printed_by'], ['users.id'], ondelete='SET NULL'),
        sa.Index('idx_barcode_labels_org', 'organization_id'),
        sa.Index('idx_barcode_labels_plant', 'plant_id'),
        sa.Index('idx_barcode_labels_entity', 'entity_type', 'entity_id'),
        sa.Index('idx_barcode_labels_value', 'barcode_value'),
        sa.CheckConstraint(
            "barcode_type IN ('code128', 'qr_code', 'ean13', 'ean8', 'datamatrix', 'pdf417')",
            name='chk_barcode_type_valid'
        ),
    )

    # Create qr_code_scans table (timescaledb hypertable for time-series)
    op.create_table(
        'qr_code_scans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),

        # Scan details
        sa.Column('scanned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('scanned_by', sa.Integer(), nullable=False),
        sa.Column('scan_type', sa.String(length=50), nullable=False),  # barcode, qr_code
        sa.Column('scan_value', sa.String(length=200), nullable=False),

        # Resolved entity
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('resolution_status', sa.String(length=50), nullable=False),  # resolved, not_found, error

        # Context
        sa.Column('operation_type', sa.String(length=50), nullable=True),  # receiving, shipping, inventory, production
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),  # mobile, tablet, scanner

        # GPS location (optional)
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),

        # Metadata
        # {
        #   "work_order_id": 123,
        #   "shipment_id": 456,
        #   "action_taken": "received",
        #   "quantity": 100
        # }
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scanned_by'], ['users.id'], ondelete='CASCADE'),
        sa.Index('idx_qr_scans_org', 'organization_id'),
        sa.Index('idx_qr_scans_plant', 'plant_id'),
        sa.Index('idx_qr_scans_user', 'scanned_by'),
        sa.Index('idx_qr_scans_time', 'scanned_at'),
        sa.Index('idx_qr_scans_value', 'scan_value'),
        sa.Index('idx_qr_scans_entity', 'entity_type', 'entity_id'),
        # GIN index for JSONB metadata
        sa.Index('idx_qr_scans_metadata_gin', 'metadata', postgresql_using='gin'),
        sa.CheckConstraint(
            "resolution_status IN ('resolved', 'not_found', 'error', 'duplicate')",
            name='chk_scan_resolution_valid'
        ),
    )

    # Enable RLS on all tables
    op.execute("ALTER TABLE shipments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE shipment_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE barcode_labels ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE qr_code_scans ENABLE ROW LEVEL SECURITY")

    # Create RLS policies
    op.execute("""
        CREATE POLICY shipments_org_isolation ON shipments
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY shipment_items_org_isolation ON shipment_items
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY barcode_labels_org_isolation ON barcode_labels
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    op.execute("""
        CREATE POLICY qr_code_scans_org_isolation ON qr_code_scans
        USING (organization_id = current_setting('app.current_organization_id', true)::int)
    """)

    # Convert qr_code_scans to TimescaleDB hypertable (for time-series optimization)
    op.execute("""
        SELECT create_hypertable('qr_code_scans', 'scanned_at',
                                 chunk_time_interval => INTERVAL '1 day',
                                 if_not_exists => TRUE)
    """)

    # Add compression policy for qr_code_scans (compress data older than 7 days)
    op.execute("""
        SELECT add_compression_policy('qr_code_scans', INTERVAL '7 days', if_not_exists => TRUE)
    """)

    # Add retention policy (keep data for 2 years)
    op.execute("""
        SELECT add_retention_policy('qr_code_scans', INTERVAL '2 years', if_not_exists => TRUE)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS shipments_org_isolation ON shipments")
    op.execute("DROP POLICY IF EXISTS shipment_items_org_isolation ON shipment_items")
    op.execute("DROP POLICY IF EXISTS barcode_labels_org_isolation ON barcode_labels")
    op.execute("DROP POLICY IF EXISTS qr_code_scans_org_isolation ON qr_code_scans")

    # Drop tables
    op.drop_table('qr_code_scans')
    op.drop_table('barcode_labels')
    op.drop_table('shipment_items')
    op.drop_table('shipments')
