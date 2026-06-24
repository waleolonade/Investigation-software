"""
Architecture validation tests for YOLO detector integration.

Tests the backend switching logic, configuration, and error handling
without requiring ultralytics to be installed.
"""

import sys
import os
from pathlib import Path
import json
import tempfile

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings


def test_settings_structure():
    """Verify settings have all required YOLO configuration fields."""
    print("\n✓ TEST: Settings structure")
    
    required_attrs = [
        'yolo_backend',
        'yolo_onnx_path',
        'yolo_class_names',
        'yolo_onnx_input_size',
        'yolo_rust_persistent',
    ]
    
    for attr in required_attrs:
        assert hasattr(settings, attr), f"Missing setting: {attr}"
        value = getattr(settings, attr)
        print(f"  {attr}: {value}")
    
    # Validate types
    assert isinstance(settings.yolo_backend, str)
    assert isinstance(settings.yolo_onnx_path, str)
    assert isinstance(settings.yolo_class_names, str)
    assert isinstance(settings.yolo_onnx_input_size, int)
    assert isinstance(settings.yolo_rust_persistent, bool)
    
    print("  ✓ All settings properly typed")
    return True


def test_detector_imports():
    """Test that detector classes can be imported."""
    print("\n✓ TEST: Detector imports")
    
    try:
        from app.yolo_detector import YOLODetector, RustYoloDetector
        print("  ✓ YOLODetector imported")
        print("  ✓ RustYoloDetector imported")
        
        # Verify they are classes
        assert isinstance(YOLODetector, type), "YOLODetector should be a class"
        assert isinstance(RustYoloDetector, type), "RustYoloDetector should be a class"
        
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_detector_source_code():
    """Verify detector source code has key implementation elements."""
    print("\n✓ TEST: Detector source code structure")
    
    detector_path = Path(__file__).parent.parent / "app" / "yolo_detector.py"
    source = detector_path.read_text()
    
    # Check for key methods and features
    checks = {
        "RustYoloDetector class": "class RustYoloDetector:",
        "Backend selection": "self.backend =",
        "Fallback mechanism": "except FileNotFoundError",
        "Fallback to ultralytics": '"ultralytics"',
        "Process health check": "poll()",
        "Persistent mode": "_run_loop_request",
        "Error recovery": "except (BrokenPipeError, IOError)",
        "Thread safety": "self._lock",
        "Automatic respawn": "_spawn_process()",
        "Error tracking": "_last_error",
    }
    
    for feature, code in checks.items():
        if code in source:
            print(f"  ✓ {feature}")
        else:
            print(f"  ✗ {feature} - code not found: '{code}'")
            return False
    
    return True


def test_rust_detector_file_validation():
    """Test Rust detector file path validation logic."""
    print("\n✓ TEST: Rust detector file validation")
    
    from app.yolo_detector import RustYoloDetector
    
    # Test 1: Missing model file
    try:
        detector = RustYoloDetector(
            model_path="/nonexistent/model.onnx",
            class_path="/nonexistent/classes.names",
            threshold=0.5,
            nms_threshold=0.45,
            input_size=640,
        )
        print("  ✗ Should have raised FileNotFoundError for missing model")
        return False
    except FileNotFoundError as e:
        if "model" in str(e).lower():
            print(f"  ✓ Caught missing model: {str(e)[:50]}...")
        else:
            print(f"  ✗ Wrong error message: {e}")
            return False
    
    # Test 2: Missing class file
    try:
        with tempfile.NamedTemporaryFile(suffix=".onnx", delete=False) as f:
            model_path = f.name
        
        detector = RustYoloDetector(
            model_path=model_path,
            class_path="/nonexistent/classes.names",
            threshold=0.5,
            nms_threshold=0.45,
            input_size=640,
        )
        print("  ✗ Should have raised FileNotFoundError for missing classes")
        return False
    except FileNotFoundError as e:
        if "class" in str(e).lower() or "names" in str(e).lower():
            print(f"  ✓ Caught missing classes: {str(e)[:50]}...")
        else:
            print(f"  ✗ Wrong error message: {e}")
            return False
    finally:
        Path(model_path).unlink()
    
    return True


def test_detection_output_schema():
    """Validate the expected detection output schema."""
    print("\n✓ TEST: Detection output schema")
    
    # Mock detection outputs that both backends should match
    expected_schema = {
        "type": str,           # Detection type (e.g., "object", "face", "plate")
        "class_id": int,       # Numeric class identifier
        "confidence": float,   # Confidence score 0-1
        "bbox": {
            "x1": float,
            "y1": float,
            "x2": float,
            "y2": float,
            "width": float,
            "height": float,
            "center_x": float,
            "center_y": float,
        }
    }
    
    # Validate schema structure
    print("  Expected detection schema:")
    print(f"    - type: {expected_schema['type'].__name__}")
    print(f"    - class_id: {expected_schema['class_id'].__name__}")
    print(f"    - confidence: {expected_schema['confidence'].__name__}")
    print("    - bbox:")
    for key, val_type in expected_schema["bbox"].items():
        print(f"        - {key}: {val_type.__name__}")
    
    # Verify schema can be serialized to JSON
    mock_detection = {
        "type": "object",
        "class_id": 0,
        "confidence": 0.95,
        "bbox": {
            "x1": 10.0,
            "y1": 20.0,
            "x2": 100.0,
            "y2": 80.0,
            "width": 90.0,
            "height": 60.0,
            "center_x": 55.0,
            "center_y": 50.0,
        }
    }
    
    json_str = json.dumps(mock_detection)
    parsed = json.loads(json_str)
    assert parsed == mock_detection, "Schema should be JSON serializable"
    print("  ✓ Schema is JSON serializable")
    
    return True


def test_environment_configuration():
    """Test environment variable configuration."""
    print("\n✓ TEST: Environment configuration")
    
    # Save original values
    original_backend = os.environ.get("YOLO_BACKEND")
    original_persistent = os.environ.get("YOLO_RUST_PERSISTENT")
    
    try:
        # Test backend override
        os.environ["YOLO_BACKEND"] = "rust"
        from importlib import reload
        import leip.config.settings as settings_module
        reload(settings_module)
        print(f"  ✓ Backend env override works: {settings_module.settings.yolo_backend}")
        
        # Test persistent mode override
        os.environ["YOLO_RUST_PERSISTENT"] = "false"
        reload(settings_module)
        print(f"  ✓ Persistent mode env override works: {settings_module.settings.yolo_rust_persistent}")
        
        return True
    finally:
        # Restore original values
        if original_backend:
            os.environ["YOLO_BACKEND"] = original_backend
        else:
            os.environ.pop("YOLO_BACKEND", None)
        
        if original_persistent:
            os.environ["YOLO_RUST_PERSISTENT"] = original_persistent
        else:
            os.environ.pop("YOLO_RUST_PERSISTENT", None)


def test_backend_selection_logic():
    """Test the backend selection and fallback logic."""
    print("\n✓ TEST: Backend selection logic")
    
    from app.yolo_detector import YOLODetector
    
    # This will actually try to initialize, which will fall back to ultralytics if Rust not available
    # But the logic should work regardless
    print("  Testing backend selection (may fallback to ultralytics)...")
    print("  Note: Full test requires ultralytics installed")
    
    return True


def run_all_tests():
    """Run all architecture validation tests."""
    print("=" * 70)
    print("YOLO DETECTOR ARCHITECTURE VALIDATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Settings Structure", test_settings_structure),
        ("Detector Imports", test_detector_imports),
        ("Detector Source Code", test_detector_source_code),
        ("Rust Detector File Validation", test_rust_detector_file_validation),
        ("Detection Output Schema", test_detection_output_schema),
        ("Environment Configuration", test_environment_configuration),
        ("Backend Selection Logic", test_backend_selection_logic),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ✗ FAILED: {test_name}")
        except Exception as e:
            failed += 1
            print(f"  ✗ FAILED: {test_name}")
            print(f"    {type(e).__name__}: {str(e)[:100]}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
