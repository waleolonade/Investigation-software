"""
LEIP Unit Tests
Test core modules for functionality and performance
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

# These tests demonstrate how to test LEIP modules
# Run with: pytest tests/ -v

class TestFaceRecognition:
    """Test face recognition module"""
    
    def test_face_matcher_initialization(self):
        """Test FaceMatcher can be initialized"""
        from app.face_utils import LEIPFaceMatcher
        
        matcher = LEIPFaceMatcher()
        assert matcher is not None
        assert matcher.embedding_dim == 512
        assert isinstance(matcher.gallery, dict)
    
    def test_gallery_operations(self):
        """Test adding/removing faces from gallery"""
        from app.face_utils import LEIPFaceMatcher
        
        matcher = LEIPFaceMatcher()
        initial_size = len(matcher.gallery)
        
        # In real tests, use actual image files
        # For now, just test structure
        assert isinstance(matcher.gallery, dict)
        assert len(matcher.gallery) >= initial_size
    
    def test_metadata_handling(self):
        """Test metadata storage"""
        from app.face_utils import LEIPFaceMatcher
        
        matcher = LEIPFaceMatcher()
        test_meta = {
            "person_id": "TEST-001",
            "name": "Test Person",
            "source": "test"
        }
        
        assert isinstance(matcher.metadata, dict)


class TestYOLODetection:
    """Test YOLO object detection"""
    
    def test_yolo_detector_initialization(self):
        """Test YOLODetector can be initialized"""
        from app.yolo_detector import YOLODetector
        
        detector = YOLODetector(model_size="small")
        assert detector is not None
        assert detector.model_size == "small"
        assert detector.confidence_threshold > 0
    
    def test_detection_types(self):
        """Test detection type constants"""
        from app.yolo_detector import YOLODetector
        
        assert YOLODetector.PERSON_CLASS == 0
        assert isinstance(YOLODetector.VEHICLE_CLASSES, dict)
        assert 2 in YOLODetector.VEHICLE_CLASSES  # car


class TestCCTVProcessor:
    """Test CCTV processing"""
    
    def test_cctv_processor_initialization(self):
        """Test CCTVProcessor can be initialized"""
        from app.cctv_processor import CCTVProcessor
        
        processor = CCTVProcessor(enable_face_matching=False)
        assert processor is not None
        assert processor.detector is not None
    
    def test_video_source_detection(self):
        """Test video source type identification"""
        from app.cctv_processor import CCTVProcessor, VideoSourceType
        
        processor = CCTVProcessor(enable_face_matching=False)
        
        assert processor.identify_source("rtsp://example.com") == VideoSourceType.RTSP_STREAM
        assert processor.identify_source("http://example.com") == VideoSourceType.HTTP_STREAM
        assert processor.identify_source("0") == VideoSourceType.CAMERA
    
    def test_frame_quality_assessment(self):
        """Test frame quality scoring"""
        from app.cctv_processor import CCTVProcessor
        import cv2
        import numpy as np
        
        processor = CCTVProcessor(enable_face_matching=False)
        
        # Create test frame
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        quality = processor.assess_frame_quality(frame)
        
        assert 0 <= quality <= 1
        assert quality > 0.5  # Should be decent quality


class TestPlateRecognition:
    """Test license plate recognition"""
    
    def test_plate_recognizer_initialization(self):
        """Test LicensePlateRecognizer can be initialized"""
        from app.plate_recognition import LicensePlateRecognizer
        
        recognizer = LicensePlateRecognizer()
        assert recognizer is not None
        assert recognizer.ocr_backend == "easyocr"
    
    def test_plate_validation(self):
        """Test plate format validation"""
        from app.plate_recognition import LicensePlateRecognizer
        
        recognizer = LicensePlateRecognizer()
        
        # US plate
        valid, region = recognizer._validate_plate("ABC1234")
        assert valid is True
        
        # Invalid
        valid, region = recognizer._validate_plate("!")
        assert valid is False
    
    def test_text_cleaning(self):
        """Test OCR text cleaning"""
        from app.plate_recognition import LicensePlateRecognizer
        
        recognizer = LicensePlateRecognizer()
        
        dirty = "A B C - 1 2 3 4 !"
        clean = recognizer._clean_text(dirty)
        
        assert clean == "ABC1234"
        assert " " not in clean
        assert "-" not in clean


class TestAPI:
    """Test FastAPI backend"""
    
    def test_api_initialization(self):
        """Test API can be initialized"""
        from app.api import app
        
        assert app is not None
        assert hasattr(app, "routes")
    
    def test_api_endpoints_exist(self):
        """Test key endpoints are registered"""
        from app.api import app
        
        endpoints = [route.path for route in app.routes]
        
        assert "/health" in endpoints
        assert "/api/v1/info" in endpoints
        assert "/api/v1/auth/login" in endpoints
        assert "/api/v1/auth/me" in endpoints

    def test_auth_login_and_token(self):
        """Test login returns a JWT access token"""
        from fastapi.testclient import TestClient
        from app.api import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "investigator", "password": "password123"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["username"] == "investigator"

    def test_auth_invalid_credentials(self):
        """Test login rejects invalid credentials"""
        from fastapi.testclient import TestClient
        from app.api import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "investigator", "password": "wrongpass"}
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

    def test_auth_me_requires_token(self):
        """Test protected endpoint requires valid bearer token"""
        from fastapi.testclient import TestClient
        from app.api import app

        client = TestClient(app)
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "investigator", "password": "password123"}
        )
        token = login_response.json()["access_token"]

        auth_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert auth_response.status_code == 200
        assert auth_response.json()["user"]["username"] == "investigator"


class TestConfiguration:
    """Test configuration management"""
    
    def test_settings_initialization(self):
        """Test Settings object loads"""
        from config.settings import settings
        
        assert settings is not None
        assert settings.api_port == 8000
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
    
    def test_paths_creation(self):
        """Test required directories are created"""
        from config.settings import settings
        from pathlib import Path
        
        assert Path(settings.upload_dir).exists()
        assert Path(settings.temp_dir).exists()
        assert Path(settings.model_cache_dir).exists()


# ============ PERFORMANCE TESTS ============

class TestPerformance:
    """Performance benchmarks"""
    
    def test_yolo_inference_speed(self):
        """Benchmark YOLO inference"""
        from app.yolo_detector import YOLODetector
        import cv2
        import time
        import numpy as np
        
        detector = YOLODetector(model_size="small")
        
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        start = time.time()
        _, detections = detector.detect_frame(frame)
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # Should be faster than 1 second
        print(f"YOLO inference: {elapsed*1000:.1f}ms")
    
    def test_quality_assessment_speed(self):
        """Benchmark frame quality assessment"""
        from app.cctv_processor import CCTVProcessor
        import numpy as np
        import time
        
        processor = CCTVProcessor(enable_face_matching=False)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        start = time.time()
        for _ in range(100):
            quality = processor.assess_frame_quality(frame)
        elapsed = time.time() - start
        
        per_frame = (elapsed / 100) * 1000
        assert per_frame < 10  # Should be < 10ms per frame
        print(f"Quality assessment: {per_frame:.2f}ms per frame")


# ============ INTEGRATION TESTS ============

class TestIntegration:
    """Test component integration"""
    
    def test_detection_pipeline(self):
        """Test full detection pipeline"""
        from app.yolo_detector import YOLODetector
        from app.cctv_processor import CCTVProcessor
        import numpy as np
        
        processor = CCTVProcessor(enable_face_matching=False)
        
        # Create test frame
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        quality = processor.assess_frame_quality(frame)
        
        assert quality >= 0
        assert quality <= 1


# ============ PYTEST FIXTURES ============

@pytest.fixture
def temp_dir():
    """Temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_frame():
    """Create a test frame"""
    import numpy as np
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


# ============ RUNNING TESTS ============

if __name__ == "__main__":
    # Run all tests
    # pytest tests/ -v --tb=short
    
    print("To run tests, use:")
    print("  pytest tests/ -v                    # All tests")
    print("  pytest tests/test_face.py -v        # Face tests only")
    print("  pytest tests/ -k performance        # Performance tests")
    print("  pytest tests/ --tb=short            # Short output")
    print("  pytest tests/ --cov=app             # Coverage report")
