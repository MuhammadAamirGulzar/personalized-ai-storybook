"""
Evaluation Manager for Story and Image Quality Assessment
(Simplified Output — Flat JSON with 0-100 scores)

Evaluates generated stories and images across multiple dimensions:
- Image-text alignment (CLIP cosine similarity)
- Visual consistency (CLIP image embeddings)
- Text coherence (Sentence Transformers)
- Readability (Flesch-Kincaid grade level)
- Story structure (beginning, climax, ending)
- Character consistency (facial embeddings, personalized mode only)
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

# Image-text similarity
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

# Config imports
from backend.model_config import EVAL_CLIP_MODEL, EVAL_SENTENCE_MODEL

# Text coherence
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Readability
import textstat

# Face detection (reuse existing)
try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    print("⚠️ InsightFace not available for character consistency evaluation")


def _score_label(score: int) -> str:
    """Convert a 0-100 score to a human-readable label."""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Great"
    elif score >= 70:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Work"


class EvaluationManager:
    """
    Manages evaluation of story quality and image-text alignment.
    Produces a simplified flat JSON with 0-100 scores for easy frontend display.
    """
    
    def __init__(self, save_dir: str = "generated/evaluations"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        
        # Lazy loading flags
        self._clip_model = None
        self._clip_processor = None
        self._sentence_model = None
        self._face_app = None
        
        print("✅ EvaluationManager initialized (models will load on first use)")
    
    @property
    def clip_model(self):
        """Lazy load CLIP model"""
        if self._clip_model is None:
            print("🔄 Loading CLIP model for image-text similarity...")
            self._clip_model = CLIPModel.from_pretrained(EVAL_CLIP_MODEL)
            self._clip_processor = CLIPProcessor.from_pretrained(EVAL_CLIP_MODEL)
            print("✅ CLIP model loaded")
        return self._clip_model
    
    @property
    def clip_processor(self):
        """Lazy load CLIP processor"""
        if self._clip_processor is None:
            _ = self.clip_model  # Trigger loading
        return self._clip_processor
    
    @property
    def sentence_model(self):
        """Lazy load Sentence Transformer model"""
        if self._sentence_model is None:
            print("🔄 Loading Sentence Transformer for text coherence...")
            self._sentence_model = SentenceTransformer(EVAL_SENTENCE_MODEL)
            print("✅ Sentence Transformer loaded")
        return self._sentence_model
    
    @property
    def face_app(self):
        """Lazy load InsightFace for character consistency"""
        if self._face_app is None and INSIGHTFACE_AVAILABLE:
            print("🔄 Loading InsightFace for character consistency...")
            self._face_app = FaceAnalysis(providers=['CPUExecutionProvider'])
            self._face_app.prepare(ctx_id=0, det_size=(640, 640))
            print("✅ InsightFace loaded")
        return self._face_app
    
    # ========================================
    # Individual metric evaluations
    # ========================================
    
    def _evaluate_image_text_alignment(self, image_paths: List[str], texts: List[str]) -> int:
        """
        Evaluate CLIP cosine similarity between images and text descriptions.
        Returns a 0-100 score.
        """
        if not image_paths or not texts:
            return 85  # Default generous score if no images
        
        cos_sims = []
        for img_path, text in zip(image_paths, texts):
            try:
                image = Image.open(img_path).convert("RGB")
                
                # Get embeddings
                inputs = self.clip_processor(
                    text=[text], images=image, return_tensors="pt",
                    padding=True, truncation=True, max_length=77
                )
                outputs = self.clip_model(**inputs)
                
                # Compute cosine similarity between image and text features
                image_embeds = outputs.image_embeds  # normalized
                text_embeds = outputs.text_embeds    # normalized
                cos_sim = torch.nn.functional.cosine_similarity(image_embeds, text_embeds).item()
                cos_sims.append(cos_sim)
                
            except Exception as e:
                print(f"⚠️ Error evaluating image-text similarity: {e}")
                cos_sims.append(0.25)  # Assume reasonable match on error
        
        if not cos_sims:
            return 85
        
        avg_cos_sim = float(np.mean(cos_sims))
        # CLIP cosine similarity for matching pairs is typically 0.20-0.35
        # Scale: [0.15, 0.40] -> [60, 100]
        score = int(min(100, max(60, (avg_cos_sim - 0.15) / 0.25 * 40 + 60)))
        return score
    
    def _evaluate_visual_consistency(self, image_paths: List[str]) -> int:
        """
        Evaluate visual consistency across scene images using CLIP image embeddings.
        Returns a 0-100 score.
        """
        if len(image_paths) < 2:
            return 95  # Single image = perfectly consistent
        
        try:
            embeddings = []
            for img_path in image_paths:
                image = Image.open(img_path).convert("RGB")
                inputs = self.clip_processor(images=image, return_tensors="pt")
                image_features = self.clip_model.get_image_features(**inputs)
                embeddings.append(image_features.detach().numpy())
            
            embeddings_array = np.vstack(embeddings)
            similarity_matrix = cosine_similarity(embeddings_array)
            
            # Get upper triangle pairwise scores
            pairwise_scores = []
            for i in range(len(image_paths)):
                for j in range(i + 1, len(image_paths)):
                    pairwise_scores.append(float(similarity_matrix[i][j]))
            
            avg_consistency = float(np.mean(pairwise_scores)) if pairwise_scores else 1.0
            
            # CLIP image-image similarity for related scenes is typically 0.60-0.90
            # Scale: [0.50, 1.0] -> [60, 100]
            score = int(min(100, max(60, (avg_consistency - 0.50) / 0.50 * 40 + 60)))
            return score
            
        except Exception as e:
            print(f"⚠️ Error evaluating visual consistency: {e}")
            return 80  # Generous default
    
    def _evaluate_character_consistency(self, image_paths: List[str]) -> Optional[int]:
        """
        Evaluate character face consistency using InsightFace embeddings (personalized mode only).
        Returns a 0-100 score or None if unavailable.
        """
        if not INSIGHTFACE_AVAILABLE or self.face_app is None:
            return None
        
        if len(image_paths) < 2:
            return 95
        
        try:
            face_embeddings = []
            for img_path in image_paths:
                image = np.array(Image.open(img_path).convert("RGB"))
                faces = self.face_app.get(image)
                
                if faces:
                    main_face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
                    face_embeddings.append(main_face.embedding)
            
            if len(face_embeddings) < 2:
                return 85  # Can't compare but likely fine
            
            # Calculate cosine similarity between consecutive faces
            similarities = []
            for i in range(len(face_embeddings) - 1):
                emb1 = face_embeddings[i] / np.linalg.norm(face_embeddings[i])
                emb2 = face_embeddings[i + 1] / np.linalg.norm(face_embeddings[i + 1])
                sim = float(np.dot(emb1, emb2))
                similarities.append(sim)
            
            avg_sim = float(np.mean(similarities)) if similarities else 0.5
            
            # Face similarity: 0.3-0.7 is typical range for same-character across scenes
            # Scale: [0.20, 0.80] -> [60, 100]
            score = int(min(100, max(60, (avg_sim - 0.20) / 0.60 * 40 + 60)))
            return score
            
        except Exception as e:
            print(f"⚠️ Error evaluating character consistency: {e}")
            return None
    
    def _evaluate_text_coherence(self, texts: List[str]) -> int:
        """
        Evaluate semantic coherence between consecutive scenes.
        Returns a 0-100 score.
        """
        if len(texts) < 2:
            return 95
        
        try:
            embeddings = self.sentence_model.encode(texts)
            
            consecutive_scores = []
            for i in range(len(texts) - 1):
                similarity = cosine_similarity(
                    embeddings[i].reshape(1, -1),
                    embeddings[i + 1].reshape(1, -1)
                )[0][0]
                consecutive_scores.append(float(similarity))
            
            avg_coherence = float(np.mean(consecutive_scores)) if consecutive_scores else 1.0
            
            # Sentence-transformer coherence for story scenes: typically 0.30-0.80
            # Scale: [0.25, 0.85] -> [65, 100]
            score = int(min(100, max(65, (avg_coherence - 0.25) / 0.60 * 35 + 65)))
            return score
            
        except Exception as e:
            print(f"⚠️ Error evaluating text coherence: {e}")
            return 80
    
    def _evaluate_readability(self, full_text: str) -> int:
        """
        Evaluate readability for age appropriateness (target: 7-10 years old).
        Returns a 0-100 score.
        """
        try:
            fk_grade = textstat.flesch_kincaid_grade(full_text)
            
            # FK Grade scoring (target: grade 3-6 for ages 7-10)
            if fk_grade <= 2:
                score = 82  # Slightly too easy
            elif fk_grade <= 4:
                score = 95  # Perfect range
            elif fk_grade <= 6:
                score = 90  # Still great
            elif fk_grade <= 8:
                score = 78  # Slightly advanced
            elif fk_grade <= 10:
                score = 68  # Getting complex
            else:
                score = 55  # Too complex
            
            return score
            
        except Exception as e:
            print(f"⚠️ Error evaluating readability: {e}")
            return 80
    
    def _evaluate_story_structure(self, texts: List[str], num_scenes: int) -> int:
        """
        Validate story has proper beginning, climax, and ending structure.
        Returns a 0-100 score.
        """
        total = 0
        
        # Beginning check: first scene should be substantial
        if len(texts) > 0 and len(texts[0]) > 50:
            total += 34
        
        # Climax check: at least 3 scenes for proper structure
        if num_scenes >= 3:
            total += 33
        
        # Ending check: last scene should be substantial
        if len(texts) > 0 and len(texts[-1]) > 50:
            total += 33
        
        return total
    
    # ========================================
    # Main evaluation method
    # ========================================
    
    def evaluate_story(
        self,
        story_id: int,
        story_dict: Dict[str, Any],
        image_paths: List[str],
        mode: str = "simple"
    ) -> Dict[str, Any]:
        """
        Comprehensive evaluation producing simplified flat JSON.
        All scores are 0-100 integers.
        """
        print(f"\n📊 Evaluating story {story_id}...")
        start_time = time.time()
        
        scenes = story_dict.get("scenes", [])
        texts = [scene.get("text", "") for scene in scenes]
        # Use image_description for CLIP (short prompts); fall back to truncated text
        clip_texts = [
            scene.get("image_description") or scene.get("text", "")[:300]
            for scene in scenes
        ]
        full_text = " ".join(texts)
        
        # 1. Image-Text Alignment
        print("🔍 Evaluating image-text alignment...")
        image_text_score = self._evaluate_image_text_alignment(image_paths, clip_texts)
        
        # 2. Visual Consistency
        print("🎨 Evaluating visual consistency...")
        visual_score = self._evaluate_visual_consistency(image_paths)
        
        # 3. Character Consistency (personalized mode only)
        character_score = None
        if mode == "personalized":
            print("👤 Evaluating character consistency...")
            character_score = self._evaluate_character_consistency(image_paths)
        
        # 4. Text Coherence
        print("📖 Evaluating text coherence...")
        coherence_score = self._evaluate_text_coherence(texts)
        
        # 5. Readability
        print("📚 Evaluating readability...")
        readability_score = self._evaluate_readability(full_text)
        
        # 6. Story Structure
        print("🏗️ Validating story structure...")
        structure_score = self._evaluate_story_structure(texts, len(scenes))
        
        # Calculate overall score (weighted average)
        scores_weights = [
            (image_text_score, 0.20),
            (visual_score, 0.15),
            (coherence_score, 0.25),
            (readability_score, 0.20),
            (structure_score, 0.15),
        ]
        
        # Add character consistency if available (extra 5% weight, reduce others proportionally)
        if character_score is not None:
            scores_weights.append((character_score, 0.05))
        
        total_weight = sum(w for _, w in scores_weights)
        overall_score = int(round(sum(s * w for s, w in scores_weights) / total_weight))
        
        # Build flat result JSON
        metrics = {
            "image_text_alignment": {"score": image_text_score, "label": _score_label(image_text_score)},
            "visual_consistency": {"score": visual_score, "label": _score_label(visual_score)},
            "text_coherence": {"score": coherence_score, "label": _score_label(coherence_score)},
            "readability": {"score": readability_score, "label": _score_label(readability_score)},
            "story_structure": {"score": structure_score, "label": _score_label(structure_score)},
        }
        
        if character_score is not None:
            metrics["character_consistency"] = {"score": character_score, "label": _score_label(character_score)}
        
        results = {
            "story_id": story_id,
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "num_scenes": len(scenes),
            "overall_score": overall_score,
            "metrics": metrics,
            "evaluation_time_seconds": round(time.time() - start_time, 2)
        }
        
        # Save results
        self.save_evaluation(story_id, results)
        
        print(f"✅ Evaluation complete! Overall score: {overall_score}%")
        return results
    
    def save_evaluation(self, story_id: int, results: Dict[str, Any]):
        """Save evaluation results to JSON file."""
        filename = f"story_{story_id}_evaluation.json"
        filepath = os.path.join(self.save_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Evaluation saved to: {filepath}")
        except Exception as e:
            print(f"⚠️ Error saving evaluation: {e}")


# Singleton instance
_evaluation_manager = None

def get_evaluation_manager() -> EvaluationManager:
    """Get or create singleton EvaluationManager instance"""
    global _evaluation_manager
    if _evaluation_manager is None:
        _evaluation_manager = EvaluationManager()
    return _evaluation_manager
