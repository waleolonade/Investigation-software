from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext

PWD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_user(db: Session, user_id: int):
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

def get_case(db: Session, case_id: str):
    return db.query(models.Case).filter(models.Case.case_id == case_id).first()

def get_cases(db: Session, skip: int = 0, limit: int = 100, status: str = None, priority: str = None):
    query = db.query(models.Case)
    if status:
        query = query.filter(models.Case.status == status)
    if priority:
        query = query.filter(models.Case.priority == priority)
    return query.offset(skip).limit(limit).all()

def create_case(db: Session, case: schemas.CaseCreate):
    db_case = models.Case(
        case_id=case.case_id,
        title=case.title,
        description=case.description,
        priority=case.priority,
        status=case.status,
        assigned_to=case.assigned_to
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

def create_detection(db: Session, detection: schemas.DetectionCreate):
    db_detection = models.Detection(
        detection_id=detection.detection_id,
        case_id=detection.case_id,
        frame_id=detection.frame_id,
        timestamp=detection.timestamp,
        detection_type=detection.detection_type,
        confidence=detection.confidence,
        bbox=detection.bbox,
        metadata_json=detection.metadata_json,
        person_id=detection.person_id,
        plate_number=detection.plate_number
    )
    db.add(db_detection)
    db.commit()
    db.refresh(db_detection)
    return db_detection

def get_detections_by_case(db: Session, case_id: str):
    return db.query(models.Detection).filter(models.Detection.case_id == case_id).all()
