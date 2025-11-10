# pg_search (Full-Text Search) - Complete Guide

**Purpose**: BM25 full-text search with relevance ranking
**Performance**: 20x faster than PostgreSQL tsvector
**Last Updated**: 2025-11-10

---

## Table of Contents

1. [Overview](#overview)
2. [Creating Search Indexes](#creating-search-indexes)
3. [Search Queries](#search-queries)
4. [Python Integration](#python-integration)
5. [Advanced Features](#advanced-features)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)

---

## Overview

pg_search (powered by ParadeDB) provides full-text search with BM25 ranking algorithm - the same algorithm used by Elasticsearch.

### Why pg_search?

**Replaces**: Elasticsearch

**Benefits**:
- **20x faster** than PostgreSQL tsvector
- BM25 ranking (same as Elasticsearch)
- No external service required
- ACID transactions with database
- $800/month cost savings
- Simple SQL interface

**Use Cases**:
- Search materials by name, description, part number
- Search work orders by customer, project, notes
- Search NCR reports by problem description, root cause
- Search maintenance records
- Global search across multiple tables

---

## Creating Search Indexes

### Basic Index

```sql
-- Create BM25 index on materials table
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number, tags}'
);
```

**Parameters:**
- `table_name`: Table to index
- `index_name`: Unique name for the index
- `key_field`: Primary key column (usually `id`)
- `text_fields`: Array of text columns to search

### Index with Numeric and Boolean Fields

```sql
-- Create index with filters
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number, tags}',
    numeric_fields => '{unit_cost, reorder_point, stock_quantity}',
    boolean_fields => '{is_active, is_hazardous}'
);
```

### Index Multiple Tables

```sql
-- Work orders
SELECT paradedb.create_bm25(
    table_name => 'work_orders',
    index_name => 'work_orders_search_idx',
    key_field => 'id',
    text_fields => '{work_order_number, project_name, customer_order_reference, notes}'
);

-- NCR reports
SELECT paradedb.create_bm25(
    table_name => 'ncr_reports',
    index_name => 'ncr_search_idx',
    key_field => 'id',
    text_fields => '{ncr_number, problem_description, root_cause, corrective_action, tags}'
);

-- Maintenance records
SELECT paradedb.create_bm25(
    table_name => 'maintenance_work_orders',
    index_name => 'maintenance_search_idx',
    key_field => 'id',
    text_fields => '{work_order_number, machine_name, description, notes}'
);
```

### Drop Index

```sql
-- Drop index
SELECT paradedb.drop_bm25('materials_search_idx');
```

### List All Indexes

```sql
-- List all BM25 indexes
SELECT paradedb.list_bm25_indexes();
```

---

## Search Queries

### Basic Search

```sql
-- Search for "steel bearing"
SELECT * FROM materials.search(
    query => 'steel bearing',
    limit_rows => 10
) ORDER BY score DESC;

-- Returns:
-- id | score | <other columns from materials table>
-- 42 | 8.5   | Steel Ball Bearing 6201
-- 13 | 7.2   | Stainless Steel Bearing Housing
-- 89 | 6.8   | Steel Roller Bearing
```

**Note**: Results automatically joined with original table

### Search with Filters

```sql
-- Search bearings under $100, only active items
SELECT * FROM materials.search(
    query => 'bearing',
    filter => 'is_active = true AND unit_cost < 100',
    limit_rows => 20
) ORDER BY score DESC;
```

### Fuzzy Search (Typo Tolerance)

```sql
-- Search "bering" (typo) - finds "bearing"
SELECT * FROM materials.search(
    query => 'bering~1',  -- Allows 1 character difference
    limit_rows => 10
) ORDER BY score DESC;

-- Search with 2 character tolerance
SELECT * FROM materials.search(
    query => 'stell~2',  -- Finds "steel"
    limit_rows => 10
) ORDER BY score DESC;
```

### Phrase Search

```sql
-- Exact phrase match
SELECT * FROM work_orders.search(
    query => '"customer order"',  -- Exact phrase
    limit_rows => 20
) ORDER BY score DESC;

-- Phrase with wildcards
SELECT * FROM work_orders.search(
    query => '"customer * order"',  -- Matches "customer purchase order", etc.
    limit_rows => 20
) ORDER BY score DESC;
```

### Boolean Operators

```sql
-- AND operator (both terms must appear)
SELECT * FROM materials.search(
    query => 'steel AND bearing',
    limit_rows => 10
) ORDER BY score DESC;

-- OR operator (either term can appear)
SELECT * FROM materials.search(
    query => 'steel OR aluminum',
    limit_rows => 10
) ORDER BY score DESC;

-- NOT operator (exclude term)
SELECT * FROM materials.search(
    query => 'bearing NOT roller',
    limit_rows => 10
) ORDER BY score DESC;

-- Complex boolean
SELECT * FROM materials.search(
    query => '(steel OR stainless) AND bearing NOT roller',
    limit_rows => 10
) ORDER BY score DESC;
```

### Field-Specific Search

```sql
-- Search specific field
SELECT * FROM materials.search(
    query => 'name:bearing',  -- Only search in "name" field
    limit_rows => 10
) ORDER BY score DESC;

-- Multiple fields
SELECT * FROM materials.search(
    query => 'name:bearing OR part_number:6201',
    limit_rows => 10
) ORDER BY score DESC;
```

### Range Queries

```sql
-- Numeric range
SELECT * FROM materials.search(
    query => '*',  -- Match all
    filter => 'unit_cost:[10 TO 100]',  -- Cost between $10-$100
    limit_rows => 20
) ORDER BY score DESC;

-- Date range (if indexed)
SELECT * FROM work_orders.search(
    query => 'urgent',
    filter => 'created_at:[2025-01-01 TO 2025-12-31]',
    limit_rows => 20
) ORDER BY score DESC;
```

### Wildcard Search

```sql
-- Suffix wildcard
SELECT * FROM materials.search(
    query => 'bear*',  -- Matches bearing, bearings, etc.
    limit_rows => 10
) ORDER BY score DESC;

-- Prefix wildcard (slower)
SELECT * FROM materials.search(
    query => '*ing',  -- Matches bearing, housing, etc.
    limit_rows => 10
) ORDER BY score DESC;

-- Middle wildcard
SELECT * FROM materials.search(
    query => 'ste*l',  -- Matches steel, stainless steel, etc.
    limit_rows => 10
) ORDER BY score DESC;
```

---

## Python Integration

### Basic Search

```python
from sqlalchemy import text
from sqlalchemy.orm import Session

def search_materials(db: Session, query: str, limit: int = 20):
    """Search materials with BM25 ranking"""
    results = db.execute(text("""
        SELECT
            m.id,
            m.part_number,
            m.name,
            m.description,
            m.unit_cost,
            s.score
        FROM materials.search(
            query => :query,
            filter => 'is_active = true',
            limit_rows => :limit
        ) s
        JOIN materials m ON m.id = s.id
        ORDER BY s.score DESC
    """), {"query": query, "limit": limit})

    return [dict(row) for row in results]

# Usage
materials = search_materials(db, "steel bearing", limit=10)
```

### Search with Filters

```python
def search_materials_advanced(
    db: Session,
    query: str,
    max_cost: float = None,
    only_active: bool = True,
    limit: int = 20
):
    """Advanced material search with filters"""
    filters = []

    if only_active:
        filters.append("is_active = true")

    if max_cost:
        filters.append(f"unit_cost <= {max_cost}")

    filter_str = " AND ".join(filters) if filters else None

    results = db.execute(text("""
        SELECT
            m.id,
            m.part_number,
            m.name,
            m.description,
            m.unit_cost,
            s.score
        FROM materials.search(
            query => :query,
            filter => :filter,
            limit_rows => :limit
        ) s
        JOIN materials m ON m.id = s.id
        ORDER BY s.score DESC
    """), {"query": query, "filter": filter_str, "limit": limit})

    return [dict(row) for row in results]

# Usage
materials = search_materials_advanced(
    db,
    query="bearing",
    max_cost=100.0,
    only_active=True,
    limit=20
)
```

### FastAPI Endpoint

```python
# backend/app/api/v1/endpoints/search.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter()

@router.get("/search/materials")
def search_materials_endpoint(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Search materials using BM25 full-text search

    Example: `/api/v1/search/materials?q=steel bearing&limit=10`
    """
    results = db.execute(text("""
        SELECT
            m.id,
            m.part_number,
            m.name,
            m.description,
            m.unit_cost,
            m.stock_quantity,
            s.score
        FROM materials.search(
            query => :query,
            filter => 'is_active = true',
            limit_rows => :limit
        ) s
        JOIN materials m ON m.id = s.id
        ORDER BY s.score DESC
    """), {"query": q, "limit": limit})

    return {
        "query": q,
        "count": results.rowcount,
        "results": [dict(row) for row in results]
    }
```

### Global Search (Multiple Tables)

```python
def global_search(db: Session, query: str, limit: int = 20):
    """Search across materials, work orders, and NCR reports"""

    # Search materials
    materials = db.execute(text("""
        SELECT
            'material' as type,
            m.id,
            m.name as title,
            m.description,
            s.score
        FROM materials.search(
            query => :query,
            limit_rows => :limit
        ) s
        JOIN materials m ON m.id = s.id
    """), {"query": query, "limit": limit})

    # Search work orders
    work_orders = db.execute(text("""
        SELECT
            'work_order' as type,
            wo.id,
            wo.work_order_number as title,
            wo.notes as description,
            s.score
        FROM work_orders.search(
            query => :query,
            limit_rows => :limit
        ) s
        JOIN work_orders wo ON wo.id = s.id
    """), {"query": query, "limit": limit})

    # Search NCR reports
    ncr_reports = db.execute(text("""
        SELECT
            'ncr_report' as type,
            ncr.id,
            ncr.ncr_number as title,
            ncr.problem_description as description,
            s.score
        FROM ncr_reports.search(
            query => :query,
            limit_rows => :limit
        ) s
        JOIN ncr_reports ncr ON ncr.id = s.id
    """), {"query": query, "limit": limit})

    # Combine and sort by score
    all_results = (
        [dict(row) for row in materials] +
        [dict(row) for row in work_orders] +
        [dict(row) for row in ncr_reports]
    )

    all_results.sort(key=lambda x: x['score'], reverse=True)

    return all_results[:limit]
```

---

## Advanced Features

### Faceted Search (Aggregations)

```sql
-- Count results by category
SELECT
    m.category,
    COUNT(*) as count
FROM materials.search(
    query => 'bearing',
    limit_rows => 1000
) s
JOIN materials m ON m.id = s.id
GROUP BY m.category
ORDER BY count DESC;

-- Results:
-- category        | count
-- ----------------+-------
-- Bearings        | 45
-- Hardware        | 12
-- Fasteners       | 8
```

### Boosting (Field Weights)

```sql
-- Boost name field more than description
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => paradedb.field('name', boost => 2.0) ||
                   paradedb.field('description', boost => 1.0) ||
                   paradedb.field('part_number', boost => 1.5)
);
```

### Highlighting (Show Matches)

```sql
-- Get highlighted snippets
SELECT
    m.id,
    m.name,
    paradedb.highlight(m.description, 'steel') as highlighted_description,
    s.score
FROM materials.search(
    query => 'steel',
    limit_rows => 10
) s
JOIN materials m ON m.id = s.id
ORDER BY s.score DESC;

-- Results:
-- highlighted_description: "Made of high-quality <em>steel</em> for durability"
```

---

## Performance Optimization

### Rebuild Index

```sql
-- Rebuild index for better performance
SELECT paradedb.drop_bm25('materials_search_idx');

SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number}'
);
```

### Custom BM25 Parameters

```sql
-- Tune BM25 parameters
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number}',
    k1 => 1.2,  -- Term frequency saturation (default 1.2)
    b => 0.75   -- Length normalization (default 0.75)
);
```

**BM25 Parameters:**
- `k1` (1.0-2.0): Term frequency saturation. Higher = more weight to term frequency
- `b` (0.0-1.0): Length normalization. Higher = penalize longer documents more

### Index Only Relevant Data

```sql
-- Index only active materials
CREATE VIEW active_materials AS
SELECT * FROM materials WHERE is_active = TRUE;

SELECT paradedb.create_bm25(
    table_name => 'active_materials',
    index_name => 'active_materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number}'
);
```

### Limit Indexed Fields

```sql
-- Index fewer fields for faster performance
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, part_number}'  -- Exclude description
);
```

---

## Troubleshooting

### Index Not Found

**Error:** `index "materials_search_idx" does not exist`

**Diagnosis:**
```sql
-- List all indexes
SELECT paradedb.list_bm25_indexes();
```

**Solution:**
```sql
-- Create index
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number}'
);
```

---

### No Results Found

**Diagnosis:**
```sql
-- Check if index has data
SELECT COUNT(*) FROM materials.search(query => '*', limit_rows => 1000);

-- Check table has data
SELECT COUNT(*) FROM materials;
```

**Solution:**
1. Rebuild index
2. Check that text fields are not NULL
3. Use wildcard search to test: `query => '*'`

---

### Slow Search Performance

**Diagnosis:**
```sql
-- Explain search query
EXPLAIN ANALYZE
SELECT * FROM materials.search(
    query => 'steel bearing',
    limit_rows => 20
) ORDER BY score DESC;
```

**Solution:**
1. Reduce number of indexed fields
2. Rebuild index
3. Limit result set with filters
4. Use more specific search terms

---

### Index Out of Sync

**Error:** Search results don't reflect recent inserts/updates

**Diagnosis:**
```sql
-- Check when index was created
SELECT paradedb.index_info('materials_search_idx');
```

**Solution:**
```sql
-- Rebuild index to sync with table
SELECT paradedb.drop_bm25('materials_search_idx');
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, part_number}'
);
```

**Note**: pg_search indexes should update automatically. If not, check PostgreSQL logs for errors.

---

## Best Practices

1. **Index only searchable text**: Don't index numeric IDs or timestamps
2. **Use filters for structured data**: Use `filter =>` for exact matches
3. **Limit result sets**: Use `limit_rows` to improve performance
4. **Boost important fields**: Use boosting to prioritize certain fields
5. **Test search relevance**: Verify top results are actually relevant
6. **Monitor index size**: Large indexes can slow down writes
7. **Rebuild indexes periodically**: For optimal performance

---

## See Also

- [EXTENSIONS_OVERVIEW.md](./EXTENSIONS_OVERVIEW.md) - Installation and architecture
- [PGMQ_GUIDE.md](./PGMQ_GUIDE.md) - Message queue operations
- [ParadeDB Documentation](https://docs.paradedb.com/) - Official pg_search docs
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25) - Understanding BM25 ranking
