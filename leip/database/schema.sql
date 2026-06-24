-- LEIP Investigation Database Schema
-- Law Enforcement Intelligence Platform
-- PostgreSQL / SQLite Compatible

-- ============================================
-- 1. CASES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS cases (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) UNIQUE NOT NULL,
    case_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'OPEN',  -- OPEN, CLOSED, PENDING, ARCHIVED
    priority VARCHAR(20) DEFAULT 'MEDIUM',  -- LOW, MEDIUM, HIGH, CRITICAL
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to VARCHAR(100),
    notes TEXT
);

-- ============================================
-- 2. EVIDENCE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    evidence_id VARCHAR(50) UNIQUE NOT NULL,
    case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    evidence_type VARCHAR(100),  -- IMAGE, VIDEO, AUDIO, DOCUMENT
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,  -- in bytes
    file_format VARCHAR(20),  -- jpg, png, mp4, etc.
    resolution VARCHAR(20),  -- e.g., "1920x1080"
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by VARCHAR(100),
    description TEXT,
    location_latitude FLOAT,
    location_longitude FLOAT,
    capture_timestamp TIMESTAMP,  -- when evidence was originally captured
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, ANALYZED, FLAGGED, ARCHIVED
    analysis_status VARCHAR(50) DEFAULT 'NOT_STARTED'  -- NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED
);

-- ============================================
-- 3. DETECTION RECORDS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    detection_id VARCHAR(50) UNIQUE NOT NULL,
    evidence_id INTEGER NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL,
    class_name VARCHAR(100),  -- person, vehicle, weapon, etc.
    confidence FLOAT,  -- 0.0 - 1.0
    bbox_x1 FLOAT,
    bbox_y1 FLOAT,
    bbox_x2 FLOAT,
    bbox_y2 FLOAT,
    bbox_width FLOAT,
    bbox_height FLOAT,
    bbox_center_x FLOAT,
    bbox_center_y FLOAT,
    detection_engine VARCHAR(50),  -- ultralytics, rust_onnx
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    flagged BOOLEAN DEFAULT FALSE,
    flag_reason VARCHAR(255),
    notes TEXT
);

-- ============================================
-- 4. SUSPECTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS suspects (
    id SERIAL PRIMARY KEY,
    suspect_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    aliases TEXT,  -- JSON or comma-separated
    date_of_birth DATE,
    gender VARCHAR(20),
    height VARCHAR(10),
    weight VARCHAR(10),
    hair_color VARCHAR(50),
    eye_color VARCHAR(50),
    distinguishing_marks TEXT,
    criminal_history TEXT,
    status VARCHAR(50) DEFAULT 'ACTIVE',  -- ACTIVE, ARRESTED, DECEASED, INACTIVE
    threat_level VARCHAR(20) DEFAULT 'MEDIUM',  -- LOW, MEDIUM, HIGH, CRITICAL
    bio_data BYTEA,  -- facial encoding or biometric data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ============================================
-- 5. FACIAL RECOGNITION RECORDS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS facial_matches (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(50) UNIQUE NOT NULL,
    detection_id INTEGER NOT NULL REFERENCES detections(id) ON DELETE CASCADE,
    suspect_id INTEGER REFERENCES suspects(id) ON DELETE SET NULL,
    match_confidence FLOAT,  -- 0.0 - 1.0
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'PENDING',  -- PENDING, CONFIRMED, REJECTED, INCONCLUSIVE
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. INVESTIGATION LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS investigation_logs (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    log_type VARCHAR(50),  -- ANALYSIS, UPDATE, FLAG, COMMENT, MATCH_FOUND
    action VARCHAR(255),
    details TEXT,
    performed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. ANALYSIS HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS analysis_history (
    id SERIAL PRIMARY KEY,
    evidence_id INTEGER NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
    backend_engine VARCHAR(50),  -- ultralytics, rust_onnx
    analysis_type VARCHAR(100),  -- object_detection, facial_recognition
    confidence_threshold FLOAT,
    nms_threshold FLOAT,
    total_detections INTEGER,
    processing_time_ms FLOAT,
    status VARCHAR(50),  -- SUCCESS, FAILED, INCOMPLETE
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    analyzed_by VARCHAR(100)
);

-- ============================================
-- 8. ALERTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(50) UNIQUE NOT NULL,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    alert_type VARCHAR(50),  -- DETECTION_MATCH, HIGH_CONFIDENCE, SUSPECT_SPOTTED
    severity VARCHAR(20) DEFAULT 'MEDIUM',  -- LOW, MEDIUM, HIGH, CRITICAL
    title VARCHAR(255) NOT NULL,
    description TEXT,
    related_detection_id INTEGER REFERENCES detections(id) ON DELETE SET NULL,
    related_suspect_id INTEGER REFERENCES suspects(id) ON DELETE SET NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 9. SYSTEM LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(20),  -- INFO, WARNING, ERROR, CRITICAL
    component VARCHAR(100),  -- detector, api, database, etc.
    message TEXT,
    stack_trace TEXT,
    user VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 10. USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    role VARCHAR(50) DEFAULT 'ANALYST',  -- ADMIN, INVESTIGATOR, ANALYST, VIEWER
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created_at ON cases(created_at);
CREATE INDEX idx_evidence_case_id ON evidence(case_id);
CREATE INDEX idx_evidence_status ON evidence(status);
CREATE INDEX idx_evidence_uploaded_at ON evidence(uploaded_at);
CREATE INDEX idx_detections_evidence_id ON detections(evidence_id);
CREATE INDEX idx_detections_class_id ON detections(class_id);
CREATE INDEX idx_detections_confidence ON detections(confidence);
CREATE INDEX idx_detections_detected_at ON detections(detected_at);
CREATE INDEX idx_suspects_status ON suspects(status);
CREATE INDEX idx_facial_matches_detection_id ON facial_matches(detection_id);
CREATE INDEX idx_facial_matches_suspect_id ON facial_matches(suspect_id);
CREATE INDEX idx_facial_matches_confidence ON facial_matches(match_confidence);
CREATE INDEX idx_investigation_logs_case_id ON investigation_logs(case_id);
CREATE INDEX idx_investigation_logs_created_at ON investigation_logs(created_at);
CREATE INDEX idx_analysis_history_evidence_id ON analysis_history(evidence_id);
CREATE INDEX idx_alerts_case_id ON alerts(case_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX idx_users_username ON users(username);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Active Cases with Evidence Count
CREATE OR REPLACE VIEW v_active_cases_summary AS
SELECT 
    c.id,
    c.case_id,
    c.case_name,
    c.status,
    c.priority,
    COUNT(DISTINCT e.id) as evidence_count,
    COUNT(DISTINCT d.id) as total_detections,
    c.created_at,
    c.assigned_to
FROM cases c
LEFT JOIN evidence e ON c.id = e.case_id
LEFT JOIN detections d ON e.id = d.evidence_id
WHERE c.status = 'OPEN'
GROUP BY c.id, c.case_id, c.case_name, c.status, c.priority, c.created_at, c.assigned_to
ORDER BY c.priority DESC, c.created_at DESC;

-- High Confidence Detections
CREATE OR REPLACE VIEW v_high_confidence_detections AS
SELECT 
    d.id,
    d.detection_id,
    d.class_name,
    d.confidence,
    e.evidence_id,
    e.filename,
    c.case_id,
    c.case_name,
    d.detected_at
FROM detections d
JOIN evidence e ON d.evidence_id = e.id
JOIN cases c ON e.case_id = c.id
WHERE d.confidence > 0.85 AND c.status = 'OPEN'
ORDER BY d.confidence DESC, d.detected_at DESC;

-- Suspect Match Report
CREATE OR REPLACE VIEW v_suspect_matches AS
SELECT 
    fm.id,
    fm.match_id,
    s.suspect_id,
    s.first_name,
    s.last_name,
    s.threat_level,
    fm.match_confidence,
    fm.status,
    e.evidence_id,
    e.filename,
    c.case_id,
    c.case_name,
    fm.created_at
FROM facial_matches fm
JOIN suspects s ON fm.suspect_id = s.id
JOIN detections d ON fm.detection_id = d.id
JOIN evidence e ON d.evidence_id = e.id
JOIN cases c ON e.case_id = c.id
WHERE fm.match_confidence > 0.75
ORDER BY fm.match_confidence DESC, fm.created_at DESC;

-- Investigation Summary
CREATE OR REPLACE VIEW v_investigation_summary AS
SELECT 
    c.id,
    c.case_id,
    c.case_name,
    c.status,
    COUNT(DISTINCT e.id) as total_evidence,
    COUNT(DISTINCT d.id) as total_detections,
    COUNT(DISTINCT CASE WHEN d.flagged THEN d.id END) as flagged_detections,
    COUNT(DISTINCT fm.id) as suspect_matches,
    c.created_at,
    c.updated_at
FROM cases c
LEFT JOIN evidence e ON c.id = e.case_id
LEFT JOIN detections d ON e.id = d.evidence_id
LEFT JOIN facial_matches fm ON d.id = fm.detection_id
GROUP BY c.id, c.case_id, c.case_name, c.status, c.created_at, c.updated_at;
