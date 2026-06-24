from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    disabled: Optional[bool] = False
    role: str = "investigator"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class DetectionBase(BaseModel):
    detection_id: str
    case_id: str
    frame_id: int
    timestamp: str
    detection_type: str
    confidence: float
    bbox: Dict[str, Any]
    metadata_json: Optional[Dict[str, Any]] = None
    person_id: Optional[str] = None
    plate_number: Optional[str] = None

class DetectionCreate(DetectionBase):
    pass

class Detection(DetectionBase):
    class Config:
        orm_mode = True

class CaseBase(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "open"
    assigned_to: Optional[str] = None

class CaseCreate(CaseBase):
    pass

class Case(CaseBase):
    created_at: datetime
    detections: List[Detection] = []

    class Config:
        orm_mode = True

class PersonBase(BaseModel):
    person_id: str
    name: Optional[str] = None
    source: str = "manual_upload"

class PersonCreate(PersonBase):
    pass

class Person(PersonBase):
    created_at: datetime
    detections: List[Detection] = []

    class Config:
        orm_mode = True

class VehicleBase(BaseModel):
    plate_number: str
    make: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class Vehicle(VehicleBase):
    detections: List[Detection] = []

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
