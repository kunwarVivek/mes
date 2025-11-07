# Traceability Domain

**Domain**: Traceability (MES Module)
**Bounded Context**: Lot Numbers, Serial Numbers, Forward/Backward Genealogy, Recall Management
**Owner**: Quality Assurance & Supply Chain
**Status**: Supporting Domain (High Strategic Importance for Regulated Industries)

---

## Domain Overview

### Purpose

The Traceability domain enables complete product and material traceability through lot numbers, serial numbers, and genealogy records. It supports forward tracing (where did this material go?) and backward tracing (where did this product come from?) for quality control, warranty management, and recall execution.

### Scope

**In Scope**:
- Lot number tracking (material batches from suppliers)
- Serial number tracking (individual finished products)
- Genealogy records (parent-child relationships: lot → product, component → assembly)
- Forward traceability (lot → all products using that lot)
- Backward traceability (product → all lots/components used)
- Recall management (identify affected products from defective lot)
- Expiry date tracking (FEFO - First Expired, First Out)

**Out of Scope**:
- Material transactions → Material domain (cross-referenced)
- Work order production → Production domain (cross-referenced)
- Quality inspections → Quality domain (cross-referenced)

### Key Business Goals

1. **100% Traceability**: All products traceable to source materials
2. **Fast Recall**: Identify affected products within 1 hour
3. **Forward/Backward Trace**: Complete genealogy in <5 seconds
4. **Expiry Management**: Zero expired material usage
5. **Compliance**: FDA 21 CFR Part 11, ISO 9001, automotive IATF 16949

---

## Core Concepts

### Lot Number

**Definition**: A unique identifier for a batch of material received from a supplier.

**Lot Number Structure**: `{material_code}-{receipt_date}-{sequence}`
- Example: `STL304-20251107-001` (Stainless Steel 304, received Nov 7, 2025, batch 1)

**Lot Attributes**:
```python
lot = {
    "lot_number": "STL304-20251107-001",
    "material_id": 456,
    "quantity": 500.0,  # kg
    "receipt_date": "2025-11-07",
    "expiry_date": None,  # NULL for non-perishable
    "supplier_id": 12,
    "supplier_lot_number": "SL-2025-XYZ",  # Supplier's internal lot number
    "certificate_file_id": 789,  # Material test certificate (MinIO)
    "remaining_quantity": 450.0,  # 50 kg consumed
    "is_active": True
}
```

**Lot Lifecycle**:
```
Received (remaining_quantity = initial quantity)
    ↓
Consumed (remaining_quantity decreases with each material issue)
    ↓
Depleted (remaining_quantity = 0, is_active = FALSE)
```

### Serial Number

**Definition**: A unique identifier for an individual finished product.

**Serial Number Structure**: `{product_code}-{year}{month}-{sequence}`
- Example: `PUMP-2511-00001` (Hydraulic Pump, November 2025, unit 1)

**Serial Attributes**:
```python
serial = {
    "serial_number": "PUMP-2511-00001",
    "product_id": 78,
    "work_order_id": 123,
    "production_date": "2025-11-07",
    "shipment_id": 456,  # NULL if not shipped
    "shipped_date": "2025-11-15",
    "customer_id": 34,
    "status": "shipped",  # in_stock, shipped, returned, scrapped
    "location": "Customer Site A"
}
```

**Serial Status Workflow**:
```
in_stock → shipped → (returned → in_stock OR scrapped)
```

### Genealogy Record

**Definition**: A parent-child relationship linking materials (lots) to products (serials) or components to assemblies.

**Relationship Types**:
- **consumed**: Lot consumed to produce serial (e.g., Lot STL304-001 → Serial PUMP-001)
- **produced**: Serial produced from work order (e.g., WO-2025-001 → Serial PUMP-001)
- **assembled_into**: Component serial assembled into parent serial (e.g., Serial MOTOR-001 assembled into Serial PUMP-001)

**Genealogy Structure**:
```python
genealogy = {
    "parent_type": "lot_number",
    "parent_id": 123,  # Lot: STL304-20251107-001
    "child_type": "serial_number",
    "child_id": 456,  # Serial: PUMP-2511-00001
    "relationship_type": "consumed",
    "quantity_used": 2.5,  # kg
    "recorded_at": "2025-11-07T14:30:00Z"
}
```

### Forward Traceability

**Definition**: "Where did this material go?" - Find all products using a specific lot.

**Query**:
```sql
-- Forward trace: Find all serials using lot STL304-20251107-001
SELECT
    sn.serial_number,
    sn.production_date,
    sn.shipment_id,
    sn.customer_id,
    gr.quantity_used
FROM genealogy_records gr
JOIN serial_numbers sn ON gr.child_type = 'serial_number' AND gr.child_id = sn.id
JOIN lot_numbers ln ON gr.parent_type = 'lot_number' AND gr.parent_id = ln.id
WHERE ln.lot_number = 'STL304-20251107-001'
AND gr.relationship_type = 'consumed';
```

**Use Case**: Supplier notifies defect in Lot STL304-001 → Identify all products using that lot for recall.

### Backward Traceability

**Definition**: "Where did this product come from?" - Find all materials used to produce a specific serial.

**Query**:
```sql
-- Backward trace: Find all lots used to produce Serial PUMP-2511-00001
SELECT
    ln.lot_number,
    ln.material_id,
    m.name AS material_name,
    ln.supplier_id,
    s.name AS supplier_name,
    gr.quantity_used
FROM genealogy_records gr
JOIN lot_numbers ln ON gr.parent_type = 'lot_number' AND gr.parent_id = ln.id
JOIN materials m ON ln.material_id = m.id
JOIN suppliers s ON ln.supplier_id = s.id
JOIN serial_numbers sn ON gr.child_type = 'serial_number' AND gr.child_id = sn.id
WHERE sn.serial_number = 'PUMP-2511-00001'
AND gr.relationship_type = 'consumed';
```

**Use Case**: Customer reports defect in PUMP-001 → Investigate which material batches were used.

### Recall Execution

**Definition**: Identify all affected products from a defective lot and notify customers.

**Recall Workflow**:
```
1. Defective lot identified (e.g., STL304-20251107-001 failed metallurgical test)
2. Forward trace: Find all products using that lot (5 products: PUMP-00001 to PUMP-00005)
3. Check shipment status: 3 shipped to customers, 2 in stock
4. Generate recall list with customer contact info
5. Place lot on hold (is_active = FALSE)
6. Notify customers (email via PGMQ)
7. Track recall responses
```

---

## Database Schema

### Tables (3 core tables)

See [DATABASE_SCHEMA.md](../02-architecture/DATABASE_SCHEMA.md) for full DDL.

#### 1. lot_numbers

Material batch tracking.

**Key Columns**:
- `lot_number`: Unique identifier (e.g., "STL304-20251107-001")
- `material_id`: FK to materials
- `quantity`: Initial quantity received
- `receipt_date`: Date received from supplier
- `expiry_date`: Expiration date (NULL for non-perishable)
- `supplier_id`: FK to suppliers
- `supplier_lot_number`: Supplier's lot number
- `certificate_file_id`: FK to file_uploads (material cert in MinIO)
- `remaining_quantity`: Quantity not yet consumed
- `is_active`: Soft delete (FALSE if depleted or on hold)

**Indexes**:
- B-tree: material_id, supplier_id
- pg_search BM25: lot_number, supplier_lot_number
- Partial index: `WHERE expiry_date IS NOT NULL AND is_active = TRUE` (expiring lots)
- Partial index: `WHERE remaining_quantity > 0` (available lots)

#### 2. serial_numbers

Individual product tracking.

**Key Columns**:
- `serial_number`: Unique identifier (e.g., "PUMP-2511-00001")
- `product_id`: FK to products
- `work_order_id`: FK to work_orders (production source)
- `production_date`: Date produced
- `shipment_id`: FK to shipments (if shipped)
- `shipped_date`: Date shipped to customer
- `customer_id`: FK to customers (if applicable)
- `status`: Enum (in_stock, shipped, returned, scrapped)
- `location`: Current location

**Indexes**:
- B-tree: product_id, work_order_id, shipment_id, status
- pg_search BM25: serial_number
- Partial index: `WHERE status = 'shipped'` (shipped serials)

#### 3. genealogy_records

Parent-child traceability relationships.

**Key Columns**:
- `parent_type`: Enum (lot_number, serial_number)
- `parent_id`: ID in parent table
- `child_type`: Enum (lot_number, serial_number, work_order)
- `child_id`: ID in child table
- `relationship_type`: Enum (consumed, produced, assembled_into)
- `quantity_used`: Quantity (for lot → serial relationships)
- `recorded_at`: Timestamp

**Indexes**:
- B-tree: (parent_type, parent_id), (child_type, child_id)
- Composite: (parent_type, parent_id, relationship_type) for forward trace
- Composite: (child_type, child_id, relationship_type) for backward trace

---

## Business Rules

### BR-TRACE-001: Lot Number Uniqueness

**Rule**: Lot numbers must be unique across the organization.

**Validation**:
```python
class CreateLotNumberUseCase:
    def execute(self, dto: CreateLotDTO) -> LotNumber:
        existing = self.lot_repo.find_by_number(dto.lot_number, dto.organization_id)
        if existing:
            raise LotNumberAlreadyExistsError(dto.lot_number)

        lot = LotNumber(...)
        return self.lot_repo.save(lot)
```

### BR-TRACE-002: Serial Number Uniqueness

**Rule**: Serial numbers must be unique across the organization.

**Validation**: Same pattern as BR-TRACE-001

### BR-TRACE-003: Cannot Consume More Than Remaining Quantity

**Rule**: Material issue cannot exceed lot remaining_quantity.

**Validation**:
```python
class IssueLotMaterialUseCase:
    def execute(self, dto: IssueLotDTO) -> MaterialTransaction:
        lot = self.lot_repo.find_by_id(dto.lot_id)

        if lot.remaining_quantity < dto.quantity:
            raise InsufficientLotQuantityError(
                lot_number=lot.lot_number,
                available=lot.remaining_quantity,
                requested=dto.quantity
            )

        # Create material transaction
        transaction = MaterialTransaction(...)

        # Update lot remaining_quantity
        lot.remaining_quantity -= dto.quantity
        if lot.remaining_quantity == 0:
            lot.is_active = False  # Depleted

        # Create genealogy record (lot → work order)
        genealogy = GenealogyRecord(
            parent_type="lot_number",
            parent_id=lot.id,
            child_type="work_order",
            child_id=dto.work_order_id,
            relationship_type="consumed",
            quantity_used=dto.quantity
        )

        return self.transaction_repo.save(transaction)
```

### BR-TRACE-004: FEFO (First Expired, First Out)

**Rule**: When issuing materials, use lots with nearest expiry date first.

**Implementation**:
```python
class RecommendLotForIssueUseCase:
    def execute(self, material_id: int, quantity: float) -> List[LotNumber]:
        # Find available lots for material, ordered by expiry date
        lots = self.lot_repo.find_available_lots(
            material_id=material_id,
            min_quantity=quantity,
            order_by='expiry_date ASC NULLS LAST'  # Expiring first, non-expiring last
        )

        # Return recommended lots
        return lots[:3]  # Top 3 recommendations
```

### BR-TRACE-005: Genealogy Record Required for Production

**Rule**: When a serial number is created from a work order, a genealogy record must link the work order → serial.

**Implementation**: Automatic in CreateSerialNumberUseCase (similar to BR-TRACE-003)

---

## Use Cases

### UC-TRACE-001: Forward Trace (Lot → Serials)

**Actor**: Quality Manager

**Preconditions**: Lot number exists, genealogy records exist

**Flow**:
1. User enters lot number to trace
2. System queries genealogy_records for all serials using that lot
3. System returns list of affected serials with shipment status
4. System highlights serials already shipped (recall required)

**API**: `GET /api/v1/traceability/forward-trace?lot_number=STL304-20251107-001`

### UC-TRACE-002: Backward Trace (Serial → Lots)

**Actor**: Quality Engineer

**Preconditions**: Serial number exists, genealogy records exist

**Flow**:
1. User enters serial number to trace
2. System queries genealogy_records for all lots consumed
3. System returns BOM-style tree of materials with lot numbers

**API**: `GET /api/v1/traceability/backward-trace?serial_number=PUMP-2511-00001`

### UC-TRACE-003: Execute Product Recall

**Actor**: Quality Manager

**Preconditions**: Defective lot identified

**Flow**:
1. User initiates recall for lot STL304-001
2. System performs forward trace (UC-TRACE-001)
3. System identifies shipped products with customer info
4. System generates recall report (CSV/PDF)
5. System places lot on hold (is_active = FALSE)
6. System queues email notifications (PGMQ)

**API**: `POST /api/v1/traceability/recall`

### UC-TRACE-004: Check Expiry (FEFO Recommendation)

**Actor**: Warehouse Operator

**Preconditions**: Material with expiry dates exists

**Flow**:
1. Operator requests material for work order
2. System recommends lots with nearest expiry (BR-TRACE-004)
3. Operator issues material from recommended lot
4. System records genealogy (lot → work order)

**API**: `GET /api/v1/traceability/recommend-lot?material_id=456&quantity=10`

---

## API Endpoints

See [API_DESIGN.md](../02-architecture/API_DESIGN.md) for complete specifications.

### Traceability Endpoints (10 total)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/lot-numbers` | Create lot number |
| GET | `/api/v1/lot-numbers?material_id=456` | List lots by material |
| POST | `/api/v1/serial-numbers` | Create serial number |
| GET | `/api/v1/serial-numbers?product_id=78` | List serials by product |
| GET | `/api/v1/traceability/forward-trace` | Lot → Serials (where did it go?) |
| GET | `/api/v1/traceability/backward-trace` | Serial → Lots (where did it come from?) |
| GET | `/api/v1/traceability/recommend-lot` | FEFO lot recommendation |
| POST | `/api/v1/traceability/recall` | Execute product recall |
| GET | `/api/v1/traceability/expiring-lots` | Lots expiring within N days |
| GET | `/api/v1/genealogy-records?serial_id=123` | Get genealogy tree |

### Example: Forward Trace

```http
GET /api/v1/traceability/forward-trace?lot_number=STL304-20251107-001
Authorization: Bearer {jwt_token}
```

**Response (200 OK)**:
```json
{
  "lot_number": "STL304-20251107-001",
  "material_name": "Stainless Steel 304 Sheet 2mm",
  "supplier": "XYZ Steel Co.",
  "receipt_date": "2025-11-07",
  "total_quantity": 500.0,
  "remaining_quantity": 450.0,
  "affected_products": [
    {
      "serial_number": "PUMP-2511-00001",
      "production_date": "2025-11-08",
      "quantity_used": 2.5,
      "status": "shipped",
      "shipment_id": 456,
      "shipped_date": "2025-11-15",
      "customer_id": 34,
      "customer_name": "ABC Manufacturing",
      "recall_required": true
    },
    {
      "serial_number": "PUMP-2511-00002",
      "production_date": "2025-11-08",
      "quantity_used": 2.5,
      "status": "in_stock",
      "recall_required": false
    }
  ],
  "total_affected": 2,
  "shipped_count": 1,
  "in_stock_count": 1
}
```

### Example: Backward Trace

```http
GET /api/v1/traceability/backward-trace?serial_number=PUMP-2511-00001
Authorization: Bearer {jwt_token}
```

**Response (200 OK)**:
```json
{
  "serial_number": "PUMP-2511-00001",
  "product_name": "Hydraulic Pump Model HP-500",
  "production_date": "2025-11-08",
  "work_order_number": "WO-2025-001",
  "genealogy_tree": [
    {
      "material_name": "Stainless Steel 304 Sheet 2mm",
      "lot_number": "STL304-20251107-001",
      "supplier": "XYZ Steel Co.",
      "quantity_used": 2.5,
      "relationship": "consumed"
    },
    {
      "material_name": "Hydraulic Seal Kit",
      "lot_number": "SEAL-20251105-003",
      "supplier": "Seal Experts Inc.",
      "quantity_used": 1.0,
      "relationship": "consumed"
    },
    {
      "component_serial": "MOTOR-2511-00045",
      "component_name": "Electric Motor 2HP",
      "relationship": "assembled_into"
    }
  ]
}
```

---

## PostgreSQL-Native Features

### 1. pg_search BM25 Full-Text Search

**Purpose**: Fast lot/serial number lookup (20x faster than LIKE queries)

**Query Example**:
```sql
-- Search lots by lot number or supplier lot number
SELECT * FROM lot_numbers
WHERE lot_numbers @@@ 'STL304-2025'
ORDER BY paradedb.rank('lot_numbers_search_idx') DESC;
```

### 2. Recursive CTE for Multi-Level Genealogy

**Purpose**: Trace multi-level assemblies (e.g., motor → pump → system)

**Query Example**:
```sql
-- Recursive forward trace (all descendants)
WITH RECURSIVE genealogy_tree AS (
    -- Base case: Direct children of lot
    SELECT
        gr.child_type,
        gr.child_id,
        gr.relationship_type,
        gr.quantity_used,
        1 AS level
    FROM genealogy_records gr
    JOIN lot_numbers ln ON gr.parent_type = 'lot_number' AND gr.parent_id = ln.id
    WHERE ln.lot_number = 'STL304-20251107-001'

    UNION ALL

    -- Recursive case: Children of children
    SELECT
        gr.child_type,
        gr.child_id,
        gr.relationship_type,
        gr.quantity_used,
        gt.level + 1
    FROM genealogy_records gr
    JOIN genealogy_tree gt ON gr.parent_type = gt.child_type AND gr.parent_id = gt.child_id
)
SELECT * FROM genealogy_tree;
```

### 3. Row-Level Security (RLS) for Multi-Tenancy

**Purpose**: Tenant isolation for lot/serial numbers

---

## Summary

The Traceability domain enables complete forward/backward tracing for quality control and recall management. Key features:

- **Forward trace**: Lot → all products (recall execution)
- **Backward trace**: Product → all materials (root cause analysis)
- **FEFO**: First Expired, First Out lot selection
- **pg_search BM25**: 20x faster lot/serial lookup
- **Recursive CTE**: Multi-level genealogy queries

**Targets**:
- 100% traceability coverage
- <5 seconds trace query performance
- <1 hour recall execution time
- Zero expired material usage (FEFO enforcement)

**Compliance**: FDA 21 CFR Part 11, ISO 9001, IATF 16949

---

## Documentation Complete

**All 8 domain documentation files created**:
1. ✅ MATERIAL_MANAGEMENT.md
2. ✅ PRODUCTION.md
3. ✅ QUALITY.md
4. ✅ MAINTENANCE.md
5. ✅ EQUIPMENT_MACHINES.md
6. ✅ SHIFT_MANAGEMENT.md
7. ✅ VISUAL_SCHEDULING.md
8. ✅ TRACEABILITY.md

**Total Documentation**:
- 3 Architecture docs: DATABASE_SCHEMA.md, OVERVIEW.md, API_DESIGN.md (~4,000 lines)
- 8 Domain docs: ~5,500 lines
- **Total**: ~9,500 lines of PostgreSQL-native documentation

**Next Step**: Archive MANUFACTURING_ERP_ARCHITECTURE.md (159KB monolithic file no longer needed)
