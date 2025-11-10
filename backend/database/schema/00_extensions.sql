-- PostgreSQL Extensions Setup
-- This file sets up all required PostgreSQL extensions for the MES system

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable TimescaleDB for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable pgcrypto for encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enable pg_trgm for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Comments
COMMENT ON EXTENSION "uuid-ossp" IS 'UUID generation functions';
COMMENT ON EXTENSION timescaledb IS 'Time-series database functionality';
COMMENT ON EXTENSION pgcrypto IS 'Cryptographic functions';
COMMENT ON EXTENSION pg_trgm IS 'Trigram-based text similarity';
