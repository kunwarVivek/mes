"""Add missing columns to existing tables for functional debt resolution

Revision ID: 021
Revises: 020
Create Date: 2025-11-12

This migration adds critical missing columns identified in functional debt audit:
- materials: barcode_data, qr_code_data, sap_material_number, stock levels
- projects: customer info, sap_sales_order, budget
- machines: machine_type, status, current_work_order_id
- organizations: industry, address, contact info
- plants: plant_type, manager_user_id
- ncr_reports: ncr_type, corrective_action, preventive_action
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    print("Adding missing columns to existing tables...")

    # 1. ADD COLUMNS TO materials TABLE
    print("  → Adding columns to materials table...")
    op.add_column('materials', sa.Column('barcode_data', sa.String(255), nullable=True))
    op.add_column('materials', sa.Column('qr_code_data', sa.Text(), nullable=True))
    op.add_column('materials', sa.Column('sap_material_number', sa.String(100), nullable=True))
    op.add_column('materials', sa.Column('minimum_stock_level', sa.Integer(), nullable=True))
    op.add_column('materials', sa.Column('maximum_stock_level', sa.Integer(), nullable=True))
    op.add_column('materials', sa.Column('standard_cost', sa.Numeric(15, 2), nullable=True))
    op.add_column('materials', sa.Column('last_cost', sa.Numeric(15, 2), nullable=True))
    op.add_column('materials', sa.Column('average_cost', sa.Numeric(15, 2), nullable=True))

    # Add indexes for materials
    op.create_index('idx_materials_barcode', 'materials', ['barcode_data'],
                   postgresql_where=sa.text('barcode_data IS NOT NULL'))
    op.create_index('idx_materials_qr', 'materials', ['qr_code_data'],
                   postgresql_where=sa.text('qr_code_data IS NOT NULL'))
    op.create_index('idx_materials_sap', 'materials', ['sap_material_number'],
                   postgresql_where=sa.text('sap_material_number IS NOT NULL'))

    # Add check constraint for stock levels
    op.create_check_constraint(
        'ck_materials_stock_levels',
        'materials',
        'minimum_stock_level IS NULL OR maximum_stock_level IS NULL OR minimum_stock_level <= maximum_stock_level'
    )

    # Add full-text search index for materials (using pg_trgm if pg_search not available)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_materials_search ON materials
        USING gin(to_tsvector('english',
            COALESCE(material_number, '') || ' ' ||
            COALESCE(name, '') || ' ' ||
            COALESCE(description, '')));
    """)

    # 2. ADD COLUMNS TO projects TABLE
    print("  → Adding columns to projects table...")
    op.add_column('projects', sa.Column('customer_name', sa.String(255), nullable=True))
    op.add_column('projects', sa.Column('customer_code', sa.String(100), nullable=True))
    op.add_column('projects', sa.Column('sap_sales_order', sa.String(100), nullable=True))
    op.add_column('projects', sa.Column('project_manager_id', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('budget', sa.Numeric(15, 2), nullable=True))
    op.add_column('projects', sa.Column('actual_cost', sa.Numeric(15, 2), nullable=True))

    # Add foreign key for project_manager
    op.create_foreign_key(
        'fk_projects_project_manager',
        'projects', 'users',
        ['project_manager_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for projects
    op.create_index('idx_projects_sap_so', 'projects', ['sap_sales_order'],
                   postgresql_where=sa.text('sap_sales_order IS NOT NULL'))
    op.create_index('idx_projects_manager', 'projects', ['project_manager_id'],
                   postgresql_where=sa.text('project_manager_id IS NOT NULL'))
    op.create_index('idx_projects_customer', 'projects', ['customer_name'],
                   postgresql_where=sa.text('customer_name IS NOT NULL'))

    # Add full-text search index for projects
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_projects_search ON projects
        USING gin(to_tsvector('english',
            COALESCE(project_code, '') || ' ' ||
            COALESCE(name, '') || ' ' ||
            COALESCE(customer_name, '') || ' ' ||
            COALESCE(description, '')));
    """)

    # 3. ADD COLUMNS TO machines TABLE
    print("  → Adding columns to machines table...")
    op.add_column('machines', sa.Column('machine_type', sa.String(100), nullable=True))
    op.add_column('machines', sa.Column('status', sa.String(50), nullable=True,
                                        server_default='available'))
    op.add_column('machines', sa.Column('current_work_order_id', sa.Integer(), nullable=True))
    op.add_column('machines', sa.Column('manufacturer', sa.String(255), nullable=True))
    op.add_column('machines', sa.Column('model_number', sa.String(100), nullable=True))
    op.add_column('machines', sa.Column('serial_number', sa.String(100), nullable=True))
    op.add_column('machines', sa.Column('installation_date', sa.Date(), nullable=True))
    op.add_column('machines', sa.Column('purchase_cost', sa.Numeric(12, 2), nullable=True))
    op.add_column('machines', sa.Column('location', sa.String(255), nullable=True))

    # Add foreign key for current_work_order
    op.create_foreign_key(
        'fk_machines_current_wo',
        'machines', 'work_orders',
        ['current_work_order_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for machines
    op.create_index('idx_machines_status', 'machines', ['status'])
    op.create_index('idx_machines_type', 'machines', ['machine_type'],
                   postgresql_where=sa.text('machine_type IS NOT NULL'))
    op.create_index('idx_machines_current_wo', 'machines', ['current_work_order_id'],
                   postgresql_where=sa.text('current_work_order_id IS NOT NULL'))

    # Add check constraint for machine status
    op.create_check_constraint(
        'ck_machines_status',
        'machines',
        "status IN ('available', 'running', 'idle', 'setup', 'down', 'maintenance', 'offline')"
    )

    # Add full-text search index for machines
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_machines_search ON machines
        USING gin(to_tsvector('english',
            COALESCE(machine_code, '') || ' ' ||
            COALESCE(name, '') || ' ' ||
            COALESCE(machine_type, '') || ' ' ||
            COALESCE(manufacturer, '') || ' ' ||
            COALESCE(model_number, '')));
    """)

    # 4. ADD COLUMNS TO organizations TABLE
    print("  → Adding columns to organizations table...")
    op.add_column('organizations', sa.Column('industry', sa.String(100), nullable=True))
    op.add_column('organizations', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('contact_email', sa.String(255), nullable=True))
    op.add_column('organizations', sa.Column('contact_phone', sa.String(50), nullable=True))
    op.add_column('organizations', sa.Column('company_size', sa.String(50), nullable=True))
    op.add_column('organizations', sa.Column('timezone', sa.String(100), nullable=True,
                                              server_default='UTC'))

    # Add full-text search index for organizations
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_organizations_search ON organizations
        USING gin(to_tsvector('english',
            COALESCE(org_name, '') || ' ' ||
            COALESCE(org_code, '') || ' ' ||
            COALESCE(industry, '')));
    """)

    # 5. ADD COLUMNS TO plants TABLE
    print("  → Adding columns to plants table...")
    op.add_column('plants', sa.Column('plant_type', sa.String(50), nullable=True))
    op.add_column('plants', sa.Column('manager_user_id', sa.Integer(), nullable=True))

    # Add foreign key for plant manager
    op.create_foreign_key(
        'fk_plants_manager',
        'plants', 'users',
        ['manager_user_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add index and constraint for plant_type
    op.create_index('idx_plants_type', 'plants', ['plant_type'],
                   postgresql_where=sa.text("is_active = true AND plant_type IS NOT NULL"))

    op.create_check_constraint(
        'ck_plants_type',
        'plants',
        "plant_type IN ('fabrication', 'production', 'assembly', 'testing', 'warehouse', 'r_and_d')"
    )

    # 6. ADD COLUMNS TO ncr_reports TABLE
    print("  → Adding columns to ncr_reports table...")
    op.add_column('ncr_reports', sa.Column('ncr_type', sa.String(50), nullable=True))
    op.add_column('ncr_reports', sa.Column('corrective_action', sa.Text(), nullable=True))
    op.add_column('ncr_reports', sa.Column('preventive_action', sa.Text(), nullable=True))
    op.add_column('ncr_reports', sa.Column('customer_affected', sa.Boolean(), nullable=True,
                                            server_default='false'))
    op.add_column('ncr_reports', sa.Column('supplier_id', sa.Integer(), nullable=True))

    # Add foreign key for supplier
    op.create_foreign_key(
        'fk_ncr_reports_supplier',
        'ncr_reports', 'suppliers',
        ['supplier_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for ncr_reports
    op.create_index('idx_ncr_reports_type', 'ncr_reports', ['ncr_type'],
                   postgresql_where=sa.text('ncr_type IS NOT NULL'))
    op.create_index('idx_ncr_reports_supplier', 'ncr_reports', ['supplier_id'],
                   postgresql_where=sa.text('supplier_id IS NOT NULL'))

    # Add check constraint for ncr_type
    op.create_check_constraint(
        'ck_ncr_reports_type',
        'ncr_reports',
        "ncr_type IN ('material', 'process', 'final_inspection', 'customer_complaint', 'supplier_issue')"
    )

    # Add full-text search index for ncr_reports
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ncr_reports_search ON ncr_reports
        USING gin(to_tsvector('english',
            COALESCE(ncr_number, '') || ' ' ||
            COALESCE(description, '') || ' ' ||
            COALESCE(root_cause, '')));
    """)

    # 7. ADD COLUMNS TO work_orders TABLE
    print("  → Adding columns to work_orders table...")
    op.add_column('work_orders', sa.Column('sap_production_order', sa.String(100), nullable=True))
    op.add_column('work_orders', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('work_orders', sa.Column('department_id', sa.Integer(), nullable=True))
    op.add_column('work_orders', sa.Column('operation_type', sa.String(100), nullable=True))

    # Add foreign key for department
    op.create_foreign_key(
        'fk_work_orders_department',
        'work_orders', 'departments',
        ['department_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for work_orders
    op.create_index('idx_work_orders_sap', 'work_orders', ['sap_production_order'],
                   postgresql_where=sa.text('sap_production_order IS NOT NULL'))
    op.create_index('idx_work_orders_department', 'work_orders', ['department_id'],
                   postgresql_where=sa.text('department_id IS NOT NULL'))

    # Add full-text search index for work_orders
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_work_orders_search ON work_orders
        USING gin(to_tsvector('english',
            COALESCE(work_order_number, '') || ' ' ||
            COALESCE(description, '')));
    """)

    print("✅ Successfully added missing columns to 7 tables:")
    print("   - materials (8 columns + indexes)")
    print("   - projects (6 columns + indexes)")
    print("   - machines (9 columns + indexes)")
    print("   - organizations (6 columns + indexes)")
    print("   - plants (2 columns + indexes)")
    print("   - ncr_reports (5 columns + indexes)")
    print("   - work_orders (4 columns + indexes)")


def downgrade():
    # Remove columns in reverse order
    print("Removing added columns from tables...")

    # work_orders
    op.drop_constraint('fk_work_orders_department', 'work_orders', type_='foreignkey')
    op.drop_index('idx_work_orders_sap', 'work_orders')
    op.drop_index('idx_work_orders_department', 'work_orders')
    op.drop_index('idx_work_orders_search', 'work_orders')
    op.drop_column('work_orders', 'operation_type')
    op.drop_column('work_orders', 'department_id')
    op.drop_column('work_orders', 'description')
    op.drop_column('work_orders', 'sap_production_order')

    # ncr_reports
    op.drop_constraint('fk_ncr_reports_supplier', 'ncr_reports', type_='foreignkey')
    op.drop_constraint('ck_ncr_reports_type', 'ncr_reports', type_='check')
    op.drop_index('idx_ncr_reports_type', 'ncr_reports')
    op.drop_index('idx_ncr_reports_supplier', 'ncr_reports')
    op.drop_index('idx_ncr_reports_search', 'ncr_reports')
    op.drop_column('ncr_reports', 'supplier_id')
    op.drop_column('ncr_reports', 'customer_affected')
    op.drop_column('ncr_reports', 'preventive_action')
    op.drop_column('ncr_reports', 'corrective_action')
    op.drop_column('ncr_reports', 'ncr_type')

    # plants
    op.drop_constraint('fk_plants_manager', 'plants', type_='foreignkey')
    op.drop_constraint('ck_plants_type', 'plants', type_='check')
    op.drop_index('idx_plants_type', 'plants')
    op.drop_column('plants', 'manager_user_id')
    op.drop_column('plants', 'plant_type')

    # organizations
    op.drop_index('idx_organizations_search', 'organizations')
    op.drop_column('organizations', 'timezone')
    op.drop_column('organizations', 'company_size')
    op.drop_column('organizations', 'contact_phone')
    op.drop_column('organizations', 'contact_email')
    op.drop_column('organizations', 'address')
    op.drop_column('organizations', 'industry')

    # machines
    op.drop_constraint('fk_machines_current_wo', 'machines', type_='foreignkey')
    op.drop_constraint('ck_machines_status', 'machines', type_='check')
    op.drop_index('idx_machines_status', 'machines')
    op.drop_index('idx_machines_type', 'machines')
    op.drop_index('idx_machines_current_wo', 'machines')
    op.drop_index('idx_machines_search', 'machines')
    op.drop_column('machines', 'location')
    op.drop_column('machines', 'purchase_cost')
    op.drop_column('machines', 'installation_date')
    op.drop_column('machines', 'serial_number')
    op.drop_column('machines', 'model_number')
    op.drop_column('machines', 'manufacturer')
    op.drop_column('machines', 'current_work_order_id')
    op.drop_column('machines', 'status')
    op.drop_column('machines', 'machine_type')

    # projects
    op.drop_constraint('fk_projects_project_manager', 'projects', type_='foreignkey')
    op.drop_index('idx_projects_sap_so', 'projects')
    op.drop_index('idx_projects_manager', 'projects')
    op.drop_index('idx_projects_customer', 'projects')
    op.drop_index('idx_projects_search', 'projects')
    op.drop_column('projects', 'actual_cost')
    op.drop_column('projects', 'budget')
    op.drop_column('projects', 'project_manager_id')
    op.drop_column('projects', 'sap_sales_order')
    op.drop_column('projects', 'customer_code')
    op.drop_column('projects', 'customer_name')

    # materials
    op.drop_constraint('ck_materials_stock_levels', 'materials', type_='check')
    op.drop_index('idx_materials_barcode', 'materials')
    op.drop_index('idx_materials_qr', 'materials')
    op.drop_index('idx_materials_sap', 'materials')
    op.drop_index('idx_materials_search', 'materials')
    op.drop_column('materials', 'average_cost')
    op.drop_column('materials', 'last_cost')
    op.drop_column('materials', 'standard_cost')
    op.drop_column('materials', 'maximum_stock_level')
    op.drop_column('materials', 'minimum_stock_level')
    op.drop_column('materials', 'sap_material_number')
    op.drop_column('materials', 'qr_code_data')
    op.drop_column('materials', 'barcode_data')
