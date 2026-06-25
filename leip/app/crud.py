"""
LEIP CRUD Operations
Database operations for all models
"""

from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid

PWD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ============ USER OPERATIONS ============

def get_user(db: Session, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = PWD_CONTEXT.hash(user.password)
    db_user = models.User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ============ CASE OPERATIONS ============

def get_case(db: Session, case_number: str):
    return db.query(models.Case).filter(models.Case.case_number == case_number).first()


def get_case_by_id(db: Session, case_id):
    return db.query(models.Case).filter(models.Case.id == case_id).first()


def get_cases(db: Session, skip: int = 0, limit: int = 100, status: str = None, priority: str = None):
    query = db.query(models.Case).filter(models.Case.is_deleted == False)
    if status:
        query = query.filter(models.Case.status == status)
    if priority:
        query = query.filter(models.Case.priority == priority)
    return query.order_by(models.Case.created_at.desc()).offset(skip).limit(limit).all()


def create_case(db: Session, case: schemas.CaseCreate):
    db_case = models.Case(
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        case_type=case.case_type,
        priority=case.priority,
        status=case.status,
        classification=case.classification,
        jurisdiction=case.jurisdiction,
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def update_case(db: Session, case_number: str, updates: schemas.CaseUpdate):
    db_case = get_case(db, case_number)
    if not db_case:
        return None
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_case, field, value)
    db_case.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_case)
    return db_case


def delete_case(db: Session, case_number: str):
    db_case = get_case(db, case_number)
    if not db_case:
        return False
    db_case.is_deleted = True
    db_case.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return True


# ============ DETECTION OPERATIONS ============

def create_detection(db: Session, detection: schemas.DetectionCreate):
    db_detection = models.Detection(
        case_id=detection.case_id,
        person_id=detection.person_id,
        vehicle_id=detection.vehicle_id,
        detection_type=detection.detection_type,
        confidence=detection.confidence,
        detection_source=detection.detection_source,
        timestamp=detection.timestamp,
        bbox=detection.bbox,
        frame_id=detection.frame_id,
        source_file=detection.source_file,
        metadata_json=detection.metadata_json,
    )
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection


def get_detections_by_case(db: Session, case_id):
    return db.query(models.Detection).filter(models.Detection.case_id == case_id).all()


# ============ PERSON OPERATIONS ============

def create_person(db: Session, person: schemas.PersonCreate):
    db_person = models.Person(
        person_number=person.person_number,
        first_name=person.first_name,
        last_name=person.last_name,
        nationality=person.nationality,
        gender=person.gender,
        status=person.status,
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


def get_person(db: Session, person_number: str):
    return db.query(models.Person).filter(models.Person.person_number == person_number).first()


def get_persons(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Person)
        .filter(models.Person.is_deleted == False)
        .order_by(models.Person.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ============ VEHICLE OPERATIONS ============

def create_vehicle(db: Session, vehicle: schemas.VehicleCreate):
    db_vehicle = models.Vehicle(
        vin=vehicle.vin,
        license_plate=vehicle.license_plate,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        color=vehicle.color,
    )
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def get_vehicle_by_plate(db: Session, license_plate: str):
    return db.query(models.Vehicle).filter(models.Vehicle.license_plate == license_plate).first()


def get_vehicles(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Vehicle)
        .filter(models.Vehicle.is_deleted == False)
        .order_by(models.Vehicle.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
