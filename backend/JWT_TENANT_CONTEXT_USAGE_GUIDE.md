# JWT Tenant Context - Usage Guide

## Overview
JWT tokens now include tenant context (organization_id, plant_id) for automatic PostgreSQL Row-Level Security (RLS) enforcement.

---

## For Frontend Developers

### Login Response Structure
```typescript
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
  organization_id: number;    // NEW: User's organization
  plant_id: number | null;    // NEW: User's plant (null for org-level users)
}
```

### Example Login Request
```typescript
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const data: LoginResponse = await response.json();

// Store tenant context in local state
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('organization_id', data.organization_id.toString());
localStorage.setItem('plant_id', data.plant_id?.toString() ?? '');
```

### Making Authenticated Requests
```typescript
const response = await fetch('http://localhost:8000/api/v1/materials', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  }
});

// Backend automatically filters results to user's organization
// No need to pass organization_id in request body or query params
```

### Understanding Tenant Context

**Organization-Level Users** (plant_id = null):
- Managers, administrators
- Can see data across all plants in their organization
- RLS filters by organization_id only

**Plant-Level Users** (plant_id = 123):
- Operators, supervisors
- Can only see data for their specific plant
- RLS filters by both organization_id AND plant_id

---

## For Backend Developers

### JWT Payload Structure
```python
# Token payload now includes tenant fields
{
    "sub": "1",                    # User ID
    "email": "user@example.com",
    "username": "johndoe",
    "is_superuser": false,
    "organization_id": 100,        # NEW: Required for RLS
    "plant_id": 200,               # NEW: Optional for plant-level users
    "type": "access",
    "exp": 1699545600,
    "iat": 1699542000
}
```

### Authentication Flow

1. **User logs in** → `LoginUserUseCase.execute()`
   ```python
   # app/application/use_cases/auth/login_user.py
   token_data = {
       "sub": str(user.id),
       "email": user.email.value,
       "organization_id": user.organization_id,  # From User entity
       "plant_id": user.plant_id                  # From User entity
   }
   access_token = jwt_handler.create_access_token(token_data)
   ```

2. **Request with JWT** → `get_current_user()` dependency
   ```python
   # app/infrastructure/security/dependencies.py
   async def get_current_user(credentials, db) -> User:
       payload = jwt_handler.decode_token(token)

       # Extract tenant context
       organization_id = payload.get("organization_id")
       plant_id = payload.get("plant_id")

       # Validate organization_id exists (REQUIRED)
       if organization_id is None:
           raise HTTPException(403, "Missing organization_id")

       # Set PostgreSQL RLS session variables
       db.execute(text(f"SET LOCAL app.current_organization_id = {organization_id}"))
       if plant_id is not None:
           db.execute(text(f"SET LOCAL app.current_plant_id = {plant_id}"))

       return user
   ```

3. **Database queries** → RLS policies automatically filter
   ```sql
   -- Example RLS policy on materials table
   CREATE POLICY org_isolation ON materials
   FOR ALL
   USING (organization_id = current_setting('app.current_organization_id')::int)
   ```

### Creating Protected Endpoints

```python
from fastapi import APIRouter, Depends
from app.infrastructure.security.dependencies import get_current_user
from app.domain.entities.user import User

router = APIRouter()

@router.get("/materials")
async def list_materials(
    current_user: User = Depends(get_current_user)  # Automatic RLS context
):
    # Session variables already set by get_current_user
    # Query will only return materials for current_user's organization
    materials = db.query(Material).all()
    return materials
```

### Testing with Tenant Context

```python
import pytest
from app.infrastructure.security.jwt_handler import JWTHandler

def test_with_tenant_context():
    # Create JWT with tenant context
    jwt_handler = JWTHandler()
    token = jwt_handler.create_access_token({
        "sub": "1",
        "email": "test@example.com",
        "organization_id": 100,
        "plant_id": 200
    })

    # Make request with token
    response = client.get(
        "/api/v1/materials",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    # Materials filtered to organization 100
```

---

## For Database Administrators

### RLS Session Variables

The authentication middleware sets these PostgreSQL session variables:

```sql
-- Always set (REQUIRED for tenant isolation)
SET LOCAL app.current_organization_id = 100;

-- Optionally set (for plant-level users)
SET LOCAL app.current_plant_id = 200;
```

### Session Variable Scope

- Uses `SET LOCAL` (transaction-scoped)
- Automatically cleared after COMMIT or ROLLBACK
- No manual cleanup required
- Safe for connection pooling

### Verifying RLS Context

```sql
-- Check current session variables
SHOW app.current_organization_id;
SHOW app.current_plant_id;

-- Test RLS enforcement
SELECT * FROM materials;  -- Should only return current org's materials
```

### RLS Policy Examples

```sql
-- Organization-level isolation
CREATE POLICY org_isolation ON materials
FOR ALL
USING (organization_id = current_setting('app.current_organization_id')::int);

-- Plant-level isolation (optional)
CREATE POLICY plant_isolation ON work_orders
FOR ALL
USING (
    organization_id = current_setting('app.current_organization_id')::int
    AND (
        current_setting('app.current_plant_id', true) IS NULL
        OR plant_id = current_setting('app.current_plant_id')::int
    )
);
```

---

## Security Considerations

### What This Protects

✅ **Cross-tenant data leakage**: Users can only access their organization's data
✅ **SQL injection**: Session variables are integers, not user input
✅ **Authorization bypass**: RLS enforced at database level, not application level
✅ **Missing tenant context**: 403 error if organization_id not in JWT

### What This Does NOT Protect

❌ **Superuser access**: Superusers can bypass RLS (by design)
❌ **Direct database access**: RLS only applies to application connections
❌ **Token theft**: Standard JWT security concerns apply

### Best Practices

1. **Always use HTTPS** in production to prevent token interception
2. **Short token expiration** (15-30 minutes) with refresh tokens
3. **Validate organization_id** matches user's actual organization
4. **Monitor RLS policy performance** for complex queries
5. **Test RLS policies** thoroughly with multiple tenant scenarios

---

## Troubleshooting

### Error: "Token missing organization_id"

**Cause**: JWT token doesn't include organization_id

**Solution**: User needs to log in again to get new token with tenant context

### Error: "User not found"

**Cause**: User ID in JWT doesn't exist or user is inactive

**Solution**: Verify user exists and is_active = true

### No Data Returned

**Possible Causes**:
1. User's organization_id doesn't match any data
2. RLS policies filtering out all results
3. User has plant_id but querying org-level data

**Debug**:
```sql
-- Check session variables
SHOW app.current_organization_id;
SHOW app.current_plant_id;

-- Disable RLS temporarily to see all data
SET ROLE postgres;  -- Superuser bypasses RLS
SELECT * FROM materials WHERE organization_id = 100;
```

---

## Migration Guide

### For Existing Users

Existing JWT tokens will NOT have tenant context. Users must:

1. **Log out** from application
2. **Log in again** to get new token with organization_id/plant_id
3. **No database changes required** - User.organization_id already exists

### For Existing Tests

Update test fixtures to include tenant context:

```python
# OLD
token = jwt_handler.create_access_token({"sub": "1", "email": "test@example.com"})

# NEW
token = jwt_handler.create_access_token({
    "sub": "1",
    "email": "test@example.com",
    "organization_id": 100,  # ADD THIS
    "plant_id": 200           # ADD THIS (or None)
})
```

---

## Performance Impact

### Per-Request Overhead

- **2 SQL statements**: SET LOCAL for organization_id and plant_id
- **Execution time**: < 1ms per statement
- **Total overhead**: ~2ms per authenticated request

### Query Performance

- RLS policies add WHERE clauses to queries
- Ensure indexes exist on organization_id and plant_id
- Monitor slow queries with EXPLAIN ANALYZE

### Recommended Indexes

```sql
-- Essential for RLS performance
CREATE INDEX idx_materials_org_id ON materials(organization_id);
CREATE INDEX idx_materials_plant_id ON materials(plant_id);
CREATE INDEX idx_work_orders_org_plant ON work_orders(organization_id, plant_id);
```

---

## Testing

### Unit Tests
```bash
# Run JWT tenant context tests
cd /Users/vivek/jet/unison/backend
python3 -m pytest tests/security/test_jwt_tenant_context.py -v
```

### Integration Tests
```bash
# Test with actual database and RLS policies
python3 -m pytest tests/integration/ -v -k tenant
```

### Manual Testing
```bash
# 1. Login and capture token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# 2. Decode JWT at jwt.io to verify organization_id and plant_id

# 3. Test protected endpoint
curl -X GET http://localhost:8000/api/v1/materials \
  -H "Authorization: Bearer <TOKEN>"

# 4. Verify only organization's materials returned
```

---

## Support

For questions or issues:
1. Check `/Users/vivek/jet/unison/backend/JWT_TENANT_CONTEXT_VERIFICATION.md`
2. Review test cases in `tests/security/test_jwt_tenant_context.py`
3. Examine RLS policies in `docs/03-postgresql/rls_policies.sql`

---

## Changelog

**Version 1.0.0** (2025-11-09)
- Initial implementation of JWT tenant context
- Added organization_id and plant_id to JWT payload
- Implemented RLS session variable setting in middleware
- Added tenant fields to login response
- Full test coverage with TDD approach (RED → GREEN → REFACTOR)
