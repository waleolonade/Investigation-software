"""
LEIP YOLO Object Detection Module
Real-time pedestrian, vehicle, and object detection for CCTV analysis
"""

import cv2
import numpy as np
import logging
import importlib
from pathlib import Path
from typing import Callable, List, Dict, Tuple, Optional
from datetime import datetime
import json
import os
import subprocess
import tempfile
import threading

# YOLO is loaded lazily in YOLODetector.__init__
from config.settings import settings

# ============ LOGGING ============
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RustYoloDetector:
    """
    A subprocess wrapper for the Rust ONNX YOLO detector with process management.
    
    Supports two modes:
    - Single-shot: spawn process, run detection, exit
    - Persistent: keep process running, send frames via JSON requests
    
    Features:
    - Automatic process respawn on crash
    - Thread-safe request handling
    - Graceful fallback if binary is missing
    """

    def __init__(
        self,
        model_path: str,
        class_path: str,
        threshold: float,
        nms_threshold: float,
        input_size: int,
        persistent: bool = False,
        binary_path: Optional[str] = None
    ):
        self.model_path = Path(model_path)
        self.class_path = Path(class_path)
        self.threshold = threshold
        self.nms_threshold = nms_threshold
        self.input_size = input_size
        self.persistent = persistent
        self.binary_path = Path(binary_path) if binary_path else self._default_binary_path()
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._last_error: Optional[str] = None

        if not self.model_path.exists():
            raise FileNotFoundError(f"Rust YOLO model not found: {self.model_path}")
        if not self.class_path.exists():
            raise FileNotFoundError(f"Rust YOLO class names file not found: {self.class_path}")
        if not self.binary_path.exists():
            raise FileNotFoundError(
                f"Rust YOLO binary not found: {self.binary_path}. "
                "Build it with: cargo build --release in yolo_detector-main"
            )

        if self.persistent:
            self._spawn_process()

    def _default_binary_path(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        release_path = root / "yolo_detector-main" / "target" / "release"
        debug_path = root / "yolo_detector-main" / "target" / "debug"
        binary_name = "yolo_detector.exe" if os.name == "nt" else "yolo_detector"

        candidate = release_path / binary_name
        if candidate.exists():
            return candidate

        candidate = debug_path / binary_name
        return candidate

    def _build_process_cmd(self) -> List[str]:
        return [
            str(self.binary_path),
            "--model",
            str(self.model_path),
            "--names",
            str(self.class_path),
            "--loop",
            "--input-size",
            str(self.input_size),
        ]

    def _spawn_process(self) -> None:
        self._terminate_process()
        cmd = self._build_process_cmd()
        logger.debug(f"Spawning persistent Rust YOLO process: {' '.join(cmd)}")
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if self._process.stdin is None or self._process.stdout is None:
            raise RuntimeError("Failed to spawn Rust YOLO persistent process")

    def _terminate_process(self) -> None:
        if self._process is not None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            finally:
                self._process = None

    def close(self) -> None:
        self._terminate_process()

    def __del__(self):
        self.close()

    def is_alive(self) -> bool:
        """Check if persistent process is running"""
        if not self.persistent or self._process is None:
            return False
        return self._process.poll() is None

    def restart(self) -> None:
        """Manually restart the persistent process"""
        logger.info("Manually restarting Rust YOLO persistent process")
        self._terminate_process()
        if self.persistent:
            self._spawn_process()

    def _run_single(self, image_path: Path) -> List[Dict]:
        cmd = [
            str(self.binary_path),
            "--model",
            str(self.model_path),
            "--names",
            str(self.class_path),
            "--image",
            str(image_path),
            "--threshold",
            str(self.threshold),
            "--nms",
            str(self.nms_threshold),
            "--input-size",
            str(self.input_size),
        ]
        logger.debug(f"Running Rust YOLO detector: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Rust YOLO detector failed ({result.returncode}): {result.stderr or result.stdout}"
            )

        detections = json.loads(result.stdout)
        if not isinstance(detections, list):
            raise ValueError("Rust YOLO detector returned unexpected output")

        return detections

    def _run_loop_request(self, image_path: Path) -> List[Dict]:
        if self._process is None or self._process.poll() is not None:
            logger.debug("Rust YOLO process died or not started, respawning...")
            self._spawn_process()

        request = {
            "image": str(image_path),
            "threshold": self.threshold,
            "nms": self.nms_threshold,
        }
        payload = json.dumps(request) + "\n"

        assert self._process is not None and self._process.stdin is not None and self._process.stdout is not None
        with self._lock:
            try:
                self._process.stdin.write(payload)
                self._process.stdin.flush()
                output_line = self._process.stdout.readline()
            except (BrokenPipeError, IOError) as e:
                logger.warning(f"Rust YOLO process pipe error: {e}. Respawning...")
                self._spawn_process()
                return self._run_loop_request(image_path)

        if not output_line:
            stderr = self._process.stderr.read() if self._process and self._process.stderr else ""
            raise RuntimeError(
                f"Rust YOLO persistent process returned no output. stderr={stderr}"
            )

        detections = json.loads(output_line)
        if not isinstance(detections, list):
            raise ValueError("Rust YOLO detector returned unexpected output")

        return detections

    def detect(self, frame: np.ndarray) -> List[Dict]:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            image_path = Path(tmp.name)

        if not cv2.imwrite(str(image_path), frame):
            image_path.unlink(missing_ok=True)
            raise RuntimeError(f"Failed to write temporary frame to {image_path}")

        try:
            if self.persistent:
                return self._run_loop_request(image_path)
            return self._run_single(image_path)
        finally:
            image_path.unlink(missing_ok=True)


class YOLODetector:
    """
    YOLO-based object detection for law enforcement
    Detects:
    - Persons (pedestrians)
    - Vehicles (cars, buses, motorcycles)
    - Backpacks, bags (for threat detection)
    - Bicycles, motorcycles
    
    Uses YOLOv8 for real-time inference
    """
    
    # COCO class mappings relevant to law enforcement
    PERSON_CLASS = 0
    VEHICLE_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
    OBJECT_CLASSES = {24: 'backpack', 26: 'handbag', 28: 'suitcase'}
    
    def __init__(
        self,
        model_size: str = "medium",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45
    ):
        """
        Initialize YOLO detector
        
        Args:
            model_size: nano, small, medium, large, xlarge
            confidence_threshold: Detection confidence (0-1)
            iou_threshold: IoU threshold for NMS
        """
        self.model_size = model_size
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.backend = settings.yolo_backend.lower()
        self.use_rust = False

        if self.backend == "rust":
            logger.info("Loading YOLO ONNX detector via Rust backend...")
            try:
                rust_model = settings.yolo_onnx_path
                class_names = settings.yolo_class_names
                input_size = settings.yolo_onnx_input_size
                self.rust_detector = RustYoloDetector(
                    model_path=rust_model,
                    class_path=class_names,
                    threshold=self.confidence_threshold,
                    nms_threshold=self.iou_threshold,
                    input_size=input_size,
                    persistent=settings.yolo_rust_persistent,
                )
                self.use_rust = True
                logger.info(f"Rust ONNX YOLO detector initialized: {rust_model}")
            except FileNotFoundError as e:
                logger.warning(f"Rust YOLO binary not found, falling back to ultralytics: {e}")
                self.backend = "ultralytics"
            except Exception as e:
                logger.warning(f"Failed to initialize Rust backend: {e}. Falling back to ultralytics.")
                self.backend = "ultralytics"

        if not self.use_rust:
            logger.info(f"Loading YOLOv8-{model_size} model...")
            try:
                ultralytics_mod = importlib.import_module('ultralytics')
                YOLO = ultralytics_mod.YOLO
            except ImportError as e:
                raise ImportError("Please install: pip install ultralytics") from e

            model_path = f"yolov8{model_size}.pt"
            self.model = YOLO(model_path)
            
            # Set device
            device = 0 if settings.yolo_device == "cuda" else "cpu"
            self.model.to(device)
            
            logger.info(f"YOLOv8 detector initialized with {model_size} model")
    
    def _map_detection_type(self, cls_id: int) -> str:
        detection_type = "object"
        if cls_id == self.PERSON_CLASS:
            detection_type = "person"
        elif cls_id in self.VEHICLE_CLASSES:
            detection_type = f"vehicle_{self.VEHICLE_CLASSES[cls_id]}"
        elif cls_id in self.OBJECT_CLASSES:
            detection_type = f"object_{self.OBJECT_CLASSES[cls_id]}"
        return detection_type

    def _build_detection(
        self,
        cls_id: int,
        confidence: float,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> Dict:
        detection_type = self._map_detection_type(cls_id)
        return {
            'type': detection_type,
            'class_id': cls_id,
            'confidence': confidence,
            'bbox': {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'width': x2 - x1,
                'height': y2 - y1,
                'center_x': (x1 + x2) // 2,
                'center_y': (y1 + y2) // 2
            }
        }

    def _detect_frame_rust(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        try:
            detections = self.rust_detector.detect(frame)
        except Exception as e:
            logger.error(f"Rust detector failed ({type(e).__name__}): {e}. Falling back to ultralytics.")
            self.use_rust = False
            try:
                ultralytics_mod = importlib.import_module('ultralytics')
                YOLO = ultralytics_mod.YOLO
                model_path = f"yolov8{self.model_size}.pt"
                self.model = YOLO(model_path)
                device = 0 if settings.yolo_device == "cuda" else "cpu"
                self.model.to(device)
            except Exception as init_err:
                logger.error(f"Failed to initialize ultralytics fallback: {init_err}")
                raise
            
            return self._detect_frame_ultralytics(frame)

        annotated_frame = frame.copy()
        converted = []

        for det in detections:
            bbox = det.get('bbox', {})
            x1 = int(bbox.get('x1', 0))
            y1 = int(bbox.get('y1', 0))
            x2 = int(bbox.get('x2', 0))
            y2 = int(bbox.get('y2', 0))
            cls_id = int(det.get('class_id', -1))
            confidence = float(det.get('confidence', 0.0))

            detection = self._build_detection(cls_id, confidence, x1, y1, x2, y2)
            converted.append(detection)

            color = (0, 255, 0) if detection['type'] == 'person' else (255, 0, 0)
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated_frame,
                f"{detection['type']} {confidence:.2f}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        return annotated_frame, converted

    def _detect_frame_ultralytics(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        results = self.model(frame, conf=self.confidence_threshold, iou=self.iou_threshold)
        
        detections = []
        annotated_frame = frame.copy()
        
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    conf = float(box.conf[0].cpu().numpy())
                    cls_id = int(box.cls[0].cpu().numpy())
                    
                    detection = self._build_detection(cls_id, conf, x1, y1, x2, y2)
                    detections.append(detection)
                    
                    color = (0, 255, 0) if detection['type'] == "person" else (255, 0, 0)
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        annotated_frame,
                        f"{detection['type']} {conf:.2f}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2
                    )
        
        return annotated_frame, detections

    def detect_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """
        Detect objects in a single frame
        
        Args:
            frame: Input frame (BGR)
            
        Returns:
            Tuple of (annotated frame, detections list)
        """
        if getattr(self, 'use_rust', False):
            return self._detect_frame_rust(frame)

        return self._detect_frame_ultralytics(frame)
    
    def detect_video_file(
        self,
        video_path: str,
        frame_skip: int = 5,
        max_frames: Optional[int] = None
    ) -> Dict:
        """
        Process video file and extract detections
        
        Args:
            video_path: Path to video file
            frame_skip: Process every Nth frame (5 = every 5th frame)
            max_frames: Maximum frames to process (None = all)
            
        Returns:
            {
                'video_path': str,
                'total_frames': int,
                'processed_frames': int,
                'duration_seconds': float,
                'fps': float,
                'frame_detections': [
                    {
                        'frame_id': int,
                        'timestamp': float,
                        'detections': [...]
                    }
                ],
                'summary': {
                    'total_persons': int,
                    'total_vehicles': int,
                    'total_objects': int
                }
            }
        """
        logger.info(f"Processing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {video_path}")
        
        # Video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        frame_detections = []
        summary = {'total_persons': 0, 'total_vehicles': 0, 'total_objects': 0}
        
        frame_id = 0
        processed_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every Nth frame
            if frame_id % frame_skip != 0:
                frame_id += 1
                continue
            
            if max_frames and processed_frames >= max_frames:
                break
            
            # Detect objects
            _, detections = self.detect_frame(frame)
            timestamp = frame_id / fps if fps > 0 else frame_id
            
            # Filter and summarize
            frame_det = {
                'frame_id': frame_id,
                'timestamp': timestamp,
                'detections': detections
            }
            frame_detections.append(frame_det)
            
            # Update summary
            for det in detections:
                if det['type'] == 'person':
                    summary['total_persons'] += 1
                elif 'vehicle' in det['type']:
                    summary['total_vehicles'] += 1
                else:
                    summary['total_objects'] += 1
            
            processed_frames += 1
            
            if processed_frames % 30 == 0:
                logger.debug(f"Processed {processed_frames} frames ({frame_id}/{total_frames})")
            
            frame_id += 1
        
        cap.release()
        
        result = {
            'video_path': str(video_path),
            'total_frames': total_frames,
            'processed_frames': processed_frames,
            'duration_seconds': duration,
            'fps': fps,
            'frame_detections': frame_detections,
            'summary': summary
        }
        
        logger.info(f"Video processing complete. Summary: {summary}")
        return result
    
    def detect_stream(
        self,
        stream_source: str,  # RTSP URL or camera index
        max_frames: int = 100,
        callback: Optional[Callable] = None
    ) -> List[Dict]:
        """
        Process real-time stream (CCTV, camera, etc.)
        
        Args:
            stream_source: RTSP URL or camera index (e.g., "rtsp://..." or 0)
            max_frames: Maximum frames to capture
            callback: Optional callback(frame_id, detections) for processing
            
        Returns:
            List of frame detections
        """
        logger.info(f"Connecting to stream: {stream_source}")
        
        cap = cv2.VideoCapture(stream_source)
        if not cap.isOpened():
            raise ConnectionError(f"Cannot connect to stream: {stream_source}")
        
        detections_list = []
        frame_id = 0
        
        while frame_id < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect
            _, detections = self.detect_frame(frame)
            frame_data = {
                'frame_id': frame_id,
                'timestamp': datetime.now().isoformat(),
                'detections': detections
            }
            detections_list.append(frame_data)
            
            # Callback
            if callback:
                callback(frame_id, detections)
            
            frame_id += 1
        
        cap.release()
        logger.info(f"Stream processing complete. Captured {frame_id} frames")
        return detections_list


# ============ UTILITY FUNCTIONS ============

def extract_person_crops(
    video_path: str,
    output_dir: str = "data/person_crops"
) -> List[str]:
    """
    Extract cropped images of detected persons for face matching
    
    Returns:
        List of saved crop file paths
    """
    detector = YOLODetector()
    result = detector.detect_video_file(video_path)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    crop_paths = []
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    for frame_det in result['frame_detections']:
        frame_id = frame_det['frame_id']
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        
        if not ret:
            continue
        
        for i, det in enumerate(frame_det['detections']):
            if det['type'] == 'person':
                x1, y1, x2, y2 = (
                    det['bbox']['x1'],
                    det['bbox']['y1'],
                    det['bbox']['x2'],
                    det['bbox']['y2']
                )
                crop = frame[y1:y2, x1:x2]
                
                crop_path = Path(output_dir) / f"person_f{frame_id}_d{i}.jpg"
                cv2.imwrite(str(crop_path), crop)
                crop_paths.append(str(crop_path))
    
    cap.release()
    logger.info(f"Extracted {len(crop_paths)} person crops to {output_dir}")
    return crop_paths


if __name__ == "__main__":
    print("LEIP YOLO Detector Module")
    print("=" * 50)
    
    detector = YOLODetector(model_size="small")
    print(f"✓ YOLOv8 detector initialized")
    print(f"✓ Ready for frame, video, and stream processing")
