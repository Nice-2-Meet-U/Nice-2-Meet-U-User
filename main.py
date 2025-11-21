from __future__ import annotations

import os
import socket
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query, Path, status
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cloud SQL Connector imports
from google.cloud.sql.connector import Connector
import pymysql

# Your model imports
from models.profile import ProfileCreate, ProfileRead, ProfileUpdate
from models.photos import PhotoCreate, PhotoRead, PhotoUpdate
from models.visibility import VisibilityCreate, VisibilityRead, VisibilityUpdate
from models.health import Health

# Load .env variables
load_dotenv()

port = int(os.environ.get("FASTAPIPORT", 8000))

# -----------------------------------------------------------
# 🚀 CLOUD SQL CONNECTOR DB CONNECTION (THE FIX!)
# -----------------------------------------------------------

INSTANCE_CONNECTION_NAME = os.environ["INSTANCE_CONNECTION_NAME"]

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

# SQLAlchemy engine using the connector
engine = create_engine(
    "mysql+pymysql://",
    creator=getconn,
    pool_pre_ping=True,
)

print("Using Cloud SQL Connector. Testing connection...")

with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
    print("✔ Database connection established via Cloud SQL Connector!")

# -----------------------------------------------------------
# FASTAPI APP SETUP
# -----------------------------------------------------------

app = FastAPI(
    title="Users Microservice API",
    description="FastAPI app exposing resources for Profiles, Photos, and Visibility.",
    version="0.1.0",
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
# Profile endpoints (stubs)
# ----------------------------
@app.get("/profiles", response_model=list[ProfileRead])
def list_profiles():
    raise HTTPException(status_code=501, detail="Not implemented")

@app.get("/profiles/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: UUID):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.post("/profiles", response_model=ProfileRead, status_code=201)
def create_profile(profile: ProfileCreate):
    return ProfileRead(**profile.model_dump())

@app.put("/profiles/{profile_id}", response_model=ProfileRead)
def update_profile(profile_id: UUID, update: ProfileUpdate):
    raise HTTPException(status_code=501, detail="Not implemented")

@app.delete("/profiles/{profile_id}", status_code=204)
def delete_profile(profile_id: UUID):
    raise HTTPException(status_code=501, detail="Not implemented")

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