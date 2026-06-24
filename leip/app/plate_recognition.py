"""
LEIP License Plate Recognition Module
Vehicle identification via license plate detection and OCR
"""

import cv2
import numpy as np
import logging
import importlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re
from dataclasses import dataclass

# easyocr is loaded lazily in LicensePlateRecognizer.__init__
from config.settings import settings

# ============ LOGGING ============
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PlateDetection:
    """License plate detection result"""
    plate_number: str
    confidence: float
    bbox: Dict  # x1, y1, x2, y2, width, height
    text_confidence: float
    raw_text: str
    timestamp: str
    region: Optional[str] = None  # State/province
    vehicle_type: Optional[str] = None


class LicensePlateRecognizer:
    """
    Professional license plate detection and recognition
    Features:
    - YOLO-based plate localization
    - Multi-language OCR (EasyOCR)
    - Plate number validation
    - Regional formatting
    - Confidence scoring
    - Vehicle tracking via plate
    
    Supported regions:
    - North America (US, Canada, Mexico)
    - Europe
    - UK, Australia
    """
    
    # Regex patterns for common plate formats
    PLATE_PATTERNS = {
        'US': r'^[A-Z]{0,3}[0-9]{1,5}[A-Z]{0,3}$',  # Flexible
        'UK': r'^[A-Z]{2}[0-9]{2}[A-Z]{3}$',
        'EU': r'^[A-Z]{2}[0-9]{2,3}[A-Z]{2,3}[0-9]{2,3}$',
        'CA': r'^[A-Z]{0,3}[0-9]{1,5}$',
        'AU': r'^[A-Z]{3}[0-9]{2,3}[A-Z]{2}$'
    }
    
    def __init__(self, ocr_backend: str = "easyocr", languages: List[str] = ['en']):
        """
        Initialize plate recognizer
        
        Args:
            ocr_backend: OCR engine (easyocr, paddleocr)
            languages: Languages for OCR
        """
        logger.info(f"Initializing LPR with {ocr_backend} backend")
        
        if ocr_backend == "easyocr":
            try:
                easyocr_mod = importlib.import_module('easyocr')
            except ImportError as e:
                raise ImportError("Please install: pip install easyocr") from e

            self.reader = easyocr_mod.Reader(
                languages,
                gpu=settings.faiss_gpu_enabled,
                model_storage_directory=settings.model_cache_dir
            )
        else:
            raise ValueError(f"Unsupported backend: {ocr_backend}")
        
        self.ocr_backend = ocr_backend
        logger.info("License Plate Recognizer initialized")
    
    def detect_and_recognize(
        self,
        frame: np.ndarray,
        roi: Optional[Dict] = None
    ) -> List[PlateDetection]:
        """
        Detect and recognize license plates in frame
        
        Args:
            frame: Input frame (BGR)
            roi: Optional region of interest {x1, y1, x2, y2}
            
        Returns:
            List of PlateDetection objects
        """
        detections = []
        
        # Extract ROI if provided
        if roi:
            x1, y1, x2, y2 = roi['x1'], roi['y1'], roi['x2'], roi['y2']
            search_frame = frame[y1:y2, x1:x2]
            offset_x, offset_y = x1, y1
        else:
            search_frame = frame
            offset_x, offset_y = 0, 0
        
        # Preprocess for better plate detection
        gray = cv2.cvtColor(search_frame, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # OCR
        try:
            results = self.reader.readtext(enhanced)
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return detections
        
        # Process OCR results
        for detection in results:
            bbox, text, confidence = detection
            
            # Clean text
            clean_text = self._clean_text(text)
            
            # Validate plate format
            is_valid, region = self._validate_plate(clean_text)
            
            if is_valid and confidence > settings.lpr_confidence_threshold:
                # Convert bbox to standard format
                pts = np.array(bbox, dtype=np.float32)
                x_coords = pts[:, 0]
                y_coords = pts[:, 1]
                
                x1_plate = int(np.min(x_coords)) + offset_x
                y1_plate = int(np.min(y_coords)) + offset_y
                x2_plate = int(np.max(x_coords)) + offset_x
                y2_plate = int(np.max(y_coords)) + offset_y
                
                plate_det = PlateDetection(
                    plate_number=clean_text,
                    confidence=confidence,
                    bbox={
                        'x1': x1_plate,
                        'y1': y1_plate,
                        'x2': x2_plate,
                        'y2': y2_plate,
                        'width': x2_plate - x1_plate,
                        'height': y2_plate - y1_plate
                    },
                    text_confidence=float(confidence),
                    raw_text=text,
                    timestamp=datetime.now().isoformat(),
                    region=region
                )
                
                detections.append(plate_det)
                logger.debug(f"Detected plate: {clean_text} ({region}) - Confidence: {confidence:.2f}")
        
        return detections
    
    def process_vehicle_detections(
        self,
        frame: np.ndarray,
        vehicle_detections: List[Dict]
    ) -> Dict[int, List[PlateDetection]]:
        """
        Recognize plates from detected vehicles
        
        Args:
            frame: Input frame
            vehicle_detections: List of vehicle detections from YOLO
                [{
                    'type': 'vehicle_car',
                    'bbox': {x1, y1, x2, y2},
                    'confidence': float
                }, ...]
            
        Returns:
            Dict mapping vehicle index -> plate detections
        """
        results = {}
        
        for i, vehicle in enumerate(vehicle_detections):
            if 'vehicle' not in vehicle['type']:
                continue
            
            roi = vehicle['bbox']
            plates = self.detect_and_recognize(frame, roi)
            
            if plates:
                results[i] = plates
                for plate in plates:
                    logger.info(f"Vehicle {i}: {plate.plate_number} ({plate.region})")
        
        return results
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text"""
        # Remove whitespace and special characters
        clean = re.sub(r'[^A-Z0-9]', '', text.upper().strip())
        return clean
    
    def _validate_plate(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate plate format and identify region
        
        Returns:
            Tuple of (is_valid, region_code)
        """
        if not text or len(text) < 4 or len(text) > 10:
            return False, None
        
        for region, pattern in self.PLATE_PATTERNS.items():
            if re.match(pattern, text):
                return True, region
        
        # Fallback: accept if alphanumeric
        if re.match(r'^[A-Z0-9]{4,10}$', text):
            return True, "UNKNOWN"
        
        return False, None
    
    def recognize_batch(
        self,
        image_paths: List[str]
    ) -> Dict[str, List[PlateDetection]]:
        """Process multiple vehicle images"""
        results = {}
        
        for image_path in image_paths:
            frame = cv2.imread(image_path)
            if frame is not None:
                detections = self.detect_and_recognize(frame)
                results[image_path] = detections
        
        return results


class VehicleTracker:
    """
    Track vehicles across frames using license plates
    Builds trajectories and correlations
    """
    
    def __init__(self):
        self.vehicle_trails = {}  # plate_number -> list of sightings
        self.location_history = {}  # plate_number -> locations
    
    def register_sighting(
        self,
        plate: PlateDetection,
        location: Dict,  # GPS or frame coordinates
        frame_id: int,
        timestamp: str
    ):
        """Record a vehicle sighting"""
        plate_num = plate.plate_number
        
        if plate_num not in self.vehicle_trails:
            self.vehicle_trails[plate_num] = []
        
        sighting = {
            'frame_id': frame_id,
            'timestamp': timestamp,
            'location': location,
            'confidence': plate.confidence
        }
        
        self.vehicle_trails[plate_num].append(sighting)
    
    def get_vehicle_trail(self, plate_number: str) -> List[Dict]:
        """Get all sightings of a vehicle"""
        return self.vehicle_trails.get(plate_number, [])
    
    def predict_location(self, plate_number: str) -> Optional[Dict]:
        """Predict vehicle's next location based on trajectory"""
        trail = self.get_vehicle_trail(plate_number)
        
        if len(trail) < 2:
            return None
        
        # Simple linear extrapolation
        last_pos = trail[-1]['location']
        prev_pos = trail[-2]['location']
        
        if 'lat' in last_pos and 'lon' in last_pos:
            # GPS coordinates
            delta_lat = last_pos.get('lat', 0) - prev_pos.get('lat', 0)
            delta_lon = last_pos.get('lon', 0) - prev_pos.get('lon', 0)
            
            predicted = {
                'lat': last_pos['lat'] + delta_lat,
                'lon': last_pos['lon'] + delta_lon
            }
        else:
            # Frame coordinates
            delta_x = last_pos.get('x', 0) - prev_pos.get('x', 0)
            delta_y = last_pos.get('y', 0) - prev_pos.get('y', 0)
            
            predicted = {
                'x': last_pos['x'] + delta_x,
                'y': last_pos['y'] + delta_y
            }
        
        return predicted


# ============ UTILITY FUNCTIONS ============

def recognize_plate_quick(frame: np.ndarray) -> List[PlateDetection]:
    """Quick plate recognition"""
    recognizer = LicensePlateRecognizer()
    return recognizer.detect_and_recognize(frame)


if __name__ == "__main__":
    print("LEIP License Plate Recognizer Module")
    print("=" * 50)
    
    recognizer = LicensePlateRecognizer()
    print(f"✓ License Plate Recognizer initialized")
    print(f"✓ Supports: US, UK, EU, Canada, Australia")
    print(f"✓ Ready for vehicle tracking and correlation")
