# BOM API Quick Reference

## Endpoints Summary

| Method | Endpoint | Description | Status Code |
|--------|----------|-------------|-------------|
| POST | `/api/v1/bom` | Create BOM header | 201 |
| GET | `/api/v1/bom` | List BOMs (paginated) | 200 |
| GET | `/api/v1/bom/{id}` | Get BOM detail | 200 |
| PUT | `/api/v1/bom/{id}` | Update BOM header | 200 |
| DELETE | `/api/v1/bom/{id}` | Soft delete BOM | 204 |
| POST | `/api/v1/bom/{id}/lines` | Add BOM line | 201 |
| PUT | `/api/v1/bom/{id}/lines/{line_id}` | Update BOM line | 200 |
| DELETE | `/api/v1/bom/{id}/lines/{line_id}` | Delete BOM line | 204 |
| GET | `/api/v1/bom/{id}/tree` | Get BOM tree explosion | 200 |

## Request/Response Examples

### Create BOM Header
```bash
POST /api/v1/bom
Content-Type: application/json
Authorization: Bearer {token}

{
  "organization_id": 1,
  "plant_id": 1,
  "bom_number": "BOM-BICYCLE-001",
  "material_id": 100,
  "bom_version": 1,
  "bom_name": "Bicycle Assembly BOM",
  "bom_type": "PRODUCTION",
  "base_quantity": 1.0,
  "unit_of_measure_id": 1,
  "effective_start_date": "2025-01-01",
  "effective_end_date": null,
  "is_active": true,
  "created_by_user_id": 1
}

Response 201:
{
  "id": 1,
  "organization_id": 1,
  "plant_id": 1,
  "bom_number": "BOM-BICYCLE-001",
  "material_id": 100,
  "bom_version": 1,
  "bom_name": "Bicycle Assembly BOM",
  "bom_type": "PRODUCTION",
  "base_quantity": 1.0,
  "unit_of_measure_id": 1,
  "effective_start_date": "2025-01-01",
  "effective_end_date": null,
  "is_active": true,
  "created_by_user_id": 1,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": null,
  "bom_lines": []
}
```

### List BOMs with Filters
```bash
GET /api/v1/bom?page=1&page_size=10&material_id=100&is_active=true
Authorization: Bearer {token}

Response 200:
{
  "items": [
    {
      "id": 1,
      "bom_number": "BOM-BICYCLE-001",
      "material_id": 100,
      "bom_name": "Bicycle Assembly BOM",
      "is_active": true,
      "bom_lines": []
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### Add BOM Line (Component)
```bash
POST /api/v1/bom/1/lines
Content-Type: application/json
Authorization: Bearer {token}

{
  "bom_header_id": 1,
  "line_number": 10,
  "component_material_id": 200,
  "quantity": 1.0,
  "unit_of_measure_id": 1,
  "scrap_factor": 5.0,
  "operation_number": 10,
  "is_phantom": false,
  "backflush": false
}

Response 201:
{
  "id": 1,
  "bom_header_id": 1,
  "line_number": 10,
  "component_material_id": 200,
  "quantity": 1.0,
  "unit_of_measure_id": 1,
  "scrap_factor": 5.0,
  "operation_number": 10,
  "is_phantom": false,
  "backflush": false,
  "created_at": "2025-01-15T10:35:00Z",
  "updated_at": null
}
```

### Get BOM Tree (Multi-Level Explosion)
```bash
GET /api/v1/bom/1/tree?max_levels=10
Authorization: Bearer {token}

Response 200:
{
  "material_id": 100,
  "bom_id": 1,
  "bom_version": 1,
  "components": [
    {
      "line_id": 1,
      "component_material_id": 200,
      "quantity": 1.0,
      "scrap_factor": 5.0,
      "level": 1,
      "is_phantom": false,
      "backflush": false,
      "components": [
        {
          "line_id": 5,
          "component_material_id": 300,
          "quantity": 3.0,
          "scrap_factor": 0.0,
          "level": 2,
          "is_phantom": false,
          "backflush": true,
          "components": []
        }
      ]
    },
    {
      "line_id": 2,
      "component_material_id": 210,
      "quantity": 2.0,
      "scrap_factor": 0.0,
      "level": 1,
      "is_phantom": false,
      "backflush": false,
      "components": []
    }
  ]
}
```

### Update BOM Line
```bash
PUT /api/v1/bom/1/lines/1
Content-Type: application/json
Authorization: Bearer {token}

{
  "quantity": 2.0,
  "scrap_factor": 10.0
}

Response 200:
{
  "id": 1,
  "bom_header_id": 1,
  "line_number": 10,
  "component_material_id": 200,
  "quantity": 2.0,
  "unit_of_measure_id": 1,
  "scrap_factor": 10.0,
  "operation_number": 10,
  "is_phantom": false,
  "backflush": false,
  "created_at": "2025-01-15T10:35:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

## Query Parameters

### List BOMs
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 50, max: 100) - Items per page
- `material_id` (int, optional) - Filter by material ID
- `is_active` (bool, optional) - Filter by active status

### BOM Tree Explosion
- `max_levels` (int, default: 10, max: 20) - Maximum recursion depth

## Error Responses

### 400 Bad Request
```json
{
  "detail": "effective_end_date must be >= effective_start_date"
}
```

### 404 Not Found
```json
{
  "detail": "BOM not found"
}
```

### 409 Conflict
```json
{
  "detail": "BOM already exists for material 100 version 1"
}
```

## Business Rules

1. **Unique Constraint:** One BOM per (organization_id, plant_id, material_id, bom_version)
2. **Versioning:** Same material can have multiple BOMs with different versions
3. **Soft Delete:** DELETE sets is_active=False (preserves data)
4. **RLS Enforcement:** Users can only access BOMs in their organization
5. **Effective Dates:** end_date must be >= start_date (if both provided)
6. **Line Numbers:** Must be unique within a BOM, typically increments of 10
7. **Tree Explosion:** Uses latest active BOM version per material
8. **Circular Prevention:** Same material can appear in different branches but not create loops

## Common Use Cases

### Use Case 1: Create Multi-Level BOM
```bash
# 1. Create top-level BOM (Bicycle)
POST /api/v1/bom {...material_id: 100...}

# 2. Add Frame component (level 1)
POST /api/v1/bom/1/lines {...component_material_id: 200...}

# 3. Create Frame BOM
POST /api/v1/bom {...material_id: 200...}

# 4. Add Steel Tube to Frame (level 2)
POST /api/v1/bom/2/lines {...component_material_id: 300...}

# 5. Get full tree
GET /api/v1/bom/1/tree
```

### Use Case 2: Update BOM Component Quantity
```bash
# 1. Get current BOM
GET /api/v1/bom/1

# 2. Identify line to update (e.g., line_id: 5)

# 3. Update quantity
PUT /api/v1/bom/1/lines/5
{
  "quantity": 3.5,
  "scrap_factor": 7.5
}
```

### Use Case 3: Version Control
```bash
# 1. Create version 1
POST /api/v1/bom {...bom_version: 1...}

# 2. Make version 1 inactive
PUT /api/v1/bom/1 {"is_active": false}

# 3. Create version 2
POST /api/v1/bom {...bom_version: 2...}

# 4. Tree explosion will use v2 (latest active)
GET /api/v1/bom/2/tree
```

## Implementation Notes

- **File:** `/Users/vivek/jet/unison/backend/app/presentation/api/v1/bom.py`
- **Tests:** `/Users/vivek/jet/unison/backend/tests/integration/test_bom_api.py`
- **Router Prefix:** `/bom`
- **Tags:** `["bom"]`
- **Authentication:** All endpoints require JWT bearer token
- **RLS:** organization_id automatically filtered from JWT context
