# PostgreSQL Extensions Module

## Overview

The `extensions.py` module provides utilities for managing and verifying PostgreSQL extensions required by Unison ERP.

## Required Extensions

| Extension | Purpose | Performance Benefit |
|-----------|---------|-------------------|
| **pgmq** | Message queue for async job processing | 30K msgs/sec throughput |
| **pg_search** | BM25 full-text search | Replaces Elasticsearch |
| **pg_duckdb** | Analytics and OLAP query acceleration | 10-100x faster queries |
| **timescaledb** | Time-series data compression | 75% storage reduction |
| **pg_cron** | Job scheduler for periodic tasks | Replaces Celery Beat |

## Installation

### Using Alembic Migration

```bash
cd backend
alembic upgrade head
```

This runs the `001_install_postgresql_extensions` migration which:
1. Creates all required extensions
2. Verifies installation
3. Provides detailed output

### Manual Installation

```sql
CREATE EXTENSION IF NOT EXISTS pgmq;
CREATE EXTENSION IF NOT EXISTS pg_search;
CREATE EXTENSION IF NOT EXISTS pg_duckdb;
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

## API Reference

### verify_extensions_installed(conn)

Verify all required extensions are installed.

```python
from app.core.extensions import verify_extensions_installed
from app.core.database import engine

with engine.connect() as conn:
    if verify_extensions_installed(conn):
        print("All extensions installed!")
    else:
        print("Missing extensions")
```

**Returns:** `bool` - True if all extensions installed

### get_extension_versions(conn)

Get version information for installed extensions.

```python
versions = get_extension_versions(conn)
# {'pgmq': '1.0.0', 'timescaledb': '2.11.0', ...}
```

**Returns:** `Dict[str, str]` - Extension name to version mapping

### get_missing_extensions(conn)

Identify which required extensions are not installed.

```python
missing = get_missing_extensions(conn)
# {'pg_duckdb', 'pg_search'}
```

**Returns:** `Set[str]` - Set of missing extension names

### verify_extensions_with_report(conn)

Get detailed report of extension status.

```python
report = verify_extensions_with_report(conn)
print(f"Installed: {report['installed']}")
print(f"Missing: {report['missing']}")
print(f"Versions: {report['versions']}")
```

**Returns:** `Dict` with keys:
- `all_installed`: bool
- `installed`: List[str]
- `missing`: List[str]
- `versions`: Dict[str, str]
- `total_required`: int

### get_extension_info(conn, extension_name)

Get detailed information about a specific extension.

```python
info = get_extension_info(conn, "pgmq")
# {
#   'name': 'pgmq',
#   'version': '1.0.0',
#   'schema': 'pgmq',
#   'relocatable': False,
#   'description': 'Message queue...'
# }
```

**Returns:** `Dict[str, str]` - Extension details

### get_all_available_extensions(conn)

List all extensions available in PostgreSQL instance.

```python
available = get_all_available_extensions(conn)
# [('pgmq', '1.0.0', 'Message queue'), ...]
```

**Returns:** `List[Tuple[str, str, str]]` - (name, version, comment)

## Testing

### Unit Tests

```bash
pytest tests/unit/test_extensions_logic.py -v
```

Tests the core logic without requiring database connection.

### Integration Tests

```bash
# Requires running PostgreSQL with extensions
pytest tests/integration/test_extensions.py -v
pytest tests/integration/test_migration_extensions.py -v
```

## Troubleshooting

### Extension Not Available

**Error:** `extension "pgmq" is not available`

**Solution:** Install extension in PostgreSQL:
- Use `tembo/tembo-pg-slim` Docker image (recommended)
- Or install extensions manually (see `/docs/03-postgresql/EXTENSIONS.md`)

### Permission Denied

**Error:** `must be superuser to create this extension`

**Solution:** Grant superuser or use database owner account:
```sql
ALTER USER unison WITH SUPERUSER;
```

### Extension Already Exists

This is not an error. `CREATE EXTENSION IF NOT EXISTS` handles this gracefully.

## Migration Rollback

To remove all extensions:

```bash
alembic downgrade -1
```

**WARNING:** This drops extensions and all dependent objects with CASCADE.

## Best Practices

1. Always verify extensions after migration: `verify_extensions_with_report()`
2. Check available extensions before attempting install: `get_all_available_extensions()`
3. Handle missing extensions gracefully in application code
4. Use connection pooling for verification checks
5. Log extension versions on application startup

## Example: Startup Verification

```python
# app/main.py
from app.core.database import engine
from app.core.extensions import verify_extensions_with_report
import logging

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def verify_extensions():
    with engine.connect() as conn:
        report = verify_extensions_with_report(conn)
        if report['all_installed']:
            logger.info(f"Extensions: {', '.join(report['installed'])}")
        else:
            logger.warning(f"Missing extensions: {report['missing']}")
```

## References

- [PostgreSQL Extensions Documentation](https://www.postgresql.org/docs/current/contrib.html)
- [PGMQ Documentation](https://github.com/tembo-io/pgmq)
- [ParadeDB (pg_search) Documentation](https://docs.paradedb.com/)
- [DuckDB PostgreSQL Extension](https://duckdb.org/docs/extensions/postgres)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [pg_cron Documentation](https://github.com/citusdata/pg_cron)
