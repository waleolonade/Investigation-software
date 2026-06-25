"""
LEIP Pydantic Schemas
Request/response models for the FastAPI endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


# ============ USER SCHEMAS ============

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: str
    disabled: Optional[bool] = False
    role: str = "investigator"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ============ CASE SCHEMAS ============

class CaseCreate(BaseModel):
    case_number: str
    title: str
    description: Optional[str] = None
    case_type: str = "general"
    priority: str = "medium"
    status: str = "open"
    classification: str = "UNCLASSIFIED"
    jurisdiction: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    classification: Optional[str] = None
    jurisdiction: Optional[str] = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    case_number: str
    title: str
    description: Optional[str] = None
    case_type: str
    priority: Any  # Enum value
    status: Any  # Enum value
    classification: str
    created_at: datetime


class CaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    case_number: str
    title: str
    status: Any
    priority: Any


# ============ DETECTION SCHEMAS ============

class DetectionCreate(BaseModel):
    case_id: Optional[uuid.UUID] = None
    person_id: Optional[uuid.UUID] = None
    vehicle_id: Optional[uuid.UUID] = None
    detection_type: str
    confidence: float
    detection_source: str = "cctv"
    timestamp: datetime
    bbox: Dict[str, Any]
    frame_id: int = 0
    source_file: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    detection_type: Any
    confidence: float
    timestamp: datetime
    frame_id: int
    bbox: Dict[str, Any]


# ============ PERSON SCHEMAS ============

class PersonCreate(BaseModel):
    person_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nationality: Optional[str] = None
    gender: Optional[str] = None
    status: str = "unknown"


class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    person_number: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime


# ============ VEHICLE SCHEMAS ============

class VehicleCreate(BaseModel):
    vin: str
    license_plate: str
    make: str
    model: str
    year: Optional[int] = None
    color: Optional[str] = None


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vin: str
    license_plate: str
    make: str
    model: str
    color: Optional[str] = None
    status: Optional[str] = None


# ============ AUTH SCHEMAS ============

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
