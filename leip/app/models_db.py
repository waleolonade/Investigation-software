"""
LEIP Database Models
SQLAlchemy ORM models for Law Enforcement Intelligence Platform
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, LargeBinary, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Case(Base):
    """Investigation Case Record"""
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(String(50), unique=True, nullable=False)
    case_name = Column(String(255), nullable=False)
    status = Column(String(50), default="OPEN")  # OPEN, CLOSED, PENDING, ARCHIVED
    priority = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    investigation_logs = relationship("InvestigationLog", back_populates="case", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="case", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_cases_status', 'status'),
        Index('idx_cases_created_at', 'created_at'),
    )


class Evidence(Base):
    """Physical/Digital Evidence Record"""
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True)
    evidence_id = Column(String(50), unique=True, nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    evidence_type = Column(String(100))  # IMAGE, VIDEO, AUDIO, DOCUMENT
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # in bytes
    file_format = Column(String(20))
    resolution = Column(String(20))  # e.g., "1920x1080"
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(100))
    description = Column(Text)
    location_latitude = Column(Float)
    location_longitude = Column(Float)
    capture_timestamp = Column(DateTime)
    status = Column(String(50), default="PENDING")  # PENDING, ANALYZED, FLAGGED, ARCHIVED
    analysis_status = Column(String(50), default="NOT_STARTED")
    
    # Relationships
    case = relationship("Case", back_populates="evidence")
    detections = relationship("Detection", back_populates="evidence", cascade="all, delete-orphan")
    analysis_history = relationship("AnalysisHistory", back_populates="evidence", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_evidence_case_id', 'case_id'),
        Index('idx_evidence_status', 'status'),
        Index('idx_evidence_uploaded_at', 'uploaded_at'),
    )


class Detection(Base):
    """YOLO Detection Record"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True)
    detection_id = Column(String(50), unique=True, nullable=False)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(Integer, nullable=False)
    class_name = Column(String(100))
    confidence = Column(Float)  # 0.0 - 1.0
    bbox_x1 = Column(Float)
    bbox_y1 = Column(Float)
    bbox_x2 = Column(Float)
    bbox_y2 = Column(Float)
    bbox_width = Column(Float)
    bbox_height = Column(Float)
    bbox_center_x = Column(Float)
    bbox_center_y = Column(Float)
    detection_engine = Column(String(50))  # ultralytics, rust_onnx
    detected_at = Column(DateTime, default=datetime.utcnow)
    flagged = Column(Boolean, default=False)
    flag_reason = Column(String(255))
    notes = Column(Text)
    
    # Relationships
    evidence = relationship("Evidence", back_populates="detections")
    facial_matches = relationship("FacialMatch", back_populates="detection", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_detections_evidence_id', 'evidence_id'),
        Index('idx_detections_class_id', 'class_id'),
        Index('idx_detections_confidence', 'confidence'),
        Index('idx_detections_detected_at', 'detected_at'),
    )


class Suspect(Base):
    """Suspect Database Record"""
    __tablename__ = "suspects"
    
    id = Column(Integer, primary_key=True)
    suspect_id = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    aliases = Column(Text)  # JSON or comma-separated
    date_of_birth = Column(DateTime)
    gender = Column(String(20))
    height = Column(String(10))
    weight = Column(String(10))
    hair_color = Column(String(50))
    eye_color = Column(String(50))
    distinguishing_marks = Column(Text)
    criminal_history = Column(Text)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, ARRESTED, DECEASED, INACTIVE
    threat_level = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    bio_data = Column(LargeBinary)  # facial encoding or biometric data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    facial_matches = relationship("FacialMatch", back_populates="suspect")
    
    __table_args__ = (
        Index('idx_suspects_status', 'status'),
    )


class FacialMatch(Base):
    """Facial Recognition Match Record"""
    __tablename__ = "facial_matches"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(50), unique=True, nullable=False)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False)
    suspect_id = Column(Integer, ForeignKey("suspects.id", ondelete="SET NULL"))
    match_confidence = Column(Float)  # 0.0 - 1.0
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    status = Column(String(50), default="PENDING")  # PENDING, CONFIRMED, REJECTED, INCONCLUSIVE
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    detection = relationship("Detection", back_populates="facial_matches")
    suspect = relationship("Suspect", back_populates="facial_matches")
    
    __table_args__ = (
        Index('idx_facial_matches_detection_id', 'detection_id'),
        Index('idx_facial_matches_suspect_id', 'suspect_id'),
        Index('idx_facial_matches_confidence', 'match_confidence'),
    )


class InvestigationLog(Base):
    """Investigation Activity Log"""
    __tablename__ = "investigation_logs"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    log_type = Column(String(50))  # ANALYSIS, UPDATE, FLAG, COMMENT, MATCH_FOUND
    action = Column(String(255))
    details = Column(Text)
    performed_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("Case", back_populates="investigation_logs")
    
    __table_args__ = (
        Index('idx_investigation_logs_case_id', 'case_id'),
        Index('idx_investigation_logs_created_at', 'created_at'),
    )


class AnalysisHistory(Base):
    """Detection Analysis History"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)
    backend_engine = Column(String(50))  # ultralytics, rust_onnx
    analysis_type = Column(String(100))  # object_detection, facial_recognition
    confidence_threshold = Column(Float)
    nms_threshold = Column(Float)
    total_detections = Column(Integer)
    processing_time_ms = Column(Float)
    status = Column(String(50))  # SUCCESS, FAILED, INCOMPLETE
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    analyzed_by = Column(String(100))
    
    # Relationships
    evidence = relationship("Evidence", back_populates="analysis_history")
    
    __table_args__ = (
        Index('idx_analysis_history_evidence_id', 'evidence_id'),
    )


class Alert(Base):
    """Investigation Alert/Notification"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(String(50), unique=True, nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    alert_type = Column(String(50))  # DETECTION_MATCH, HIGH_CONFIDENCE, SUSPECT_SPOTTED
    severity = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    title = Column(String(255), nullable=False)
    description = Column(Text)
    related_detection_id = Column(Integer, ForeignKey("detections.id", ondelete="SET NULL"))
    related_suspect_id = Column(Integer, ForeignKey("suspects.id", ondelete="SET NULL"))
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("Case", back_populates="alerts")
    
    __table_args__ = (
        Index('idx_alerts_case_id', 'case_id'),
        Index('idx_alerts_severity', 'severity'),
    )


class SystemLog(Base):
    """System/Application Log"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True)
    log_level = Column(String(20))  # INFO, WARNING, ERROR, CRITICAL
    component = Column(String(100))
    message = Column(Text)
    stack_trace = Column(Text)
    user = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_system_logs_created_at', 'created_at'),
    )


class User(Base):
    """System User Account"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100), unique=True)
    role = Column(String(50), default="ANALYST")  # ADMIN, INVESTIGATOR, ANALYST, VIEWER
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_users_username', 'username'),
    )
