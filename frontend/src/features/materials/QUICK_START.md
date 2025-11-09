# Materials Module - Quick Start Guide

## 30-Second Overview

**What**: Complete CRUD module for material management
**How**: Built with TDD (34 tests, 100% passing)
**Why**: Reference implementation for 9 remaining modules

---

## File Structure at a Glance

```
materials/
├── __tests__/          # 5 test files, 34 tests
├── components/         # Table, Form, Filters
├── hooks/              # 5 TanStack Query hooks
├── pages/              # List page, Form page
├── services/           # API client
├── schemas/            # Zod validation
├── types/              # TypeScript types
└── index.ts            # Exports
```

---

## Run Tests

```bash
# All tests
npm test -- src/features/materials/__tests__/

# Specific test
npm test -- src/features/materials/__tests__/material.service.test.ts

# Watch mode
npm test:watch -- src/features/materials/__tests__/
```

**Expected Result**: 5 files, 34 tests, 100% pass rate

---

## Import & Use

```typescript
// Import everything
import {
  MaterialsPage,
  MaterialFormPage,
  useMaterials,
  useCreateMaterial,
  materialService,
  type Material,
} from '@/features/materials'

// Use in routes
<Route path="/materials" element={<MaterialsPage />} />
<Route path="/materials/create" element={<MaterialFormPage />} />
<Route path="/materials/:id/edit" element={<MaterialFormPage />} />

// Use hooks in components
const { data, isLoading } = useMaterials({ is_active: true })
const createMutation = useCreateMaterial()
```

---

## Key Files

### For Understanding
1. `MATERIALS_MODULE_TDD_EVIDENCE.md` - Complete build story
2. `VERIFICATION_SUMMARY.md` - Final status (this file)
3. `REFERENCE_PATTERNS.md` - Copy-paste templates

### For Coding
1. `services/material.service.ts` - API client pattern
2. `hooks/useMaterials.ts` - Query hook pattern
3. `components/MaterialForm.tsx` - Form pattern
4. `pages/MaterialsPage.tsx` - Page pattern

### For Testing
1. `__tests__/material.service.test.ts` - Service test pattern
2. `__tests__/MaterialForm.test.tsx` - Component test pattern

---

## Replicate This Module

1. **Copy** `REFERENCE_PATTERNS.md`
2. **Replace** all instances:
   - `Material` → `YourEntity`
   - `materials` → `yourEntities`
3. **Follow** TDD cycle (RED → GREEN)
4. **Run** tests until 100% pass
5. **Document** in module README

---

## TDD Workflow

```
1. Write test → npm test (RED - should fail)
2. Write code → npm test (GREEN - should pass)
3. Refactor → npm test (stays GREEN)
```

---

## Test Results

```
✓ material.service.test.ts (7 tests)
✓ useMaterials.test.tsx (4 tests)
✓ MaterialsTable.test.tsx (8 tests)
✓ useMaterialMutations.test.tsx (5 tests)
✓ MaterialForm.test.tsx (10 tests)

Tests: 34 passed (34)
Exit Code: 0
```

---

## Stack Used

- **React** - UI framework
- **TypeScript** - Type safety
- **TanStack Query** - Server state management
- **Zod** - Schema validation
- **Vitest** - Testing framework
- **React Testing Library** - Component testing
- **Axios** - HTTP client

---

## Backend API

```
Base URL: /api/v1/materials

GET    /                 List (paginated)
POST   /                 Create
GET    /:id              Get single
PUT    /:id              Update
DELETE /:id              Delete (soft)
GET    /search           Search
```

---

## Quick Checklist

Creating a new CRUD module? Use this checklist:

- [ ] Create directory structure
- [ ] Copy types from REFERENCE_PATTERNS.md
- [ ] Copy service + tests (RED → GREEN)
- [ ] Copy hooks + tests (RED → GREEN)
- [ ] Copy components + tests (RED → GREEN)
- [ ] Copy pages
- [ ] Update index.ts exports
- [ ] Run all tests (must pass 100%)
- [ ] Add routes to app
- [ ] Manual smoke test

---

## Support Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `MATERIALS_MODULE_TDD_EVIDENCE.md` | Full TDD story | Understanding build process |
| `VERIFICATION_SUMMARY.md` | Final verification | Checking completion status |
| `REFERENCE_PATTERNS.md` | Code templates | Building new modules |
| `QUICK_START.md` | This file | Getting started quickly |

---

## Contact / Questions

- Reference implementation: `/src/features/materials/`
- Test examples: `/src/features/materials/__tests__/`
- Pattern templates: `REFERENCE_PATTERNS.md`
- Full documentation: `MATERIALS_MODULE_TDD_EVIDENCE.md`

---

**Status**: ✅ Production Ready
**Tests**: 34/34 passing
**Reference Quality**: Excellent
**Ready for Replication**: Yes

**Built with TDD, verified with tests, documented for reuse.**
