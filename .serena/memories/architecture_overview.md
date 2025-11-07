# Unison Architecture Overview

## Backend - Domain-Driven Design (DDD)

### Layer Structure
```
backend/app/
├── domain/              # Pure business logic
│   ├── entities/       # User, Token
│   ├── value_objects/  # Email, Username (with validation)
│   ├── repositories/   # IUserRepository (interface)
│   └── exceptions/     # Domain-specific errors
│
├── application/         # Use cases & orchestration
│   ├── use_cases/
│   │   ├── user/       # CreateUser, UpdateUser, DeleteUser, GetUser, GetAllUsers
│   │   └── auth/       # LoginUser, RefreshToken
│   └── dtos/           # CreateUserDTO, LoginDTO, TokenResponseDTO
│
├── infrastructure/      # Technical implementations
│   ├── persistence/    # UserRepository (SQLAlchemy)
│   ├── security/       # JWTHandler, CasbinEnforcer, RBAC
│   └── tasks/          # Celery tasks (email, cleanup, reports)
│
└── presentation/        # API layer
    └── api/v1/         # Auth, Users endpoints
```

## Frontend - Atomic Design

### Component Hierarchy
```
frontend/src/
├── components/ui/       # ShadCN atoms (Button, Card, Input, Label)
├── design-system/       # Legacy atoms, molecules, organisms
├── stores/             # Zustand (auth, ui)
├── schemas/            # Zod validation
├── services/           # API clients
├── hooks/              # TanStack Query hooks
└── pages/              # Complete views
```

## Key Principles
- **SOLID**: Every class has single responsibility
- **DDD**: Business logic in domain layer, isolated from frameworks
- **Atomic Design**: Components compose from atoms → molecules → organisms
- **Type Safety**: TypeScript + Zod on frontend, Pydantic on backend
