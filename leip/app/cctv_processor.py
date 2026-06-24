"""
LEIP CCTV Processor Module
Real-time video processing, frame extraction, and multi-modal analysis
"""

import cv2
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple, Union
from datetime import datetime
import json
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import ffmpeg
except ImportError:
    ffmpeg = None

from config.settings import settings
from app.yolo_detector import YOLODetector
from app.face_utils import LEIPFaceMatcher
from app.database import SessionLocal
from app import crud, schemas
import uuid

# ============ LOGGING ============
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoSourceType(str, Enum):
    """Supported video source types"""
    FILE = "file"
    RTSP_STREAM = "rtsp_stream"
    HTTP_STREAM = "http_stream"
    CAMERA = "camera"
    UNKNOWN = "unknown"


@dataclass
class FrameMetadata:
    """Metadata for a processed frame"""
    frame_id: int
    timestamp: float
    source: str
    width: int
    height: int
    fps: float
    quality_score: float  # Brightness, contrast, etc.


class CCTVProcessor:
    """
    Comprehensive CCTV video processing engine
    Features:
    - Multi-source video ingestion (files, RTSP streams, cameras)
    - Real-time frame processing
    - Object detection (persons, vehicles)
    - Face extraction for matching
    - Video quality assessment
    - Multi-threading support
    - Event logging
    """
    
    def __init__(self, enable_face_matching: bool = True):
        """
        Initialize CCTV processor
        
        Args:
            enable_face_matching: Whether to enable face detection on frames
        """
        self.detector = YOLODetector(
            model_size=settings.yolo_model_size,
            confidence_threshold=settings.yolo_confidence_threshold
        )
        
        self.face_matcher = None
        if enable_face_matching:
            try:
                self.face_matcher = LEIPFaceMatcher()
            except Exception as e:
                logger.warning(f"Face matcher not initialized: {e}")
        
        logger.info("CCTV Processor initialized")
    
    def identify_source(self, source: str) -> VideoSourceType:
        """Identify the type of video source"""
        if source.startswith("rtsp://"):
            return VideoSourceType.RTSP_STREAM
        elif source.startswith("http://") or source.startswith("https://"):
            return VideoSourceType.HTTP_STREAM
        elif source.isdigit():
            return VideoSourceType.CAMERA
        elif Path(source).exists():
            return VideoSourceType.FILE
        else:
            return VideoSourceType.UNKNOWN
    
    def assess_frame_quality(self, frame: np.ndarray) -> float:
        """
        Assess video frame quality (0-1)
        Factors: Brightness, contrast, blur detection
        
        Returns:
            Quality score between 0 and 1
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Brightness (avoid too dark/bright)
        mean_brightness = gray.mean()
        brightness_score = 1 - abs(mean_brightness - 127) / 127
        
        # Contrast (Laplacian variance as blur detector)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        contrast_score = min(1, laplacian_var / 500)  # Normalize
        
        # Combined score
        quality = (brightness_score * 0.4 + contrast_score * 0.6)
        return float(quality)
    
    def extract_keyframes(
        self,
        video_path: str,
        frame_skip: int = 5,
        quality_threshold: float = 0.3
    ) -> List[Tuple[int, np.ndarray]]:
        """
        Extract high-quality keyframes from video
        
        Args:
            video_path: Path to video file
            frame_skip: Process every Nth frame
            quality_threshold: Minimum quality score
            
        Returns:
            List of (frame_id, frame) tuples
        """
        logger.info(f"Extracting keyframes from {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Cannot open video: {video_path}")
        
        keyframes = []
        frame_id = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_id % frame_skip != 0:
                frame_id += 1
                continue
            
            # Quality check
            quality = self.assess_frame_quality(frame)
            if quality >= quality_threshold:
                keyframes.append((frame_id, frame))
            
            frame_id += 1
        
        cap.release()
        logger.info(f"Extracted {len(keyframes)} keyframes")
        return keyframes
    
    def process_video(
        self,
        video_source: str,
        output_dir: Optional[Union[str, Path]] = None,
        frame_skip: int = 5,
        extract_faces: bool = True,
        save_annotated: bool = False,
        callback: Optional[Callable] = None,
        case_id: Optional[str] = None
    ) -> Dict:
        """
        Comprehensive video processing pipeline
        
        Args:
            video_source: File path, RTSP URL, or camera index
            output_dir: Directory to save results
            frame_skip: Process every Nth frame
            extract_faces: Whether to extract faces for matching
            save_annotated: Whether to save annotated frames
            callback: Optional callback(frame_metadata, detections)
            
        Returns:
            Processing report with all results
        """
        source_type = self.identify_source(video_source)
        logger.info(f"Processing video source ({source_type.value}): {video_source}")
        
        # Setup output directory
        output_dir_path: Optional[Path] = None
        if output_dir:
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_source)
        if not cap.isOpened():
            raise IOError(f"Cannot open video source: {video_source}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if source_type == VideoSourceType.FILE else -1
        
        logger.info(f"Video properties: {width}x{height} @ {fps} FPS, {total_frames} frames")
        
        # Results collection
        results = {
            'source': str(video_source),
            'source_type': source_type.value,
            'metadata': {
                'width': width,
                'height': height,
                'fps': fps,
                'total_frames': total_frames
            },
            'frames_processed': 0,
            'detections_summary': {
                'total_persons': 0,
                'total_vehicles': 0,
                'total_objects': 0,
                'frames_with_detections': 0
            },
            'quality_summary': {
                'avg_quality': 0,
                'min_quality': 1,
                'max_quality': 0
            },
            'frame_results': []
        }
        
        frame_id = 0
        quality_scores = []
        video_writer = None
        
        if save_annotated:
            if not output_dir_path:
                raise ValueError("output_dir must be provided when save_annotated=True")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore[attr-defined]
            output_path = str(output_dir_path / "annotated.mp4")
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every Nth frame
                if frame_id % frame_skip != 0:
                    frame_id += 1
                    continue
                
                timestamp = frame_id / fps
                
                # Quality assessment
                quality = self.assess_frame_quality(frame)
                quality_scores.append(quality)
                
                # Object detection
                annotated, detections = self.detector.detect_frame(frame)
                
                # Face extraction (if enabled and quality is good)
                faces_extracted = []
                if extract_faces and quality > 0.3 and self.face_matcher:
                    # Save high-quality frames for face extraction
                    faces_extracted = self._extract_faces_from_frame(
                        frame, detections, frame_id, output_dir_path
                    )
                
                # Frame metadata
                metadata = FrameMetadata(
                    frame_id=frame_id,
                    timestamp=timestamp,
                    source=str(video_source),
                    width=width,
                    height=height,
                    fps=fps,
                    quality_score=quality
                )
                
                # Frame result
                frame_result = {
                    'frame_id': frame_id,
                    'timestamp': timestamp,
                    'quality_score': quality,
                    'detections': detections,
                    'faces_extracted': len(faces_extracted)
                }
                
                # Update summary
                if detections:
                    results['detections_summary']['frames_with_detections'] += 1
                    for det in detections:
                        if det['type'] == 'person':
                            results['detections_summary']['total_persons'] += 1
                        elif 'vehicle' in det['type']:
                            results['detections_summary']['total_vehicles'] += 1
                        else:
                            results['detections_summary']['total_objects'] += 1
                
                # Store results
                results['frame_results'].append(frame_result)
                results['frames_processed'] += 1
                
                # Save annotated frame
                if video_writer:
                    video_writer.write(annotated)
                
                # Callback
                if callback:
                    callback(metadata, detections)
                
                # Progress logging
                if results['frames_processed'] % 30 == 0:
                    logger.debug(f"Processed {results['frames_processed']} frames")
                
                frame_id += 1
        
        finally:
            cap.release()
            if video_writer:
                video_writer.release()
        
        # Calculate quality summary
        if quality_scores:
            results['quality_summary'] = {
                'avg_quality': float(np.mean(quality_scores)),
                'min_quality': float(np.min(quality_scores)),
                'max_quality': float(np.max(quality_scores))
            }
        
        # Save results
        if output_dir_path:
            results_file = output_dir_path / "processing_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {results_file}")
            
        # Save to database if case_id provided
        if case_id:
            db = SessionLocal()
            try:
                for frame_result in results['frame_results']:
                    for det in frame_result['detections']:
                        detection_create = schemas.DetectionCreate(
                            detection_id=str(uuid.uuid4()),
                            case_id=case_id,
                            frame_id=frame_result['frame_id'],
                            timestamp=str(frame_result['timestamp']),
                            detection_type=det['type'],
                            confidence=det['confidence'],
                            bbox=det['bbox']
                        )
                        crud.create_detection(db, detection_create)
            except Exception as e:
                logger.error(f"Failed to save detections to database: {e}")
            finally:
                db.close()
        
        logger.info(f"Video processing complete. Summary: {results['detections_summary']}")
        return results
    
    def _extract_faces_from_frame(
        self,
        frame: np.ndarray,
        detections: List[Dict],
        frame_id: int,
        output_dir: Optional[Path]
    ) -> List[str]:
        """Extract face crops for persons detected in frame"""
        if not output_dir:
            return []
        
        faces_dir = output_dir / "faces"
        faces_dir.mkdir(parents=True, exist_ok=True)
        
        extracted = []
        for i, det in enumerate(detections):
            if det['type'] == 'person':
                x1, y1, x2, y2 = (
                    det['bbox']['x1'],
                    det['bbox']['y1'],
                    det['bbox']['x2'],
                    det['bbox']['y2']
                )
                
                # Extract face region
                face_crop = frame[y1:y2, x1:x2]
                
                if face_crop.size > 0:
                    face_path = faces_dir / f"face_f{frame_id}_{i}.jpg"
                    cv2.imwrite(str(face_path), face_crop)
                    extracted.append(str(face_path))
        
        return extracted
    
    def batch_process_videos(
        self,
        video_paths: List[str],
        output_dir: str = "data/cctv_results"
    ) -> Dict[str, Dict]:
        """
        Process multiple videos in batch
        
        Returns:
            Dict mapping video path -> results
        """
        results = {}
        for i, video_path in enumerate(video_paths, 1):
            logger.info(f"Processing video {i}/{len(video_paths)}: {video_path}")
            video_output_dir = Path(output_dir) / f"video_{i}"
            
            try:
                result = self.process_video(
                    video_path,
                    output_dir=str(video_output_dir),
                    extract_faces=True
                )
                results[video_path] = result
            except Exception as e:
                logger.error(f"Failed to process {video_path}: {e}")
                results[video_path] = {'error': str(e)}
        
        return results


# ============ UTILITY FUNCTIONS ============

def process_cctv_footage(
    video_source: str,
    output_dir: Optional[str] = None
) -> Dict:
    """Quick CCTV processing"""
    processor = CCTVProcessor()
    return processor.process_video(video_source, output_dir)


if __name__ == "__main__":
    print("LEIP CCTV Processor Module")
    print("=" * 50)
    
    processor = CCTVProcessor(enable_face_matching=True)
    print(f"✓ CCTV Processor initialized")
    print(f"✓ Ready for video, stream, and camera processing")
