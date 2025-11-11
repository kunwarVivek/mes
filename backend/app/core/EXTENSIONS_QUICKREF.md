# PostgreSQL Extensions - Quick Reference

## TL;DR

```bash
# Install extensions
cd backend && alembic upgrade head

# Check status
python3 scripts/check_extensions.py

# Rollback
alembic downgrade -1
```

## Required Extensions (5)

| Extension | Purpose | Replaces |
|-----------|---------|----------|
| pgmq | Message queue (30K msgs/sec) | Celery + RabbitMQ |
| pg_search | BM25 full-text search | Elasticsearch |
| pg_duckdb | Analytics (10-100x faster) | Data warehouse |
| timescaledb | Time-series (75% compression) | InfluxDB/Prometheus |
| pg_cron | Job scheduler | Celery Beat |

## Python API

```python
from app.core.extensions import verify_extensions_with_report
from app.core.database import engine

with engine.connect() as conn:
    report = verify_extensions_with_report(conn)
    print(report)
```

## Files

```
database/migrations/versions/
  └── 001_install_postgresql_extensions.py  # Migration

backend/app/core/
  ├── extensions.py                         # Core module
  ├── EXTENSIONS_PYTHON_API.md              # Python API docs
  └── EXTENSIONS_QUICKREF.md                # This file

backend/scripts/
  └── check_extensions.py                   # CLI tool

backend/tests/
  ├── unit/test_extensions_logic.py         # 11 unit tests
  └── integration/
      ├── test_extensions.py                # 8 integration tests
      └── test_migration_extensions.py      # 6 migration tests

docs/03-postgresql/
  ├── README.md                             # Index of all guides
  ├── EXTENSIONS_OVERVIEW.md                # Installation & overview
  ├── PGMQ_GUIDE.md                         # Message queue guide
  ├── PG_CRON_GUIDE.md                      # Job scheduler guide
  ├── PG_SEARCH_GUIDE.md                    # Full-text search guide
  ├── TIMESCALEDB_GUIDE.md                  # Time-series guide
  └── MIGRATION_GUIDE.md                    # Migration from Celery/Redis
```

## CLI Commands

```bash
# Status check
python3 scripts/check_extensions.py

# Detailed info
python3 scripts/check_extensions.py -v

# List available
python3 scripts/check_extensions.py -a
```

## Migration Commands

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Show current revision
alembic current

# Show history
alembic history
```

## Test Commands

```bash
# Unit tests (no DB required)
pytest tests/unit/test_extensions_logic.py -v

# Integration tests (requires DB)
pytest tests/integration/test_extensions.py -v

# Migration tests
pytest tests/integration/test_migration_extensions.py -v
```

## Troubleshooting

### Extension not available
```bash
# Check available extensions
python3 scripts/check_extensions.py -a

# Use Tembo PostgreSQL image
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  quay.io/tembo/standard-cnpg:15.3.0-1-1c1ba53
```

### Permission denied
```sql
-- Grant superuser
ALTER USER unison WITH SUPERUSER;
```

### Check installation
```python
from app.core.extensions import verify_extensions_installed
from app.core.database import engine

with engine.connect() as conn:
    if verify_extensions_installed(conn):
        print("✓ All extensions installed")
    else:
        print("✗ Missing extensions")
```

## Exit Codes

- 0: All tests passed / All extensions installed
- 1: Tests failed / Extensions missing / Error occurred
