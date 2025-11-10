-- ============================================================================
-- Row-Level Security (RLS) Policies for Multi-Tenant Isolation
-- ============================================================================
--
-- Purpose: Enforce tenant isolation at the database level using PostgreSQL RLS
-- Context: All queries are filtered by organization_id from session variable
-- Session Variable: app.current_organization_id (set by backend middleware)
--
-- CRITICAL SECURITY: Without RLS, users could potentially access other
-- organizations' data via direct database access or ORM bypasses.
--
-- Generated: 2025-11-10
-- ============================================================================

-- Set session variable helper function (for testing)
CREATE OR REPLACE FUNCTION set_rls_context(org_id INTEGER, plant_id INTEGER DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_organization_id', org_id::TEXT, false);
    IF plant_id IS NOT NULL THEN
        PERFORM set_config('app.current_plant_id', plant_id::TEXT, false);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get current organization ID from session (with error handling)
CREATE OR REPLACE FUNCTION get_current_organization_id()
RETURNS INTEGER AS $$
DECLARE
    org_id TEXT;
BEGIN
    org_id := current_setting('app.current_organization_id', true);
    IF org_id IS NULL OR org_id = '' THEN
        RAISE EXCEPTION 'RLS context not set: app.current_organization_id is required';
    END IF;
    RETURN org_id::INTEGER;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'RLS context not set: app.current_organization_id is required';
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- ORGANIZATIONS TABLE - NO RLS (Root tenant table)
-- ============================================================================
-- Organizations table should NOT have RLS as it's the root multi-tenant table
-- Users can only see their own organization via application-level filtering

ALTER TABLE organizations DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- PLANTS & LOCATIONS
-- ============================================================================

ALTER TABLE plants ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS plants_tenant_isolation ON plants;
CREATE POLICY plants_tenant_isolation ON plants
    USING (organization_id = get_current_organization_id());

ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS departments_tenant_isolation ON departments;
CREATE POLICY departments_tenant_isolation ON departments
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- USERS & IDENTITY
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS users_tenant_isolation ON users;
CREATE POLICY users_tenant_isolation ON users
    USING (organization_id = get_current_organization_id());

ALTER TABLE roles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS roles_tenant_isolation ON roles;
CREATE POLICY roles_tenant_isolation ON roles
    USING (organization_id = get_current_organization_id());

ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS user_roles_tenant_isolation ON user_roles;
CREATE POLICY user_roles_tenant_isolation ON user_roles
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- MATERIALS & INVENTORY
-- ============================================================================

ALTER TABLE material ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS material_tenant_isolation ON material;
CREATE POLICY material_tenant_isolation ON material
    USING (organization_id = get_current_organization_id());

ALTER TABLE bom ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS bom_tenant_isolation ON bom;
CREATE POLICY bom_tenant_isolation ON bom
    USING (organization_id = get_current_organization_id());

ALTER TABLE bom_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS bom_items_tenant_isolation ON bom_items;
CREATE POLICY bom_items_tenant_isolation ON bom_items
    USING (organization_id = get_current_organization_id());

ALTER TABLE bom_routes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS bom_routes_tenant_isolation ON bom_routes;
CREATE POLICY bom_routes_tenant_isolation ON bom_routes
    USING (organization_id = get_current_organization_id());

ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inventory_tenant_isolation ON inventory;
CREATE POLICY inventory_tenant_isolation ON inventory
    USING (organization_id = get_current_organization_id());

ALTER TABLE material_transactions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS material_transactions_tenant_isolation ON material_transactions;
CREATE POLICY material_transactions_tenant_isolation ON material_transactions
    USING (organization_id = get_current_organization_id());

ALTER TABLE inventory_alert ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inventory_alert_tenant_isolation ON inventory_alert;
CREATE POLICY inventory_alert_tenant_isolation ON inventory_alert
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- PROJECTS & WORK ORDERS
-- ============================================================================

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS projects_tenant_isolation ON projects;
CREATE POLICY projects_tenant_isolation ON projects
    USING (organization_id = get_current_organization_id());

ALTER TABLE project_milestones ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS project_milestones_tenant_isolation ON project_milestones;
CREATE POLICY project_milestones_tenant_isolation ON project_milestones
    USING (organization_id = get_current_organization_id());

ALTER TABLE work_order ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS work_order_tenant_isolation ON work_order;
CREATE POLICY work_order_tenant_isolation ON work_order
    USING (organization_id = get_current_organization_id());

ALTER TABLE work_center ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS work_center_tenant_isolation ON work_center;
CREATE POLICY work_center_tenant_isolation ON work_center
    USING (organization_id = get_current_organization_id());

ALTER TABLE work_order_operations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS work_order_operations_tenant_isolation ON work_order_operations;
CREATE POLICY work_order_operations_tenant_isolation ON work_order_operations
    USING (organization_id = get_current_organization_id());

ALTER TABLE production_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS production_logs_tenant_isolation ON production_logs;
CREATE POLICY production_logs_tenant_isolation ON production_logs
    USING (organization_id = get_current_organization_id());

ALTER TABLE lanes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lanes_tenant_isolation ON lanes;
CREATE POLICY lanes_tenant_isolation ON lanes
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- QUALITY MANAGEMENT
-- ============================================================================

ALTER TABLE ncr ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ncr_tenant_isolation ON ncr;
CREATE POLICY ncr_tenant_isolation ON ncr
    USING (organization_id = get_current_organization_id());

ALTER TABLE ncr_approvals ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ncr_approvals_tenant_isolation ON ncr_approvals;
CREATE POLICY ncr_approvals_tenant_isolation ON ncr_approvals
    USING (organization_id = get_current_organization_id());

ALTER TABLE inspection_plans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inspection_plans_tenant_isolation ON inspection_plans;
CREATE POLICY inspection_plans_tenant_isolation ON inspection_plans
    USING (organization_id = get_current_organization_id());

ALTER TABLE inspection_characteristics ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inspection_characteristics_tenant_isolation ON inspection_characteristics;
CREATE POLICY inspection_characteristics_tenant_isolation ON inspection_characteristics
    USING (organization_id = get_current_organization_id());

ALTER TABLE inspection_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS inspection_logs_tenant_isolation ON inspection_logs;
CREATE POLICY inspection_logs_tenant_isolation ON inspection_logs
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- MACHINES & EQUIPMENT
-- ============================================================================

ALTER TABLE machines ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS machines_tenant_isolation ON machines;
CREATE POLICY machines_tenant_isolation ON machines
    USING (organization_id = get_current_organization_id());

ALTER TABLE machine_status_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS machine_status_history_tenant_isolation ON machine_status_history;
CREATE POLICY machine_status_history_tenant_isolation ON machine_status_history
    USING (organization_id = get_current_organization_id());

ALTER TABLE maintenance ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS maintenance_tenant_isolation ON maintenance;
CREATE POLICY maintenance_tenant_isolation ON maintenance
    USING (organization_id = get_current_organization_id());

ALTER TABLE maintenance_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS maintenance_logs_tenant_isolation ON maintenance_logs;
CREATE POLICY maintenance_logs_tenant_isolation ON maintenance_logs
    USING (organization_id = get_current_organization_id());

ALTER TABLE downtime_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS downtime_logs_tenant_isolation ON downtime_logs;
CREATE POLICY downtime_logs_tenant_isolation ON downtime_logs
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- SHIFTS
-- ============================================================================

ALTER TABLE shifts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS shifts_tenant_isolation ON shifts;
CREATE POLICY shifts_tenant_isolation ON shifts
    USING (organization_id = get_current_organization_id());

ALTER TABLE work_center_shifts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS work_center_shifts_tenant_isolation ON work_center_shifts;
CREATE POLICY work_center_shifts_tenant_isolation ON work_center_shifts
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- TRACEABILITY
-- ============================================================================

ALTER TABLE lot_batches ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lot_batches_tenant_isolation ON lot_batches;
CREATE POLICY lot_batches_tenant_isolation ON lot_batches
    USING (organization_id = get_current_organization_id());

ALTER TABLE serial_numbers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS serial_numbers_tenant_isolation ON serial_numbers;
CREATE POLICY serial_numbers_tenant_isolation ON serial_numbers
    USING (organization_id = get_current_organization_id());

ALTER TABLE lot_genealogy ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS lot_genealogy_tenant_isolation ON lot_genealogy;
CREATE POLICY lot_genealogy_tenant_isolation ON lot_genealogy
    USING (organization_id = get_current_organization_id());

ALTER TABLE traceability_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS traceability_events_tenant_isolation ON traceability_events;
CREATE POLICY traceability_events_tenant_isolation ON traceability_events
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- WORKFLOWS & APPROVALS
-- ============================================================================

ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS workflows_tenant_isolation ON workflows;
CREATE POLICY workflows_tenant_isolation ON workflows
    USING (organization_id = get_current_organization_id());

ALTER TABLE workflow_states ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS workflow_states_tenant_isolation ON workflow_states;
CREATE POLICY workflow_states_tenant_isolation ON workflow_states
    USING (organization_id = get_current_organization_id());

ALTER TABLE workflow_transitions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS workflow_transitions_tenant_isolation ON workflow_transitions;
CREATE POLICY workflow_transitions_tenant_isolation ON workflow_transitions
    USING (organization_id = get_current_organization_id());

ALTER TABLE workflow_instances ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS workflow_instances_tenant_isolation ON workflow_instances;
CREATE POLICY workflow_instances_tenant_isolation ON workflow_instances
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- CUSTOM FIELDS & CONFIGURATION
-- ============================================================================

ALTER TABLE custom_fields ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS custom_fields_tenant_isolation ON custom_fields;
CREATE POLICY custom_fields_tenant_isolation ON custom_fields
    USING (organization_id = get_current_organization_id());

ALTER TABLE field_values ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS field_values_tenant_isolation ON field_values;
CREATE POLICY field_values_tenant_isolation ON field_values
    USING (organization_id = get_current_organization_id());

ALTER TABLE type_lists ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS type_lists_tenant_isolation ON type_lists;
CREATE POLICY type_lists_tenant_isolation ON type_lists
    USING (organization_id = get_current_organization_id());

ALTER TABLE type_list_values ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS type_list_values_tenant_isolation ON type_list_values;
CREATE POLICY type_list_values_tenant_isolation ON type_list_values
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- BRANDING & CUSTOMIZATION
-- ============================================================================

ALTER TABLE branding ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS branding_tenant_isolation ON branding;
CREATE POLICY branding_tenant_isolation ON branding
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- LOGISTICS & SHIPPING
-- ============================================================================

ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS shipments_tenant_isolation ON shipments;
CREATE POLICY shipments_tenant_isolation ON shipments
    USING (organization_id = get_current_organization_id());

ALTER TABLE shipment_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS shipment_items_tenant_isolation ON shipment_items;
CREATE POLICY shipment_items_tenant_isolation ON shipment_items
    USING (organization_id = get_current_organization_id());

ALTER TABLE qr_code_scans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS qr_code_scans_tenant_isolation ON qr_code_scans;
CREATE POLICY qr_code_scans_tenant_isolation ON qr_code_scans
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- REPORTING
-- ============================================================================

ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reports_tenant_isolation ON reports;
CREATE POLICY reports_tenant_isolation ON reports
    USING (organization_id = get_current_organization_id());

ALTER TABLE report_executions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS report_executions_tenant_isolation ON report_executions;
CREATE POLICY report_executions_tenant_isolation ON report_executions
    USING (organization_id = get_current_organization_id());

ALTER TABLE dashboards ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS dashboards_tenant_isolation ON dashboards;
CREATE POLICY dashboards_tenant_isolation ON dashboards
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- INFRASTRUCTURE & AUDIT
-- ============================================================================

ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS file_uploads_tenant_isolation ON file_uploads;
CREATE POLICY file_uploads_tenant_isolation ON file_uploads
    USING (organization_id = get_current_organization_id());

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs;
CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    USING (organization_id = get_current_organization_id());

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS notifications_tenant_isolation ON notifications;
CREATE POLICY notifications_tenant_isolation ON notifications
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- COSTING & FINANCIALS
-- ============================================================================

ALTER TABLE material_costing ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS material_costing_tenant_isolation ON material_costing;
CREATE POLICY material_costing_tenant_isolation ON material_costing
    USING (organization_id = get_current_organization_id());

ALTER TABLE cost_layers ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS cost_layers_tenant_isolation ON cost_layers;
CREATE POLICY cost_layers_tenant_isolation ON cost_layers
    USING (organization_id = get_current_organization_id());

ALTER TABLE work_order_costing ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS work_order_costing_tenant_isolation ON work_order_costing;
CREATE POLICY work_order_costing_tenant_isolation ON work_order_costing
    USING (organization_id = get_current_organization_id());

-- ============================================================================
-- VALIDATION & TESTING
-- ============================================================================

-- Test function to validate RLS is working
CREATE OR REPLACE FUNCTION test_rls_isolation()
RETURNS TABLE(test_name TEXT, result TEXT) AS $$
BEGIN
    -- Test 1: Set org 1 context
    PERFORM set_rls_context(1);

    -- Test 2: Query should only return org 1 data
    RETURN QUERY
    SELECT 'RLS Context Set'::TEXT, ('Org ID: ' || get_current_organization_id()::TEXT)::TEXT;

    -- Test 3: Try to access org 2 data (should return 0 rows)
    RETURN QUERY
    SELECT 'Cross-tenant isolation'::TEXT,
           CASE
               WHEN (SELECT COUNT(*) FROM material WHERE organization_id = 2) = 0
                   THEN 'PASS'
               ELSE 'FAIL'
           END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS & DOCUMENTATION
-- ============================================================================

COMMENT ON FUNCTION get_current_organization_id() IS 'Returns the current organization ID from session variable. Throws error if not set.';
COMMENT ON FUNCTION set_rls_context(INTEGER, INTEGER) IS 'Helper function to set RLS context for testing. In production, this is set by the backend middleware.';
COMMENT ON FUNCTION test_rls_isolation() IS 'Test function to validate RLS policies are working correctly.';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Row-Level Security (RLS) Policies Applied Successfully';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Total policies created: 50+';
    RAISE NOTICE '';
    RAISE NOTICE 'IMPORTANT: Backend middleware MUST set session variables:';
    RAISE NOTICE '  - app.current_organization_id (REQUIRED)';
    RAISE NOTICE '  - app.current_plant_id (OPTIONAL)';
    RAISE NOTICE '';
    RAISE NOTICE 'Test RLS: SELECT * FROM test_rls_isolation();';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
END $$;
