from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models.schemas import (
    LoginRequest,
    LoginResponse,
    TwoFactorRequest,
    TwoFactorResponse,
    SessionResponse,
)
from backend.services import icloud_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=None)
async def login(request: LoginRequest) -> LoginResponse | JSONResponse:
    result = icloud_service.login(request.apple_id, request.password)

    if "error" in result:
        status_code = 401 if result["error"] == "invalid_credentials" else 500
        return JSONResponse(status_code=status_code, content=result)

    return LoginResponse(**result)


@router.post("/2fa", response_model=None)
async def two_factor(request: TwoFactorRequest) -> TwoFactorResponse | JSONResponse:
    result = icloud_service.validate_2fa(request.code)

    if "error" in result:
        status_code = 401 if result["error"] in ("2fa_failed", "not_authenticated") else 500
        return JSONResponse(status_code=status_code, content=result)

    return TwoFactorResponse(**result)


@router.get("/session")
async def session() -> SessionResponse:
    result = icloud_service.get_session_status()
    return SessionResponse(**result)
