# MES Database Schema

This directory contains SQL schema files for documentation and reference purposes.

## Approach

For this new SaaS application, we use a **consolidated migration approach** instead of accumulating many migration files:

1. **Single Initial Migration**: `migrations/versions/001_initial_schema.py`
   - Creates all tables from SQLAlchemy models using `Base.metadata.create_all()`
   - Converts time-series tables to TimescaleDB hypertables
   - Applies Row-Level Security (RLS) policies for multi-tenant isolation
   - Clean, comprehensive, and easy to understand

2. **Future Changes**: Use incremental alembic migrations as needed
   - `alembic revision --autogenerate -m "description"`
   - Keep migrations focused and atomic

3. **SQL Schema Files**: Reference documentation (optional)
   - Generated from SQLAlchemy models for documentation
   - Can be used to understand database structure
   - Not used for actual database creation (migrations handle that)

## Database Initialization

### Fresh Database Setup

```bash
# Create database
createdb mes_db

# Run migrations
cd backend
alembic upgrade head
```

This will:
1. Install PostgreSQL extensions (TimescaleDB, uuid-ossp, pgcrypto, pg_trgm)
2. Create all tables from SQLAlchemy models
3. Set up TimescaleDB hypertables for time-series data
4. Enable Row-Level Security policies for multi-tenant isolation

### Schema Generation (Optional)

To generate SQL schema files from models for documentation:

```bash
cd backend
python database/generate_schema.py
```

This creates/updates SQL files in `database/schema/`:
- `02_materials.sql` through `13_infrastructure.sql`
- `99_rls_policies.sql`

## Tables Overview

### Core (01_core.sql)
- `organizations` - Top-level tenants
- `users` - System users
- `plants` - Manufacturing sites
- `departments` - Functional units
- `projects` - Project management

### Materials (02_materials.sql)
- `materials` - Material master data
- `material_categories` - Material categorization
- `units_of_measure` - UoM definitions
- `bom_headers`, `bom_lines` - Bill of Materials

### Production (03_production.sql)
- `work_orders` - Manufacturing orders
- `work_order_operations` - Operation sequences
- `work_centers` - Production resources
- `work_order_materials` - Material requirements
- `rework_configs` - Rework configurations
- `production_logs` - Production tracking (TimescaleDB)
- `work_center_shifts` - Shift assignments

### Quality (04_quality.sql)
- `ncrs` - Non-Conformance Reports
- `inspection_logs` - Basic inspections
- `inspection_plans` - Quality plans
- `inspection_points` - Checkpoint definitions
- `inspection_characteristics` - Measurable characteristics
- `inspection_measurements` - SPC data (TimescaleDB)

### Machines & Shifts (05_machines_shifts.sql)
- `machines` - Equipment master
- `machine_status_history` - Machine state tracking
- `shifts` - Shift definitions
- `shift_handovers` - Shift transitions
- `shift_performances` - Shift KPIs
- `lanes` - Production lanes
- `lane_assignments` - Work order lane assignments

### Projects (06_projects.sql)
- `project_documents` - Document management
- `project_milestones` - Milestone tracking
- `rda_drawings` - Drawing approvals
- `project_bom` - Project-specific BOMs

### RBAC (07_rbac.sql)
- `roles` - Role definitions
- `user_roles` - User-role assignments
- `user_plant_access` - Plant-level access control

### Configuration (08_configuration.sql)
- `custom_fields` - Dynamic field definitions
- `field_values` - Custom field values
- `type_lists` - Configurable taxonomies
- `type_list_values` - Type list items
- `workflows` - Workflow definitions
- `workflow_states` - State machine states
- `workflow_transitions` - Transition rules
- `approvals` - Approval instances
- `workflow_history` - Workflow audit trail

### Logistics (09_logistics.sql)
- `shipments` - Shipment tracking
- `shipment_items` - Shipment line items
- `barcode_labels` - Label generation
- `qr_code_scans` - Scan events (TimescaleDB)

### Reporting (10_reporting.sql)
- `reports` - Report definitions
- `report_executions` - Execution history
- `dashboards` - Dashboard configurations

### Traceability (11_traceability.sql)
- `lot_batches` - Lot tracking
- `serial_numbers` - Serial number tracking
- `traceability_links` - Parent-child relationships
- `genealogy_records` - Traceability history (TimescaleDB)

### Branding (12_branding.sql)
- `organization_branding` - White-label configuration
- `email_templates` - Email template management

### Infrastructure (13_infrastructure.sql)
- `audit_logs` - Comprehensive audit trail (TimescaleDB)
- `notifications` - In-app notifications
- `system_settings` - Configuration management
- `file_uploads` - File tracking
- `sap_sync_logs` - SAP integration logs (TimescaleDB)
- `sap_mappings` - Entity mappings

## Multi-Tenancy

All tables with `organization_id` have Row-Level Security (RLS) policies that enforce:

```sql
organization_id = current_setting('app.current_organization_id', true)::int
```

This ensures complete data isolation between organizations at the database level.

## Time-Series Tables

TimescaleDB hypertables for efficient time-series data management:

- `production_logs` - 1 week chunks
- `qr_code_scans` - 1 week chunks
- `inspection_measurements` - 1 month chunks
- `genealogy_records` - 3 month chunks
- `audit_logs` - 6 month chunks
- `sap_sync_logs` - 1 month chunks

## Indexes

All tables include appropriate indexes for:
- Foreign keys
- Frequently queried columns
- Unique constraints
- Composite queries

See individual SQL files for detailed index definitions.

## Migration History

### Archived Migrations
Old incremental migrations have been archived in `migrations/versions/_archived_migrations/`.
These were consolidated into the single initial migration for cleaner schema management.

### Current Migration
- `001_initial_schema.py` - Comprehensive initial schema (2025-11-10)

## Best Practices

1. **Never modify the initial migration** after it's been deployed
2. **Use incremental migrations** for all future schema changes
3. **Test migrations** on a copy of production before deployment
4. **Backup database** before running migrations in production
5. **Document migrations** with clear descriptions of changes

## Support

For schema questions or issues, refer to:
- SQLAlchemy model definitions in `app/models/`
- Alembic migration files in `migrations/versions/`
- This documentation
