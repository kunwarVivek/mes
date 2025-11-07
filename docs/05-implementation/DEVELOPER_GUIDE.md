# Developer Quick Start Guide

## Backend Development (DDD)

### Adding a New Feature

Follow DDD layers from inside-out:

#### 1. Domain Layer

**Create Entity:**
```python
# app/domain/entities/product.py
class Product:
    def __init__(self, id, name, price):
        self._id = id
        self._name = name
        self._price = price
```

**Create Value Object:**
```python
# app/domain/value_objects/price.py
class Price:
    def __init__(self, amount: float):
        if amount < 0:
            raise DomainValidationException("Price cannot be negative")
        self._amount = amount
```

**Create Repository Interface:**
```python
# app/domain/repositories/product_repository.py
class IProductRepository(ABC):
    @abstractmethod
    def create(self, product: Product) -> Product:
        pass
```

#### 2. Application Layer

**Create DTO:**
```python
# app/application/dtos/product_dto.py
class CreateProductDTO(BaseModel):
    name: str
    price: float
```

**Create Use Case:**
```python
# app/application/use_cases/product/create_product.py
class CreateProductUseCase:
    def __init__(self, product_repository: IProductRepository):
        self._repository = product_repository

    def execute(self, dto: CreateProductDTO) -> Product:
        product = Product(...)
        return self._repository.create(product)
```

#### 3. Infrastructure Layer

**Create Database Model:**
```python
# app/infrastructure/persistence/models.py
class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
```

**Create Repository Implementation:**
```python
# app/infrastructure/persistence/product_repository_impl.py
class ProductRepository(IProductRepository):
    def create(self, product: Product) -> Product:
        db_product = self._mapper.to_model(product)
        self._db.add(db_product)
        self._db.commit()
        return self._mapper.to_entity(db_product)
```

#### 4. Presentation Layer

**Create API Endpoint:**
```python
# app/presentation/api/v1/products.py
@router.post("/", response_model=ProductResponseDTO)
def create_product(
    dto: CreateProductDTO,
    repository: ProductRepository = Depends(get_repository)
):
    use_case = CreateProductUseCase(repository)
    return use_case.execute(dto)
```

### Running Database Migrations

```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Add products table"

# Apply migration
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

---

## Frontend Development (Atomic Design)

### Adding a New Component

Follow Atomic Design hierarchy from bottom-up:

#### 1. Create Atom

```tsx
// src/design-system/atoms/Badge.tsx
export interface BadgeProps {
  variant?: 'success' | 'warning' | 'error'
  children: ReactNode
}

export const Badge = ({ variant = 'success', children }: BadgeProps) => {
  return (
    <span className={`badge badge--${variant}`}>
      {children}
    </span>
  )
}
```

```css
/* src/design-system/atoms/Badge.css */
.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-full);
  font-size: 0.875rem;
  font-weight: 500;
}

.badge--success {
  background-color: var(--color-success);
  color: white;
}
```

#### 2. Create Molecule

```tsx
// src/design-system/molecules/StatusCard.tsx
import { Card, Badge } from '../atoms'

export const StatusCard = ({ title, status, description }) => {
  return (
    <Card variant="elevated" padding="md">
      <div className="status-card">
        <h3>{title}</h3>
        <Badge variant={status}>{status}</Badge>
        <p>{description}</p>
      </div>
    </Card>
  )
}
```

#### 3. Create Organism

```tsx
// src/design-system/organisms/ProductGrid.tsx
import { StatusCard } from '../molecules'

export const ProductGrid = ({ products }) => {
  return (
    <div className="product-grid">
      {products.map(product => (
        <StatusCard
          key={product.id}
          title={product.name}
          status={product.status}
          description={product.description}
        />
      ))}
    </div>
  )
}
```

#### 4. Create Page

```tsx
// src/pages/ProductsPage.tsx
import { ProductGrid } from '@/design-system/organisms'

export const ProductsPage = () => {
  const { data: products } = useProducts()

  return (
    <div className="products-page">
      <Header title="Products" />
      <main>
        <ProductGrid products={products} />
      </main>
    </div>
  )
}
```

### Using Design System Tokens

Always use CSS variables from the design system:

```css
/* ❌ Bad */
.my-component {
  color: #0ea5e9;
  padding: 16px;
  border-radius: 8px;
}

/* ✅ Good */
.my-component {
  color: var(--color-primary-500);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
}
```

### Creating API Services

```typescript
// src/services/product.service.ts
export const productService = {
  getProducts: async (): Promise<Product[]> => {
    const response = await apiClient.get('/api/v1/products/')
    return response.data
  },

  createProduct: async (data: CreateProductDto): Promise<Product> => {
    const response = await apiClient.post('/api/v1/products/', data)
    return response.data
  },
}
```

### Creating TanStack Query Hooks

```typescript
// src/hooks/useProducts.ts
export const useProducts = () => {
  return useQuery({
    queryKey: ['products'],
    queryFn: productService.getProducts,
  })
}

export const useCreateProduct = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: productService.createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    },
  })
}
```

---

## Code Style Guidelines

### Backend

**Python Style (PEP 8 + DDD)**

```python
# ✅ Good: Clear separation, explicit types
class CreateUserUseCase:
    """Single Responsibility: Create new users"""

    def __init__(self, user_repository: IUserRepository):
        self._repository = user_repository

    def execute(self, dto: CreateUserDTO) -> User:
        email = Email(dto.email)
        username = Username(dto.username)

        if self._repository.exists_by_email(email):
            raise DuplicateEntityException("Email already registered")

        user = User(...)
        return self._repository.create(user)

# ❌ Bad: Mixed concerns, unclear types
def create_user(email, username, password, db):
    if db.query(User).filter_by(email=email).first():
        raise Exception("Email exists")
    user = User(email=email, username=username, password=hash(password))
    db.add(user)
    db.commit()
    return user
```

### Frontend

**TypeScript Style (Atomic Design)**

```tsx
// ✅ Good: Explicit props, documented, typed
/**
 * Button Atom
 * Single Responsibility: Button interaction
 */
export interface ButtonProps {
  variant?: 'primary' | 'secondary'
  onClick?: () => void
  children: ReactNode
}

export const Button = ({ variant = 'primary', onClick, children }: ButtonProps) => {
  return (
    <button className={`button button--${variant}`} onClick={onClick}>
      {children}
    </button>
  )
}

// ❌ Bad: Unclear props, no types
export const Button = ({ type, click, text }) => {
  return <button className={type} onClick={click}>{text}</button>
}
```

---

## Testing

### Backend Tests

```python
# tests/unit/domain/test_email.py
def test_email_validation():
    # Valid email
    email = Email("user@example.com")
    assert email.value == "user@example.com"

    # Invalid email
    with pytest.raises(DomainValidationException):
        Email("invalid-email")

# tests/integration/use_cases/test_create_user.py
def test_create_user_use_case(in_memory_repository):
    use_case = CreateUserUseCase(in_memory_repository)
    dto = CreateUserDTO(email="test@example.com", username="testuser", password="password123")

    user = use_case.execute(dto)

    assert user.email.value == "test@example.com"
    assert user.username.value == "testuser"
```

### Frontend Tests

```tsx
// src/design-system/atoms/__tests__/Button.test.tsx
describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    fireEvent.click(screen.getByText('Click me'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

---

## Common Patterns

### Error Handling

**Backend:**
```python
# Use domain exceptions
if not user:
    raise EntityNotFoundException(f"User {id} not found")

# API layer catches and converts
except EntityNotFoundException as e:
    raise HTTPException(status_code=404, detail=str(e))
```

**Frontend:**
```tsx
// Display user-friendly errors
{error && (
  <div className="error-message" role="alert">
    {error.response?.data?.detail || 'Something went wrong'}
  </div>
)}
```

### Validation

**Backend (Value Objects):**
```python
class Username:
    def __init__(self, value: str):
        if len(value) < 3:
            raise DomainValidationException("Username too short")
```

**Frontend (Form Components):**
```tsx
const validate = () => {
  if (username.length < 3) {
    setError('Username must be at least 3 characters')
  }
}
```

---

## Debugging Tips

### Backend

```python
# Use logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Creating user: {dto.email}")

# Use debugger
import pdb; pdb.set_trace()
```

### Frontend

```tsx
// Use React DevTools
// Console logging
console.log('User data:', user)

// TanStack Query DevTools (already included)
```

---

## Performance Optimization

### Backend

- Use database indexes on frequently queried fields
- Implement pagination for large datasets
- Use async/await for I/O operations
- Cache frequently accessed data

### Frontend

- Lazy load components with React.lazy()
- Use TanStack Query caching effectively
- Optimize images and assets
- Implement virtual scrolling for long lists

---

## Deployment Checklist

### Backend

- [ ] Update `SECRET_KEY` in production
- [ ] Set proper `BACKEND_CORS_ORIGINS`
- [ ] Run migrations on production database
- [ ] Set up error monitoring (Sentry)
- [ ] Configure logging

### Frontend

- [ ] Update `VITE_API_URL` for production
- [ ] Build optimized bundle (`npm run build`)
- [ ] Test in production-like environment
- [ ] Set up CDN for static assets

---

## Resources

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed architecture documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Atomic Design Methodology](https://bradfrost.com/blog/post/atomic-web-design/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
