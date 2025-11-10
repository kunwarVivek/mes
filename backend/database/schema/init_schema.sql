-- Master Schema Initialization Script
-- MES (Manufacturing Execution System) Database Schema
--
-- This script orchestrates the creation of the complete database schema
-- Execute this file to set up a fresh database instance
--
-- Usage: psql -U postgres -d mes_db -f init_schema.sql

\echo '========================================='
\echo 'MES Database Schema Initialization'
\echo '========================================='
\echo ''

-- Set client encoding
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

\echo 'Step 1: Installing PostgreSQL extensions...'
\i 00_extensions.sql

\echo 'Step 2: Creating core tables (organizations, users, plants, departments, projects)...'
\i 01_core.sql

\echo 'Step 3: Creating materials and BOM tables...'
-- \i 02_materials.sql

\echo 'Step 4: Creating production tables (work orders, operations, work centers)...'
-- \i 03_production.sql

\echo 'Step 5: Creating quality management tables (NCRs, inspections, SPC)...'
-- \i 04_quality.sql

\echo 'Step 6: Creating machine and shift tables...'
-- \i 05_machines_shifts.sql

\echo 'Step 7: Creating project management tables (documents, milestones, RDA)...'
-- \i 06_projects.sql

\echo 'Step 8: Creating RBAC tables (roles, permissions)...'
-- \i 07_rbac.sql

\echo 'Step 9: Creating configuration tables (custom fields, workflows)...'
-- \i 08_configuration.sql

\echo 'Step 10: Creating logistics tables (shipments, barcodes)...'
-- \i 09_logistics.sql

\echo 'Step 11: Creating reporting tables (reports, dashboards)...'
-- \i 10_reporting.sql

\echo 'Step 11: Creating traceability tables (lots, serials, genealogy)...'
-- \i 11_traceability.sql

\echo 'Step 12: Creating branding tables (white-label customization)...'
-- \i 12_branding.sql

\echo 'Step 13: Creating infrastructure tables (audit, notifications, settings, files, SAP)...'
-- \i 13_infrastructure.sql

\echo 'Step 14: Applying Row-Level Security policies...'
-- \i 99_rls_policies.sql

\echo ''
\echo '========================================='
\echo 'Schema initialization complete!'
\echo '========================================='
\echo ''
\echo 'Next steps:'
\echo '1. Run database migrations: alembic upgrade head'
\echo '2. Create initial admin user'
\echo '3. Configure application settings'
