#!/usr/bin/env python3
"""
Generate SQL Schema Files from SQLAlchemy Models

This script reads SQLAlchemy models and generates clean SQL schema files
organized by domain/module. This is useful for:
- Initial database setup
- Documentation
- Schema review and auditing
- Migration consolidation

Usage:
    python generate_schema.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql

# Import all models to register them with Base
from app.core.database import Base
import app.models  # This imports all models via __init__.py


# Define schema file organization
SCHEMA_MODULES = {
    '02_materials.sql': [
        'materials', 'material_categories', 'units_of_measure',
        'bom_headers', 'bom_lines'
    ],
    '03_production.sql': [
        'work_orders', 'work_order_operations', 'work_centers',
        'work_order_materials', 'rework_configs', 'production_logs',
        'work_center_shifts'
    ],
    '04_quality.sql': [
        'ncrs', 'inspection_logs',
        'inspection_plans', 'inspection_points', 'inspection_characteristics',
        'inspection_measurements'
    ],
    '05_machines_shifts.sql': [
        'machines', 'machine_status_history',
        'shifts', 'shift_handovers', 'shift_performances',
        'lanes', 'lane_assignments'
    ],
    '06_projects.sql': [
        'project_documents', 'project_milestones',
        'rda_drawings', 'project_bom'
    ],
    '07_rbac.sql': [
        'roles', 'user_roles', 'user_plant_access'
    ],
    '08_configuration.sql': [
        'custom_fields', 'field_values', 'type_lists', 'type_list_values',
        'workflows', 'workflow_states', 'workflow_transitions',
        'approvals', 'workflow_history'
    ],
    '09_logistics.sql': [
        'shipments', 'shipment_items', 'barcode_labels', 'qr_code_scans'
    ],
    '10_reporting.sql': [
        'reports', 'report_executions', 'dashboards'
    ],
    '11_traceability.sql': [
        'lot_batches', 'serial_numbers', 'traceability_links', 'genealogy_records'
    ],
    '12_branding.sql': [
        'organization_branding', 'email_templates'
    ],
    '13_infrastructure.sql': [
        'audit_logs', 'notifications', 'system_settings',
        'file_uploads', 'sap_sync_logs', 'sap_mappings'
    ],
}


def get_table_sql(table) -> str:
    """Generate CREATE TABLE SQL for a table"""
    create_table = CreateTable(table).compile(dialect=postgresql.dialect())
    return str(create_table).strip() + ';\n'


def get_index_sql(table) -> List[str]:
    """Generate CREATE INDEX SQL for table indexes"""
    indexes = []
    for index in table.indexes:
        create_index = CreateIndex(index).compile(dialect=postgresql.dialect())
        indexes.append(str(create_index).strip() + ';\n')
    return indexes


def generate_schema_file(filename: str, table_names: List[str], metadata: MetaData) -> str:
    """Generate SQL content for a schema file"""
    lines = []

    # Header
    module_name = filename.replace('.sql', '').replace('_', ' ').title()
    lines.append(f"-- {module_name}")
    lines.append(f"-- Auto-generated from SQLAlchemy models\n\n")

    # Find tables
    tables_found = []
    for table_name in table_names:
        if table_name in metadata.tables:
            tables_found.append(metadata.tables[table_name])
        else:
            lines.append(f"-- WARNING: Table '{table_name}' not found in metadata\n")

    # Generate SQL for each table
    for table in tables_found:
        lines.append(f"\n-- {table.name.upper()} TABLE\n")
        lines.append(f"-- {'-' * 60}\n")

        # Table creation
        lines.append(get_table_sql(table))
        lines.append('\n')

        # Indexes
        index_sqls = get_index_sql(table)
        if index_sqls:
            lines.append("-- Indexes\n")
            for idx_sql in index_sqls:
                lines.append(idx_sql)
            lines.append('\n')

        # Comments
        if table.comment:
            lines.append(f"COMMENT ON TABLE {table.name} IS '{table.comment}';\n\n")

    return ''.join(lines)


def generate_rls_policies(metadata: MetaData) -> str:
    """Generate RLS policies for all tables with organization_id"""
    lines = []
    lines.append("-- Row-Level Security (RLS) Policies\n")
    lines.append("-- Multi-tenant isolation based on organization_id\n\n")

    for table_name, table in metadata.tables.items():
        # Check if table has organization_id column
        if 'organization_id' in table.c:
            lines.append(f"-- Enable RLS on {table_name}\n")
            lines.append(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;\n\n")

            lines.append(f"-- Organization isolation policy for {table_name}\n")
            lines.append(f"CREATE POLICY {table_name}_org_isolation ON {table_name}\n")
            lines.append(f"    USING (organization_id = current_setting('app.current_organization_id', true)::int);\n\n")

    return ''.join(lines)


def main():
    """Main execution"""
    print("=" * 70)
    print("SQL Schema Generator from SQLAlchemy Models")
    print("=" * 70)
    print()

    # Get metadata from Base
    metadata = Base.metadata

    print(f"Found {len(metadata.tables)} tables in metadata:")
    for table_name in sorted(metadata.tables.keys()):
        print(f"  - {table_name}")
    print()

    # Create schema directory
    schema_dir = Path(__file__).parent / 'schema'
    schema_dir.mkdir(exist_ok=True)
    print(f"Schema directory: {schema_dir}")
    print()

    # Generate each schema file
    for filename, table_names in SCHEMA_MODULES.items():
        filepath = schema_dir / filename
        print(f"Generating {filename}...")

        content = generate_schema_file(filename, table_names, metadata)

        with open(filepath, 'w') as f:
            f.write(content)

        print(f"  ✓ Created {filepath} ({len(content)} bytes)")

    # Generate RLS policies file
    print("\nGenerating RLS policies...")
    rls_content = generate_rls_policies(metadata)
    rls_filepath = schema_dir / '99_rls_policies.sql'

    with open(rls_filepath, 'w') as f:
        f.write(rls_content)

    print(f"  ✓ Created {rls_filepath} ({len(rls_content)} bytes)")

    print()
    print("=" * 70)
    print("Schema generation complete!")
    print("=" * 70)
    print()
    print("To initialize a fresh database:")
    print(f"  psql -U postgres -d mes_db -f {schema_dir}/init_schema.sql")


if __name__ == '__main__':
    main()
