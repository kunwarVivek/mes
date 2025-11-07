from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.infrastructure.persistence.user_repository_impl import UserRepository
from app.application.use_cases.user import (
    CreateUserUseCase,
    GetUserUseCase,
    GetAllUsersUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase
)
from app.application.dtos.user_dto import CreateUserDTO, UpdateUserDTO, UserResponseDTO
from app.domain.exceptions import (
    DomainValidationException,
    EntityNotFoundException,
    DuplicateEntityException
)

router = APIRouter()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injection for UserRepository"""
    return UserRepository(db)


def map_to_response_dto(user) -> UserResponseDTO:
    """Map domain entity to response DTO"""
    return UserResponseDTO(
        id=user.id,
        email=user.email.value,
        username=user.username.value,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.get("/", response_model=List[UserResponseDTO])
def read_users(
    skip: int = 0,
    limit: int = 100,
    repository: UserRepository = Depends(get_user_repository)
):
    """Get all users with pagination"""
    try:
        use_case = GetAllUsersUseCase(repository)
        users = use_case.execute(skip=skip, limit=limit)
        return [map_to_response_dto(user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    user_dto: CreateUserDTO,
    repository: UserRepository = Depends(get_user_repository)
):
    """Create a new user"""
    try:
        use_case = CreateUserUseCase(repository)
        user = use_case.execute(user_dto)
        return map_to_response_dto(user)
    except DomainValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntityException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", response_model=UserResponseDTO)
def read_user(
    user_id: int,
    repository: UserRepository = Depends(get_user_repository)
):
    """Get a specific user by ID"""
    try:
        use_case = GetUserUseCase(repository)
        user = use_case.execute(user_id)
        return map_to_response_dto(user)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=UserResponseDTO)
def update_user(
    user_id: int,
    user_dto: UpdateUserDTO,
    repository: UserRepository = Depends(get_user_repository)
):
    """Update an existing user"""
    try:
        use_case = UpdateUserUseCase(repository)
        user = use_case.execute(user_id, user_dto)
        return map_to_response_dto(user)
    except EntityNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateEntityException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    repository: UserRepository = Depends(get_user_repository)
):
    """Delete a user"""
    try:
        use_case = DeleteUserUseCase(repository)
        use_case.execute(user_id)
        return None
    except EntityNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
