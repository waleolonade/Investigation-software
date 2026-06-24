"""
Integration tests for YOLO detector with fallback mechanisms.

Tests:
1. Backend selection logic
2. Graceful fallback from Rust to ultralytics
3. Detection output format consistency
4. Error handling and recovery
"""

import sys
import os
from pathlib import Path
import logging
import tempfile
import numpy as np
import cv2

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from app.yolo_detector import YOLODetector, RustYoloDetector

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_test_image(width=640, height=480):
    """Create a simple test image with a red square."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    # Draw a red rectangle (simulating an object)
    cv2.rectangle(image, (100, 100), (200, 200), (0, 0, 255), -1)
    # Add some noise to make it more realistic
    noise = np.random.randint(0, 50, image.shape, dtype=np.uint8)
    image = cv2.add(image, noise)
    return image


def test_settings_loading():
    """Test that settings load correctly with defaults."""
    print("\n✓ TEST: Settings loading")
    assert hasattr(settings, 'yolo_backend')
    assert hasattr(settings, 'yolo_onnx_path')
    assert hasattr(settings, 'yolo_class_names')
    assert hasattr(settings, 'yolo_onnx_input_size')
    assert hasattr(settings, 'yolo_rust_persistent')
    print(f"  Backend: {settings.yolo_backend}")
    print(f"  ONNX path: {settings.yolo_onnx_path}")
    print(f"  Input size: {settings.yolo_onnx_input_size}")
    print(f"  Rust persistent: {settings.yolo_rust_persistent}")


def test_rust_detector_missing_binary():
    """Test that RustYoloDetector gracefully fails when binary is missing."""
    print("\n✓ TEST: Rust detector missing binary")
    try:
        detector = RustYoloDetector(
            model_path="yolov8m.onnx",
            class_path="coco.names",
            threshold=0.5,
            nms_threshold=0.45,
            input_size=640,
            persistent=False,
            binary_path="/nonexistent/yolo_detector"
        )
        print("  ✗ FAIL: Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"  ✓ Correctly raised FileNotFoundError: {str(e)[:60]}...")
        return True


def test_yolo_detector_backend_selection():
    """Test that YOLODetector selects correct backend."""
    print("\n✓ TEST: Backend selection with fallback")
    
    # Test 1: Request Rust backend (should fall back to ultralytics)
    print("  Testing Rust backend (with fallback)...")
    os.environ["YOLO_BACKEND"] = "rust"
    detector = YOLODetector()
    print(f"    Requested: rust")
    print(f"    Actual backend: {detector.backend}")
    print(f"    Use Rust: {detector.use_rust}")
    assert detector.backend in ["rust", "ultralytics"], f"Invalid backend: {detector.backend}"
    
    # Test 2: Request ultralytics backend
    print("  Testing ultralytics backend...")
    os.environ["YOLO_BACKEND"] = "ultralytics"
    detector2 = YOLODetector()
    print(f"    Requested: ultralytics")
    print(f"    Actual backend: {detector2.backend}")
    print(f"    Use Rust: {detector2.use_rust}")
    assert detector2.backend == "ultralytics"
    assert detector2.use_rust is False
    
    return True


def test_detection_output_format():
    """Test that detection output has consistent format."""
    print("\n✓ TEST: Detection output format")
    
    os.environ["YOLO_BACKEND"] = "ultralytics"
    detector = YOLODetector()
    
    # Create test image
    test_image = create_test_image()
    
    # Run detection
    annotated_frame, detections = detector.detect_frame(test_image)
    
    print(f"  Detections found: {len(detections)}")
    print(f"  Output image shape: {annotated_frame.shape}")
    
    # Validate output format
    assert isinstance(annotated_frame, np.ndarray), "Annotated frame should be numpy array"
    assert len(annotated_frame.shape) == 3, "Frame should be 3D (H, W, C)"
    assert annotated_frame.shape[2] in [3, 4], "Frame should be RGB or RGBA"
    
    # Validate detections format
    assert isinstance(detections, list), "Detections should be a list"
    
    for det in detections:
        assert isinstance(det, dict), "Each detection should be a dict"
        required_keys = {"type", "class_id", "confidence", "bbox"}
        assert required_keys.issubset(det.keys()), f"Missing keys in detection: {det.keys()}"
        
        # Validate bbox format
        bbox = det["bbox"]
        required_bbox_keys = {"x1", "y1", "x2", "y2", "width", "height", "center_x", "center_y"}
        assert required_bbox_keys.issubset(bbox.keys()), f"Invalid bbox keys: {bbox.keys()}"
        
        print(f"    Detection: class_id={det['class_id']}, confidence={det['confidence']:.2f}, "
              f"bbox_size={bbox['width']:.0f}x{bbox['height']:.0f}")
    
    return True


def test_detection_consistency():
    """Test that multiple detections on same image are consistent."""
    print("\n✓ TEST: Detection consistency")
    
    os.environ["YOLO_BACKEND"] = "ultralytics"
    detector = YOLODetector()
    
    test_image = create_test_image()
    
    # Run detection twice
    _, det1 = detector.detect_frame(test_image)
    _, det2 = detector.detect_frame(test_image)
    
    print(f"  Run 1: {len(det1)} detections")
    print(f"  Run 2: {len(det2)} detections")
    
    # Should have same number of detections
    assert len(det1) == len(det2), "Detection count should be consistent"
    
    # Sort by class_id and confidence for comparison
    det1_sorted = sorted(det1, key=lambda x: (x['class_id'], x['confidence']))
    det2_sorted = sorted(det2, key=lambda x: (x['class_id'], x['confidence']))
    
    # Validate consistency (allowing small float tolerance)
    for d1, d2 in zip(det1_sorted, det2_sorted):
        assert d1['class_id'] == d2['class_id'], "Class IDs should match"
        assert abs(d1['confidence'] - d2['confidence']) < 0.01, "Confidence should match"
    
    return True


def test_error_recovery():
    """Test error handling and recovery."""
    print("\n✓ TEST: Error recovery")
    
    os.environ["YOLO_BACKEND"] = "ultralytics"
    detector = YOLODetector()
    
    try:
        # Try detecting invalid input
        invalid_frame = np.zeros((10, 10), dtype=np.uint8)  # Wrong shape
        detector.detect_frame(invalid_frame)
        print("  Note: Invalid frame was processed (may be auto-fixed by detector)")
    except Exception as e:
        print(f"  ✓ Caught error gracefully: {type(e).__name__}")
    
    # Detector should still work after error
    valid_frame = create_test_image()
    _, detections = detector.detect_frame(valid_frame)
    print(f"  ✓ Detector recovered, processed frame normally")
    print(f"    Detections: {len(detections)}")
    
    return True


def test_end_to_end_workflow():
    """Test complete workflow: detect objects, annotate, validate output."""
    print("\n✓ TEST: End-to-end workflow")
    
    os.environ["YOLO_BACKEND"] = "ultralytics"
    detector = YOLODetector()
    
    # Create synthetic video frames
    frames = [create_test_image() for _ in range(3)]
    all_detections = []
    
    for i, frame in enumerate(frames):
        annotated, detections = detector.detect_frame(frame)
        all_detections.append(detections)
        print(f"  Frame {i+1}: {len(detections)} objects detected")
        
        # Validate output
        assert annotated.shape == frame.shape[:2] + (3,), "Output shape mismatch"
        assert isinstance(detections, list), "Detections should be list"
    
    print(f"  ✓ Processed {len(frames)} frames successfully")
    print(f"  ✓ Total detections across frames: {sum(len(d) for d in all_detections)}")
    
    return True


def run_all_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("YOLO DETECTOR INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        ("Settings Loading", test_settings_loading),
        ("Rust Binary Missing", test_rust_detector_missing_binary),
        ("Backend Selection", test_yolo_detector_backend_selection),
        ("Detection Format", test_detection_output_format),
        ("Detection Consistency", test_detection_consistency),
        ("Error Recovery", test_error_recovery),
        ("End-to-End Workflow", test_end_to_end_workflow),
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
            print(f"    Error: {type(e).__name__}: {str(e)[:100]}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
