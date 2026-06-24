"""
LEIP Configuration Module
Centralized settings management with environment-based overrides
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file if env_file.exists() else None)

class Settings(BaseSettings):
    """Application configuration with validation"""
    
    # ============ DATABASE ============
    database_url: str = Field(
        default="sqlite:///./leip.db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_echo_sql: bool = Field(default=False, env="DATABASE_ECHO_SQL")
    
    # ============ FACE RECOGNITION ============
    face_model_name: str = Field(default="ArcFace", env="FACE_MODEL_NAME")
    face_similarity_threshold: float = Field(default=0.6, env="FACE_SIMILARITY_THRESHOLD")
    face_embedding_dim: int = Field(default=512, env="FACE_EMBEDDING_DIM")
    face_detector_backend: str = Field(default="retinaface", env="FACE_DETECTOR_BACKEND")
    max_faces_per_image: int = Field(default=10, env="MAX_FACES_PER_IMAGE")
    
    # ============ YOLO DETECTION ============
    yolo_model_size: str = Field(default="medium", env="YOLO_MODEL_SIZE")
    yolo_confidence_threshold: float = Field(default=0.5, env="YOLO_CONFIDENCE_THRESHOLD")
    yolo_iou_threshold: float = Field(default=0.45, env="YOLO_IOU_THRESHOLD")
    yolo_device: str = Field(default="cpu", env="YOLO_DEVICE")
    yolo_backend: str = Field(default="ultralytics", env="YOLO_BACKEND")
    yolo_onnx_path: str = Field(default="yolov8m.onnx", env="YOLO_ONNX_PATH")
    yolo_class_names: str = Field(default="coco.names", env="YOLO_CLASS_NAMES")
    yolo_onnx_input_size: int = Field(default=640, env="YOLO_ONNX_INPUT_SIZE")
    yolo_rust_persistent: bool = Field(default=True, env="YOLO_RUST_PERSISTENT")
    
    # ============ LICENSE PLATE RECOGNITION ============
    lpr_engine: str = Field(default="easyocr", env="LPR_ENGINE")
    lpr_confidence_threshold: float = Field(default=0.4, env="LPR_CONFIDENCE_THRESHOLD")
    lpr_batch_size: int = Field(default=32, env="LPR_BATCH_SIZE")
    
    # ============ FAISS VECTOR SEARCH ============
    faiss_index_type: str = Field(default="HNSW", env="FAISS_INDEX_TYPE")
    faiss_hnsw_m: int = Field(default=32, env="FAISS_HNSW_M")
    faiss_hnsw_ef_construction: int = Field(default=200, env="FAISS_HNSW_EF_CONSTRUCTION")
    faiss_hnsw_ef_search: int = Field(default=100, env="FAISS_HNSW_EF_SEARCH")
    faiss_gpu_enabled: bool = Field(default=False, env="FAISS_GPU_ENABLED")
    
    # ============ API SERVER ============
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    api_workers: int = Field(default=4, env="API_WORKERS")
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # ============ LOGGING ============
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/leip.log", env="LOG_FILE")
    log_max_bytes: int = Field(default=10485760, env="LOG_MAX_BYTES")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # ============ STORAGE ============
    upload_dir: str = Field(default="data/uploads", env="UPLOAD_DIR")
    temp_dir: str = Field(default="data/temp", env="TEMP_DIR")
    model_cache_dir: str = Field(default="models/cache", env="MODEL_CACHE_DIR")
    max_file_size_mb: int = Field(default=500, env="MAX_FILE_SIZE_MB")
    
    # ============ CCTV PROCESSING ============
    cctv_frame_skip: int = Field(default=5, env="CCTV_FRAME_SKIP")
    cctv_batch_size: int = Field(default=16, env="CCTV_BATCH_SIZE")
    cctv_buffer_size: int = Field(default=100, env="CCTV_BUFFER_SIZE")
    cctv_timeout_seconds: int = Field(default=30, env="CCTV_TIMEOUT_SECONDS")
    
    # ============ SECURITY & AUTH ============
    enable_rbac: bool = Field(default=True, env="ENABLE_RBAC")
    enable_api_key_auth: bool = Field(default=True, env="ENABLE_API_KEY_AUTH")
    allow_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        env="ALLOW_CORS_ORIGINS"
    )
    session_timeout_minutes: int = Field(default=30, env="SESSION_TIMEOUT_MINUTES")
    
    # ============ MONITORING ============
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # ============ DEVELOPMENT ============
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    testing_mode: bool = Field(default=False, env="TESTING_MODE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def validate_paths(self):
        """Ensure required directories exist"""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        Path(self.model_cache_dir).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.validate_paths()
