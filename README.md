# LEIP: Law Enforcement Intelligence Platform

An enterprise-grade, intelligence-led policing and investigative analysis platform. LEIP combines real-time object detection (YOLOv8), biometric facial recognition (DeepFace & FAISS), automated license plate recognition (ALPR), and comprehensive case/evidence management into a unified, secure web application.

---

## 🏛️ System Overview

LEIP is designed to assist law enforcement agencies, private investigators, and forensic analysts in organizing cases, analyzing media evidence, identifying suspects, tracking vehicles, and generating audit-compliant intelligence reports.

```mermaid
graph TD
    A[CCTV / Image Evidence] --> B(YOLOv8 Object Detector)
    A --> C(DeepFace & FAISS Face Matcher)
    A --> D(ALPR Plate Recognition)
    
    B --> E[FastAPI Core Service]
    C --> E
    D --> E
    
    E --> F[(PostgreSQL Database)]
    E --> G[Streamlit Intel Center]
    E --> H[JSON Intelligence Reports]
```

---

## 🛠️ Technology Stack

*   **Backend Framework**: FastAPI (Asynchronous Python REST API)
*   **Object Detection Engine**: YOLOv8 (Ultralytics) with options for PyTorch or optimized C++ Rust ONNX inference backends
*   **Facial Recognition**: DeepFace (biometric feature extraction) & FAISS (fast vector similarity search)
*   **ALPR**: EasyOCR / PaddleOCR with predictive vehicle routing
*   **Database & ORM**: PostgreSQL with SQLAlchemy 2.0 (UUID-based keys, comprehensive indexes, soft deletes, and JSONB audit trails)
*   **Frontend Interface**: Streamlit (FBI-style tactical dark theme)
*   **Security & Encryption**: Cryptography, PyJWT, and Passlib (PBKDF2)

---

## 📋 Key Features

### 1. Advanced Evidence Analysis
*   **Multi-Class Object Detection**: Automated detection of people, vehicles, weapons, and custom objects.
*   **Biometric Face Search**: 1:1 facial verification and 1:N database gallery search with customizable confidence thresholds.
*   **Automated CCTV Processing**: Asynchronous video frame extraction and analysis with background tasks.

### 2. Intelligent Case Management
*   **Core Entities**: Maintain detailed profiles of **Cases**, **Persons**, **Vehicles**, and **Evidence**.
*   **Chain of Custody**: Log collection dates, storage locations, security levels, and handler details for all physical and digital evidence.
*   **Entity Linking**: Automatically associate detections and phone logs with target suspect profiles.

### 3. Investigation Records & Reporting
*   **Tactical Dashboard**: View metrics on active cases, total evidence files, and detection alerts.
*   **Intelligence Reports**: Generate structured case summaries detailing detection metrics, suspect profiles, and timeline events.
*   **Audit Logging**: Immutable action-level audit trail documenting IP address, browser agent, user ID, and executed actions.

---

## 🗄️ Database Architecture (SQLAlchemy ORM)

LEIP uses a highly structured, relational database model with automated lifecycle columns:
*   **BaseModel**: Implements auto-generated UUID primary keys, `created_at`, `updated_at`, creator tracking (`created_by`/`updated_by`), soft-deletes (`is_deleted`/`deleted_at`), and schema versioning.
*   **User**: Role-based access control (RBAC) supporting `INVESTIGATOR`, `ANALYST`, and `ADMINISTRATOR`. Includes login lockouts, email verification, and specific permission matrices.
*   **Case**: Stores case numbers, titles, priority levels (Low to Critical), status (Open to Solved), sensitivity classifications (e.g. Secret, Unclassified), and geographic coordinates.
*   **Person**: Suspect biography records, physical descriptions (tattoos, eye/hair color), identification documents (SSN, Passport), criminal history logs, and facial recognition vector bindings.
*   **Vehicle**: Registers VIN, license plate numbers, owner links, vehicle status (e.g. Stolen, Active), and GPS coordinates.
*   **Detection**: Stores bounding box coordinates (`bbox`), frame IDs, detection types (person, vehicle, face, license_plate), confidence scores, and source media references.
*   **Evidence**: Tracks chain of custody, storage conditions, restriction overrides, and access logs.
*   **AuditLog**: Captures every API call for compliance and forensic accountability.

---

## 🚀 Installation & Setup

### Prerequisites
*   Python 3.10 or 3.11
*   PostgreSQL Database (optional; defaults to SQLite if database URL is unconfigured)

### 1. Clone & Set Up Environment
```bash
# Clone the repository
git clone https://github.com/waleolonade/Investigation-software.git
cd Investigation-software

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r leip/requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in `leip/` directory using the provided template:
```env
API_HOST=127.0.0.1
API_PORT=8000
DATABASE_URL=postgresql://postgres:password@localhost:5432/leip
SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
LOG_LEVEL=INFO
```

### 3. Start the FastAPI Backend
```bash
cd leip
uvicorn app.api:app --reload
```
Once started, the interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Run the Streamlit Intel Center (Frontend)
```bash
streamlit run frontend/app.py
```
This will open the tactical dark-themed interface in your default browser at `http://localhost:8501`.

---

## 🛡️ API Endpoint Documentation

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticate user and issue JWT token |
| | `GET` | `/api/v1/auth/me` | Fetch active user credentials and role |
| **Cases** | `POST` | `/api/v1/cases` | Create a new investigation case |
| | `GET` | `/api/v1/cases/{case_id}` | Fetch case details, priority, and detections |
| | `GET` | `/api/v1/cases` | List cases with optional status/priority filters |
| **Faces** | `POST` | `/api/v1/faces/upload` | Register suspect facial image to gallery |
| | `POST` | `/api/v1/faces/search` | Search gallery for matching face (1:N) |
| | `POST` | `/api/v1/faces/verify` | Verify match between two face images (1:1) |
| **CCTV** | `POST` | `/api/v1/cctv/process-video`| Upload and queue video for async analysis |
| | `GET` | `/api/v1/cctv/job/{job_id}` | Check status of video processing task |
| **Vehicles**| `POST` | `/api/v1/vehicles/track` | Query tracking history and predicted coordinates |
| **Reports** | `POST` | `/api/v1/reports/case-summary`| Generate detailed JSON case report summary |

---

## 🔒 Security & Compliance
1.  **RBAC Enforced**: API routes verify token claims (`investigator`, `analyst`, `administrator`) before serving requested resources.
2.  **Password Security**: Utilizes Argon2/PBKDF2 via Passlib to ensure passwords cannot be reversed.
3.  **Comprehensive Audits**: Every database change or search action is timestamped and linked to the active analyst session ID.
