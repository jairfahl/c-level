"""Auth router — demo token endpoint for frontend access."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.core.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token", response_model=TokenResponse, status_code=200)
async def get_token(body: TokenRequest) -> TokenResponse:
    """Gera um JWT para acesso à API. Qualquer username é aceito (demo)."""
    token = create_access_token(data={"sub": body.username})
    return TokenResponse(access_token=token)
