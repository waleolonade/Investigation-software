"""
LEIP Face Recognition Module
Face detection, embedding extraction, and gallery matching with FAISS
"""

import cv2
import numpy as np
import faiss
import pickle
import logging
import importlib
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from datetime import datetime
import json

# InsightFace and DeepFace are loaded lazily during runtime
from config.settings import settings

# ============ LOGGING ============
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LEIPFaceMatcher:
    """
    Professional face recognition matcher for law enforcement
    Features:
    - 1:1 verification (probe vs. suspect)
    - 1:N identification (search gallery)
    - FAISS-accelerated similarity search
    - Confidence scoring with thresholding
    - Audit logging for chain-of-custody
    """
    
    def __init__(
        self,
        embedding_dim: int = 512,
        index_type: str = "HNSW",
        db_path: Optional[str] = None,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None
    ):
        """
        Initialize face matcher
        
        Args:
            embedding_dim: Dimension of face embeddings (512 for ArcFace)
            index_type: FAISS index type (Flat, HNSW, IVF)
            db_path: Path to pickle file storing embeddings
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
        """
        self.embedding_dim = embedding_dim
        self.index_type = index_type
        
        # Paths
        self.db_path = Path(db_path or f"{settings.model_cache_dir}/face_gallery.pkl")
        self.index_path = Path(index_path or f"{settings.model_cache_dir}/face_index.faiss")
        self.metadata_path = Path(metadata_path or f"{settings.model_cache_dir}/face_metadata.json")
        
        # Initialize model - InsightFace for high accuracy
        logger.info("Initializing InsightFace model (buffalo_l)...")
        try:
            insightface_app = importlib.import_module('insightface.app')
            FaceAnalysis = insightface_app.FaceAnalysis
        except ImportError as e:
            raise ImportError("Please install: pip install insightface") from e

        try:
            deepface_mod = importlib.import_module('deepface')
            self.DeepFace = deepface_mod.DeepFace
        except ImportError:
            self.DeepFace = None

        self.app = FaceAnalysis(name='buffalo_l', providers=['CPUProvider'])
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        
        # Data structures
        self.gallery = {}  # person_id -> embedding (numpy array)
        self.metadata = {}  # person_id -> metadata dict (name, photo_date, etc.)
        self.index = None
        self.id_to_person = {}  # Index ID -> person_id mapping
        
        # Load existing data
        self._load_data()
        logger.info(f"Face Matcher initialized. Gallery size: {len(self.gallery)}")
    
    def detect_faces(self, image_input) -> Tuple[List, np.ndarray]:
        """
        Detect all faces in an image
        
        Args:
            image_input: File path (str) or numpy array
            
        Returns:
            Tuple of (face list, image array)
        """
        # Load image
        if isinstance(image_input, str):
            img = cv2.imread(image_input)
            if img is None:
                raise FileNotFoundError(f"Image not found: {image_input}")
        else:
            img = image_input.copy()
        
        # Convert BGR to RGB for InsightFace
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        faces = self.app.get(img_rgb)
        logger.debug(f"Detected {len(faces)} faces in image")
        return faces, img
    
    def extract_embedding(self, image_input) -> Optional[np.ndarray]:
        """
        Extract primary face embedding from image
        
        Args:
            image_input: File path or numpy array
            
        Returns:
            Normalized face embedding (1D array) or None
        """
        try:
            faces, _ = self.detect_faces(image_input)
            if not faces:
                logger.warning("No faces detected in image")
                return None
            
            # Return primary face embedding (already normalized by InsightFace)
            embedding = faces[0].normed_embedding.astype('float32')
            return embedding
        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None
    
    def verify_1_to_1(
        self,
        probe_image,
        gallery_image,
        method: str = "deepface"
    ) -> Dict:
        """
        1:1 Verification - Compare two images
        
        Args:
            probe_image: Suspect/query image
            gallery_image: Known/reference image
            method: 'deepface' or 'embedding' (embedding is faster)
            
        Returns:
            {
                'verified': bool,
                'distance': float,
                'similarity': float,
                'threshold': float,
                'confidence': float
            }
        """
        try:
            if method == "deepface":
                if self.DeepFace is None:
                    raise ImportError("Please install: pip install deepface to enable DeepFace verification")
                # Use DeepFace verification (more robust)
                result = self.DeepFace.verify(
                    img1_path=probe_image if isinstance(probe_image, str) else None,
                    img2_path=gallery_image if isinstance(gallery_image, str) else None,
                    model_name="ArcFace",
                    detector_backend="retinaface",
                    enforce_detection=False
                )
                
                verified = result["verified"]
                distance = result["distance"]
                threshold = result["threshold"]
                similarity = 1 - distance
            
            else:  # embedding method (faster)
                probe_emb = self.extract_embedding(probe_image)
                gallery_emb = self.extract_embedding(gallery_image)
                
                if probe_emb is None or gallery_emb is None:
                    return {
                        'verified': False,
                        'distance': 999,
                        'similarity': 0.0,
                        'threshold': settings.face_similarity_threshold,
                        'confidence': 0.0
                    }
                
                # Cosine distance (embeddings are normalized)
                distance = float(np.linalg.norm(probe_emb - gallery_emb))
                similarity = 1 - (distance / 2)  # Normalize to [0, 1]
                threshold = settings.face_similarity_threshold
                verified = similarity >= threshold
            
            confidence = max(0, min(1, similarity))  # Clamp to [0, 1]
            
            result_dict = {
                'verified': verified,
                'distance': float(distance),
                'similarity': float(similarity),
                'threshold': float(threshold),
                'confidence': float(confidence)
            }
            
            logger.info(f"1:1 Verification - Similarity: {similarity:.3f}, Verified: {verified}")
            return result_dict
        
        except Exception as e:
            logger.error(f"1:1 verification failed: {e}")
            return {
                'verified': False,
                'distance': 999,
                'similarity': 0.0,
                'threshold': settings.face_similarity_threshold,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def add_to_gallery(
        self,
        person_id: str,
        image_path: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add face to searchable gallery
        
        Args:
            person_id: Unique identifier (suspect ID, mugshot ID, etc.)
            image_path: Path to face image
            metadata: Optional metadata (name, date, source, etc.)
            
        Returns:
            Success boolean
        """
        try:
            embedding = self.extract_embedding(image_path)
            if embedding is None:
                logger.warning(f"Failed to extract embedding for {person_id}")
                return False
            
            # Store embedding and metadata
            self.gallery[person_id] = embedding
            self.metadata[person_id] = metadata or {
                'person_id': person_id,
                'added_date': datetime.now().isoformat(),
                'image_path': str(image_path)
            }
            
            # Save to disk
            self._save_data()
            
            # Rebuild index
            self._build_index()
            
            logger.info(f"Added {person_id} to gallery. Gallery size: {len(self.gallery)}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to add {person_id} to gallery: {e}")
            return False
    
    def search_gallery(
        self,
        probe_image,
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        1:N Identification - Search gallery for matches
        
        Args:
            probe_image: Probe/query image
            top_k: Number of top results to return
            threshold: Similarity threshold (default: config value)
            
        Returns:
            List of matches:
            [{
                'rank': int,
                'person_id': str,
                'similarity': float,
                'distance': float,
                'metadata': dict
            }, ...]
        """
        try:
            if threshold is None:
                threshold = settings.face_similarity_threshold
            
            # Extract probe embedding
            probe_emb = self.extract_embedding(probe_image)
            if probe_emb is None or self.index is None or len(self.gallery) == 0:
                logger.warning("Gallery is empty or probe embedding extraction failed")
                return []
            
            # Search FAISS index
            probe_emb_arr = np.array([probe_emb]).astype('float32')
            distances, indices = self.index.search(probe_emb_arr, min(top_k, len(self.gallery)))
            
            results = []
            person_ids = list(self.gallery.keys())
            
            for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < 0 or idx >= len(person_ids):
                    continue
                
                person_id = person_ids[idx]
                similarity = float(dist)  # FAISS IP: higher is better
                
                if similarity >= threshold:
                    results.append({
                        'rank': rank + 1,
                        'person_id': person_id,
                        'similarity': similarity,
                        'confidence': min(1.0, similarity),  # Confidence score
                        'distance': 1 - similarity,
                        'metadata': self.metadata.get(person_id, {})
                    })
            
            logger.info(f"Gallery search returned {len(results)} matches above threshold {threshold}")
            return results
        
        except Exception as e:
            logger.error(f"Gallery search failed: {e}")
            return []
    
    def batch_search(
        self,
        probe_images: List[str],
        top_k: int = 5,
        threshold: Optional[float] = None
    ) -> Dict[str, List[Dict]]:
        """
        Search multiple probe images
        
        Args:
            probe_images: List of image paths
            top_k: Number of top results per probe
            threshold: Similarity threshold
            
        Returns:
            Dict mapping image path -> list of matches
        """
        results = {}
        for probe_image in probe_images:
            results[probe_image] = self.search_gallery(probe_image, top_k, threshold)
        
        logger.info(f"Batch search completed for {len(probe_images)} images")
        return results
    
    def _build_index(self):
        """Build FAISS index from gallery"""
        if not self.gallery:
            logger.warning("Gallery is empty, skipping index build")
            return
        
        person_ids = list(self.gallery.keys())
        embeddings = np.array([self.gallery[pid] for pid in person_ids]).astype('float32')
        
        logger.info(f"Building {self.index_type} FAISS index with {len(embeddings)} embeddings...")
        
        if self.index_type == "Flat":
            # Exact search
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        
        elif self.index_type == "HNSW":
            # Fast approximate search
            self.index = faiss.IndexHNSWFlat(self.embedding_dim, settings.faiss_hnsw_m)
            self.index.hnsw.efConstruction = settings.faiss_hnsw_ef_construction
            self.index.hnsw.efSearch = settings.faiss_hnsw_ef_search
        
        elif self.index_type == "IVF":
            # Inverted file index (scalable)
            nlist = min(4096, max(1, len(person_ids) // 10))
            quantizer = faiss.IndexFlatIP(self.embedding_dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist, faiss.METRIC_INNER_PRODUCT)
            self.index.train(embeddings)
        
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        # Add embeddings to index
        self.index.add(embeddings)
        self.id_to_person = {i: person_ids[i] for i in range(len(person_ids))}
        
        # Save index
        faiss.write_index(self.index, str(self.index_path))
        logger.info(f"Index built and saved to {self.index_path}")
    
    def _save_data(self):
        """Persist gallery to disk"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, 'wb') as f:
            pickle.dump(self.gallery, f)
        
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
        
        logger.debug(f"Gallery saved to {self.db_path}")
    
    def _load_data(self):
        """Load gallery from disk"""
        if self.db_path.exists():
            with open(self.db_path, 'rb') as f:
                self.gallery = pickle.load(f)
            logger.info(f"Loaded {len(self.gallery)} embeddings from {self.db_path}")
        
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
        
        if self.index_path.exists() and self.gallery:
            self.index = faiss.read_index(str(self.index_path))
            logger.info(f"Loaded FAISS index from {self.index_path}")
        elif self.gallery:
            self._build_index()


# ============ UTILITY FUNCTIONS ============

def compare_faces_simple(image1: str, image2: str) -> Dict:
    """
    Quick face comparison (1:1) between two images
    
    Returns:
        Verification result dictionary
    """
    matcher = LEIPFaceMatcher()
    return matcher.verify_1_to_1(image1, image2)


def search_suspect(probe_image: str, top_k: int = 10) -> List[Dict]:
    """
    Quick search for suspect in gallery
    
    Returns:
        List of potential matches
    """
    matcher = LEIPFaceMatcher()
    return matcher.search_gallery(probe_image, top_k)


if __name__ == "__main__":
    # Example usage
    print("LEIP Face Matcher Module")
    print("=" * 50)
    
    matcher = LEIPFaceMatcher()
    print(f"✓ Face Matcher initialized")
    print(f"✓ Gallery size: {len(matcher.gallery)}")
    print(f"✓ Ready for 1:1 verification and 1:N search")
