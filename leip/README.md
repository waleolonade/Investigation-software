# LEIP - Law Enforcement Intelligence Platform

**Professional Facial Recognition & Multi-Modal Investigation System**

A comprehensive, enterprise-grade investigation platform combining facial recognition, CCTV integration, vehicle detection, real-time mapping, and database correlations for authorized law enforcement agencies.

---

## ⚠️ CRITICAL LEGAL & ETHICAL NOTICE

**This software is for authorized law enforcement use ONLY under:**
- Government/law enforcement contracts
- Proper warrants and data-sharing agreements
- CJIS, GDPR, and relevant compliance frameworks
- Formal partnerships with data sources (hospitals, schools, social media)
- Ethical AI practices and human oversight

**Unauthorized use for surveillance, data scraping, or privacy violations is illegal.**

---

## Project Structure

```
leip/
├── app/                    # Core application modules
│   ├── face_utils.py      # Face detection, matching, embeddings
│   ├── cctv_processor.py  # CCTV/video frame processing
│   ├── yolo_detector.py   # YOLO-based pedestrian/vehicle detection
│   ├── plate_recognition.py # License plate detection & OCR
│   ├── database.py        # Database operations & queries
│   ├── api.py             # FastAPI backend
│   └── __init__.py
├── models/                # Pre-trained models & indexes
│   ├── face_gallery.pkl   # Face embedding database
│   ├── face_index.faiss   # FAISS vector index
│   └── weights/           # YOLO weights (auto-downloaded)
├── data/                  # Test/sample data
│   ├── sample_images/
│   ├── sample_videos/
│   └── test_cases.csv
├── config/                # Configuration files
│   ├── settings.py        # Application settings
│   ├── database.py        # Database config
│   └── logging.yaml       # Logging configuration
├── tests/                 # Unit & integration tests
│   ├── test_face.py
│   ├── test_cctv.py
│   └── test_api.py
├── frontend/              # Dashboard & UI
│   ├── app.py            # Streamlit dashboard
│   └── static/           # CSS, JS, maps
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── docker-compose.yml    # Docker orchestration
└── README.md

```

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Face Recognition** | InsightFace, DeepFace, ArcFace embeddings |
| **Detection** | YOLOv8 (pedestrians, vehicles) |
| **Plate Recognition** | EasyOCR, PaddleOCR |
| **Vector Search** | FAISS (GPU-accelerated) |
| **Backend** | FastAPI, Python 3.12+ |
| **Database** | PostgreSQL + PostGIS |
| **Real-time** | Kafka streams |
| **Frontend** | Streamlit, Folium maps |
| **Deployment** | Docker, Kubernetes |
| **Monitoring** | Prometheus, Grafana |

---

## Phase-by-Phase Implementation Plan

### Phase 1: Face Detection & Matching ✅ (In Progress)
- Extract face embeddings from images/video
- Build searchable gallery (FAISS index)
- 1:1 verification and 1:N identification
- Similarity scoring and thresholding

### Phase 2: CCTV & Multi-Modal Detection
- Real-time video stream processing
- YOLO human/vehicle detection
- Extract frames for face matching
- Movement tracking across frames

### Phase 3: License Plate Recognition
- Detect vehicle plates in CCTV
- OCR for plate number extraction
- Link plates to DMV/vehicle owner databases
- Create vehicle trajectory correlations

### Phase 4: Backend API
- RESTful endpoints for all operations
- Queue-based async processing (Celery)
- Database integration with audit logging
- Role-based access control (RBAC)

### Phase 5: Dashboard & Visualization
- Streamlit web interface
- Match visualization (confidence scores, timelines)
- Case management and reporting
- Export capabilities (PDF, CSV)

### Phase 6: Real-Time Mapping & Tracing
- Interactive maps (Folium/Leaflet)
- Location overlay of detections
- Geofencing and alerts
- Predictive analytics (hotspots)

### Phase 7: External Integrations
- Social media OSINT (authorized APIs only)
- Educational/hospital record linkage (via partnerships)
- Real-time alert systems
- Multi-agency collaboration tools

---

## Quick Start

### Local Setup

```bash
# 1. Clone and setup
git clone <repo>
cd leip
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with database credentials, API keys, etc.

# 4. Initialize database
python -m alembic upgrade head

# 5. Run tests
pytest tests/

# 6. Start API server
python -m uvicorn app.api:app --reload

# 7. Launch dashboard (separate terminal)
streamlit run frontend/app.py
```

### Docker Deployment

```bash
docker-compose up -d
# Services: API (port 8000), Dashboard (port 8501), PostgreSQL, Kafka
```

---

## Core Features

### 1. Face Matching Engine
- **1:1 Verification**: Compare probe vs. gallery images
- **1:N Identification**: Search gallery for matches
- **Multi-view Fusion**: Handle different angles/lighting
- **Confidence Scoring**: Threshold-based filtering

### 2. CCTV Integration
- **Real-time Streaming**: Process video feeds
- **Frame Extraction**: Intelligent keyframe selection
- **Detection Pipeline**: Humans + vehicles
- **Metadata Extraction**: Timestamps, locations

### 3. Vehicle & Plate Detection
- **Object Detection**: YOLOv8 for vehicles
- **Plate Localization**: Specialized models
- **OCR**: Extract alphanumeric plate data
- **Database Correlation**: Link to vehicle owner info

### 4. Database & Correlations
- **Embeddings Database**: PostgreSQL + FAISS
- **Knowledge Graph**: Entity relationships (Person → Vehicle → Location)
- **Audit Logs**: Chain-of-custody for evidence
- **Full-text Search**: Query by multiple attributes

### 5. Real-Time Mapping
- **Interactive Maps**: Overlay detections
- **Movement Trails**: Track trajectories
- **Geofencing**: Alerts on boundary crossing
- **Heatmaps**: Hotspot analysis

### 6. Case Management
- **Evidence Management**: Organized storage with metadata
- **Reporting**: Automated PDFs with findings
- **Collaboration**: Secure multi-user access
- **Audit Trail**: All actions logged

---

## Configuration

Create `.env` file from `.env.example`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/leip_db

# Face Recognition
FACE_SIMILARITY_THRESHOLD=0.6
FACE_MODEL_NAME=ArcFace

# YOLO
YOLO_MODEL_SIZE=medium  # nano, small, medium, large, xlarge
YOLO_CONFIDENCE_THRESHOLD=0.5
YOLO_IOU_THRESHOLD=0.45
YOLO_DEVICE=cpu
YOLO_BACKEND=ultralytics  # rust or ultralytics
YOLO_ONNX_PATH=yolov8m.onnx
YOLO_CLASS_NAMES=coco.names
YOLO_ONNX_INPUT_SIZE=640
YOLO_RUST_PERSISTENT=true

# API
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-here

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/leip.log

# Security
ENABLE_RBAC=true
JWT_EXPIRATION_HOURS=24
```

---

## API Endpoints (FastAPI)

```
POST   /api/v1/faces/upload          - Upload and index face
GET    /api/v1/faces/search          - Search gallery (1:N)
POST   /api/v1/faces/verify          - Verify 1:1 comparison
POST   /api/v1/cctv/process-frame    - Process CCTV frame
POST   /api/v1/cctv/process-video    - Process video file
GET    /api/v1/detections            - Get detections for case
POST   /api/v1/cases                 - Create investigation case
GET    /api/v1/cases/{case_id}       - Get case details
GET    /api/v1/map/detections        - Get detections for map overlay
POST   /api/v1/reports/generate      - Generate case report
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=app

# Specific test
pytest tests/test_face.py::test_face_matching
```

---

## Performance & Scaling

| Component | Capacity | Optimization |
|-----------|----------|--------------|
| Face Embeddings | 10M+ faces | FAISS IndexIVFPQ compression |
| CCTV Streams | 100+ concurrent | Frame skipping, GPU processing |
| Plate Recognition | 1000+ plates/min | Batch inference |
| Queries | 1000+ QPS | Caching, index sharding |

---

## Security Best Practices

✅ **Implemented:**
- Role-based access control (RBAC)
- JWT authentication
- Encrypted audit logs
- Secure password hashing
- HTTPS/TLS enforcement
- Data anonymization options

⚠️ **To Implement (Enterprise):**
- Hardware security modules (HSMs)
- Biometric MFA
- Threat detection & SIEM integration
- Penetration testing
- Bug bounty program

---

## Monitoring & Observability

Metrics exposed via Prometheus:
- API response times
- Face match latency
- CCTV processing throughput
- Database query performance
- Error rates by component

Logs aggregated with ELK stack for investigation.

---

## Resources

- [InsightFace GitHub](https://github.com/deepinsight/insightface)
- [YOLO Documentation](https://docs.ultralytics.com/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [NIST Face Recognition Evaluations](https://nvlpubs.nist.gov/nistpubs/ir/2023/NIST.IR.8323.pdf)

---

## Legal Compliance Checklist

- [ ] Formal government/law enforcement contract
- [ ] Data-sharing agreements with external sources
- [ ] CJIS compliance (US) or equivalent
- [ ] Bias audits and fairness reports
- [ ] Privacy impact assessment (PIA)
- [ ] Ethical AI review board approval
- [ ] Pen testing & security certification
- [ ] Data retention & destruction policies
- [ ] Warrant procedures documented
- [ ] Training program for operators

---

## Contributors

This platform is developed for authorized law enforcement agencies only. Contributions must align with legal and ethical standards.

---

## License

**RESTRICTED USE LICENSE** - This software is proprietary and may only be used by authorized law enforcement agencies under formal contract. Unauthorized distribution or use is prohibited by law.

---

## Support & Contact

For technical support or inquiries regarding deployment in law enforcement agencies, contact: [your-agency-email]

---

**Last Updated**: 2024  
**Version**: 0.1.0-MVP
