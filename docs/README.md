# Unison Manufacturing ERP - Documentation Index

**Version**: 2.0
**Last Updated**: 2025-11-07
**System**: Unison Manufacturing ERP (MES for MSME)
**Architecture**: PostgreSQL-Native Stack

---

## 📚 Documentation Structure

### 01. Requirements
Requirements and functional specifications for the system.

- **[PRD (Product Requirements Document)](./01-requirements/PRD.md)**
  - Business challenges, solution overview, user personas
  - 16 core feature requirements (Material, Production, Quality, Maintenance, MES modules)
  - Target: 83%+ MES coverage for MSME manufacturers

- **[FRD (Functional Requirements Document)](./01-requirements/FRD.md)**
  - Business rules, workflows, state machines
  - Data models and validation rules
  - API contracts and integration specifications

---

### 02. Architecture
System architecture, technology stack, and design decisions.

- **[Architecture Overview](./02-architecture/OVERVIEW.md)**
  - System context, high-level architecture
  - Domain-Driven Design (DDD) layers
  - Multi-tenant SaaS patterns

- **[Technology Stack](./02-architecture/TECH_STACK.md)**
  - PostgreSQL-native architecture rationale
  - Backend: FastAPI, Python 3.11, SQLAlchemy 2.0
  - Frontend: React 18, TypeScript, Vite, Tailwind CSS
  - Why we eliminated Redis, Celery, RabbitMQ, Elasticsearch

- **[Database Schema](./02-architecture/DATABASE_SCHEMA.md)**
  - Complete normalized schema (50+ tables)
  - Row-Level Security (RLS) policies
  - Indexes, constraints, relationships

- **[API Design](./02-architecture/API_DESIGN.md)**
  - RESTful API patterns
  - Authentication & authorization
  - 150+ endpoint specifications

- **[Deployment Guide](./02-architecture/DEPLOYMENT.md)**
  - Docker Compose setup (3-4 containers)
  - Production deployment considerations
  - Health checks and monitoring

---

### 03. PostgreSQL-Native Stack
PostgreSQL extensions and native features replacing traditional tech stack.

- **[PostgreSQL Extensions Guide](./03-postgresql/EXTENSIONS.md)**
  - **pgmq**: Message queue (30K msgs/sec) - replaces Celery + RabbitMQ
  - **pg_cron**: Scheduled tasks - replaces Celery Beat
  - **pg_search (ParadeDB)**: Full-text search with BM25 ranking - replaces Elasticsearch
  - **pg_duckdb**: Analytics engine (10-1500x faster OLAP)
  - **timescaledb**: Time-series optimization (75% compression)

- **[Migration Guide: Redis/Celery → PostgreSQL](./03-postgresql/MIGRATION_GUIDE.md)**
  - Step-by-step migration process
  - Code examples: Celery tasks → PGMQ jobs
  - Redis cache → UNLOGGED tables
  - Performance validation

- **[init-extensions.sql](./03-postgresql/init-extensions.sql)**
  - Database initialization script
  - Extension setup, queue creation, cache tables
  - Hypertable configuration for time-series

---

### 04. Domain Documentation
Detailed specifications for each business domain.

- **[Material Management](./04-domains/MATERIAL_MANAGEMENT.md)**
  - Materials, BOMs, inventory tracking
  - Multi-location warehouse management
  - FIFO/LIFO costing

- **[Production Management](./04-domains/PRODUCTION.md)**
  - Work orders, operations, routing
  - Lane-based scheduling (Kanban)
  - Production logging (PWA mobile)

- **[Quality Management](./04-domains/QUALITY.md)**
  - NCR workflows, inspection plans
  - Statistical Process Control (SPC)
  - First Pass Yield (FPY), Cp/Cpk tracking

- **[Maintenance Management](./04-domains/MAINTENANCE.md)**
  - Preventive maintenance (PM) scheduling
  - Downtime tracking, MTBF/MTTR metrics
  - Work order automation

- **[Equipment & Machines](./04-domains/EQUIPMENT_MACHINES.md)**
  - Machine master data, capacity planning
  - Utilization tracking, OEE calculation
  - Machine status monitoring

- **[Shift Management](./04-domains/SHIFT_MANAGEMENT.md)**
  - Shift definitions, schedules, handovers
  - Shift performance tracking
  - Multi-shift production planning

- **[Visual Scheduling](./04-domains/VISUAL_SCHEDULING.md)**
  - Frappe-Gantt interactive scheduler
  - Drag-and-drop work order planning
  - Capacity-based scheduling

- **[Traceability](./04-domains/TRACEABILITY.md)**
  - Serial number tracking, lot genealogy
  - Forward/backward traceability
  - Recall management

---

### 05. Implementation Guides
Phase-wise development roadmap for developers.

- **[Phase 1: Foundation (Weeks 1-8)](./05-implementation/PHASE_1_FOUNDATION.md)**
  - Multi-tenancy, authentication, authorization
  - Material management, project management
  - 15 core tables, 25 API endpoints

- **[Phase 2: Production Core (Weeks 9-16)](./05-implementation/PHASE_2_PRODUCTION_CORE.md)**
  - Work orders, lanes, scheduling
  - PWA mobile production logging
  - 12 tables, 30 API endpoints

- **[Phase 3: Quality & Analytics (Weeks 17-24)](./05-implementation/PHASE_3_QUALITY_ANALYTICS.md)**
  - NCR workflows, KPI dashboards
  - Reporting engine, OEE calculation
  - 13 tables, 20 API endpoints

- **[Phase 4: MES Modules (Weeks 25-32)](./05-implementation/PHASE_4_MES_MODULES.md)**
  - Equipment, maintenance, shift management
  - Visual scheduling, traceability
  - 15 tables, 40 API endpoints

---

## 🚀 Quick Start for Developers

### For New Claude Code Sessions

**Context Loading Order:**
1. Read `docs/README.md` (this file) first for navigation
2. Load `docs/02-architecture/TECH_STACK.md` for technology decisions
3. Load relevant domain docs from `04-domains/` based on feature scope
4. Load implementation phase guide from `05-implementation/` for current sprint

**Phase-Based Development:**
- Each phase document is self-contained with:
  - Database tables to create
  - API endpoints to implement
  - Domain services with business logic
  - Frontend components to build
  - Testing requirements

### For Architecture Reviews

**Read in this order:**
1. `02-architecture/OVERVIEW.md` → System understanding
2. `02-architecture/TECH_STACK.md` → Technology decisions
3. `03-postgresql/EXTENSIONS.md` → PostgreSQL-native rationale
4. `02-architecture/DATABASE_SCHEMA.md` → Data model

### For Feature Development

**Example: Implementing Maintenance Management**
1. Read `01-requirements/FRD.md` → Section 2.14 (Business Rules)
2. Read `04-domains/MAINTENANCE.md` → Complete domain specification
3. Read `05-implementation/PHASE_4_MES_MODULES.md` → Implementation guide
4. Read `02-architecture/DATABASE_SCHEMA.md` → Tables: pm_schedules, maintenance_work_orders
5. Read `02-architecture/API_DESIGN.md` → API contracts for maintenance endpoints

---

## 📊 System Metrics

**Tech Stack Optimization:**
- **Before**: Redis + Celery + RabbitMQ + Elasticsearch = 8-10 containers
- **After**: PostgreSQL-native extensions = 3-4 containers
- **Result**: 60% fewer containers, 40-60% lower infrastructure costs

**MES Coverage:**
- **Before Gap Analysis**: 68% MES coverage
- **After 6 New Modules**: 83%+ MES coverage (target achieved)

**Performance Benchmarks:**
| Component | Traditional | PostgreSQL-Native | Improvement |
|-----------|-------------|-------------------|-------------|
| Message Queue | Celery: ~500 jobs/hour | PGMQ: 30K msgs/sec | 300x faster |
| Full-Text Search | tsvector | pg_search (BM25) | 20x faster |
| Analytics | Materialized Views | pg_duckdb | 10-1500x faster |
| Cache | Redis: <1ms | UNLOGGED: 1-2ms | Acceptable trade-off |
| Time-Series | Native tables | timescaledb | 75% compression |

---

## 🎯 Architecture Decisions

### Why PostgreSQL-Native?

**Context**: B2B SaaS for MSME manufacturers with:
- Low job volume: 2-5 jobs per customer
- Cache latency: 1-5ms acceptable
- Team: Minimal expertise, startup
- Deployment: Both on-premise and cloud

**Decision**: Use PostgreSQL extensions instead of separate services

**Rationale**:
1. **Simplicity**: Single database to manage, backup, monitor
2. **Cost**: 60% fewer containers = lower infrastructure costs
3. **Performance**: PGMQ (30K msgs/sec) >> Celery (100 jobs/hour) for MSME scale
4. **Reliability**: ACID transactions across all operations
5. **Expertise**: PostgreSQL skills >> Redis + Celery + RabbitMQ skills

**Trade-offs Accepted**:
- Cache latency: 1-2ms (UNLOGGED) vs <1ms (Redis) - acceptable for dashboards
- Search: BM25 in pg_search vs Elasticsearch - sufficient for MSME scale

---

## 🛠️ Development Workflow

### Session Initialization
```bash
# 1. Read master index
cat docs/README.md

# 2. Load PostgreSQL extensions
psql -f docs/03-postgresql/init-extensions.sql

# 3. Run backend
cd backend && uvicorn app.main:app --reload

# 4. Run frontend
cd frontend && npm run dev
```

### Adding New Feature
```bash
# 1. Update requirements
docs/01-requirements/FRD.md → Add business rules

# 2. Design database tables
docs/02-architecture/DATABASE_SCHEMA.md → Add tables

# 3. Create domain service
docs/04-domains/[DOMAIN].md → Document service

# 4. Implement API
docs/02-architecture/API_DESIGN.md → Add endpoints

# 5. Update phase guide
docs/05-implementation/PHASE_X.md → Add to checklist
```

---

## 📞 Support

**Documentation Issues**: Create GitHub issue with `docs` label
**Architecture Questions**: Reference specific doc section in issue
**Migration Questions**: See `03-postgresql/MIGRATION_GUIDE.md`

---

**Last Updated**: 2025-11-07
**Documentation Version**: 2.0 (PostgreSQL-Native Architecture)
