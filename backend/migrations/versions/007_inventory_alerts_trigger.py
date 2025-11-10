"""Inventory Alerts Trigger and LISTEN/NOTIFY

Revision ID: 007_inventory_alerts
Revises: 006_configure_pg_cron
Create Date: 2025-11-10 19:00:00.000000

Creates infrastructure for real-time inventory alerts:
1. inventory_alerts table for alert history
2. Trigger function to detect low stock conditions
3. PostgreSQL LISTEN/NOTIFY for real-time WebSocket notifications
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_inventory_alerts'
down_revision = '006_configure_pg_cron'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create inventory alerts infrastructure.

    Business Rules:
    - Alert when quantity_on_hand <= reorder_point
    - Alert when quantity_on_hand crosses back above reorder_point (restocked)
    - Alert severity based on how far below reorder point
    """
    conn = op.get_bind()

    # ========================================================================
    # 1. Create inventory_alerts table
    # ========================================================================
    print("Creating inventory_alerts table...")

    op.create_table(
        'inventory_alerts',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('storage_location_id', sa.Integer(), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),  # LOW_STOCK, RESTOCKED, OUT_OF_STOCK
        sa.Column('severity', sa.String(20), nullable=False),  # INFO, WARNING, CRITICAL
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('quantity_on_hand', sa.Numeric(15, 4), nullable=False),
        sa.Column('reorder_point', sa.Numeric(15, 4), nullable=True),
        sa.Column('max_stock_level', sa.Numeric(15, 4), nullable=True),
        sa.Column('is_acknowledged', sa.Boolean(), default=False, nullable=False),
        sa.Column('acknowledged_by_user_id', sa.Integer(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('ix_inventory_alerts_material_id', 'inventory_alerts', ['material_id'])
    op.create_index('ix_inventory_alerts_organization_plant', 'inventory_alerts', ['organization_id', 'plant_id'])
    op.create_index('ix_inventory_alerts_is_acknowledged', 'inventory_alerts', ['is_acknowledged'])
    op.create_index('ix_inventory_alerts_created_at', 'inventory_alerts', ['created_at'])

    # Add foreign keys
    op.create_foreign_key(
        'fk_inventory_alerts_organization',
        'inventory_alerts', 'organization',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_inventory_alerts_plant',
        'inventory_alerts', 'plant',
        ['plant_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_inventory_alerts_material',
        'inventory_alerts', 'material',
        ['material_id'], ['id'],
        ondelete='CASCADE'
    )

    print("  ✓ inventory_alerts table created")

    # ========================================================================
    # 2. Enable RLS on inventory_alerts
    # ========================================================================
    print("Enabling RLS on inventory_alerts...")

    conn.execute(text("""
        ALTER TABLE inventory_alerts ENABLE ROW LEVEL SECURITY;
    """))

    conn.execute(text("""
        CREATE POLICY inventory_alerts_organization_isolation ON inventory_alerts
        FOR ALL
        USING (
            organization_id = current_setting('app.current_organization_id', TRUE)::INTEGER
            AND (
                current_setting('app.current_plant_id', TRUE) IS NULL
                OR plant_id = current_setting('app.current_plant_id', TRUE)::INTEGER
            )
        );
    """))

    print("  ✓ RLS policies created")

    # ========================================================================
    # 3. Create trigger function for inventory alerts
    # ========================================================================
    print("Creating inventory alert trigger function...")

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION check_inventory_alerts()
        RETURNS TRIGGER AS $$
        DECLARE
            v_material RECORD;
            v_alert_type VARCHAR(50);
            v_severity VARCHAR(20);
            v_message TEXT;
            v_should_alert BOOLEAN := FALSE;
        BEGIN
            -- Get material information
            SELECT m.material_code, m.description, m.reorder_point, m.max_stock_level
            INTO v_material
            FROM material m
            WHERE m.id = NEW.material_id;

            -- Skip if material has no reorder point configured
            IF v_material.reorder_point IS NULL THEN
                RETURN NEW;
            END IF;

            -- Determine alert conditions
            IF NEW.quantity_on_hand <= 0 THEN
                -- Out of stock
                v_alert_type := 'OUT_OF_STOCK';
                v_severity := 'CRITICAL';
                v_message := format(
                    'Material %s (%s) is OUT OF STOCK in location %s',
                    v_material.material_code,
                    v_material.description,
                    NEW.storage_location_id
                );
                v_should_alert := TRUE;

            ELSIF NEW.quantity_on_hand <= v_material.reorder_point THEN
                -- Below reorder point
                v_alert_type := 'LOW_STOCK';

                -- Severity based on how far below reorder point
                IF NEW.quantity_on_hand <= (v_material.reorder_point * 0.5) THEN
                    v_severity := 'CRITICAL';
                ELSIF NEW.quantity_on_hand <= (v_material.reorder_point * 0.75) THEN
                    v_severity := 'WARNING';
                ELSE
                    v_severity := 'INFO';
                END IF;

                v_message := format(
                    'Material %s (%s) is below reorder point. Current: %.2f, Reorder Point: %.2f',
                    v_material.material_code,
                    v_material.description,
                    NEW.quantity_on_hand,
                    v_material.reorder_point
                );
                v_should_alert := TRUE;

            ELSIF OLD.quantity_on_hand <= v_material.reorder_point
                  AND NEW.quantity_on_hand > v_material.reorder_point THEN
                -- Restocked (crossed back above reorder point)
                v_alert_type := 'RESTOCKED';
                v_severity := 'INFO';
                v_message := format(
                    'Material %s (%s) has been restocked. Current: %.2f, Reorder Point: %.2f',
                    v_material.material_code,
                    v_material.description,
                    NEW.quantity_on_hand,
                    v_material.reorder_point
                );
                v_should_alert := TRUE;
            END IF;

            -- Create alert if conditions met
            IF v_should_alert THEN
                INSERT INTO inventory_alerts (
                    organization_id,
                    plant_id,
                    material_id,
                    storage_location_id,
                    alert_type,
                    severity,
                    message,
                    quantity_on_hand,
                    reorder_point,
                    max_stock_level,
                    is_acknowledged
                ) VALUES (
                    NEW.organization_id,
                    NEW.plant_id,
                    NEW.material_id,
                    NEW.storage_location_id,
                    v_alert_type,
                    v_severity,
                    v_message,
                    NEW.quantity_on_hand,
                    v_material.reorder_point,
                    v_material.max_stock_level,
                    FALSE
                );

                -- Send NOTIFY for WebSocket clients
                PERFORM pg_notify(
                    'inventory_alerts',
                    json_build_object(
                        'alert_type', v_alert_type,
                        'severity', v_severity,
                        'material_id', NEW.material_id,
                        'material_code', v_material.material_code,
                        'message', v_message,
                        'quantity_on_hand', NEW.quantity_on_hand,
                        'reorder_point', v_material.reorder_point,
                        'organization_id', NEW.organization_id,
                        'plant_id', NEW.plant_id,
                        'timestamp', NOW()
                    )::TEXT
                );
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    print("  ✓ Trigger function created")

    # ========================================================================
    # 4. Create trigger on inventory table
    # ========================================================================
    print("Creating inventory update trigger...")

    conn.execute(text("""
        CREATE TRIGGER trg_inventory_alerts
        AFTER UPDATE OF quantity_on_hand ON inventory
        FOR EACH ROW
        WHEN (OLD.quantity_on_hand IS DISTINCT FROM NEW.quantity_on_hand)
        EXECUTE FUNCTION check_inventory_alerts();
    """))

    print("  ✓ Trigger created on inventory table")

    print("\n✅ Inventory alerts infrastructure created successfully!")
    print("   - Real-time alerts via pg_notify on 'inventory_alerts' channel")
    print("   - Alert history stored in inventory_alerts table")
    print("   - Triggers on inventory.quantity_on_hand changes")


def downgrade() -> None:
    """Remove inventory alerts infrastructure"""
    conn = op.get_bind()

    print("Removing inventory alerts infrastructure...")

    # Drop trigger
    try:
        conn.execute(text("DROP TRIGGER IF EXISTS trg_inventory_alerts ON inventory;"))
        print("  ✓ Trigger dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop trigger: {e}")

    # Drop function
    try:
        conn.execute(text("DROP FUNCTION IF EXISTS check_inventory_alerts();"))
        print("  ✓ Function dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop function: {e}")

    # Drop table
    try:
        op.drop_table('inventory_alerts')
        print("  ✓ Table dropped")
    except Exception as e:
        print(f"  ✗ Failed to drop table: {e}")

    print("\n✅ Inventory alerts infrastructure removed")
