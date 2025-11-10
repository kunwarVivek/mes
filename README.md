# Unison Manufacturing ERP

**A PostgreSQL-native Manufacturing Execution System (MES) for SMEs**

[![CI/CD](https://github.com/kunwarVivek/mes/actions/workflows/ci.yml/badge.svg)](https://github.com/kunwarVivek/mes/actions)

---

## 🚨 Recent Audit Findings (2025-11-10)

A **comprehensive audit** was conducted against PRD/FRD/Architecture requirements.

### Overall Status: 🟡 65/100

- **Database**: 50% (RLS ✅ Fixed, Hypertables ✅ Fixed)
- **Backend**: 65% (Core APIs ✅ Done, Integrations ⚠️ Partial)
- **Frontend**: 45% (Basic features ✅ Done, PWA ❌ Not activated)
- **Security**: ✅ Fixed (RLS policies implemented)
- **CI/CD**: ✅ Implemented

### Critical Fixes Implemented ✅

1. **Row-Level Security (RLS)**: 50+ policies for multi-tenant isolation
2. **TimescaleDB Hypertables**: 9 time-series tables with compression
3. **PostgreSQL Extensions**: Setup for pgmq, pg_cron
4. **Health Check Endpoints**: `/health`, `/ready`, `/live`, `/startup`
5. **CI/CD Pipeline**: Automated testing, security scans

### Immediate Action Required

```bash
# Apply database fixes
cd backend
psql -d unison -f database/schema/15_rls_policies.sql
psql -d unison -f database/schema/16_timescaledb_hypertables.sql

# Install extensions
sudo apt-get install pgmq postgresql-15-cron
```

---

## 🎯 Project Overview

Unison is a **B2B SaaS Manufacturing ERP** for discrete manufacturing SMEs delivering **83%+ MES coverage** with PostgreSQL-native architecture.

### Key Features

- Multi-tenant SaaS with RLS security
- Material & BOM management
- Work order planning & execution
- Quality management (NCR, inspections)
- Equipment tracking & OEE
- Preventive maintenance
- Traceability (serial/lot tracking)
- Visual scheduling (Gantt)
- Custom fields & workflows
- White-label branding

---

## ⚡ Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

**API**: http://localhost:8000 | **Docs**: http://localhost:8000/docs
**App**: http://localhost:5173

---

## 📚 Documentation

- [PRD](docs/01-requirements/PRD.md) - Product requirements
- [Architecture](docs/02-architecture/OVERVIEW.md)
- [Database Schema](docs/02-architecture/DATABASE_SCHEMA.md)
- [PostgreSQL Extensions](docs/03-postgresql/EXTENSIONS.md)

---

## 🏗️ Tech Stack

**Backend**: FastAPI, SQLAlchemy, PostgreSQL 15+, TimescaleDB
**Frontend**: React 18, TypeScript, Vite, TailwindCSS, ShadCN UI
**Database**: PostgreSQL + pgmq + pg_cron + timescaledb

---

## 📜 License

MIT License - See [LICENSE](LICENSE)
