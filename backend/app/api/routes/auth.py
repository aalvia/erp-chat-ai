from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.database.session import get_db
from app.models import User
from app.schemas.dto import LoginRequest, TokenResponse, UserOut
from app.services.mappers import user_out
from app.services.user_service import authenticate

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate(db, data.username, data.password)
    token = create_access_token(user.id, user.token_version)
    return TokenResponse(access_token=token, user=user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return user_out(user)
