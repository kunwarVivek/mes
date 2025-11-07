# Development Workflow

## Adding a New Feature (Backend)

### 1. Domain Layer First
```python
# Create Entity
# app/domain/entities/product.py
class Product:
    def __init__(self, id, name, price):
        self._id = id
        self._name = name
        self._price = price

# Create Value Object (if needed)
# app/domain/value_objects/price.py
class Price:
    def __init__(self, amount: float):
        if amount < 0:
            raise DomainValidationException("Price cannot be negative")
        self._amount = amount

# Create Repository Interface
# app/domain/repositories/product_repository.py
class IProductRepository(ABC):
    @abstractmethod
    def create(self, product: Product) -> Product:
        pass
```

### 2. Application Layer
```python
# Create DTO
# app/application/dtos/product_dto.py
class CreateProductDTO(BaseModel):
    name: str
    price: float

# Create Use Case
# app/application/use_cases/product/create_product.py
class CreateProductUseCase:
    def __init__(self, repository: IProductRepository):
        self._repository = repository

    def execute(self, dto: CreateProductDTO) -> Product:
        product = Product(...)
        return self._repository.create(product)
```

### 3. Infrastructure Layer
```python
# Create Database Model
# app/infrastructure/persistence/models.py
class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)

# Implement Repository
# app/infrastructure/persistence/product_repository_impl.py
class ProductRepository(IProductRepository):
    def create(self, product: Product) -> Product:
        db_product = self._mapper.to_model(product)
        self._db.add(db_product)
        self._db.commit()
        return self._mapper.to_entity(db_product)
```

### 4. Presentation Layer
```python
# Create API Endpoint
# app/presentation/api/v1/products.py
@router.post("/", response_model=ProductResponseDTO)
def create_product(
    dto: CreateProductDTO,
    repository: ProductRepository = Depends(get_repository),
    current_user: User = Depends(get_current_user)  # If protected
):
    use_case = CreateProductUseCase(repository)
    return use_case.execute(dto)
```

### 5. Database Migration
```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "Add products table"

# Apply migration
docker-compose exec backend alembic upgrade head
```

## Adding a New Feature (Frontend)

### 1. Create Zod Schema
```typescript
// src/schemas/product.schema.ts
export const createProductSchema = z.object({
  name: z.string().min(1, "Name is required"),
  price: z.number().positive("Price must be positive")
})

export type CreateProductFormData = z.infer<typeof createProductSchema>
```

### 2. Create Service
```typescript
// src/services/product.service.ts
export const productService = {
  create: async (data: CreateProductFormData) => {
    const response = await apiClient.post('/api/v1/products/', data)
    return response.data
  }
}
```

### 3. Create TanStack Query Hook
```typescript
// src/hooks/useProducts.ts
export const useCreateProduct = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: productService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
    }
  })
}
```

### 4. Create UI Component
```tsx
// src/pages/CreateProductPage.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export const CreateProductPage = () => {
  const { register, handleSubmit } = useForm({
    resolver: zodResolver(createProductSchema)
  })

  const createProduct = useCreateProduct()

  const onSubmit = async (data) => {
    await createProduct.mutateAsync(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input {...register('name')} />
      <Input {...register('price')} type="number" />
      <Button type="submit">Create</Button>
    </form>
  )
}
```

## Running Celery Tasks

### Define Task
```python
# app/infrastructure/tasks/product_tasks.py
@celery_app.task(name="process_product_import")
def process_product_import(file_path: str):
    # Long-running import logic
    return {"status": "completed", "products_imported": 100}
```

### Trigger from Use Case
```python
from app.infrastructure.tasks import process_product_import

class ImportProductsUseCase:
    def execute(self, file_path: str):
        # Trigger async task
        task = process_product_import.delay(file_path)
        return {"task_id": task.id, "status": "processing"}
```

## Testing

### Backend Unit Test
```python
# tests/unit/domain/test_price.py
def test_price_validation():
    # Valid price
    price = Price(10.99)
    assert price.amount == 10.99

    # Invalid price
    with pytest.raises(DomainValidationException):
        Price(-5.00)
```

### Frontend Component Test
```tsx
// src/components/__tests__/ProductCard.test.tsx
describe('ProductCard', () => {
  it('renders product info', () => {
    render(<ProductCard name="Widget" price={19.99} />)
    expect(screen.getByText('Widget')).toBeInTheDocument()
    expect(screen.getByText('$19.99')).toBeInTheDocument()
  })
})
```

## Common Commands

```bash
# Backend
docker-compose exec backend alembic upgrade head      # Run migrations
docker-compose exec backend pytest                     # Run tests
docker-compose logs -f celery_worker                  # View Celery logs

# Frontend
cd frontend && npm run dev                            # Start dev server
cd frontend && npm run build                          # Production build
cd frontend && npm run lint                           # Lint code

# Database
docker-compose exec postgres psql -U postgres -d unison  # Access DB
```
