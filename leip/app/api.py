"""
LEIP FastAPI Backend
RESTful API for all investigation operations
"""

import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks, Depends, status, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict
from datetime import datetime, timedelta
import uuid
from pathlib import Path
import shutil
import json

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config.settings import settings
from app.face_utils import LEIPFaceMatcher
from app.cctv_processor import CCTVProcessor
from app.yolo_detector import YOLODetector
from app.plate_recognition import LicensePlateRecognizer, VehicleTracker

# Database imports
from app.database import engine, get_db
from app import models, schemas, crud

# ============ LOGGING ============
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ INITIALIZE APP ============
app = FastAPI(
    title="LEIP - Law Enforcement Intelligence Platform",
    description="Professional facial recognition and investigation system",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ AUTH HELPERS ============
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.jwt_expiration_hours))
    sub_claim = data.get("sub")
    if not isinstance(sub_claim, str) or not sub_claim:
        raise ValueError("JWT subject claim must be a non-empty string")
    to_encode.update({"exp": expire, "sub": sub_claim})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
        if not isinstance(username, str):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ============ GLOBALS ============
face_matcher = None
cctv_processor = None
plate_recognizer = None
vehicle_tracker = VehicleTracker()

def initialize_models():
    """Initialize AI models on startup"""
    global face_matcher, cctv_processor, plate_recognizer
    logger.info("Initializing AI models...")
    
    try:
        face_matcher = LEIPFaceMatcher()
        logger.info("✓ Face Matcher initialized")
    except Exception as e:
        logger.warning(f"Face Matcher initialization failed: {e}")
    
    try:
        cctv_processor = CCTVProcessor(enable_face_matching=True)
        logger.info("✓ CCTV Processor initialized")
    except Exception as e:
        logger.warning(f"CCTV Processor initialization failed: {e}")
    
    try:
        plate_recognizer = LicensePlateRecognizer()
        logger.info("✓ Plate Recognizer initialized")
    except Exception as e:
        logger.warning(f"Plate Recognizer initialization failed: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    # Create DB tables
    models.Base.metadata.create_all(bind=engine)
    
    # Pre-populate fake users for testing if DB is empty
    db = next(get_db())
    if not crud.get_user_by_username(db, "investigator"):
        crud.create_user(db, schemas.UserCreate(
            username="investigator",
            full_name="Investigation Analyst",
            email="investigator@example.com",
            password="password123",
            role="investigator"
        ))
    if not crud.get_user_by_username(db, "admin"):
        crud.create_user(db, schemas.UserCreate(
            username="admin",
            full_name="LEIP Administrator",
            email="admin@example.com",
            password="adminPassword!",
            role="administrator"
        ))
    db.close()

    initialize_models()

# ============ HEALTH & INFO ============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }

@app.get("/api/v1/info")
async def system_info(db: Session = Depends(get_db)):
    """Get system information"""
    cases_count = len(crud.get_cases(db))
    return {
        "platform_name": "LEIP",
        "version": "0.1.0",
        "environment": {
            "face_model": settings.face_model_name,
            "yolo_size": settings.yolo_model_size,
            "faiss_index_type": settings.faiss_index_type
        },
        "gallery_size": len(face_matcher.gallery) if face_matcher else 0,
        "cases_count": cases_count
    }

# ============ FACE RECOGNITION ENDPOINTS ============

@app.post("/api/v1/faces/upload")
async def upload_face(
    person_id: str,
    file: UploadFile = File(...),
    metadata: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    if not face_matcher:
        raise HTTPException(status_code=503, detail="Face matcher not available")
    
    try:
        upload_dir = Path(settings.upload_dir) / person_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        filename = Path(file.filename or "upload.bin").name
        file_path = upload_dir / filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        meta_dict = {}
        if metadata:
            meta_dict = json.loads(metadata)
        meta_dict.update({
            'upload_date': datetime.now().isoformat(),
            'filename': filename
        })
        
        success = face_matcher.add_to_gallery(person_id, str(file_path), meta_dict)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to extract face from image")
            
        # Ensure Person exists in DB
        person = crud.get_person(db, person_id)
        if not person:
            full_name = meta_dict.get('name', 'Unknown')
            name_parts = full_name.split(maxsplit=1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            crud.create_person(db, schemas.PersonCreate(
                person_number=person_id,
                first_name=first_name,
                last_name=last_name,
                status="active"
            ))
        
        return {
            "status": "success",
            "person_id": person_id,
            "filename": filename,
            "gallery_size": len(face_matcher.gallery)
        }
    
    except Exception as e:
        logger.error(f"Face upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/faces/search")
async def search_faces(
    file: UploadFile = File(...),
    top_k: int = Query(10, ge=1, le=100),
    threshold: Optional[float] = Query(None)
):
    if not face_matcher:
        raise HTTPException(status_code=503, detail="Face matcher not available")
    
    try:
        probe_dir = Path(settings.temp_dir)
        probe_dir.mkdir(parents=True, exist_ok=True)
        probe_filename = Path(file.filename or "probe.bin").name
        probe_path = probe_dir / probe_filename
        
        with open(probe_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        matches = face_matcher.search_gallery(str(probe_path), top_k, threshold)
        
        probe_path.unlink()
        
        return {
            "status": "success",
            "matches_count": len(matches),
            "matches": matches,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Face search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/faces/verify")
async def verify_faces(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...)
):
    if not face_matcher:
        raise HTTPException(status_code=503, detail="Face matcher not available")
    
    try:
        temp_dir = Path(settings.temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        path1 = temp_dir / "verify_1.jpg"
        path2 = temp_dir / "verify_2.jpg"
        
        with open(path1, "wb") as f:
            f.write(await file1.read())
        with open(path2, "wb") as f:
            f.write(await file2.read())
        
        result = face_matcher.verify_1_to_1(str(path1), str(path2))
        
        path1.unlink()
        path2.unlink()
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Face verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ VIDEO PROCESSING ENDPOINTS ============

@app.post("/api/v1/cctv/process-video")
async def process_video_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    frame_skip: int = Query(5, ge=1, le=30),
    case_id: Optional[str] = Query(None)
):
    if not cctv_processor:
        raise HTTPException(status_code=503, detail="CCTV processor not available")
    
    try:
        job_id = str(uuid.uuid4())
        
        video_dir = Path(settings.upload_dir) / "videos" / job_id
        video_dir.mkdir(parents=True, exist_ok=True)
        
        video_filename = Path(file.filename or "video.bin").name
        video_path = video_dir / video_filename
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        if background_tasks:
            background_tasks.add_task(
                cctv_processor.process_video,
                str(video_path),
                output_dir=str(video_dir),
                frame_skip=frame_skip,
                case_id=case_id
            )
        
        return {
            "status": "processing",
            "job_id": job_id,
            "video_filename": video_filename
        }
    
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cctv/job/{job_id}")
async def get_job_status(job_id: str):
    job_dir = Path(settings.upload_dir) / "videos" / job_id
    
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    
    results_file = job_dir / "processing_results.json"
    
    if results_file.exists():
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        return {
            "status": "completed",
            "job_id": job_id,
            "results": results
        }
    else:
        return {
            "status": "processing",
            "job_id": job_id
        }

# ============ CASE MANAGEMENT ============

@app.post("/api/v1/cases")
async def create_case(request: schemas.CaseCreate, db: Session = Depends(get_db)):
    """Create a new investigation case"""
    case = crud.create_case(db, request)
    logger.info(f"Case created: {case.case_number}")
    return {
        "status": "success",
        "case_id": case.case_number,
        "case_data": {
            "case_id": case.case_number,
            "title": case.title,
            "description": case.description,
            "priority": case.priority.value if hasattr(case.priority, "value") else case.priority,
            "status": case.status.value if hasattr(case.status, "value") else case.status,
            "assigned_to": str(case.assigned_to) if case.assigned_to else None
        }
    }

@app.get("/api/v1/cases/{case_id}")
async def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get case details"""
    case = crud.get_case(db, case_id)
    if not case:
        try:
            case_uuid = uuid.UUID(case_id)
            case = crud.get_case_by_id(db, case_uuid)
        except ValueError:
            pass
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {
        "status": "success",
        "case_data": {
            "case_id": case.case_number,
            "title": case.title,
            "description": case.description,
            "priority": case.priority.value if hasattr(case.priority, "value") else case.priority,
            "status": case.status.value if hasattr(case.status, "value") else case.status,
            "assigned_to": str(case.assigned_to) if case.assigned_to else None,
            "detections": len(case.detections)
        }
    }

@app.get("/api/v1/cases")
async def list_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all cases with optional filters"""
    cases = crud.get_cases(db, status=status, priority=priority)
    
    return {
        "status": "success",
        "total_cases": len(cases),
        "cases": [{
            "case_id": c.case_number,
            "title": c.title,
            "status": c.status.value if hasattr(c.status, "value") else c.status,
            "priority": c.priority.value if hasattr(c.priority, "value") else c.priority
        } for c in cases]
    }

# ============ VEHICLE TRACKING ============

@app.post("/api/v1/vehicles/track")
async def track_vehicle(plate_number: str):
    """Get vehicle tracking history"""
    trail = vehicle_tracker.get_vehicle_trail(plate_number)
    predicted_location = vehicle_tracker.predict_location(plate_number)
    
    return {
        "status": "success",
        "plate_number": plate_number,
        "sightings_count": len(trail),
        "trail": trail,
        "predicted_location": predicted_location
    }

# ============ REPORTING ============

@app.post("/api/v1/reports/case-summary")
async def generate_case_report(case_id: str, db: Session = Depends(get_db)):
    """Generate case summary report"""
    case = crud.get_case(db, case_id)
    if not case:
        try:
            case_uuid = uuid.UUID(case_id)
            case = crud.get_case_by_id(db, case_uuid)
        except ValueError:
            pass
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    detections = crud.get_detections_by_case(db, case.id)
    
    report = {
        "report_id": str(uuid.uuid4()),
        "case_id": case.case_number,
        "title": case.title,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_detections": len(detections),
            "persons_detected": sum(1 for d in detections if getattr(d.detection_type, "value", d.detection_type) == 'person'),
            "vehicles_detected": sum(1 for d in detections if getattr(d.detection_type, "value", d.detection_type) == 'vehicle'),
            "matches_found": sum(1 for d in detections if getattr(d.detection_type, "value", d.detection_type) == 'face')
        },
        "detections": [{"id": str(d.id), "type": getattr(d.detection_type, "value", d.detection_type), "confidence": d.confidence} for d in detections]
    }
    
    return {
        "status": "success",
        "report": report
    }

# ============ AUTHENTICATION ============

@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Authenticate user and issue JWT token
    """
    user = crud.get_user_by_username(db, username=username)
    if not user or not crud.PWD_CONTEXT.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
        }
    }


@app.get("/api/v1/auth/me")
async def read_current_user(current_user: models.User = Depends(get_current_active_user)):
    return {
        "status": "success",
        "user": {
            "username": current_user.username,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role
        }
    }

# ============ ERROR HANDLERS ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail}
    )

# ============ ROOT ENDPOINT ============

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LEIP - Law Enforcement Intelligence Platform",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )