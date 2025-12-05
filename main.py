from __future__ import annotations

import os
import socket
from datetime import datetime
from typing import Optional
from uuid import UUID
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

load_dotenv()

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import create_engine, text

# Your model imports
from models.health import Health
from models.photos import PhotoCreate, PhotoRead, PhotoUpdate
from models.profile import ProfileCreate, ProfileRead, ProfileUpdate
from models.user import LoginRequest, SignupRequest, TokenResponse, UserPublic
from models.visibility import VisibilityCreate, VisibilityRead, VisibilityUpdate
from services.profile_repository import ProfileRepository
from services.user_repository import UserRepository
from utils.auth import TokenPayload, create_access_token, get_current_user

port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------
# 🚀 DB CONNECTION (Cloud SQL with local fallback)
# -----------------------------------------------------------

required_env = ["DB_USER", "DB_PASS", "DB_NAME"]
missing_env = [key for key in required_env if not os.environ.get(key)]

engine = None

if missing_env:
    print(
        f"⚠️  Missing DB env vars {missing_env}. "
        "Skipping database connection; API will start but DB-backed endpoints will fail."
    )
else:
    prefer_local = os.environ.get("USE_LOCAL_DB", "").lower() in ("1", "true", "yes")
    instance_conn_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    local_host = os.environ.get("LOCAL_DB_HOST", "127.0.0.1")
    local_port = int(os.environ.get("LOCAL_DB_PORT", "3306"))

    if prefer_local or not instance_conn_name:
        # Direct TCP connection to local MySQL (Docker)
        print(f"Using local MySQL at {local_host}:{local_port}")
        url = (
            f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}"
            f"@{local_host}:{local_port}/{os.environ['DB_NAME']}"
        )
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✔ Database connection established to local MySQL!")
        except Exception as exc:
            print(
                f"⚠️  Local DB connection failed ({exc}). "
                "Continuing startup without a DB connection; DB-backed endpoints will fail."
            )
            engine = None
    else:
        # Cloud SQL via connector
        from google.cloud.sql.connector import Connector  # type: ignore
        import pymysql  # noqa: F401

        INSTANCE_CONNECTION_NAME = instance_conn_name

        def getconn():
            connector = Connector()  # creates secure Cloud SQL tunnel
            conn = connector.connect(
                INSTANCE_CONNECTION_NAME,
                "pymysql",
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASS"],
                db=os.environ["DB_NAME"],
            )
            return conn

        try:
            engine = create_engine(
                "mysql+pymysql://",
                creator=getconn,
                pool_pre_ping=True,
            )

            print("Using Cloud SQL Connector. Testing connection...")

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✔ Database connection established via Cloud SQL Connector!")
        except Exception as exc:
            print(
                f"⚠️  Cloud SQL connection failed ({exc}). "
                "Continuing startup without a DB connection; DB-backed endpoints will fail."
            )
            engine = None

user_repository = UserRepository(engine)
profile_repository = ProfileRepository(engine)

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "").lower() in ("1", "true", "yes")
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")
FRONTEND_CALLBACK_PATH = os.environ.get("FRONTEND_CALLBACK_PATH", "/auth/google/callback")
FRONTEND_PROFILE_PATH = os.environ.get("FRONTEND_PROFILE_PATH", "/profile")
FRONTEND_ONBOARDING_PATH = os.environ.get("DEFAULT_REDIRECT_PATH") or os.environ.get(
    "FRONTEND_ONBOARDING_PATH", "/onboarding"
)
DEFAULT_REDIRECT_PATH = os.environ.get("DEFAULT_REDIRECT_PATH", FRONTEND_ONBOARDING_PATH)

# -----------------------------------------------------------
# FASTAPI APP SETUP
# -----------------------------------------------------------

app = FastAPI(
    title="Users Microservice API",
    description="FastAPI app exposing resources for Profiles, Photos, and Visibility.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health utility
def make_health(echo: Optional[str], path_echo: Optional[str] = None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo,
    )

# Health endpoints
@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = None):
    return make_health(echo=echo)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(path_echo: str, echo: str | None = None):
    return make_health(echo=echo, path_echo=path_echo)

# ----------------------------
# Auth endpoints
# ----------------------------

def _require_google_env() -> tuple[str, str, str]:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI.",
    )
    return client_id, client_secret, redirect_uri


def _build_frontend_redirect(
    *,
    state: str | None,
    next_path: str | None,
    has_profile: bool,
) -> str:
    """
    Build the URL to send the browser back into the frontend app after the backend
    has created the session cookie.
    """
    query: dict[str, str] = {}
    if next_path and next_path.startswith("/"):
        query["next"] = next_path
    if state:
        query["state"] = state

    if query:
        qs = urlencode(query)
        return f"{FRONTEND_ORIGIN}{FRONTEND_CALLBACK_PATH}?{qs}"

    # Fallback to onboarding or profile depending on whether the user already has a profile.
    target_path = FRONTEND_PROFILE_PATH if has_profile else DEFAULT_REDIRECT_PATH
    if not target_path.startswith("/"):
        target_path = f"/{target_path}"
    return f"{FRONTEND_ORIGIN}{target_path}"


def _token_response(
    user: UserPublic,
    *,
    provider: str,
    redirect_to: str | None = None,
) -> JSONResponse | RedirectResponse:
    profile = profile_repository.get_by_user_id(str(user.id))
    token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        name=user.name,
        provider=provider,
    )
    payload = {
        "token": token,
        "user": user.model_dump(mode="json"),
        "profile_id": str(profile.id) if profile else None,
    }
    if redirect_to:
        response = RedirectResponse(url=redirect_to, status_code=status.HTTP_302_FOUND)
    else:
        response = JSONResponse(payload)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return response


@app.get("/auth/google", include_in_schema=True)
def start_google_login(state: str | None = None, next_path: str | None = Query(None, alias="next")):
    client_id, _, redirect_uri = _require_google_env()
    resolved_state = state or next_path
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    if resolved_state:
        params["state"] = resolved_state
    prepared = requests.Request("GET", GOOGLE_AUTH_BASE, params=params).prepare()
    return RedirectResponse(prepared.url)


@app.get("/auth/google/callback", response_model=TokenResponse)
def google_callback(
    code: str = Query(...),
    state: str | None = None,
    next_path: str | None = Query(None, alias="next"),
    return_json: bool = Query(
        False,
        description="Return JSON instead of redirecting back into the frontend app.",
        alias="json",
    ),
):
    client_id, client_secret, redirect_uri = _require_google_env()
    token_resp = requests.post(
        GOOGLE_TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    if not token_resp.ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {token_resp.text}",
        )
    token_data = token_resp.json()
    id_token_value = token_data.get("id_token")
    if not id_token_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="id_token missing from Google response.",
        )
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token_value, google_requests.Request(), audience=client_id
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify Google token: {exc}",
        ) from exc

    email = id_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google token did not include an email address.",
        )

    user = user_repository.upsert_google_user(
        email=email,
        name=id_info.get("name"),
        google_sub=id_info.get("sub"),
        picture=id_info.get("picture"),
    )

    profile = profile_repository.get_by_user_id(str(user.id))
    redirect_target = (
        None
        if return_json
        else _build_frontend_redirect(
            state=state,
            next_path=next_path,
            has_profile=profile is not None,
        )
    )
    # Pass through profile awareness so the payload includes profile_id for clients.
    return _token_response(user, provider="google", redirect_to=redirect_target)


@app.post("/auth/signup", response_model=TokenResponse)
def signup(payload: SignupRequest = Body(...)):
    try:
        user = user_repository.create_local_user(
            email=payload.email, password=payload.password, name=payload.name
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _token_response(user, provider="local")


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest = Body(...)):
    user = user_repository.verify_local_credentials(email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return _token_response(user, provider="local")


@app.get("/auth/me", response_model=UserPublic)
async def get_me(current_user: TokenPayload = Depends(get_current_user)):
    user = user_repository.get_user_by_id(current_user.sub)
    if user:
        return user
    try:
        return UserPublic(
            id=UUID(current_user.sub),
            email=current_user.email,
            name=current_user.name,
            provider=current_user.provider,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )


@app.post("/auth/logout")
async def logout():
    response = JSONResponse({"detail": "Logged out"})
    response.delete_cookie("access_token")
    return response

# ----------------------------
# Profile endpoints
# ----------------------------
@app.get("/profiles/me", response_model=ProfileRead)
def get_my_profile(current_user: TokenPayload = Depends(get_current_user)):
    profile = profile_repository.get_by_user_id(current_user.sub)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return profile


@app.get("/profiles/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: UUID, current_user: TokenPayload = Depends(get_current_user)):
    profile = profile_repository.get_by_id(str(profile_id))
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    if str(profile.user_id) != current_user.sub:
        # Only owner can fetch; relax this later if profiles become public.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    return profile


@app.post("/profiles", response_model=ProfileRead, status_code=201)
def create_profile(profile: ProfileCreate, current_user: TokenPayload = Depends(get_current_user)):
    existing = profile_repository.get_by_user_id(current_user.sub)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists for this user.",
        )
    created = profile_repository.create_profile(user_id=current_user.sub, payload=profile)
    return created


@app.put("/profiles/me", response_model=ProfileRead)
def update_my_profile(update: ProfileUpdate, current_user: TokenPayload = Depends(get_current_user)):
    existing = profile_repository.get_by_user_id(current_user.sub)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    updated = profile_repository.update_profile(
        profile_id=str(existing.id),
        user_id=current_user.sub,
        update=update,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return updated


@app.delete("/profiles/me", status_code=204)
def delete_my_profile(current_user: TokenPayload = Depends(get_current_user)):
    existing = profile_repository.get_by_user_id(current_user.sub)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    deleted = profile_repository.delete_profile(
        profile_id=str(existing.id),
        user_id=current_user.sub,
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ----------------------------
# Photos endpoints (stubs)
# ----------------------------
@app.get("/photos", response_model=list[PhotoRead])
def list_photos():
    raise HTTPException(status_code=501, detail="Not implemented")

@app.get("/photos/{photo_id}", response_model=PhotoRead)
def get_photo(photo_id: UUID):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.post("/photos", response_model=PhotoRead, status_code=201)
def create_photo(photo: PhotoCreate):
    return PhotoRead(**photo.model_dump())

@app.put("/photos/{photo_id}", response_model=PhotoRead)
def update_photo(photo_id: UUID, update: PhotoUpdate):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.delete("/photos/{photo_id}", status_code=204)
def delete_photo(photo_id: UUID):
    raise HTTPException(status_code=501, detail="Not implemented")

# ----------------------------
# Visibility endpoints (stubs)
# ----------------------------
@app.get("/visibility", response_model=list[VisibilityRead])
def list_visibility():
    raise HTTPException(status_code=501, detail="Not implemented")

@app.get("/visibility/{visibility_id}", response_model=VisibilityRead)
def get_visibility(visibility_id: UUID):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.post("/visibility", response_model=VisibilityRead, status_code=201)
def create_visibility(visibility: VisibilityCreate):
    return VisibilityRead(**visibility.model_dump())

@app.put("/visibility/{visibility_id}", response_model=VisibilityRead)
def update_visibility(visibility_id: UUID, update: VisibilityUpdate):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.delete("/visibility/{visibility_id}", status_code=204)
def delete_visibility(visibility_id: UUID):
    raise HTTPException(status_code=501, detail="Not implemented")

# Root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the Users API. See /docs for OpenAPI UI."}

# FastAPI entrypoint
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
