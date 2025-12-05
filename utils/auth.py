from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.environ.get("JWT_EXPIRES_MINUTES", "60"))

bearer_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str
    email: str
    name: Optional[str] = None
    provider: str
    iat: int
    exp: int


def _require_secret() -> str:
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET is not configured on the server.",
        )
    return JWT_SECRET


def create_access_token(
    *,
    user_id: str,
    email: str,
    name: Optional[str],
    provider: str,
    expires_minutes: Optional[int] = None,
) -> str:
    """Create a signed JWT with common claims."""
    secret = _require_secret()
    now = datetime.utcnow()
    exp_delta = timedelta(minutes=expires_minutes or JWT_EXPIRES_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "provider": provider,
        "iat": int(now.timestamp()),
        "exp": int((now + exp_delta).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    secret = _require_secret()
    try:
        data = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            options={
                # Allow for minor clock skew without rejecting tokens.
                "verify_iat": False,
            },
        )
        return TokenPayload(**data)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc


def _extract_token(request: Request, credentials: HTTPAuthorizationCredentials | None) -> Optional[str]:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    cookie_token = request.cookies.get("access_token")
    return cookie_token


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    """FastAPI dependency to decode JWT from Authorization header or cookie."""
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
        )
    return decode_token(token)
