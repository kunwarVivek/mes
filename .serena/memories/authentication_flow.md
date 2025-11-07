# Authentication & Authorization Flow

## JWT Authentication

### Login Flow
1. **User submits credentials** → `POST /api/v1/auth/login`
   ```json
   {
     "email": "user@example.com",
     "password": "password123"
   }
   ```

2. **Backend validates** via `LoginUserUseCase`:
   - Get user from repository by email
   - Verify password with bcrypt
   - Check if user is active

3. **Generate JWT tokens**:
   - Access token (expires in 30 min)
   - Refresh token (expires in 7 days)

4. **Response**:
   ```json
   {
     "access_token": "eyJ...",
     "refresh_token": "eyJ...",
     "token_type": "bearer",
     "expires_at": "2024-01-01T12:00:00"
   }
   ```

5. **Frontend stores tokens** in Zustand (persisted to localStorage)

### Protected Routes
```python
# Backend dependency
from app.infrastructure.security.dependencies import get_current_user

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    return {"user": current_user.username}
```

### Token Refresh Flow
1. **Access token expires** → 401 response
2. **Frontend intercepts** in axios interceptor
3. **Calls refresh endpoint** → `POST /api/v1/auth/refresh`
4. **Backend validates refresh token** via `RefreshTokenUseCase`
5. **Returns new token pair**
6. **Frontend retries original request**

## RBAC with Casbin

### Roles Defined
- **user**: Read users, write own profile
- **admin**: Read, write, delete users
- **superuser**: Inherits admin role

### Policy Model (casbin_model.conf)
```
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

### Using RBAC in Endpoints
```python
from app.infrastructure.security.rbac_dependencies import require_permission

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission("users", "delete"))
):
    # Only admin/superuser can access
    ...
```

### Role Assignment
- Determined by `is_superuser` flag in User entity
- Superuser → admin role
- Regular user → user role
- Can be extended with user_roles table for complex scenarios

## Security Best Practices Applied
✅ Password hashing with bcrypt
✅ JWT with expiration
✅ Refresh token rotation
✅ Role-based access control
✅ Bearer token authentication
✅ CORS configuration
✅ Token validation on every request
