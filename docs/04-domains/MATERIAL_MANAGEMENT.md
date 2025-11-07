# Material Management Domain

**Domain**: Material Management
**Bounded Context**: Material Master Data, Inventory Tracking, Supplier Management
**Owner**: Supply Chain & Procurement
**Status**: Core Domain (High Strategic Importance)

---

## Table of Contents

1. [Domain Overview](#domain-overview)
2. [Core Concepts](#core-concepts)
3. [Database Schema](#database-schema)
4. [Business Rules](#business-rules)
5. [Use Cases](#use-cases)
6. [API Endpoints](#api-endpoints)
7. [PostgreSQL-Native Features](#postgresql-native-features)
8. [Integration Points](#integration-points)

---

## Domain Overview

### Purpose

The Material Management domain handles all aspects of material master data, inventory tracking, and supplier relationships for manufacturing operations. It provides the foundation for production planning, procurement, and cost management across the ERP system.

### Scope

**In Scope**:
- Material master data (raw materials, components, assemblies, finished goods)
- Material categorization and classification
- Inventory tracking with real-time updates (FIFO/LIFO costing)
- Material transactions (receipts, issues, adjustments, transfers)
- Supplier management and relationships
- Request for Quotations (RFQ) workflow
- Barcode/QR code generation and scanning (async via PGMQ)
- Material search (BM25 full-text search)
- Inventory valuation and costing

**Out of Scope**:
- Purchase order processing → Procurement domain
- Bill of Materials (BOM) management → Project domain
- Production consumption tracking → Production domain
- Quality inspection of incoming materials → Quality domain

### Key Business Goals

1. **Accurate Inventory**: Real-time inventory tracking with 99%+ accuracy
2. **Cost Visibility**: FIFO/LIFO costing for accurate material valuation
3. **Fast Lookup**: <100ms material search across 10K+ SKUs (pg_search BM25)
4. **Traceability**: Full material transaction history with audit trail
5. **Supplier Performance**: Track supplier quality, lead times, and pricing
6. **Mobile-First**: PWA-based barcode scanning for material receipts/issues

---

## Core Concepts

### Material

**Definition**: A distinct item (raw material, component, subassembly, or finished good) that can be purchased, tracked, consumed, or sold.

**Key Attributes**:
- **Material Code**: Unique identifier (e.g., "MAT-SS304-001")
- **Name**: Human-readable name (e.g., "Stainless Steel 304 Sheet 2mm")
- **Category**: Classification (raw material, component, subassembly, finished good)
- **Unit of Measure**: kg, ltr, pcs, m², etc.
- **Standard Cost**: Average cost for accounting (updated periodically)
- **Barcode/QR Code**: Unique identifier for mobile scanning
- **SAP Material Number**: External system reference (optional)

**Material Types**:
```python
class MaterialType(Enum):
    RAW_MATERIAL = "raw_material"         # Steel, aluminum, fasteners
    COMPONENT = "component"               # Machined parts, electronics
    SUBASSEMBLY = "subassembly"          # Pre-assembled modules
    FINISHED_GOOD = "finished_good"      # Final products ready for shipment
    CONSUMABLE = "consumable"            # Welding wire, cutting oil, gloves
    TOOL = "tool"                        # Cutting tools, jigs, fixtures
```

### Inventory

**Definition**: Quantity of a material physically available at a specific plant location.

**Inventory Movements**:
- **Receipt**: Incoming material from supplier or production
- **Issue**: Material consumed by production or transferred out
- **Adjustment**: Corrections for physical count discrepancies
- **Transfer**: Material moved between plants (internal transfer)

**Costing Methods**:
- **FIFO** (First-In-First-Out): Oldest material consumed first (default)
- **LIFO** (Last-In-First-Out): Newest material consumed first (rare)
- **Weighted Average**: Average cost across all batches (simplified accounting)

### Material Transaction

**Definition**: A timestamped record of inventory movement (receipt, issue, adjustment, transfer).

**Transaction Types**:
```python
class TransactionType(Enum):
    RECEIPT = "receipt"                  # Incoming from supplier
    ISSUE = "issue"                      # Consumed by production
    ADJUSTMENT = "adjustment"            # Physical count correction
    TRANSFER_OUT = "transfer_out"        # Sent to another plant
    TRANSFER_IN = "transfer_in"          # Received from another plant
    RETURN_TO_SUPPLIER = "return"        # Rejected material
```

**Cost Calculation Example (FIFO)**:
```python
# Material: SS304 Sheet
# Batch 1: 100 kg @ $5/kg (oldest)
# Batch 2: 150 kg @ $6/kg
# Current inventory: 250 kg

# Issue 120 kg for production:
# Cost = (100 kg × $5) + (20 kg × $6) = $500 + $120 = $620
# Remaining inventory: 130 kg @ $6/kg
```

### Supplier

**Definition**: An external vendor that provides materials to the organization.

**Supplier Performance Metrics**:
- **Quality Rating**: % of materials passing incoming inspection
- **On-Time Delivery**: % of deliveries within lead time
- **Lead Time**: Average days from PO to receipt
- **Price Variance**: Actual price vs quoted price (%)

### Request for Quotation (RFQ)

**Definition**: A formal request sent to suppliers to obtain pricing and terms for materials.

**RFQ Workflow**:
```
Draft → Sent to Suppliers → Quotes Received → Evaluation → Award/Reject → Close
```

---

## Database Schema

### Tables (6 core tables)

See [DATABASE_SCHEMA.md](../02-architecture/DATABASE_SCHEMA.md) for full DDL with PostgreSQL-native features.

#### 1. material_categories

Hierarchical classification of materials (e.g., "Metals > Steel > Stainless > SS304").

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `name`: Category name
- `code`: Unique category code
- `parent_category_id`: Self-referencing FK for hierarchy
- `description`: Category description

**Example Hierarchy**:
```
Metals (L1)
└── Steel (L2)
    ├── Stainless Steel (L3)
    │   ├── SS304 (L4)
    │   └── SS316 (L4)
    └── Mild Steel (L3)
```

#### 2. materials

Master data for all materials tracked in the system.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `category_id`: FK to material_categories
- `material_code`: Unique identifier (e.g., "MAT-SS304-001")
- `name`: Material name
- `description`: Detailed description
- `material_type`: Enum (raw_material, component, subassembly, finished_good)
- `unit_of_measure`: kg, ltr, pcs, m², etc.
- `standard_cost`: Average cost for accounting
- `barcode_data`: Barcode/QR code value
- `sap_material_number`: External SAP reference (optional)
- `min_stock_level`: Reorder point trigger
- `max_stock_level`: Maximum inventory level
- `lead_time_days`: Procurement lead time
- `is_active`: Soft delete flag

**Indexes**:
- **pg_search BM25**: Full-text search on name, description, material_code, barcode_data, sap_material_number
- B-tree: category_id, material_type, is_active

**Row-Level Security**:
```sql
CREATE POLICY materials_tenant_isolation ON materials
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

#### 3. material_inventory

Current inventory quantities by plant.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `material_id`: FK to materials
- `plant_id`: FK to plants
- `quantity_on_hand`: Current physical quantity
- `quantity_allocated`: Reserved for production (not yet issued)
- `quantity_available`: quantity_on_hand - quantity_allocated
- `last_transaction_at`: Timestamp of most recent transaction

**Unique Constraint**: `(organization_id, material_id, plant_id)` - one inventory record per material per plant

**Indexes**:
- B-tree: material_id, plant_id
- Partial index: `WHERE quantity_on_hand < min_stock_level` (low stock alerts)

#### 4. material_transactions

Audit trail of all inventory movements (timescaledb hypertable for time-series optimization).

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `material_id`: FK to materials
- `plant_id`: FK to plants
- `transaction_type`: Enum (receipt, issue, adjustment, transfer_in, transfer_out)
- `quantity`: Signed decimal (+receipt, -issue)
- `unit_cost`: Cost per unit at transaction time
- `total_cost`: quantity × unit_cost
- `reference_type`: Related entity type (purchase_order, work_order, shipment)
- `reference_id`: Related entity ID
- `transaction_date`: Date of transaction
- `notes`: Optional transaction details
- `created_by`: FK to users (who recorded transaction)
- `created_at`: Timestamp (auto-generated)

**timescaledb Hypertable**:
```sql
SELECT create_hypertable('material_transactions', 'created_at',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- 75% compression after 7 days
ALTER TABLE material_transactions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, material_id, plant_id'
);
SELECT add_compression_policy('material_transactions', INTERVAL '7 days', if_not_exists => TRUE);

-- 3-year retention policy
SELECT add_retention_policy('material_transactions', INTERVAL '3 years', if_not_exists => TRUE);
```

**Indexes**:
- B-tree: material_id, plant_id, transaction_type
- Time-series: created_at DESC (timescaledb optimized)

#### 5. suppliers

Vendor master data.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `name`: Supplier name
- `code`: Unique supplier code
- `contact_person`: Primary contact name
- `email`: Contact email
- `phone`: Contact phone
- `address`: Supplier address
- `payment_terms`: Net 30, Net 60, etc.
- `lead_time_days`: Average delivery lead time
- `quality_rating`: Decimal (0-100) - % passing inspection
- `on_time_delivery_rating`: Decimal (0-100) - % on-time deliveries
- `is_active`: Soft delete flag

**pg_search BM25 Index**:
```sql
SELECT paradedb.create_bm25(
    table_name => 'suppliers',
    index_name => 'suppliers_search_idx',
    key_field => 'id',
    text_fields => '{name, code, contact_person, email, address}',
    numeric_fields => '{quality_rating, on_time_delivery_rating}',
    boolean_fields => '{is_active}'
);
```

#### 6. rfqs (Request for Quotations)

Procurement RFQ workflow.

**Key Columns**:
- `id`: Primary key
- `organization_id`: Multi-tenant isolation
- `rfq_number`: Unique RFQ identifier
- `material_id`: FK to materials
- `quantity`: Requested quantity
- `unit_of_measure`: kg, ltr, pcs
- `required_date`: Date material needed by
- `status`: Enum (draft, sent, quotes_received, evaluated, awarded, closed)
- `supplier_id`: FK to suppliers (if single-source)
- `notes`: RFQ details and specifications
- `created_by`: FK to users
- `created_at`: Timestamp

**RFQ Workflow States**:
```
draft → sent → quotes_received → evaluated → awarded/rejected → closed
```

---

## Business Rules

### BR-MAT-001: Material Code Uniqueness

**Rule**: Material codes must be unique within an organization.

**Validation**:
```python
class CreateMaterialUseCase:
    def execute(self, dto: CreateMaterialDTO) -> Material:
        # Check uniqueness
        existing = self.material_repo.find_by_code(dto.material_code, dto.organization_id)
        if existing:
            raise MaterialCodeAlreadyExistsError(dto.material_code)

        # Create material
        material = Material(
            material_code=dto.material_code,
            name=dto.name,
            organization_id=dto.organization_id
        )
        return self.material_repo.save(material)
```

### BR-MAT-002: Inventory Cannot Go Negative

**Rule**: Material inventory quantity_on_hand cannot be negative. Issues must be validated against available quantity.

**Validation**:
```python
class IssueMaterialUseCase:
    def execute(self, dto: IssueMaterialDTO) -> MaterialTransaction:
        # Load current inventory
        inventory = self.inventory_repo.find_by_material_and_plant(
            dto.material_id, dto.plant_id
        )

        # Validate sufficient quantity
        if inventory.quantity_available < dto.quantity:
            raise InsufficientInventoryError(
                material_id=dto.material_id,
                available=inventory.quantity_available,
                requested=dto.quantity
            )

        # Create issue transaction
        transaction = MaterialTransaction(
            material_id=dto.material_id,
            plant_id=dto.plant_id,
            transaction_type=TransactionType.ISSUE,
            quantity=-dto.quantity,  # Negative for issue
            unit_cost=self._calculate_fifo_cost(inventory, dto.quantity),
            reference_type=dto.reference_type,
            reference_id=dto.reference_id
        )

        # Save transaction and update inventory (atomic)
        return self.transaction_repo.save(transaction)
```

### BR-MAT-003: FIFO Costing

**Rule**: Material costs are calculated using FIFO (First-In-First-Out) method by default.

**Implementation**:
```python
class FIFOCostingService:
    def calculate_issue_cost(
        self,
        material_id: int,
        plant_id: int,
        quantity: Decimal
    ) -> Decimal:
        """Calculate cost using FIFO method"""
        # Get all receipt transactions ordered by date (oldest first)
        receipts = self.transaction_repo.find_receipts_by_material(
            material_id, plant_id, order_by='created_at ASC'
        )

        remaining_qty = quantity
        total_cost = Decimal('0')

        for receipt in receipts:
            available_qty = receipt.quantity - receipt.quantity_consumed

            if available_qty >= remaining_qty:
                # This batch covers remaining quantity
                total_cost += remaining_qty * receipt.unit_cost
                remaining_qty = Decimal('0')
                break
            else:
                # Consume entire batch, continue to next
                total_cost += available_qty * receipt.unit_cost
                remaining_qty -= available_qty

        if remaining_qty > 0:
            raise InsufficientInventoryError("Not enough batches to cover quantity")

        return total_cost
```

### BR-MAT-004: Barcode Uniqueness

**Rule**: Barcode/QR codes must be unique across all materials within an organization.

**Validation**:
```python
class GenerateBarcodeUseCase:
    def execute(self, dto: GenerateBarcodeDTO) -> BarcodeLabel:
        material = self.material_repo.find_by_id(dto.material_id)

        # Check if barcode already exists
        if material.barcode_data:
            raise BarcodeAlreadyExistsError(material.id, material.barcode_data)

        # Generate unique barcode (material code + checksum)
        barcode_data = self._generate_barcode_value(material.material_code)

        # Queue async job for barcode image generation (PGMQ)
        job_id = self.queue.send('barcode_generation', {
            'material_id': material.id,
            'barcode_data': barcode_data,
            'format': dto.format  # 'code128', 'qr', 'datamatrix'
        })

        # Update material with barcode data
        material.barcode_data = barcode_data
        self.material_repo.save(material)

        return BarcodeLabel(job_id=job_id, barcode_data=barcode_data)
```

### BR-MAT-005: Minimum Stock Alerts

**Rule**: When inventory falls below `min_stock_level`, trigger reorder alert (real-time via LISTEN/NOTIFY).

**Implementation**:
```sql
-- Trigger function for low stock alerts
CREATE OR REPLACE FUNCTION notify_low_stock_alert() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity_on_hand < (
        SELECT min_stock_level FROM materials WHERE id = NEW.material_id
    ) THEN
        PERFORM pg_notify('low_stock_alert',
            json_build_object(
                'material_id', NEW.material_id,
                'plant_id', NEW.plant_id,
                'quantity_on_hand', NEW.quantity_on_hand,
                'min_stock_level', (SELECT min_stock_level FROM materials WHERE id = NEW.material_id)
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER low_stock_alert_trigger
AFTER UPDATE ON material_inventory
FOR EACH ROW
WHEN (OLD.quantity_on_hand IS DISTINCT FROM NEW.quantity_on_hand)
EXECUTE FUNCTION notify_low_stock_alert();
```

**Backend WebSocket Handler**:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    conn = await asyncpg.connect(DATABASE_URL)

    # Subscribe to low stock alerts
    await conn.add_listener('low_stock_alert',
        lambda conn, pid, channel, payload:
            asyncio.create_task(websocket.send_text(payload))
    )

    # Keep connection alive
    while True:
        await asyncio.sleep(1)
```

### BR-MAT-006: Material Deactivation

**Rule**: Materials cannot be deleted if they have:
- Active inventory (quantity_on_hand > 0)
- Associated transactions
- Active BOMs referencing them

**Validation**:
```python
class DeactivateMaterialUseCase:
    def execute(self, material_id: int) -> Material:
        material = self.material_repo.find_by_id(material_id)

        # Check for active inventory
        inventory = self.inventory_repo.find_by_material(material_id)
        if any(inv.quantity_on_hand > 0 for inv in inventory):
            raise CannotDeactivateMaterialError(
                "Material has active inventory"
            )

        # Check for active BOMs (cross-domain check)
        boms = self.bom_repo.find_by_material(material_id)
        if any(bom.is_active for bom in boms):
            raise CannotDeactivateMaterialError(
                "Material is referenced in active BOMs"
            )

        # Soft delete
        material.is_active = False
        return self.material_repo.save(material)
```

---

## Use Cases

### UC-MAT-001: Create Material

**Actor**: Procurement Manager, Inventory Manager

**Preconditions**: User has `material:create` permission

**Flow**:
1. User submits material details (code, name, category, UOM, standard cost)
2. System validates material code uniqueness (BR-MAT-001)
3. System creates material record
4. System generates barcode/QR code (async via PGMQ) (BR-MAT-004)
5. System returns material ID and barcode job ID

**Postconditions**: Material exists in system, barcode generation queued

**API**: `POST /api/v1/materials`

### UC-MAT-002: Receive Material from Supplier

**Actor**: Warehouse Operator (mobile PWA)

**Preconditions**: Purchase order exists, material receipt expected

**Flow**:
1. Operator scans barcode/QR code (mobile camera)
2. System looks up material by barcode
3. Operator enters received quantity and validates against PO
4. System creates receipt transaction (transaction_type='receipt')
5. System updates material_inventory.quantity_on_hand (+quantity)
6. System calculates unit_cost from PO or weighted average
7. System triggers LISTEN/NOTIFY for real-time inventory update

**Postconditions**: Inventory increased, transaction recorded, real-time dashboard updated

**API**: `POST /api/v1/materials/receive`

### UC-MAT-003: Issue Material to Production

**Actor**: Production Supervisor

**Preconditions**: Work order exists and requires material

**Flow**:
1. Supervisor selects work order and material to issue
2. System displays available inventory (quantity_available)
3. Supervisor enters quantity to issue
4. System validates sufficient inventory (BR-MAT-002)
5. System calculates FIFO cost (BR-MAT-003)
6. System creates issue transaction (transaction_type='issue', negative quantity)
7. System updates material_inventory.quantity_on_hand (-quantity)
8. System updates work order material consumption
9. System triggers LISTEN/NOTIFY for real-time updates

**Postconditions**: Inventory decreased, work order updated, cost tracked

**API**: `POST /api/v1/materials/{id}/issue`

### UC-MAT-004: Search Materials (BM25 Full-Text)

**Actor**: Any authenticated user

**Preconditions**: User has `material:read` permission

**Flow**:
1. User enters search query (e.g., "stainless steel 304")
2. System performs pg_search BM25 full-text search
3. System ranks results by relevance
4. System returns top 20 results with highlighting

**Postconditions**: Relevant materials displayed in <100ms

**API**: `GET /api/v1/materials?search=stainless%20steel%20304`

**Backend Query**:
```python
# pg_search BM25 query (20x faster than tsvector)
results = session.execute(
    text("""
        SELECT * FROM materials
        WHERE materials @@@ :query
        ORDER BY paradedb.rank('materials_search_idx') DESC
        LIMIT 20
    """),
    {'query': 'stainless steel 304'}
).fetchall()
```

### UC-MAT-005: Generate Barcode (Async via PGMQ)

**Actor**: System (async worker)

**Preconditions**: Material created, barcode data assigned

**Flow**:
1. PGMQ worker reads message from `barcode_generation` queue
2. Worker generates barcode image (PNG) using python-barcode or qrcode
3. Worker uploads image to MinIO object storage
4. Worker creates barcode_labels record with file path
5. Worker marks PGMQ message as processed

**Postconditions**: Barcode image available at MinIO URL

**PGMQ Worker**:
```python
import pgmq
from barcode import Code128
from io import BytesIO

async def process_barcode_generation_job(msg: dict):
    # Generate barcode image
    barcode = Code128(msg['barcode_data'], writer=ImageWriter())
    buffer = BytesIO()
    barcode.write(buffer)
    buffer.seek(0)

    # Upload to MinIO
    file_path = f"barcodes/{msg['material_id']}.png"
    minio_client.put_object(
        bucket_name='unison-files',
        object_name=file_path,
        data=buffer,
        content_type='image/png'
    )

    # Save barcode label record
    label = BarcodeLabel(
        material_id=msg['material_id'],
        barcode_data=msg['barcode_data'],
        file_path=file_path
    )
    session.add(label)
    session.commit()
```

### UC-MAT-006: Physical Inventory Count (Adjustment)

**Actor**: Warehouse Manager

**Preconditions**: Periodic cycle count or annual physical inventory

**Flow**:
1. Manager initiates physical count for plant
2. Operators count material quantities
3. Manager compares physical count to system inventory
4. For discrepancies, manager creates adjustment transactions
5. System creates adjustment transaction (transaction_type='adjustment')
6. System updates material_inventory.quantity_on_hand
7. System logs adjustment reason and approver

**Postconditions**: Inventory adjusted to match physical count, discrepancies audited

**API**: `POST /api/v1/materials/{id}/adjust`

---

## API Endpoints

See [API_DESIGN.md](../02-architecture/API_DESIGN.md) for complete specifications.

### Material Endpoints (11 total)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/materials` | Create material | JWT + `material:create` |
| GET | `/api/v1/materials` | List materials (paginated, searchable) | JWT + `material:read` |
| GET | `/api/v1/materials?search=query` | Full-text search (BM25) | JWT + `material:read` |
| GET | `/api/v1/materials/{id}` | Get material details | JWT + `material:read` |
| PUT | `/api/v1/materials/{id}` | Update material | JWT + `material:update` |
| DELETE | `/api/v1/materials/{id}` | Deactivate material (soft delete) | JWT + `material:delete` |
| GET | `/api/v1/materials/{id}/inventory` | Get inventory across plants | JWT + `material:read` |
| GET | `/api/v1/materials/{id}/transactions` | Get transaction history | JWT + `material:read` |
| POST | `/api/v1/materials/receive` | Receive material from supplier | JWT + `material:receive` |
| POST | `/api/v1/materials/{id}/issue` | Issue material to production | JWT + `material:issue` |
| POST | `/api/v1/materials/{id}/adjust` | Physical inventory adjustment | JWT + `material:adjust` |
| GET | `/api/v1/materials/{id}/barcode` | Generate barcode (async via PGMQ) | JWT + `material:read` |

### Example: Create Material

```http
POST /api/v1/materials
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "material_code": "MAT-SS304-001",
  "name": "Stainless Steel 304 Sheet 2mm",
  "description": "Cold rolled SS304 sheet, 2mm thickness, 1220x2440mm",
  "category_id": 15,
  "material_type": "raw_material",
  "unit_of_measure": "sheet",
  "standard_cost": 45.50,
  "min_stock_level": 50,
  "max_stock_level": 200,
  "lead_time_days": 14,
  "sap_material_number": "100000123"
}
```

**Response (201 Created)**:
```json
{
  "id": 456,
  "material_code": "MAT-SS304-001",
  "name": "Stainless Steel 304 Sheet 2mm",
  "description": "Cold rolled SS304 sheet, 2mm thickness, 1220x2440mm",
  "category_id": 15,
  "category_name": "Stainless Steel Sheets",
  "material_type": "raw_material",
  "unit_of_measure": "sheet",
  "standard_cost": 45.50,
  "barcode_data": "MAT-SS304-001-CHK789",
  "barcode_job_id": "barcode_gen_12345",
  "min_stock_level": 50,
  "max_stock_level": 200,
  "lead_time_days": 14,
  "sap_material_number": "100000123",
  "is_active": true,
  "created_at": "2025-11-07T17:30:00Z",
  "updated_at": "2025-11-07T17:30:00Z"
}
```

### Example: Search Materials (BM25)

```http
GET /api/v1/materials?search=stainless%20steel%20304&limit=20
Authorization: Bearer {jwt_token}
```

**Backend Query (pg_search BM25)**:
```sql
SELECT * FROM materials
WHERE materials @@@ 'stainless steel 304'
ORDER BY paradedb.rank('materials_search_idx') DESC
LIMIT 20;
```

**Response (200 OK)**:
```json
{
  "items": [
    {
      "id": 456,
      "material_code": "MAT-SS304-001",
      "name": "Stainless Steel 304 Sheet 2mm",
      "description": "Cold rolled SS304 sheet...",
      "relevance_score": 15.3
    },
    {
      "id": 457,
      "material_code": "MAT-SS304-002",
      "name": "Stainless Steel 304 Pipe 50mm",
      "description": "SS304 seamless pipe...",
      "relevance_score": 12.8
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "query": "stainless steel 304",
  "execution_time_ms": 5
}
```

### Example: Issue Material to Production

```http
POST /api/v1/materials/456/issue
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "quantity": 25,
  "plant_id": 1,
  "reference_type": "work_order",
  "reference_id": 789,
  "notes": "Material issued for WO-2025-001"
}
```

**Response (201 Created)**:
```json
{
  "transaction_id": 12345,
  "material_id": 456,
  "material_code": "MAT-SS304-001",
  "transaction_type": "issue",
  "quantity": -25,
  "unit_cost": 45.50,
  "total_cost": 1137.50,
  "plant_id": 1,
  "reference_type": "work_order",
  "reference_id": 789,
  "remaining_inventory": 175,
  "created_at": "2025-11-07T17:45:00Z"
}
```

---

## PostgreSQL-Native Features

### 1. pg_search BM25 Full-Text Search

**Purpose**: Fast, relevance-ranked material search (20x faster than tsvector)

**Index Creation**:
```sql
SELECT paradedb.create_bm25(
    table_name => 'materials',
    index_name => 'materials_search_idx',
    key_field => 'id',
    text_fields => '{name, description, material_code, barcode_data, sap_material_number}',
    numeric_fields => '{standard_cost}',
    boolean_fields => '{is_active}'
);
```

**Query Performance**:
- **pg_search BM25**: 5ms average for 10K materials
- **PostgreSQL tsvector**: 100ms average for 10K materials
- **Improvement**: 20x faster

### 2. timescaledb Hypertable (material_transactions)

**Purpose**: Time-series optimization for transaction history with 75% compression

**Hypertable Setup**:
```sql
SELECT create_hypertable('material_transactions', 'created_at',
    chunk_time_interval => INTERVAL '1 month'
);

-- Compression policy (after 7 days)
ALTER TABLE material_transactions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'organization_id, material_id, plant_id'
);
SELECT add_compression_policy('material_transactions', INTERVAL '7 days');

-- Retention policy (3 years)
SELECT add_retention_policy('material_transactions', INTERVAL '3 years');
```

**Query Performance**:
- **Standard PostgreSQL**: 2s for 1M transactions
- **timescaledb**: 200ms for 1M transactions
- **Improvement**: 10x faster

### 3. LISTEN/NOTIFY for Real-Time Inventory Updates

**Purpose**: Pub/sub messaging for live dashboard updates (no polling required)

**Trigger Setup**:
```sql
CREATE OR REPLACE FUNCTION notify_inventory_update() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('inventory_updated',
        json_build_object(
            'material_id', NEW.material_id,
            'plant_id', NEW.plant_id,
            'quantity_on_hand', NEW.quantity_on_hand,
            'quantity_available', NEW.quantity_available,
            'timestamp', NOW()
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER inventory_update_notify
AFTER UPDATE ON material_inventory
FOR EACH ROW
WHEN (OLD.quantity_on_hand IS DISTINCT FROM NEW.quantity_on_hand)
EXECUTE FUNCTION notify_inventory_update();
```

**WebSocket Integration**:
```python
# Backend (FastAPI + asyncpg)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    conn = await asyncpg.connect(DATABASE_URL)

    await conn.add_listener('inventory_updated',
        lambda conn, pid, channel, payload:
            asyncio.create_task(websocket.send_text(payload))
    )

    # Keep alive
    while True:
        await asyncio.sleep(1)
```

```javascript
// Frontend (React)
const ws = new WebSocket(`wss://api.example.com/ws?token=${token}`);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  if (update.event === 'inventory_updated') {
    updateInventoryDashboard(update.data);
  }
};
```

### 4. PGMQ for Async Barcode Generation

**Purpose**: Message queue for background jobs (30K msgs/sec)

**Queue Setup**:
```sql
SELECT pgmq.create('barcode_generation');
```

**Send Job**:
```python
# API handler
queue.send('barcode_generation', {
    'material_id': 456,
    'barcode_data': 'MAT-SS304-001-CHK789',
    'format': 'code128'
})
```

**Worker Process**:
```python
# PGMQ worker
while True:
    msg = queue.read('barcode_generation', vt=30, qty=10)
    for m in msg:
        process_barcode_generation_job(m['message'])
        queue.archive('barcode_generation', m['msg_id'])
```

### 5. Row-Level Security (RLS) for Multi-Tenancy

**Purpose**: Database-level tenant isolation (no application-level filtering)

**Policy Setup**:
```sql
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;

CREATE POLICY materials_tenant_isolation ON materials
    USING (organization_id = current_setting('app.current_organization_id')::INTEGER);
```

**Context Setting (JWT Middleware)**:
```python
def set_rls_context(db: Session, organization_id: int):
    db.execute(text(f"SET app.current_organization_id = {organization_id}"))
```

**Result**: All queries automatically filtered by organization_id - no SQL injection risk, no accidental cross-tenant data leaks.

---

## Integration Points

### Upstream Dependencies (Data Consumed)

1. **Multi-Tenancy Domain** (`organizations`, `plants`)
   - Material belongs to organization
   - Inventory tracked by plant
   - RLS context from JWT

2. **User Domain** (`users`)
   - Transaction created_by references users
   - Material created_by, updated_by

### Downstream Consumers (Data Provided)

1. **Project Domain** (Bill of Materials)
   - BOM line items reference materials
   - Material costs for project budgeting

2. **Production Domain** (Work Orders)
   - Work order material requirements
   - Material consumption tracking via issues

3. **Quality Domain** (Inspections)
   - Incoming inspection for received materials
   - Non-conformance reports for defective materials

4. **Procurement Domain** (Purchase Orders)
   - PO line items reference materials
   - Material receipts from PO deliveries

5. **Logistics Domain** (Shipments)
   - Shipment items reference materials
   - Material transfers between plants

6. **SAP Integration**
   - Material master sync (inbound/outbound)
   - SAP material numbers mapped to internal IDs

### External Integrations

1. **MinIO Object Storage**
   - Barcode/QR code images stored at `minio:9000/unison-files/barcodes/`
   - API: S3-compatible REST API

2. **SAP ERP** (Optional)
   - Material master data sync via REST API
   - Mapping table: `sap_mappings(entity_type='material')`

---

## Summary

The Material Management domain provides the foundation for inventory tracking, costing, and procurement across the manufacturing ERP. Key PostgreSQL-native features include:

- **pg_search BM25**: 20x faster material search
- **timescaledb**: 10x faster transaction history queries with 75% compression
- **LISTEN/NOTIFY**: Real-time inventory updates via WebSocket (no polling)
- **PGMQ**: 30K msgs/sec async barcode generation
- **RLS**: Database-level tenant isolation (security + simplicity)

**Performance Targets**:
- Material search: <100ms for 10K+ SKUs
- Inventory updates: <50ms with real-time notifications
- Transaction history: <200ms for 1M+ records
- Barcode generation: 2-5 seconds (async)

**Next Domain**: [PRODUCTION.md](./PRODUCTION.md) - Work Order Management and Production Logging
