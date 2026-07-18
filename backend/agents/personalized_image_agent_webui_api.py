# backend/agents/personalized_image_agent_webui_api.py
"""
Personalized image generation using Stable Diffusion WebUI Local API
with IP-Adapter FaceID Plus v2 for facial likeness.

Features:
- Gender-aware face application (skips gender-mismatched scenes)
- Two-pass generation for multi-character scenes (only main character gets face)
- ADetailer integration for automatic face/hand quality improvement
- Optimized LoRA/IP-Adapter weights based on community best practices
"""
import os
import re
import base64
import requests
import subprocess
import numpy as np
from io import BytesIO
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple
from backend.utils.ollama_manager import OllamaManager
from backend.utils.bedrock_client import invoke_bedrock
from backend.model_config import WEBUI_URL, CHARACTER_COUNT_JUDGE_MODEL, IMAGE_PROMPT_CONDENSER_MODEL, LORA_NAME, VISION_AGENT_MODEL

# InsightFace for gender detection
try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    print("[WebUI API] ⚠️ InsightFace not available — gender detection disabled")


class PersonalizedImageAgentWebUIAPI:
    """
    Personalized image generation using Stable Diffusion WebUI Local API
    with IP-Adapter FaceID Plus v2 for facial likeness
    """
    
    # Gender keyword maps for scene analysis
    MALE_KEYWORDS = [
        'boy', 'man', 'male', 'prince', 'king', 'father', 'dad', 'brother',
        'son', 'he ', ' he ', 'his ', ' his ', 'him ', ' him ',
        'gentleman', 'sir', 'mr', 'lord', 'uncle', 'grandfather', 'grandpa',
        'hero', 'wizard', 'knight', 'warrior',
    ]
    FEMALE_KEYWORDS = [
        'girl', 'woman', 'female', 'princess', 'queen', 'mother', 'mom',
        'sister', 'daughter', 'she ', ' she ', 'her ', ' her ',
        'lady', 'madam', 'mrs', 'miss', 'aunt', 'grandmother', 'grandma',
        'heroine', 'witch', 'fairy',
    ]
    
    # InsightFace for gender detection
    try:
        from insightface.app import FaceAnalysis
        INSIGHTFACE_AVAILABLE = True
    except ImportError:
        INSIGHTFACE_AVAILABLE = False
        print("[WebUI API] ⚠️ InsightFace not available — gender detection disabled")
    
    def __init__(
        self,
        webui_url: str = WEBUI_URL,
        sd_model_path: str = None,
        lora_path: str = None,
        **kwargs
    ):
        """
        Initialize with WebUI API
        
        Args:
            webui_url: WebUI server URL (default: localhost:7861)
            sd_model_path: Not used (WebUI manages models)
            lora_path: LoRA name (just the filename without extension)
        """
        self.webui_url = webui_url.rstrip('/')
        self.user_photo = None
        self.user_face_crop = None  # Tight crop of the face for better ControlNet detection
        self.detected_gender = None  # Will be set by detect_gender()
        self.output_dir = Path("generated/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Face analysis for gender detection (InsightFace - fallback)
        self._face_app = None
        
        # HuggingFace ViT gender classifier (primary - lazy loaded on first use)
        self._vit_gender_pipe = None
        self._vit_available = None  # None = not checked, True/False after first attempt
        
        # LoRA name
        if lora_path:
            self.lora_name = Path(lora_path).stem
        else:
            self.lora_name = LORA_NAME
        
        # Metadata for user photo analysis
        self.meta_data = {}
        # Scene analysis cache to prevent LLM Judge from hanging when Ollama is paused
        self.scene_analysis_cache = {}
        # Character info for gender-guard
        self.main_character = ""
        self.all_characters = []
        
        # Vision-extracted features (hair, skin tone, glasses)
        self.user_features = ""
        
        # Check if ADetailer is available
        self.adetailer_available = self._check_adetailer()
        
        # Test connection
        try:
            requests.get(f"{self.webui_url}/sdapi/v1/options", timeout=3)
            print(f"[WebUI API] ✅ Connected to WebUI at {self.webui_url}")
        except requests.exceptions.RequestException as e:
            print(f"[WebUI API] ⚠️ WebUI not reachable at {self.webui_url}: {e}")
    
    def _check_adetailer(self) -> bool:
        """Check if ADetailer extension is available in WebUI"""
        try:
            response = requests.get(f"{self.webui_url}/sdapi/v1/scripts", timeout=2)
            if response.status_code == 200:
                scripts = response.json()
                all_scripts = scripts.get("txt2img", []) + scripts.get("img2img", [])
                for script_name in all_scripts:
                    if "adetailer" in script_name.lower():
                        print("[WebUI API] ✅ ADetailer extension detected")
                        return True
            print("[WebUI API] ⚠️ ADetailer not detected — skipping auto face/hand fix")
            return False
        except Exception:
            return False
    
    @property
    def face_app(self):
        """Lazy-load InsightFace for gender detection"""
        if self._face_app is None and INSIGHTFACE_AVAILABLE:
            try:
                self._face_app = FaceAnalysis(providers=['CPUExecutionProvider'])
                self._face_app.prepare(ctx_id=0, det_size=(320, 320))
                print("[WebUI API] ✅ InsightFace loaded for gender detection")
            except Exception as e:
                print(f"[WebUI API] ⚠️ InsightFace init failed: {e}")
                self._face_app = None
        return self._face_app
    
    def set_user_photo(self, photo_path_or_image, use_vision=False):
        """Set user's reference photo and detect gender"""
        if isinstance(photo_path_or_image, str):
            if not os.path.exists(photo_path_or_image):
                raise FileNotFoundError(f"Photo not found: {photo_path_or_image}")
            self.user_photo = Image.open(photo_path_or_image).convert("RGB")
            print(f"[WebUI API] ✅ User photo loaded")
        elif isinstance(photo_path_or_image, Image.Image):
            self.user_photo = photo_path_or_image.convert("RGB")
            print("[WebUI API] ✅ User photo set")
        else:
            raise ValueError("photo_path_or_image must be a file path or PIL Image")
        
        # Auto-detect gender from the photo
        self.detected_gender = self._detect_gender_from_photo()
        
        # Extract visual features (hair, skin, glasses) via Vision Model
        if use_vision:
            self._extract_visual_features()
        else:
            self.user_features = ""
        
        # Pre-crop the face to help WebUI's preprocessor
        self._crop_user_face()

    def check_face_in_image(self, image: Image.Image) -> dict:
        """
        Check whether a detectable face exists in an image.
        Used by the /api/check-face endpoint before generation starts.

        Returns:
            dict with keys:
                face_detected (bool)
                confidence (float 0.0-1.0)
                gender ('male' | 'female' | None)
        """
        if self.face_app is None:
            # InsightFace unavailable — optimistic fallback
            return {"face_detected": True, "confidence": 0.0, "gender": None}

        try:
            img_array = np.array(image.convert("RGB"))
            faces = self.face_app.get(img_array)

            if not faces:
                return {"face_detected": False, "confidence": 0.0, "gender": None}

            # Use the largest face for confidence/gender
            main_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

            # Estimate confidence from bounding box area ratio
            img_area = image.width * image.height
            bbox = main_face.bbox
            face_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            confidence = min(float(face_area / img_area) * 4.0, 1.0)  # rough heuristic

            # Gender from InsightFace
            raw_g = getattr(main_face, 'sex', None) or getattr(main_face, 'gender', None)
            gender = None
            if raw_g is not None:
                if isinstance(raw_g, str):
                    gender = "male" if raw_g.strip().lower() in ('m', 'male') else "female"
                else:
                    try:
                        gender = "male" if float(raw_g) >= 0.5 else "female"
                    except (ValueError, TypeError):
                        pass

            return {"face_detected": True, "confidence": round(confidence, 2), "gender": gender}
        except Exception as e:
            print(f"[WebUI API] ⚠️ check_face_in_image failed: {e}")
            return {"face_detected": True, "confidence": 0.0, "gender": None}

    def set_first_frame_reference(self, scene_image: Image.Image) -> bool:
        """
        Extract the main character's face from a generated scene image and
        use it as the consistency reference for all subsequent scenes.

        This is used in two scenarios:
          1. Personalized mode: user uploaded a photo but no face was detected in it.
             After scene 1 is generated, we harvest the face from that scene.
          2. Simple mode: no user photo at all. Scene 1's face drives all later scenes.

        Returns:
            True if a face was successfully found and set, False otherwise.
        """
        if self.face_app is None:
            print("[WebUI API] ⚠️ InsightFace not available — cannot extract first-frame reference")
            return False

        try:
            img_array = np.array(scene_image.convert("RGB"))
            faces = self.face_app.get(img_array)

            if not faces:
                print("[WebUI API] ⚠️ No face found in Scene 1 — character consistency unavailable")
                return False

            # Use the largest face as the main character
            main_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

            # Crop that face with generous padding and resize to 512x512
            x1, y1, x2, y2 = main_face.bbox
            w, h = x2 - x1, y2 - y1
            pad_x, pad_y = w * 0.35, h * 0.35
            x1 = max(0, int(x1 - pad_x))
            y1 = max(0, int(y1 - pad_y))
            x2 = min(scene_image.width, int(x2 + pad_x))
            y2 = min(scene_image.height, int(y2 + pad_y))

            face_crop = scene_image.crop((x1, y1, x2, y2)).resize((512, 512), Image.LANCZOS)
            self.user_photo = face_crop
            self.user_face_crop = face_crop

            # Detect gender from that extracted face using ViT → InsightFace fallback
            self.detected_gender = self._detect_gender_from_photo()

            print(f"[WebUI API] ✅ First-frame reference set — gender: {self.detected_gender}")
            return True

        except Exception as e:
            print(f"[WebUI API] ⚠️ set_first_frame_reference failed: {e}")
            return False

    def _extract_visual_features(self):
        """
        Extract hair style, hair color, skin tone, and glasses from the user's photo.
        Uses Claude Sonnet 4.6's native multimodal vision via Amazon Bedrock.
        No local GPU or Llava model needed in cloud deployment.
        """
        if self.user_photo is None:
            return

        print(f"[WebUI API] 👁️ Extracting visual features via Bedrock vision (Claude 4.6)...")
        try:
            from backend.utils.bedrock_client import invoke_bedrock_vision
            from backend.model_config import VISION_AGENT_MODEL

            # Resize for cost/speed efficiency — 512x512 is plenty for feature extraction
            resized = self.user_photo.resize((512, 512), Image.LANCZOS)
            photo_b64 = self._image_to_base64(resized)

            vision_prompt = (
                "Describe this person's hair color, hair length/style, skin tone, "
                "and whether they are wearing glasses. "
                "Keep it under 12 words. "
                "Example: short curly brown hair, dark skin tone, wearing glasses"
            )

            features = invoke_bedrock_vision(
                image_base64=photo_b64,
                prompt=vision_prompt,
                system="You are a visual description assistant. Output a concise comma-separated phrase only.",
                model_id=VISION_AGENT_MODEL,
                temperature=0.2,
                max_tokens=60,
            )

            features = features.replace("\n", " ").strip('\"\'.') if features else ""
            if features:
                self.user_features = features
                print(f"[WebUI API] ✅ Extracted Features: '{self.user_features}'")
            else:
                print("[WebUI API] ⚠️ Bedrock vision returned empty features — skipping")

        except Exception as e:
            print(f"[WebUI API] ⚠️ Failed to extract visual features via Bedrock: {e}")
            self.user_features = ""


    def _crop_user_face(self):
        """
        Detect the main face in user_photo and create a tight crop.
        This helps WebUI's ip-adapter-faceid preprocessor find the face reliably.
        """
        if self.user_photo is None or self.face_app is None:
            return
            
        try:
            import numpy as np
            img_array = np.array(self.user_photo)
            faces = self.face_app.get(img_array)
            
            if not faces:
                print("[WebUI API] ⚠️ No face detected for cropping — using full photo")
                self.user_face_crop = self.user_photo
                return
                
            # Use largest face
            face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
            x1, y1, x2, y2 = face.bbox
            
            # Add 30% margin
            w, h = x2 - x1, y2 - y1
            mx, my = w * 0.3, h * 0.3
            
            x1 = max(0, int(x1 - mx))
            y1 = max(0, int(y1 - my))
            x2 = min(self.user_photo.width, int(x2 + mx))
            y2 = min(self.user_photo.height, int(y2 + my))
            
            crop = self.user_photo.crop((x1, y1, x2, y2))
            
            # Resize to 512x512 — WebUI's IP-Adapter runs at res=512 and its internal
            # InsightFace uses det_size=(640,640). A tiny crop (<200px) gets padded into
            # a blank 640x640 canvas causing "No face found". At 512x512 the face fills
            # the image and is always detectable.
            self.user_face_crop = crop.resize((512, 512), Image.LANCZOS)
            print(f"[WebUI API] ✅ User face cropped and resized to 512×512 for WebUI detection")
        except Exception as e:
            print(f"[WebUI API] ⚠️ Face cropping failed: {e}")
            self.user_face_crop = self.user_photo
    
    def _load_vit_gender_pipe(self):
        """
        Lazily load HuggingFace ViT gender classification pipeline.
        Model: dima806/man_woman_clf (~85MB, CPU-friendly, ~98% accuracy)
        Cached after first load so subsequent calls are instant.
        """
        if self._vit_available is False:
            return None  # Already tried and failed
        
        if self._vit_gender_pipe is not None:
            return self._vit_gender_pipe  # Already loaded
        
        try:
            from transformers import pipeline as hf_pipeline
            print("[WebUI API] 🔄 Loading ViT gender classifier (first-run may download ~350MB)...")
            self._vit_gender_pipe = hf_pipeline(
                "image-classification",
                model="rizvandwiki/gender-classification",
                device=-1,  # Force CPU to avoid VRAM conflicts with WebUI
            )
            self._vit_available = True
            print("[WebUI API] ✅ ViT gender classifier ready")
            return self._vit_gender_pipe
        except Exception as e:
            print(f"[WebUI API] ⚠️ ViT gender classifier unavailable: {e} — falling back to InsightFace")
            self._vit_available = False
            return None

    def _detect_gender_with_vit(self) -> Optional[str]:
        """
        Detect gender using HuggingFace ViT model (primary detector, ~98% accuracy).
        Returns 'male', 'female', or None if detection fails.
        """
        pipe = self._load_vit_gender_pipe()
        if pipe is None or self.user_photo is None:
            return None
        
        try:
            results = pipe(self.user_photo)  # Accepts PIL image directly
            # Results expected: [{'label': 'male', 'score': 0.03}, {'label': 'female', 'score': 0.97}]
            top = max(results, key=lambda r: r['score'])
            label = top['label'].strip().lower()
            score = top['score']
            
            # Require at least 60% confidence from ViT
            if score < 0.60:
                print(f"[WebUI API] ⚠️ ViT gender ambiguous (label={label}, score={score:.2f}) — trying InsightFace")
                return None
            
            gender = "male" if label in ('man', 'male', 'boy', 'm') else "female"
            print(f"[WebUI API] ✅ ViT detected gender: {gender} (confidence: {score:.1%})")
            return gender
        except Exception as e:
            print(f"[WebUI API] ⚠️ ViT gender detection failed: {e}")
            return None

    def _detect_gender_from_photo(self) -> Optional[str]:  # noqa
        """
        Detect gender using a two-stage approach:
          Stage 1: HuggingFace ViT classifier (primary — ~98% accuracy)
          Stage 2: InsightFace buffalo_l (fallback — fast but less reliable)
        
        Returns:
            'male', 'female', or None if both stages fail or are ambiguous
        """
        if self.user_photo is None:
            return None
        
        # --- Stage 1: ViT (Primary, most accurate) ---
        vit_result = self._detect_gender_with_vit()
        if vit_result is not None:
            return vit_result
        
        # --- Stage 2: InsightFace (Fallback) ---
        print("[WebUI API] 🔄 Using InsightFace as fallback gender detector...")
        if self.face_app is None:
            return None
        
        try:
            img_array = np.array(self.user_photo)
            faces = self.face_app.get(img_array)
            
            if not faces:
                print("[WebUI API] ⚠️ No face detected in user photo — gender unknown")
                return None
            
            # Use the largest face (most likely the subject)
            main_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            
            # Try to read the gender from all known InsightFace attribute names
            raw_gender = None
            for attr in ['sex', 'gender']:
                raw_gender = getattr(main_face, attr, None)
                if raw_gender is None:
                    try:
                        raw_gender = main_face.get(attr, None)
                    except Exception:
                        pass
                if raw_gender is not None:
                    break

            if raw_gender is None:
                print("[WebUI API] ⚠️ Gender attribute not available in InsightFace output")
                return None

            # --- Handle STRING format: 'M', 'F', 'male', 'female' ---
            if isinstance(raw_gender, str):
                g = raw_gender.strip().lower()
                if g in ('m', 'male'):
                    print("[WebUI API] ✅ Detected gender from photo: male")
                    return "male"
                elif g in ('f', 'female'):
                    print("[WebUI API] ✅ Detected gender from photo: female")
                    return "female"
                else:
                    print(f"[WebUI API] ⚠️ Unrecognised gender string: '{raw_gender}'")
                    return None

            # --- Handle FLOAT/INT format: ~1.0 = male, ~0.0 = female ---
            try:
                sex_score = float(raw_gender)
                MALE_THRESHOLD = 0.70
                FEMALE_THRESHOLD = 0.30
                if sex_score >= MALE_THRESHOLD:
                    print(f"[WebUI API] ✅ Detected gender from photo: male (score: {sex_score:.2f})")
                    return "male"
                elif sex_score <= FEMALE_THRESHOLD:
                    print(f"[WebUI API] ✅ Detected gender from photo: female (score: {1.0 - sex_score:.2f})")
                    return "female"
                else:
                    print(f"[WebUI API] ⚠️ Gender detection ambiguous (score={sex_score:.2f}) — skipping face injection")
                    return None
            except (ValueError, TypeError):
                print(f"[WebUI API] ⚠️ Could not interpret gender value: {raw_gender!r}")
                return None
                
        except Exception as e:
            print(f"[WebUI API] ⚠️ Gender detection failed: {e}")
            return None

    def should_apply_face(self, scene_text: str, main_character: str = None) -> bool:
        """
        Check if the user face should be applied to this scene.
        Strictly prevents mismatching gender injection (e.g. boy on girl).
        """
        if not self.detected_gender:
            return True # If unknown, allow personalization
            
        is_male = (self.detected_gender == "male")
        # Check for exclusive gendered terms in the prompt
        has_male_words = any(w in f" {scene_text.lower()} " for w in [" boy", " man", " he ", " him", " his "])
        has_female_words = any(w in f" {scene_text.lower()} " for w in [" girl", " woman", " she ", " her ", " hers "])
        
        # Scenario: Male User + Prompt about Girls only
        if is_male and has_female_words and not has_male_words:
            # Exception: if main_character name is present, assume it refers to the user
            if main_character and main_character.lower() in scene_text.lower():
                return True
            print(f"[WebUI API] 🛑 Gender mismatch (User: Male, Scene: Only Female words) — skipping personalization")
            return False
            
        # Scenario: Female User + Prompt about Boys only (e.g. "two boys playing")
        if not is_male and has_male_words and not has_female_words:
            if main_character and main_character.lower() in scene_text.lower():
                return True
            print(f"[WebUI API] 🛑 Gender mismatch (User: Female, Scene: Only Male words) — skipping personalization")
            return False
            
        return True
    
    def _count_characters_in_scene(self, scene_description: str, char_names: list = None) -> int:
        """
        Estimate the number of human characters described in a scene.
        Uses fast pattern matching first, then falls back to LLM for complex cases.
        """
        desc_lower = scene_description.lower()
        
        # 1. Names check (Fastest)
        if char_names and len(char_names) >= 2:
            found_names = [name for name in char_names if name.lower() in desc_lower]
            if len(found_names) >= 2:
                return len(found_names)

        # 2. Strong Multi-character patterns (Fast)
        multi_patterns = [
            r'\btwo\b', r'\bthree\b', r'\bfour\b', r'\bfive\b',
            r'\b2\b', r'\b3\b', r'\b4\b', r'\b5\b',
            r'\bboth\b', r'\btogether\b', r'\bgroup\b',
            r'\bfriends\b', r'\bfamily\b', r'\bchildren\b', r'\bkids\b',
            r'\bcouple\b', r'\bpair\b', r'\bboys\b', r'\bgirls\b', r'\bmen\b', r'\bwomen\b'
        ]
        
        for pattern in multi_patterns:
            if re.search(pattern, desc_lower):
                return 2  # At least 2 characters

        # 3. Conjunction check (boy and his friend)
        char_keywords = ['boy', 'girl', 'man', 'woman', 'child', 'kid', 'friend', 'adventurer']
        hits = [word for word in char_keywords if word in desc_lower]
        if len(hits) >= 1 and (" and " in desc_lower or " with " in desc_lower):
             return 2

        # 4. LLM Judge Fallback via Bedrock (Safest/Smartest)
        print(f"[WebUI API] 🧠 Pattern match uncertain — calling Bedrock LLM to verify character count...")
        judge_prompt = f"""Count the number of human characters in the following scene.
Output ONLY the integer number (e.g. 1, 2, 3). Do NOT explain.
If the scene describes a specific main character plus others (friends, crowd, family), the count should be >= 2.

Scene text: "{scene_description}"

Character count:"""
        
        try:
            output = invoke_bedrock(
                prompt=judge_prompt,
                system="You are an expert visual analyzer. Output only a single integer.",
                model_id=CHARACTER_COUNT_JUDGE_MODEL,
                temperature=0.0,
                max_tokens=10,
            )
            import re as regex
            digit_match = regex.search(r'\d+', output)
            if digit_match:
                count = int(digit_match.group())
                print(f"[WebUI API] 🧠 LLM Judge decided: {count} character(s)")
                return count
        except Exception as e:
            print(f"[WebUI API] ⚠️ LLM Judge failed: {e} — defaulting to 1")

        return 1
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64"""
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def _get_adetailer_args(self) -> dict:
        """Get ADetailer configuration for the alwayson_scripts payload.
        Uses hand_yolov8n for hand detection and correction."""
        if not self.adetailer_available:
            return {}
        
        return {
            "ADetailer": {
                "args": [
                    True,   # ad_enable
                    False,  # skip_img2img
                    {
                        "ad_model": "hand_yolov8n.pt",
                        "ad_confidence": 0.3,
                        "ad_denoising_strength": 0.5,
                        "ad_inpaint_only_masked": True,
                        "ad_inpaint_only_masked_padding": 32,
                        "ad_prompt": "natural hands, well-proportioned, correct anatomy",
                        "ad_negative_prompt": "extra fingers, missing fingers, fused fingers, deformed hands, mutated hands, bad anatomy",
                        "ad_use_cfg_scale": True,
                        "ad_cfg_scale": 7.0,  # Hands need high CFG to fix structure (1.5 is too low)
                        "ad_use_steps": False,
                        # CRITICAL: Prevent the global FaceID ControlNet from drawing faces on hands
                        "ad_controlnet_model": "None"
                    }
                ]
            }
        }
    
    def cleanup(self):
        """Release InsightFace models and clear memory.
        Call this after generation is complete to prevent memory leaks."""
        if self._face_app is not None:
            del self._face_app
            self._face_app = None
            
        if getattr(self, '_vit_gender_pipe', None) is not None:
            del self._vit_gender_pipe
            self._vit_gender_pipe = None
            self._vit_available = None
        
        if self.user_photo is not None:
            del self.user_photo
            self.user_photo = None
        
        self.detected_gender = None
        self.scene_analysis_cache = {}  # Clear cache
        
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("[WebUI API] 🧹 Agent memory cleaned up")
        except Exception:
            pass
    
    def analyze_story_scenes(self, scenes: list, characters: list, main_character: str):
        """
        Pre-analyze all scenes in the story to determine character counts and 
        face-application feasibility BEFORE Ollama is paused.
        """
        self.main_character = main_character
        self.all_characters = characters
        print(f"[WebUI API] 🧠 Pre-analyzing {len(scenes)} scenes for image generation...")
        for scene in scenes:
            scene_num = scene.get("scene_number", 0)
            full_text = scene.get("text", "")
            description = scene.get("image_description") or full_text
            
            # 1. Determine if face should be applied. 
            # We strictly use the FULL scene text here, as the condensed 'image_description' 
            # often loses pronouns (he/she/girl/boy) causing the gender filter to fail.
            apply_face = self.should_apply_face(full_text, main_character)
            
            # 2. Determine character count (triggers LLM Judge if needed)
            char_count = self._count_characters_in_scene(description, char_names=characters)
            
            # Cache results indexed by scene number
            self.scene_analysis_cache[scene_num] = {
                "apply_face": apply_face,
                "char_count": char_count
            }
        print(f"[WebUI API] ✅ Scene analysis complete and cached.")
    
    def _generate_base_scene(self, prompt_text: str, filename: str) -> Tuple[Image.Image, str]:
        """
        Generate a base scene WITHOUT IP-Adapter (for multi-character scenes).
        Uses standard txt2img with ADetailer for quality.
        
        Returns:
            (PIL Image, output path)
        """
        # Smart Gender Injection:
        # 1. If main character name is in the prompt, ensure they have the right foundation.
        # 2. If no mentioned characters but prompt has people, assume it's the main character.
        # 3. DO NOT override if an explicit opposite gender is mentioned (e.g. "a girl" vs user "boy").
        
        from backend.utils.content_safety import ContentSafetyFilter
        safe_negative = ContentSafetyFilter.get_child_safe_negative_prompt()
        
        gender_prefix = "boy" if self.detected_gender == "male" else "girl"
        is_main_char_present = self.main_character and self.main_character.lower() in prompt_text.lower()
        has_opposite_gender = ("girl" in prompt_text.lower() or "woman" in prompt_text.lower()) if self.detected_gender == "male" else ("boy" in prompt_text.lower() or "man" in prompt_text.lower())
        
        if is_main_char_present and not has_opposite_gender:
            # "Oliver playing" -> "boy Oliver playing"
            positive_prompt = f"{gender_prefix} {prompt_text}, best quality, high quality"
        elif not any(c.lower() in prompt_text.lower() for c in self.all_characters) and not has_opposite_gender:
            # "Someone watching TV" -> "boy watching TV" (assumes main character)
            positive_prompt = f"{gender_prefix} {prompt_text}, best quality, high quality"
        else:
            # "Alice (girl) playing" or "A girl watching TV" -> Keep as is to avoid "boy a girl"
            positive_prompt = f"{prompt_text}, best quality, high quality"
        
        # Build alwayson_scripts
        alwayson_scripts = {}
        adetailer_args = self._get_adetailer_args()
        alwayson_scripts.update(adetailer_args)
        
        payload = {
            "prompt": positive_prompt,
            "negative_prompt": safe_negative,
            "steps": 35,
            "cfg_scale": 7.0,
            "width": 512,
            "height": 512,
            "sampler_name": "DPM++ 2M Karras",
            "batch_size": 1,
            "n_iter": 1,
            "alwayson_scripts": alwayson_scripts
        }
        
        print(f"[WebUI API] Pass 1: Generating base scene (no face injection)...")
        
        response = requests.post(
            f"{self.webui_url}/sdapi/v1/txt2img",
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        result = response.json()
        
        image_data = base64.b64decode(result['images'][0])
        image = Image.open(BytesIO(image_data)).convert("RGB")
        
        output_path = self.output_dir / filename
        image.save(output_path)
        
        return image, str(output_path)
    
    def _inpaint_main_character_face(
        self, 
        base_image: Image.Image, 
        filename: str
    ) -> str:
        """
        Inpaint ONLY the main character's face using IP-Adapter FaceID.
        Detects the largest face in the image and creates a mask for it.
        
        Args:
            base_image: The base scene image from Pass 1
            filename: Output filename
            
        Returns:
            Path to the final image
        """
        if self.user_photo is None:
            raise ValueError("User photo not set")
        
        # Detect faces in the base image to find the main character (largest face)
        faces = []
        if self.face_app is not None:
            try:
                img_array = np.array(base_image)
                faces = self.face_app.get(img_array)
            except Exception as e:
                print(f"[WebUI API] ⚠️ Face detection in scene failed: {e}")
        
        if not faces:
            print("[WebUI API] ⚠️ No faces detected in scene — applying face globally (fallback)")
            return self._generate_with_face(
                prompt_text="portrait, best quality",
                filename=filename,
                use_base_image=base_image
            )
        
        # Find the largest face that MATCHES the user's detected gender (if available)
        valid_faces = faces
        if self.detected_gender is not None:
            filtered = []
            for f in faces:
                # Use same robust parsing as _detect_gender_from_photo
                raw_g = getattr(f, 'sex', None) or f.get('sex', None)
                if raw_g is None:
                    raw_g = getattr(f, 'gender', None) or f.get('gender', None)
                
                face_gender = None
                if raw_g is not None:
                    if isinstance(raw_g, str):
                        g_lower = raw_g.strip().lower()
                        if g_lower in ('m', 'male'): face_gender = "male"
                        elif g_lower in ('f', 'female'): face_gender = "female"
                    else:
                        try:
                            score = float(raw_g)
                            face_gender = "male" if score >= 0.5 else "female"
                        except (ValueError, TypeError):
                            pass
                
                if face_gender == self.detected_gender:
                    filtered.append(f)
            
            if filtered:
                valid_faces = filtered
                print(f"[WebUI API]   Filtered to {len(valid_faces)} face(s) matching gender '{self.detected_gender}'")
            if not valid_faces:
                print(f"[WebUI API] 🛑 No faces matched user gender '{self.detected_gender}' — skipping inpaint to prevent mismatch")
                return base_image
        
        # Find the largest face from the valid pool (assumed to be the main character)
        main_face = max(valid_faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        
        # Create a mask: white = area to inpaint (main character's face), black = keep
        mask = Image.new("L", base_image.size, 0)  # Black background (keep everything)
        
        # Expand bounding box slightly for natural blending (reduced to 15% to prevent mask overlap on adjacent faces)
        x1, y1, x2, y2 = main_face.bbox
        w, h = x2 - x1, y2 - y1
        padding_x = int(w * 0.15)  # 15% padding for tighter blend
        padding_y = int(h * 0.15)
        
        x1 = max(0, int(x1) - padding_x)
        y1 = max(0, int(y1) - padding_y)
        x2 = min(base_image.width, int(x2) + padding_x)
        y2 = min(base_image.height, int(y2) + padding_y)
        
        # Draw white ellipse on mask (area to inpaint)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.ellipse([x1, y1, x2, y2], fill=255)
        
        print(f"[WebUI API] Pass 2: Inpainting main character face at bbox [{x1},{y1},{x2},{y2}]...")
        print(f"[WebUI API]   Found {len(faces)} face(s) originally — inpainting exactly 1 target face")
        
        # Prepare img2img inpainting payload with IP-Adapter
        image_b64 = self._image_to_base64(base_image)
        mask_b64 = self._image_to_base64(mask)
        # The ip-adapter_face_id_plus preprocessor has resolution=None, so it does NOT
        # resize the input before running InsightFace. On large/tall photos the face can
        # be too small relative to det_size=(640,640) and detection fails. Resize to
        # 512x512 to match what the WebUI frontend's Gradio canvas does automatically.
        resized_photo = self.user_photo.resize((512, 512), Image.LANCZOS)
        user_photo_b64 = self._image_to_base64(resized_photo)
        
        # ControlNet unit for face injection — user-tested optimal config
        controlnet_unit = {
            "enabled": True,
            "input_mode": "simple",
            "module": "ip-adapter_face_id_plus",
            "model": "ip-adapter-faceid-plusv2_sd15",
            "weight": 1.0,
            "image": user_photo_b64,
            "resize_mode": "Crop and Resize",
            "control_mode": "Balanced",
            "guidance_start": 0.2,
            "guidance_end": 0.8,
            # CRITICAL: When inpaint_full_res=True, ControlNet's try_crop_image_with_a1111_mask
            # will crop the reference image (user photo) to match the tiny inpaint mask area.
            # For small face bboxes this crops out the face entirely → "No face found".
            # Setting this to False tells ControlNet to always use the full user photo for
            # face embedding extraction, regardless of the inpaint mask region.
            "inpaint_crop_input_image": False,
        }
        
        # Build alwayson_scripts for inpainting
        alwayson_scripts = {
            "controlnet": {
                "args": [controlnet_unit]
            }
        }
        # ADetailer hand fixing is skipped here because it was already done in Pass 1!
        
        # Inpainting prompt reflects the actual user's gender for correct style bias
        # Inpainting prompt reflects user gender + extracted vision features
        gender_label = "man" if self.detected_gender == "male" else "woman"
        feature_str = f", {self.user_features}" if self.user_features else ""
        prompt = f"{gender_label}{feature_str}, <lora:{self.lora_name}:1>"
        
        from backend.utils.content_safety import ContentSafetyFilter
        safe_negative = ContentSafetyFilter.get_child_safe_negative_prompt()

        payload = {
            "init_images": [image_b64],
            "mask": mask_b64,
            "prompt": prompt,
            "negative_prompt": safe_negative,
            "steps": 30,
            "cfg_scale": 1.5,
            "width": 512,
            "height": 512,
            "sampler_name": "DPM++ 2M SDE Karras",
            "denoising_strength": 0.65, # Increased from 0.55 to allow more facial restructuring
            "inpainting_fill": 1,  # 1 = Original content
            "inpaint_full_res": True,
            "inpaint_full_res_padding": 32,
            "mask_blur": 8,
            "batch_size": 1,
            "n_iter": 1,
            "override_settings": {
                "CLIP_stop_at_last_layers": 1,
            },
            "alwayson_scripts": alwayson_scripts
        }
        
        try:
            response = requests.post(
                f"{self.webui_url}/sdapi/v1/img2img",
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            
            image_data = base64.b64decode(result['images'][0])
            final_image = Image.open(BytesIO(image_data))
            
            output_path = self.output_dir / filename
            final_image.save(output_path)
            print(f"[WebUI API] ✅ Main character face inpainted successfully")
            
            return str(output_path)
            
        except Exception as e:
            print(f"[WebUI API] ⚠️ Inpainting failed: {e} — returning base scene")
            output_path = self.output_dir / filename
            base_image.save(output_path)
            return str(output_path)
    
    def _generate_with_face(
        self,
        prompt_text: str,
        filename: str,
        use_base_image: Image.Image = None
    ) -> str:
        """
        Generate image WITH IP-Adapter FaceID (for single-character scenes).
        This is the optimized version of the original approach.
        
        Args:
            prompt_text: Scene description
            filename: Output filename
            use_base_image: Optional base image for img2img mode
            
        Returns:
            Path to generated image
        """
        # Prepare prompt matching user's successful UI test + extracted features
        gender_label = "woman" if self.detected_gender == "female" else "man"
        feature_str = f", {self.user_features}" if self.user_features else ""
        positive_prompt = f"{prompt_text}, {gender_label}{feature_str}, <lora:{self.lora_name}:1>"
        
        # The ip-adapter_face_id_plus preprocessor has resolution=None, so it does NOT
        # resize the input before running InsightFace. Resize to 512x512 to match what
        # the WebUI frontend's Gradio canvas does automatically.
        resized_photo = self.user_photo.resize((512, 512), Image.LANCZOS)
        user_photo_b64 = self._image_to_base64(resized_photo)
        
        # ControlNet unit — user-tested optimal: weight 1.0, guidance 0.2-0.8
        controlnet_unit = {
            "enabled": True,
            "input_mode": "simple",
            "module": "ip-adapter_face_id_plus",
            "model": "ip-adapter-faceid-plusv2_sd15",
            "weight": 1.0,
            "image": user_photo_b64,
            "resize_mode": "Crop and Resize",
            "control_mode": "Balanced",
            "guidance_start": 0.0,
            "guidance_end": 1.0,
            "pixel_perfect": True,
            "processor_res": 512,
        }
        
        # Build alwayson_scripts
        alwayson_scripts = {
            "controlnet": {
                "args": [controlnet_unit]
            }
        }
        adetailer_args = self._get_adetailer_args()
        alwayson_scripts.update(adetailer_args)
        
        from backend.utils.content_safety import ContentSafetyFilter
        safe_negative = ContentSafetyFilter.get_child_safe_negative_prompt()
        
        payload = {
            "prompt": positive_prompt,
            "negative_prompt": safe_negative,
            "steps": 30,
            "cfg_scale": 1.5,
            "width": 512,
            "height": 512,
            "sampler_name": "DPM++ 2M SDE Karras",
            "batch_size": 1,
            "n_iter": 1,
            "override_settings": {
                "CLIP_stop_at_last_layers": 1,
            },
            "alwayson_scripts": alwayson_scripts
        }
        
        print(f"[WebUI API] Generating with face injection (single-character mode)...")
        print(f"  - Steps: 30, CFG: 1.5, Sampler: DPM++ 2M SDE Karras")
        print(f"  - LoRA weight: 1.0, IP-Adapter weight: 1.0, Guidance: 0.2-0.8")
        
        try:
            response = requests.post(
                f"{self.webui_url}/sdapi/v1/txt2img",
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            
            image_data = base64.b64decode(result['images'][0])
            image = Image.open(BytesIO(image_data))
            
            output_path = self.output_dir / filename
            image.save(output_path)
            print(f"✅ Image saved: {output_path}")
            
            return str(output_path)
            
        except requests.exceptions.RequestException as e:
            print(f"[WebUI API] ❌ Request failed: {e}")
            raise
        except Exception as e:
            print(f"[WebUI API] ❌ Error: {e}")
            raise
    
    def _generate_without_face(self, prompt_text: str, filename: str) -> str:
        """
        Generate image WITHOUT IP-Adapter (for gender-mismatched scenes).
        Still uses ADetailer for quality.
        
        Args:
            prompt_text: Scene description
            filename: Output filename
            
        Returns:
            Path to generated image
        """
        print(f"[WebUI API] Generating WITHOUT face injection (gender mismatch or no main character)...")
        image, path = self._generate_base_scene(prompt_text, filename)
        return path
    
    def _condense_prompt(self, description: str, max_words: int = 15) -> str:
        """
        Use LLM to condense a long scene description into a short, visual-only
        SD-optimized prompt (max 15 words). This prevents CLIP token overflow
        which dilutes IP-Adapter FaceID likeness.
        
        Args:
            description: The original (potentially long) scene description
            max_words: Maximum words for the condensed prompt
            
        Returns:
            Short, visual-only prompt optimized for Stable Diffusion
        """
        words = description.split()
        if len(words) <= max_words:
            # Already short enough — no need to condense
            return description
        
        # CRITICAL: Only call LLM if it's currently running (avoid deadlocks during SD gen)
        if not OllamaManager.is_ollama_running():
            fallback = " ".join(words[:max_words])
            print(f"[WebUI API] ⚠️ Ollama is paused — skipping LLM condensation, using basic truncation: '{fallback}...'")
            return fallback

        print(f"[WebUI API] 📝 Condensing prompt ({len(words)} words → max {max_words} words)...")
        
        condense_prompt = f"""You are a Stable Diffusion prompt optimizer. Convert the following scene description into a SHORT visual prompt for AI image generation.

Rules:
- Output ONLY the condensed prompt, nothing else
- Maximum {max_words} words
- Focus on: character appearance, action, setting, mood
- Remove: dialogue, inner thoughts, story context, abstract concepts
- Use comma-separated visual tags
- Do NOT use quotes or explanations

Scene description: {description}

Short visual prompt:"""

        try:
            proc = subprocess.run(
                ["ollama", "run", IMAGE_PROMPT_CONDENSER_MODEL],
                input=condense_prompt.encode("utf-8"),
                capture_output=True,
                check=False,
                timeout=15,  # Quick timeout — this should be fast
            )
            if proc.returncode == 0:
                condensed = proc.stdout.decode("utf-8").strip()
                # Clean up any markdown or quotes the LLM might add
                condensed = condensed.strip('"\'`')
                condensed = condensed.replace("```", "").strip()
                # Remove any line that starts with explanation-like text
                lines = condensed.split('\n')
                condensed = lines[0].strip()  # Take only the first line
                
                # Safety: if the LLM returned something too long or empty, fallback
                condensed_words = condensed.split()
                if len(condensed_words) > max_words * 2:
                    condensed = " ".join(condensed_words[:max_words])
                if len(condensed) < 5:
                    raise ValueError("LLM returned empty/too-short result")
                
                print(f"[WebUI API] 📝 Condensed: '{condensed}'")
                return condensed
            else:
                raise RuntimeError(f"Ollama returned code {proc.returncode}")
                
        except Exception as e:
            # Fallback: simple truncation
            print(f"[WebUI API] ⚠️ Prompt condensation failed ({e}), using truncation")
            return " ".join(words[:max_words])

    def generate_personalized_image(
        self,
        prompt_text: str,
        filename: str = "personalized_output.png",
        scale: float = 1.0,
        num_inference_steps: int = 30,
        guidance_scale: float = 1.5,
        control_start: float = 0.2,
        control_end: float = 0.8,
        characters: list = None,
        main_character: str = "",
        condense: bool = True,
        **kwargs,
    ):
        """
        Generate personalized image using WebUI API with intelligent face application.
        
        Workflow:
        1. Condense long prompts via LLM for CLIP compatibility
        2. Check if face should be applied (gender match)
        3. If multi-character scene: two-pass (base scene → inpaint main character)
        4. If single-character scene: direct generation with IP-Adapter
        5. ADetailer auto-fixes hands
        
        Args:
            prompt_text: Text description
            filename: Output filename
            scale: IP-Adapter weight (1.0 default, user-tested optimal)
            num_inference_steps: Steps (30 default, user-tested optimal)
            guidance_scale: CFG scale (1.5 default, user-tested optimal)
            control_start: Start control at % (0.2 default)
            control_end: End control at % (0.8 default)
            characters: List of character names from the story
            main_character: Name of the main character
            
        Returns:
            Path to generated image
        """
        if self.user_photo is None:
            raise ValueError("User photo not set. Call set_user_photo() first.")
        
        # Step 0: Condense long prompts for better CLIP/FaceID compatibility
        if condense:
            prompt_text = self._condense_prompt(prompt_text)
        
        print(f"\n[WebUI API] ═══════════════════════════════════════")
        print(f"[WebUI API] Generating: '{prompt_text[:80]}...'")
        
        scene_num = kwargs.get("scene_number", 0) if "scene_number" in kwargs else 0
        cache = self.scene_analysis_cache.get(scene_num, {})
        
        apply_face = self.should_apply_face(prompt_text, main_character)
        
        if not apply_face:
            # Gender mismatch — generate without face injection
            return self._generate_without_face(prompt_text, filename)
        
        # Step 2: How many characters in this scene?
        char_count = cache.get("char_count")
        if char_count is None:
            char_count = self._count_characters_in_scene(prompt_text, char_names=characters)
        
        print(f"[WebUI API] Estimated characters in scene: {char_count}")
        
        if char_count >= 2:
            # Multi-character scene: two-pass approach
            print(f"[WebUI API] 🎭 Multi-character scene — using two-pass generation")
            
            # Pass 1: Generate base scene without face
            base_image, base_path = self._generate_base_scene(prompt_text, f"base_{filename}")
            
            # Pass 2: Inpaint only the main character's face
            final_path = self._inpaint_main_character_face(base_image, filename)
            
            # Clean up base image
            try:
                base_path_obj = Path(base_path)
                if base_path_obj.exists():
                    base_path_obj.unlink()
            except Exception:
                pass
            
            return final_path
        else:
            # Single-character scene: direct generation with face
            print(f"[WebUI API] 👤 Single-character scene — direct face injection")
            return self._generate_with_face(prompt_text, filename)