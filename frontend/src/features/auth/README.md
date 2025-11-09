# AuthFlow - Authentication Feature

Complete authentication flow implementation with Login, Register pages, and route protection built using TDD methodology.

## Overview

The AuthFlow feature provides a complete authentication system including:
- User login and registration
- Protected route wrapper
- Persistent authentication state
- Form validation and error handling
- Mock API integration (ready for real API)

## Components

### 1. Auth Store (`stores/authStore.ts`)

Zustand store managing authentication state:

```typescript
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: User, token: string) => void
  clearAuth: () => void
  setLoading: (isLoading: boolean) => void
}
```

**Features**:
- Token persistence in localStorage
- SSR-safe implementation
- Centralized auth state management

### 2. useAuth Hook (`hooks/useAuth.ts`)

Authentication operations hook:

```typescript
interface UseAuthReturn {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterFormData) => Promise<void>
  logout: () => void
}
```

**Features**:
- Login/register/logout operations
- Mock API integration
- Loading state management
- Error handling

### 3. ProtectedRoute (`components/ProtectedRoute.tsx`)

Route wrapper requiring authentication:

```typescript
interface ProtectedRouteProps {
  children: ReactNode
  fallback?: ReactNode
}
```

**Features**:
- Redirects unauthenticated users to /login
- Optional loading fallback
- Preserves auth state

### 4. LoginPage (`pages/LoginPage.tsx`)

Login form with validation:

**Form Fields**:
- Email (validated)
- Password (min 8 chars)
- Remember me checkbox
- Forgot password link

**Features**:
- Email format validation
- Password length validation
- Error message display
- Loading states
- Redirects to /dashboard on success

### 5. RegisterPage (`pages/RegisterPage.tsx`)

Registration form with validation:

**Form Fields**:
- Full name
- Email (validated)
- Organization name
- Password (min 8 chars)
- Confirm password (must match)

**Features**:
- Comprehensive validation
- Password confirmation check
- Error message display
- Loading states
- Redirects to /login on success

## Usage

### Basic Authentication Flow

```typescript
import { useAuth, ProtectedRoute } from '@/features/auth'

// In a component
function MyComponent() {
  const { login, register, logout, isAuthenticated, user } = useAuth()

  const handleLogin = async () => {
    try {
      await login('test@example.com', 'password123')
      // Redirect to dashboard
    } catch (error) {
      // Handle error
    }
  }

  return (
    <div>
      {isAuthenticated ? (
        <p>Welcome, {user?.name}</p>
      ) : (
        <button onClick={handleLogin}>Login</button>
      )}
    </div>
  )
}
```

### Protected Routes

```typescript
import { ProtectedRoute } from '@/features/auth'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
```

### Using Auth Pages

```typescript
import { LoginPage, RegisterPage } from '@/features/auth'

function AuthRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}
```

## Form Validation Rules

### Email
- Required
- Valid email format: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`

### Password
- Required
- Minimum 8 characters

### Registration
- All fields required
- Password and confirm password must match

## Mock API

The current implementation uses mock APIs for development:

### Login
- **Success**: `email === 'test@example.com' && password === 'password123'`
- **Failure**: Throws 'Invalid credentials'

### Register
- **Success**: All required fields filled, passwords match
- **Failure**: Throws error message

**To replace with real API**: Update `mockLogin` and `mockRegister` functions in `hooks/useAuth.ts`

## State Persistence

- **Token**: Stored in localStorage as 'token'
- **User**: Not persisted (fetched on page load with token)
- **Auto-logout**: Token cleared from localStorage on logout

## Security Considerations

✅ **Token-only storage** - No passwords in localStorage
✅ **Input sanitization** - Form validation prevents invalid data
✅ **HTTPS required** - For production deployment
⚠️ **CSRF protection** - To be implemented with real API
⚠️ **Token refresh** - To be implemented for session management

## Testing

All components have comprehensive test coverage:

```bash
npm test -- src/features/auth/__tests__/AuthFlow.test.tsx
```

**Test Coverage**:
- 22 tests covering all authentication flows
- 100% component coverage
- Edge cases: validation, errors, loading states
- Integration testing: form submission, API calls, redirects

See `AUTHFLOW_TDD_EVIDENCE.md` for detailed TDD methodology and test results.

## File Structure

```
features/auth/
├── __tests__/
│   └── AuthFlow.test.tsx          # Comprehensive test suite
├── components/
│   └── ProtectedRoute.tsx         # Route protection HOC
├── hooks/
│   └── useAuth.ts                 # Authentication hook
├── pages/
│   ├── LoginPage.tsx              # Login form
│   ├── LoginPage.css              # Login styles
│   ├── RegisterPage.tsx           # Registration form
│   └── RegisterPage.css           # Registration styles
├── stores/
│   └── authStore.ts               # Zustand auth store
├── index.ts                       # Feature exports
├── README.md                      # This file
└── AUTHFLOW_TDD_EVIDENCE.md       # TDD methodology evidence
```

## Dependencies

- `react` - UI framework
- `react-router-dom` - Routing and navigation
- `zustand` - State management
- `@testing-library/react` - Testing utilities
- `@testing-library/user-event` - User interaction testing
- `vitest` - Test runner

## Design System Integration

Uses existing design system components:
- `AuthLayout` - Authentication page template
- `Input` - Form input atom
- `Button` - Button atom with loading states
- `Checkbox` - Checkbox atom

## Future Enhancements

1. **API Integration**
   - Replace mock APIs with real backend endpoints
   - Add API error handling and retry logic

2. **Token Management**
   - Implement automatic token refresh
   - Add token expiration handling

3. **Password Reset**
   - Forgot password flow
   - Email verification
   - Password reset page

4. **Enhanced Security**
   - Two-factor authentication (2FA)
   - OAuth social login providers
   - CSRF protection
   - Rate limiting

5. **UX Improvements**
   - Email verification after registration
   - Remember device option
   - Session timeout warnings
   - Better error messages

6. **Analytics**
   - Track login/registration events
   - Monitor authentication failures
   - User session analytics

## Contributing

When adding new authentication features:
1. Write tests first (TDD approach)
2. Follow existing component patterns
3. Update this README
4. Maintain test coverage above 90%

## License

Part of the Unison Manufacturing ERP system.
