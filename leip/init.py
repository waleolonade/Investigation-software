"""
LEIP Application Initializer
Minimal example to test core modules
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_face_module():
    """Test face recognition module"""
    print("\n" + "="*60)
    print("Testing Face Recognition Module")
    print("="*60)
    
    try:
        from app.face_utils import LEIPFaceMatcher
        matcher = LEIPFaceMatcher()
        print("✓ Face Matcher initialized successfully")
        print(f"  - Gallery size: {len(matcher.gallery)}")
        print(f"  - Embedding dimension: {matcher.embedding_dim}")
        print(f"  - Index type: {matcher.index_type}")
        return True
    except Exception as e:
        print(f"✗ Face Module test failed: {e}")
        return False

def test_yolo_module():
    """Test YOLO detection module"""
    print("\n" + "="*60)
    print("Testing YOLO Detection Module")
    print("="*60)
    
    try:
        from app.yolo_detector import YOLODetector
        detector = YOLODetector(model_size="small")
        print("✓ YOLO Detector initialized successfully")
        print(f"  - Model size: small")
        print(f"  - Classes: Person, Vehicles, Objects")
        return True
    except Exception as e:
        print(f"✗ YOLO Module test failed: {e}")
        return False

def test_cctv_module():
    """Test CCTV processor module"""
    print("\n" + "="*60)
    print("Testing CCTV Processor Module")
    print("="*60)
    
    try:
        from app.cctv_processor import CCTVProcessor
        processor = CCTVProcessor(enable_face_matching=False)
        print("✓ CCTV Processor initialized successfully")
        print(f"  - Ready for video processing")
        return True
    except Exception as e:
        print(f"✗ CCTV Module test failed: {e}")
        return False

def test_plate_module():
    """Test license plate recognition module"""
    print("\n" + "="*60)
    print("Testing License Plate Recognition Module")
    print("="*60)
    
    try:
        from app.plate_recognition import LicensePlateRecognizer
        recognizer = LicensePlateRecognizer()
        print("✓ License Plate Recognizer initialized successfully")
        print(f"  - Supported regions: US, UK, EU, CA, AU")
        return True
    except Exception as e:
        print(f"✗ Plate Module test failed: {e}")
        return False

def test_api_module():
    """Test FastAPI backend"""
    print("\n" + "="*60)
    print("Testing FastAPI Backend")
    print("="*60)
    
    try:
        from app.api import app
        print("✓ FastAPI app initialized successfully")
        print(f"  - Endpoints available at /api/v1/")
        print(f"  - Docs at /docs")
        return True
    except Exception as e:
        print(f"✗ API Module test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║ LEIP - Law Enforcement Intelligence Platform          ║")
    print("║ Initialization & Module Testing                       ║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "Face Recognition": test_face_module(),
        "YOLO Detection": test_yolo_module(),
        "CCTV Processing": test_cctv_module(),
        "Plate Recognition": test_plate_module(),
        "FastAPI Backend": test_api_module()
    }
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    for module, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{module:.<40} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print("="*60)
    print(f"Total: {passed}/{total} modules passed\n")
    
    if passed == total:
        print("✓ All systems operational. Ready for deployment.\n")
        print("NEXT STEPS:")
        print("1. Configure .env file with your settings")
        print("2. Run: python -m uvicorn app.api:app --reload")
        print("3. Run (separate terminal): streamlit run frontend/app.py")
        print("4. Access API at http://localhost:8000")
        print("5. Access Dashboard at http://localhost:8501\n")
    else:
        print(f"⚠ {total - passed} module(s) failed. Check error messages above.\n")

if __name__ == "__main__":
    main()
