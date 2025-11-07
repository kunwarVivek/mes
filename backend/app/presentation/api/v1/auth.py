from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.infrastructure.persistence.user_repository_impl import UserRepository
from app.application.use_cases.auth import LoginUserUseCase, RefreshTokenUseCase
from app.application.dtos.auth_dto import LoginDTO, TokenResponseDTO, RefreshTokenDTO
from app.domain.exceptions import EntityNotFoundException, DomainValidationException

router = APIRouter()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injection for UserRepository"""
    return UserRepository(db)


@router.post("/login", response_model=TokenResponseDTO)
def login(
    login_dto: LoginDTO,
    repository: UserRepository = Depends(get_user_repository)
):
    """User login endpoint"""
    try:
        use_case = LoginUserUseCase(repository)
        token = use_case.execute(login_dto.email, login_dto.password)

        return TokenResponseDTO(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            token_type=token.token_type,
            expires_at=token.expires_at
        )

    except EntityNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except DomainValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponseDTO)
def refresh_token(
    refresh_dto: RefreshTokenDTO,
    repository: UserRepository = Depends(get_user_repository)
):
    """Refresh access token"""
    try:
        use_case = RefreshTokenUseCase(repository)
        token = use_case.execute(refresh_dto.refresh_token)

        return TokenResponseDTO(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            token_type=token.token_type,
            expires_at=token.expires_at
        )

    except DomainValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
