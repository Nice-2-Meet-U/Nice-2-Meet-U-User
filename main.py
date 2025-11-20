from __future__ import annotations

import os
import socket
from sqlalchemy import create_engine, text
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Path, status
from dotenv import load_dotenv

from models.profile import ProfileCreate, ProfileRead, ProfileUpdate
from models.photos import PhotoCreate, PhotoRead, PhotoUpdate
from models.visibility import VisibilityCreate, VisibilityRead, VisibilityUpdate
from models.health import Health


load_dotenv()

port = int(os.environ.get("FASTAPIPORT", 8000))

engine = create_engine(
    f"mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASS']}@{os.environ['DB_HOST']}/{os.environ['DB_NAME']}"
)

with engine.connect() as conn:
    conn.execute(text("SELECT 1"))  # Test the connection
    print("Database connection established.")
    
app = FastAPI(
    title="Users Microservice API",
    description="FastAPI app exposing resources for Profiles, Photos, and Visibility.",
    version="0.1.0",
)

# -----------------------------------------------------------------------------
# Health endpoints
# -----------------------------------------------------------------------------

def make_health(echo: Optional[str], path_echo: Optional[str] = None) -> Health:
    return Health(
        status=200,
        status_message="OK",
        timestamp=datetime.utcnow().isoformat() + "Z",
        ip_address=socket.gethostbyname(socket.gethostname()),
        echo=echo,
        path_echo=path_echo,
    )


@app.get("/health", response_model=Health)
def get_health_no_path(echo: str | None = Query(None, description="Optional echo string")):
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

@app.get("/profiles", response_model=list[ProfileRead])
def list_profiles():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.get("/profiles/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.post("/profiles", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(profile: ProfileCreate):
    profile_read = ProfileRead(**profile.model_dump())
    return profile_read


@app.put("/profiles/{profile_id}", response_model=ProfileRead)
def update_profile(profile_id: UUID, update: ProfileUpdate):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(profile_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# -----------------------------------------------------------------------------
# Photos endpoints
# -----------------------------------------------------------------------------

@app.get("/photos", response_model=list[PhotoRead])
def list_photos():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.get("/photos/{photo_id}", response_model=PhotoRead)
def get_photo(photo_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.post("/photos", response_model=PhotoRead, status_code=status.HTTP_201_CREATED)
def create_photo(photo: PhotoCreate):
    photo_read = PhotoRead(**photo.model_dump())
    return photo_read


@app.put("/photos/{photo_id}", response_model=PhotoRead)
def update_photo(photo_id: UUID, update: PhotoUpdate):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.delete("/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(photo_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


# -----------------------------------------------------------------------------
# Visibility endpoints
# -----------------------------------------------------------------------------

@app.get("/visibility", response_model=list[VisibilityRead])
def list_visible():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.get("/visibility/{visibility_id}", response_model=VisibilityRead)
def get_visibility(visibility_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.post("/visibility", response_model=VisibilityRead, status_code=status.HTTP_201_CREATED)
def create_visibility(visibility: VisibilityCreate):
    visibility_read = VisibilityRead(**visibility.model_dump())
    return visibility_read


@app.put("/visibility/{visibility_id}", response_model=VisibilityRead)
def update_visibility(visibility_id: UUID, update: VisibilityUpdate):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


@app.delete("/visibility/{visibility_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_visibility(visibility_id: UUID):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")


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
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
