from __future__ import annotations

import os
import socket
from datetime import datetime

from typing import Dict, List
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi import Query, Path
from typing import Optional

from models.profile import ProfileCreate, ProfileRead, ProfileUpdate
from models.health import Health

port = int(os.environ.get("FASTAPIPORT", 8000))

app = FastAPI(
    title="Person/Address API",
    description="Demo FastAPI app using Pydantic v2 models for Person and Address",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Health endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str]=None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo
    )

@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
    # Works because path_echo is optional in the model
    return make_health(echo=echo, path_echo=None)

@app.get("/health/{path_echo}", response_model=Health)
def get_health_with_path(
    path_echo: str = Path(..., description="Required echo in the URL path"),
    echo: str | None = Query(None, description="Optional echo string"),
):
    return make_health(echo=echo, path_echo=path_echo)

# -----------------------------------------------------------------------------
# Profile endpoints
# -----------------------------------------------------------------------------

@app.get("/profiles", response_model=ProfileRead)
def list_profiles():

@app.get("/profiles/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: UUID):

@app.post("/profiles", response_model=ProfileRead, status_code=201)
def create_profile(person: ProfileCreate):
    # Each profile gets its own UUID; stored as ProfileRead
    profile_read = ProfileRead(**profile.model_dump())

@app.patch("/profiles/{profile_id}", response_model=ProfileRead)
def update_profile(profile_id: UUID, update: ProfileUpdate):

@app.delete("/profiles/{profile_id}", status_code=204, response_model=None)
def delete_profile(profile_id: UUID):

# -----------------------------------------------------------------------------
# Photos endpoints
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Root
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the Users API. See /docs for OpenAPI UI."}

# -----------------------------------------------------------------------------
# Entrypoint for `python main.py`
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
