from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, JSON, Text, Enum, Index, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from datetime import datetime, timezone
import uuid
from enum import Enum as PyEnum
from app.database import Base

# Enums for better type safety
class CaseStatus(PyEnum):
    OPEN = "open"
    UNDER_INVESTIGATION = "under_investigation"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"
    CLOSED_UNSOLVED = "closed_unsolved"
    CLOSED_SOLVED = "closed_solved"

class CasePriority(PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"

class EvidenceType(PyEnum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    EMAIL = "email"
    CHAT = "chat"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SOCIAL_MEDIA = "social_media"
    WEBSITE = "website"
    DATABASE = "database"

class DetectionType(PyEnum):
    PERSON = "person"
    VEHICLE = "vehicle"
    FACE = "face"
    LICENSE_PLATE = "license_plate"
    OBJECT = "object"
    WEAPON = "weapon"
    CONTROLLED_SUBSTANCE = "controlled_substance"
    COUNTERFEIT = "counterfeit"
    DIGITAL_FORENSIC = "digital_forensic"
    BIOMETRIC = "biometric"
    GEO_LOCATION = "geo_location"
    TIME_STAMP = "time_stamp"

class UserRole(PyEnum):
    INVESTIGATOR = "investigator"
    SENIOR_INVESTIGATOR = "senior_investigator"
    SUPERVISOR = "supervisor"
    ANALYST = "analyst"
    FORENSIC_EXPERT = "forensic_expert"
    ADMINISTRATOR = "administrator"
    SYSTEM_ADMIN = "system_admin"
    MANAGER = "manager"
    DIRECTOR = "director"
    COMPLIANCE_OFFICER = "compliance_officer"
    EXTERNAL_EXPERT = "external_expert"

# Base class with common fields
class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # Audit trail
    audit_trail = Column(JSONB, default=list, nullable=False)
    version = Column(Integer, default=1, nullable=False)

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    disabled = Column(Boolean, default=False, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.INVESTIGATOR, nullable=False)
    
    # Extended user fields
    badge_number = Column(String(50), unique=True, nullable=True)
    department = Column(String(100), nullable=True)
    division = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Permissions and preferences
    permissions = Column(JSONB, default=dict, nullable=False)
    preferences = Column(JSONB, default=dict, nullable=False)
    notification_settings = Column(JSONB, default=dict, nullable=False)
    
    # Relationships
    assigned_cases = relationship("Case", foreign_keys="Case.assigned_to", back_populates="assigned_investigator")
    created_cases = relationship("Case", foreign_keys="Case.created_by", back_populates="case_creator")
    assigned_evidence = relationship("Evidence", foreign_keys="Evidence.assigned_to", back_populates="assigned_user")
    created_evidence = relationship("Evidence", foreign_keys="Evidence.created_by", back_populates="evidence_creator")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    __table_args__ = (
        Index('idx_users_role', 'role'),
        Index('idx_users_department', 'department'),
        Index('idx_users_email_verified', 'email_verified'),
    )

class Case(BaseModel):
    __tablename__ = "cases"
    
    # Case identification
    case_number = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    case_type = Column(String(100), nullable=False)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    status = Column(Enum(CaseStatus), default=CaseStatus.OPEN, nullable=False)
    
    # Case metadata
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    opened_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    closed_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    escalation_date = Column(DateTime, nullable=True)
    
    # Classification and sensitivity
    classification = Column(String(50), nullable=False, default="UNCLASSIFIED")
    sensitivity_level = Column(Integer, default=1, nullable=False)  # 1-5 scale
    need_to_know = Column(String(255), nullable=True)
    
    # Case location and jurisdiction
    jurisdiction = Column(String(100), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_address = Column(Text, nullable=True)
    
    # Additional metadata
    tags = Column(ARRAY(String), default=list, nullable=False)
    related_incidents = Column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)
    lead_score = Column(Integer, default=0, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)
    budget_code = Column(String(50), nullable=True)
    cost_center = Column(String(50), nullable=True)
    
    # Relationships
    assigned_investigator = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_cases")
    case_creator = relationship("User", foreign_keys=[created_by], back_populates="created_cases")
    supervisor = relationship("User", foreign_keys=[supervisor_id])
    
    detections = relationship("Detection", back_populates="case", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="case", cascade="all, delete-orphan")
    timeline_events = relationship("CaseTimeline", back_populates="case", cascade="all, delete-orphan")
    analysis_reports = relationship("AnalysisReport", back_populates="case", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_cases_assigned_to', 'assigned_to'),
        Index('idx_cases_status', 'status'),
        Index('idx_cases_priority', 'priority'),
        Index('idx_cases_opened_date', 'opened_date'),
        Index('idx_cases_case_number', 'case_number'),
        Index('idx_cases_classification', 'classification'),
        Index('idx_cases_tags', 'tags', postgresql_using='gin'),
        Index('idx_cases_location', 'location_lat', 'location_lon'),
        UniqueConstraint('case_number', name='uq_cases_case_number'),
    )

class Person(BaseModel):
    __tablename__ = "persons"
    
    # Personal identification
    person_number = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    alias = Column(ARRAY(String), default=list, nullable=False)
    
    # Biographic information
    date_of_birth = Column(DateTime, nullable=True)
    place_of_birth = Column(String(200), nullable=True)
    nationality = Column(String(100), nullable=True)
    citizenship = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    marital_status = Column(String(20), nullable=True)
    occupation = Column(String(100), nullable=True)
    education = Column(String(100), nullable=True)
    
    # Physical description
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    eye_color = Column(String(30), nullable=True)
    hair_color = Column(String(30), nullable=True)
    hair_length = Column(String(30), nullable=True)
    distinguishing_marks = Column(Text, nullable=True)
    tattoos = Column(ARRAY(String), default=list, nullable=False)
    
    # Contact information
    phone_numbers = Column(ARRAY(String), default=list, nullable=False)
    email_addresses = Column(ARRAY(String), default=list, nullable=False)
    address_history = Column(JSONB, default=list, nullable=False)
    
    # Identification documents
    ssn = Column(String(20), nullable=True)
    passport_number = Column(String(30), nullable=True)
    drivers_license = Column(String(30), nullable=True)
    government_id = Column(String(30), nullable=True)
    vehicle_registration = Column(String(30), nullable=True)
    
    # Criminal history
    criminal_record = Column(JSONB, default=dict, nullable=False)
    known_associates = Column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)
    gang_affiliation = Column(String(100), nullable=True)
    risk_assessment = Column(JSONB, default=dict, nullable=False)
    
    # Biometric data
    fingerprints = Column(JSONB, nullable=True)
    dna_profile = Column(JSONB, nullable=True)
    facial_recognition_id = Column(String(100), nullable=True)
    voice_print = Column(JSONB, nullable=True)
    
    # Current status
    status = Column(String(50), default="unknown")  # alive, deceased, missing, etc.
    last_known_location = Column(JSONB, nullable=True)
    current_whereabouts = Column(JSONB, nullable=True)
    witness_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    detections = relationship("Detection", back_populates="person")
    vehicles = relationship("VehicleOwner", back_populates="person")
    phones = relationship("PhoneNumber", back_populates="person")
    social_media = relationship("SocialMediaAccount", back_populates="person")
    
    __table_args__ = (
        Index('idx_persons_name', 'first_name', 'last_name'),
        Index('idx_persons_dob', 'date_of_birth'),
        Index('idx_persons_status', 'status'),
        Index('idx_persons_alias', 'alias', postgresql_using='gin'),
        Index('idx_persons_phone_numbers', 'phone_numbers', postgresql_using='gin'),
        Index('idx_persons_email_addresses', 'email_addresses', postgresql_using='gin'),
    )

class Vehicle(BaseModel):
    __tablename__ = "vehicles"
    
    # Vehicle identification
    vin = Column(String(17), unique=True, index=True, nullable=False)
    license_plate = Column(String(20), unique=True, index=True, nullable=False)
    license_plate_state = Column(String(30), nullable=True)
    license_plate_type = Column(String(30), nullable=True)
    
    # Vehicle details
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    body_type = Column(String(50), nullable=True)
    transmission = Column(String(30), nullable=True)
    fuel_type = Column(String(30), nullable=True)
    engine_size = Column(Float, nullable=True)
    horsepower = Column(Integer, nullable=True)
    
    # Registration details
    registration_date = Column(DateTime, nullable=True)
    registration_expiry = Column(DateTime, nullable=True)
    insurance_provider = Column(String(100), nullable=True)
    insurance_policy = Column(String(100), nullable=True)
    ownership_type = Column(String(50), nullable=True)
    
    # Vehicle status
    status = Column(String(50), default="active")  # active, stolen, impounded, etc.
    last_known_location = Column(JSONB, nullable=True)
    gps_tracking = Column(JSONB, nullable=True)
    stolen_date = Column(DateTime, nullable=True)
    impound_date = Column(DateTime, nullable=True)
    
    # Additional metadata
    vehicle_history = Column(JSONB, default=list, nullable=False)
    modifications = Column(JSONB, default=list, nullable=False)
    damage_report = Column(JSONB, default=dict, nullable=False)
    maintenance_history = Column(JSONB, default=list, nullable=False)
    
    # Relationships
    detections = relationship("Detection", back_populates="vehicle")
    owners = relationship("VehicleOwner", back_populates="vehicle")
    
    __table_args__ = (
        Index('idx_vehicles_license_plate', 'license_plate'),
        Index('idx_vehicles_vin', 'vin'),
        Index('idx_vehicles_make_model', 'make', 'model'),
        Index('idx_vehicles_status', 'status'),
    )

class VehicleOwner(BaseModel):
    __tablename__ = "vehicle_owners"
    
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    ownership_type = Column(String(50), default="owner")  # owner, driver, beneficiary
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    person = relationship("Person", back_populates="vehicles")
    vehicle = relationship("Vehicle", back_populates="owners")
    
    __table_args__ = (
        UniqueConstraint('person_id', 'vehicle_id', name='uq_person_vehicle'),
        Index('idx_vehicle_owners_person', 'person_id'),
        Index('idx_vehicle_owners_vehicle', 'vehicle_id'),
    )

class PhoneNumber(BaseModel):
    __tablename__ = "phone_numbers"
    
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    phone_type = Column(String(30), nullable=True)  # mobile, home, work
    carrier = Column(String(50), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    call_logs = Column(JSONB, default=list, nullable=False)
    sms_logs = Column(JSONB, default=list, nullable=False)
    
    person = relationship("Person", back_populates="phones")
    
    __table_args__ = (
        Index('idx_phone_numbers_person', 'person_id'),
        Index('idx_phone_numbers_number', 'phone_number'),
    )

class SocialMediaAccount(BaseModel):
    __tablename__ = "social_media_accounts"
    
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True)
    platform = Column(String(50), nullable=False)  # facebook, twitter, instagram, etc.
    username = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    profile_url = Column(String(500), nullable=True)
    account_metadata = Column(JSONB, default=dict, nullable=False)
    friends_list = Column(ARRAY(String), default=list, nullable=False)
    post_history = Column(JSONB, default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    person = relationship("Person", back_populates="social_media")
    
    __table_args__ = (
        UniqueConstraint('platform', 'username', name='uq_social_media_platform_username'),
        Index('idx_social_media_person', 'person_id'),
        Index('idx_social_media_platform', 'platform'),
    )

class Detection(BaseModel):
    __tablename__ = "detections"
    
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)
    
    # Detection details
    detection_type = Column(Enum(DetectionType), nullable=False)
    detection_subtype = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=False)
    confidence_level = Column(String(20), nullable=True)
    detection_source = Column(String(100), nullable=False)  # camera, drone, satellite, etc.
    
    # Location and time
    timestamp = Column(DateTime, nullable=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_alt = Column(Float, nullable=True)
    location_accuracy = Column(Float, nullable=True)
    
    # Detection data
    bbox = Column(JSONB, nullable=False)  # [x1, y1, x2, y2]
    frame_id = Column(Integer, default=0, nullable=False)
    video_sequence = Column(Integer, nullable=True)
    source_file = Column(String(500), nullable=True)
    
    # Additional metadata
    metadata_json = Column(JSONB, nullable=True)
    contextual_data = Column(JSONB, nullable=True)
    alert_triggered = Column(Boolean, default=False, nullable=False)
    alert_type = Column(String(50), nullable=True)
    match_score = Column(Float, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Relationships
    case = relationship("Case", back_populates="detections")
    person = relationship("Person", back_populates="detections")
    vehicle = relationship("Vehicle", back_populates="detections")
    reviewer = relationship("User")
    images = relationship("DetectionImage", back_populates="detection", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_detections_case_id', 'case_id'),
        Index('idx_detections_person_id', 'person_id'),
        Index('idx_detections_vehicle_id', 'vehicle_id'),
        Index('idx_detections_timestamp', 'timestamp'),
        Index('idx_detections_type', 'detection_type'),
        Index('idx_detections_location', 'location_lat', 'location_lon'),
        Index('idx_detections_confidence', 'confidence'),
    )

class DetectionImage(BaseModel):
    __tablename__ = "detection_images"
    
    detection_id = Column(UUID(as_uuid=True), ForeignKey("detections.id"), nullable=False)
    image_path = Column(String(500), nullable=False)
    image_type = Column(String(50), nullable=False)  # original, cropped, enhanced
    image_hash = Column(String(64), nullable=True)
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String(20), nullable=True)
    metadata = Column(JSONB, nullable=True)
    is_watermarked = Column(Boolean, default=False, nullable=False)
    
    detection = relationship("Detection", back_populates="images")

class Evidence(BaseModel):
    __tablename__ = "evidence"
    
    evidence_number = Column(String(50), unique=True, index=True, nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True)
    
    # Evidence details
    evidence_type = Column(Enum(EvidenceType), nullable=False)
    sub_type = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Chain of custody
    collection_date = Column(DateTime, nullable=False)
    collection_location = Column(String(255), nullable=True)
    collected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    collected_by_name = Column(String(255), nullable=True)
    collection_method = Column(String(100), nullable=True)
    
    # Evidence status
    status = Column(String(50), default="pending")  # pending, analyzed, in_transit, stored, etc.
    storage_location = Column(String(255), nullable=True)
    storage_conditions = Column(JSONB, nullable=True)
    
    # Handling and security
    security_level = Column(String(50), default="standard")
    restricted_access = Column(Boolean, default=False, nullable=False)
    access_log = Column(JSONB, default=list, nullable=False)
    
    # Analysis
    analyzed = Column(Boolean, default=False, nullable=False)
    analyzed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    analyzed_date = Column(DateTime, nullable=True)
    analysis_results = Column(JSONB, nullable=True)
    
    # Metadata
    file_paths = Column(ARRAY(String), default=list, nullable=False)
    file_hashes = Column(JSONB, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    case = relationship("Case", back_populates="evidence")
    person = relationship("Person")
    assigned_user = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_evidence")
    evidence_creator = relationship("User", foreign_keys=[created_by], back_populates="created_evidence")
    collector = relationship("User", foreign_keys=[collected_by])
    analyst = relationship("User", foreign_keys=[analyzed_by])
    
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    __table_args__ = (
        Index('idx_evidence_case_id', 'case_id'),
        Index('idx_evidence_person_id', 'person_id'),
        Index('idx_evidence_type', 'evidence_type'),
        Index('idx_evidence_status', 'status'),
        Index('idx_evidence_collection_date', 'collection_date'),
        Index('idx_evidence_assigned_to', 'assigned_to'),
    )

class CaseNote(BaseModel):
    __tablename__ = "case_notes"
    
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, update, finding, action
    is_private = Column(Boolean, default=False, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    
    case = relationship("Case", back_populates="notes")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_case_notes_case_id', 'case_id'),
        Index('idx_case_notes_user_id', 'user_id'),
        Index('idx_case_notes_type', 'note_type'),
    )

class Task(BaseModel):
    __tablename__ = "tasks"
    
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    
    due_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    completion_notes = Column(Text, nullable=True)
    
    # Task metadata
    task_type = Column(String(50), default="investigation")  # investigation, analysis, interview, etc.
    dependencies = Column(ARRAY(UUID(as_uuid=True)), default=list, nullable=False)
    attachments = Column(ARRAY(String), default=list, nullable=False)
    
    case = relationship("Case", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index('idx_tasks_case_id', 'case_id'),
        Index('idx_tasks_assigned_to', 'assigned_to'),
        Index('idx_tasks_status', 'status'),
        Index('idx_tasks_due_date', 'due_date'),
    )

class CaseTimeline(BaseModel):
    __tablename__ = "case_timeline"
    
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # detection, evidence, interview, update, etc.
    event_title = Column(String(255), nullable=False)
    event_description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False)
    event_location = Column(JSONB, nullable=True)
    
    # Related entities
    related_detection_id = Column(UUID(as_uuid=True), ForeignKey("detections.id"), nullable=True)
    related_evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=True)
    related_person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=True)
    
    # Additional metadata
    metadata_json = Column(JSONB, nullable=True)
    importance = Column(Integer, default=1, nullable=False)  # 1-5 scale
    
    case = relationship("Case", back_populates="timeline_events")
    detection = relationship("Detection")
    evidence = relationship("Evidence")
    person = relationship("Person")
    
    __table_args__ = (
        Index('idx_timeline_case_id', 'case_id'),
        Index('idx_timeline_event_date', 'event_date'),
        Index('idx_timeline_event_type', 'event_type'),
    )

class AnalysisReport(BaseModel):
    __tablename__ = "analysis_reports"
    
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    report_title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # summary, forensic, financial, etc.
    report_content = Column(Text, nullable=False)
    report_summary = Column(Text, nullable=True)
    report_metadata = Column(JSONB, nullable=True)
    
    findings = Column(JSONB, nullable=True)
    recommendations = Column(JSONB, nullable=True)
    conclusions = Column(JSONB, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_date = Column(DateTime, nullable=True)
    approval_status = Column(String(50), default="draft")  # draft, review, approved, rejected
    
    attachments = Column(ARRAY(String), default=list, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    case = relationship("Case", back_populates="analysis_reports")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    
    __table_args__ = (
        Index('idx_reports_case_id', 'case_id'),
        Index('idx_reports_type', 'report_type'),
        Index('idx_reports_approval_status', 'approval_status'),
    )

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # create, read, update, delete, export, etc.
    resource_type = Column(String(50), nullable=False)  # case, person, vehicle, evidence, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    
    action_details = Column(JSONB, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 ready
    user_agent = Column(String(255), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Performance and system metrics
    execution_time_ms = Column(Float, nullable=True)
    resource_usage = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource_type', 'resource_type'),
        Index('idx_audit_logs_resource_id', 'resource_id'),
        Index('idx_audit_logs_timestamp', 'created_at'),
    )

class AlertRule(BaseModel):
    __tablename__ = "alert_rules"
    
    rule_name = Column(String(255), nullable=False)
    rule_description = Column(Text, nullable=True)
    rule_condition = Column(JSONB, nullable=False)  # Store condition logic
    rule_action = Column(JSONB, nullable=False)  # Store action to take
    
    entity_type = Column(String(50), nullable=False)  # detection, case, evidence, etc.
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    priority = Column(Enum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0, nullable=False)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    __table_args__ = (
        Index('idx_alert_rules_entity_type', 'entity_type'),
        Index('idx_alert_rules_is_active', 'is_active'),
        Index('idx_alert_rules_severity', 'severity'),
    )