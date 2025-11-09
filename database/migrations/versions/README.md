# Database Migrations

## Prerequisites

### PostgreSQL Extensions Required

The following PostgreSQL extensions must be available for migrations to succeed:

1. **pgmq** - Message queue (30K msgs/sec throughput)
2. **pg_search** (paradedb) - BM25 full-text search
3. **pg_duckdb** - Analytics engine (10-100x faster OLAP)
4. **timescaledb** - Time-series compression (75% compression)
5. **pg_cron** - Job scheduler

### Installation Options

#### Option 1: Tembo PostgreSQL (Recommended)
```bash
# Use Tembo's PostgreSQL image with all extensions pre-installed
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_USER=unison \
  -e POSTGRES_PASSWORD=unison_dev_password \
  -e POSTGRES_DB=unison_erp \
  quay.io/tembo/standard-cnpg:15.3.0-1-1c1ba53
```

#### Option 2: Build Custom Image
See `/Users/vivek/jet/unison/docs/03-postgresql/EXTENSIONS.md` for manual installation instructions.

#### Option 3: Development Testing
For testing without full extensions, comment out unavailable extensions in the migration file.

### Running Migrations

```bash
# From backend directory
cd backend

# Run migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Check current revision
alembic current
```

## Migration Files

- `001_install_postgresql_extensions.py` - Install all required PostgreSQL extensions
