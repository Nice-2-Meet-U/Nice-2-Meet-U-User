from __future__ import annotations

from fastapi import Depends, FastAPI
from dotenv import load_dotenv

load_dotenv()

from utils.auth import TokenPayload, get_current_user

app = FastAPI(
    title="Profiles Service",
    description="Example secondary microservice protected by JWT from Users service.",
    version="0.1.0",
)


@app.get("/profiles/me")
async def my_profile(current_user: TokenPayload = Depends(get_current_user)):
    """
    Protected endpoint that requires a valid JWT issued by the Users microservice.
    Returns a minimal profile view keyed by the authenticated user id.
    """
    return {
        "profile_id": current_user.sub,
        "email": current_user.email,
        "name": current_user.name,
        "message": "JWT validated in Profiles service.",
    }
