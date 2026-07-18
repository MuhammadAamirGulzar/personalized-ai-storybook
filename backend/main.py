# main.py
import os
import uvicorn
import json
import re
import time
import traceback
import torch
import subprocess
import sys
from fastapi import FastAPI, Request, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.agents.editor_agent import export_pdf
from PIL import Image as PILImage

# --- Import Agents ---
from backend.agents.prompt_agent import PromptAgent
from backend.agents.story_agent import StoryAgent
from backend.agents.image_agent import ImageAgent
from backend.agents.chatbot_agent import ChatbotAgent
from backend.utils.tts_manager import get_tts_manager
from backend.utils.evaluation_manager import get_evaluation_manager
from backend.utils.ollama_manager import OllamaManager
from backend.model_config import IMAGE_PROMPT_CONDENSER_MODEL

# Feature flag for LangChain Workshop Agent
USE_LANGCHAIN_WORKSHOP = True  # Set to False to use original implementation

if USE_LANGCHAIN_WORKSHOP:
    try:
        from backend.agents.idea_workshop_agent_langchain import IdeaWorkshopAgentLangChain as IdeaWorkshopAgent
        print("✅ Using LangChain Workshop Agent (Advanced Conversation Rules)")
    except ImportError as e:
        print(f"⚠️ LangChain Workshop Agent not available, falling back to original: {e}")
        from backend.agents.idea_workshop_agent import IdeaWorkshopAgent
else:
    from backend.agents.idea_workshop_agent import IdeaWorkshopAgent

# Personalized Image Agent using WebUI Local API (Perfect Results)
try:
    from backend.agents.personalized_image_agent_webui_api import PersonalizedImageAgentWebUIAPI as PersonalizedImageAgent
    PERSONALIZED_AGENT_AVAILABLE = True
    print("✅ Using WebUI Local API - Perfect Results (requires WebUI running)")
except ImportError as e:
    print(f"⚠️  WebUI API agent not available: {e}")
    print("⚠️  Falling back to standalone IP-Adapter")
    try:
        from backend.agents.personalized_image_agent import PersonalizedImageAgent
        PERSONALIZED_AGENT_AVAILABLE = True
        print("✅ Using Standalone IP-Adapter")
    except ImportError:
        PERSONALIZED_AGENT_AVAILABLE = False
# ReviewerAgent is now only called inside DirectorAgent
# from backend.agents.reviewer_agent import ReviewerAgent

# --- Import Auth ---
from backend.auth.routes import router as auth_router
from backend.auth.database import engine, Base, get_db
from backend.auth.dependencies import get_current_user_optional, get_current_user
from backend.auth.models import User
from backend.auth.db_models import Story, ChatConversation, ChatMessage, WorkshopSession, WorkshopMessage, WorkshopStory
from sqlalchemy.orm import Session

# -------------------
# Utility: Device info
# -------------------
def get_device_info():
    if torch.cuda.is_available():
        return {"device": "cuda", "name": torch.cuda.get_device_name(0)}
    else:
        return {"device": "cpu"}

# -------------------------
# Helper: Safe filename gen
# -------------------------
def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    name = re.sub(r"[-\s]+", "_", name)
    return name

# -------------------------
# Helper: Save agent output
# -------------------------
def save_agent_output(agent_name: str, title: str, timestamp: int, data: dict):
    safe_title = sanitize_filename(title or "untitled_story")
    dir_map = {
        "prompt": os.path.join(GENERATED_DIR, "prompts"),
        "writer": os.path.join(GENERATED_DIR, "drafts"),
        "reviewer": os.path.join(GENERATED_DIR, "reviews"),
        "editor": os.path.join(GENERATED_DIR, "edits"),
        "story": os.path.join(GENERATED_DIR, "stories")
    }
    out_dir = dir_map.get(agent_name)
    if not out_dir:
        print(f"⚠️ Unknown agent type: {agent_name}")
        return
    os.makedirs(out_dir, exist_ok=True)
    filename = f"{safe_title}_{agent_name}_{timestamp}.json"
    filepath = os.path.join(out_dir, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {agent_name} output to {filepath}")
    except Exception as e:
        print(f"❌ Failed to save {agent_name} output: {e}")

# -------------------------
# FastAPI app setup
# -------------------------
app = FastAPI(title="Storybook FYP - Unified Pipeline")

# Clear GPU cache on startup (simple approach)
try:
    if torch.cuda.is_available():
        print("🧹 Clearing GPU cache on startup...")
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        print("✅ GPU cache cleared")
except Exception as e:
    print(f"⚠️ Could not clear GPU cache: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def cloud_passthrough_middleware(request: Request, call_next):
    """Cloud mode: No local Ollama to manage. LLM calls go directly to Amazon Bedrock."""
    response = await call_next(request)
    return response


# Generated directories
BASE_DIR = os.path.dirname(__file__)
GENERATED_DIR = os.path.join(BASE_DIR, "..", "generated")
IMAGES_DIR = os.path.join(GENERATED_DIR, "images")
STORIES_DIR = os.path.join(GENERATED_DIR, "stories")
AUDIO_DIR = os.path.join(GENERATED_DIR, "audio")

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(STORIES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

@app.on_event("startup")
def startup_event():
    """Cloud deployment startup — Bedrock handles LLM, EC2 handles image generation."""
    print("🚀 Backend starting up in CLOUD mode (Amazon Bedrock + EC2 WebUI)...")
    print(f"🌐 LLM: Amazon Bedrock (Claude Sonnet 4.6)")
    from backend.model_config import WEBUI_URL
    print(f"🎨 Image Generation: Stable Diffusion WebUI at {WEBUI_URL}")

# Serve generated static files
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# Initialize database tables (lazy initialization with error handling)
def init_database():
    """Initialize database tables if connection is available"""
    try:
        # Import all models to ensure they're registered
        from backend.auth.db_models import Story, ChatConversation, ChatMessage, WorkshopSession, WorkshopMessage, WorkshopStory
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables initialized successfully (including Story, Chat, and Workshop tables)")
    except Exception as e:
        print(f"⚠️ Warning: Could not initialize database: {e}")
        print("⚠️ Authentication features will not be available until database is configured.")
        print("⚠️ To fix: Set DATABASE_URL environment variable or configure PostgreSQL connection.")

# Try to initialize database, but don't fail if it's not available
init_database()

# Include auth routes
app.include_router(auth_router)

# -------------------------
# Routes
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(BASE_DIR, "static", "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse("<h2>Index page not found. Please ensure backend/static/index.html exists.</h2>")
    return FileResponse(index_path)

@app.get("/device")
async def device():
    return get_device_info()

# -------------------------
# Face Detection Endpoint
# -------------------------
@app.post("/api/check-face")
async def api_check_face(request: Request):
    """
    Lightweight face detection check on an uploaded photo.
    Called by the frontend immediately after the user uploads their photo.
    Returns whether a face was detected, so the UI can warn + offer re-upload.
    """
    import base64
    import io
    body = await request.json()
    image_data = body.get("image")
    if not image_data:
        raise HTTPException(status_code=400, detail="Missing 'image' field")

    try:
        # Decode base64 → PIL
        raw = image_data.split(',')[1] if ',' in image_data else image_data
        photo_bytes = base64.b64decode(raw)
        photo = PILImage.open(io.BytesIO(photo_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    if not PERSONALIZED_AGENT_AVAILABLE:
        # Optimistic fallback: assume face present if we can't check
        return {"face_detected": True, "confidence": 1.0, "gender": None}

    try:
        checker = PersonalizedImageAgent()
        result = checker.check_face_in_image(photo)
        
        # Free memory immediately after check!
        if hasattr(checker, 'cleanup'):
            try:
                checker.cleanup()
            except Exception:
                pass
        del checker
        import gc
        gc.collect()
        
        return result
    except Exception as e:
        print(f"⚠️ /api/check-face error: {e}")
        # Don't block the user — return optimistic default
        return {"face_detected": True, "confidence": 0.0, "gender": None}


# -------------------------
# Main generation endpoint
# -------------------------
@app.post("/api/generate")

async def api_generate(
    request: Request, 
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    body = await request.json()
    prompt = body.get("prompt")
    generate_images = body.get("generate_images", True)
    use_personalized = body.get("use_personalized_images", False)
    user_photo_data = body.get("user_photo")  # Base64 encoded image
    extract_visual_features = body.get("extract_visual_features", False)  # Dynamic Vision AI toggle
    use_first_frame_as_reference = body.get("use_first_frame_as_reference", False)  # "Continue Anyway" fallback
    mode = body.get("mode", "simple")  # 'simple' or 'personalized'
    genre = body.get("genre", "Fantasy")  # Story genre
    num_pages = body.get("num_pages", 3)  # Number of pages/scenes (1-5)
    timestamp = int(time.time())


    # Validate num_pages (cap at 6)
    if not isinstance(num_pages, int) or num_pages < 3:
        num_pages = 3
    num_pages = min(num_pages, 6)  # Cap at 6 pages

    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' in request body.")
    
    # Check if user is authenticated for image generation
    if generate_images and current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login to generate images. Guest users can only create text stories."
        )

    # --- Memory Clearance: Auto-clear VRAM & RAM before text generation ---
    print("🧹 Preparing memory for text generation...")
    try:
        import requests
        # Attempt to aggressively unload WebUI checkpoints from VRAM AND RAM
        for port in [7860, 7861]:
            try:
                # Force WebUI to dump cached checkpoints from System RAM (not just VRAM)
                # and dump ControlNet from VRAM
                requests.post(
                    f"http://127.0.0.1:{port}/sdapi/v1/options", 
                    json={
                        "control_net_model_cache_size": 0,
                        "sd_checkpoint_cache": 0
                    }, 
                    timeout=10
                )
                
                # Unload active base checkpoint
                requests.post(f"http://127.0.0.1:{port}/sdapi/v1/unload-checkpoint", timeout=10)
                print(f"🧹 Successfully requested WebUI (port {port}) to dump all models from VRAM and RAM")
            except Exception as e:
                print(f"⚠️ WebUI flush timed out/failed on port {port}: {e}")
                pass
    except Exception as e:
        print(f"⚠️ Could not unload WebUI models: {e}")
        
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            print("🧹 Cleared PyTorch GPU cache before text generation")
    except Exception:
        pass

    import gc
    gc.collect()

    # --- Step 1: PromptAgent ---
    prompt_agent = PromptAgent()
    processed_prompt, prompt_type = prompt_agent.process_prompt(prompt)
    prompt_data = {
        "original_prompt": prompt,
        "prompt_type": prompt_type,
        "enhanced_prompt": processed_prompt,
        "genre": genre,
        "num_pages": num_pages
    }
    save_agent_output("prompt", f"prompt_{timestamp}", timestamp, prompt_data)

    if prompt_type in ["invalid", "nonsense"]:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Your prompt appears invalid or meaningless. Please enter a more meaningful idea."},
        )

    # --- Step 2: StoryAgent (runs the full Writer -> Reviewer -> Editor pipeline) ---
    story_agent = StoryAgent(writer_max_scenes=num_pages, genre=genre)
    try:
        # result now contains 'story', 'outputs', and 'status'
        result, story_status = story_agent.generate_story(processed_prompt, generate_images=False)
        final_story = result.get("story", {})
        agent_outputs = result.get("outputs", {})
        story_title = final_story.get("title", "untitled_story")

        # --- Save all intermediate agent outputs ---
        for agent_name, output_data in agent_outputs.items():
            save_agent_output(agent_name, story_title, timestamp, output_data)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Story generation failed: {e}")

    # --- Step 2.5: Inject Genre Styling & Condense image prompts (while Ollama is still running) ---
    if generate_images:
        print(f"📝 Preparing image prompts with '{genre}' styling...")
        style_map = {
            "Fantasy": "soft watercolor illustration, whimsical atmosphere, clean lines, storybook aesthetic",
            "Fairy Tale": "enchanted world, gentle pastel colors, storybook style, high-detail painterly",
            "Adventure": "vibrant 2D cartoon, bold outlines, expressive, high contrast, flat vector art",
            "Sci-Fi": "stylized 3D render, Pixar-inspired, smooth textures, bright colors, clean shapes"
        }
        genre_style = style_map.get(genre, "beautifully illustrated children's storybook style")

        import subprocess
        for scene in final_story.get("scenes", []):
            description = scene.get("image_description") or scene.get("text", "")
            
            # Optimization: If it's already a short, clean prompt, don't call the LLM again.
            # Just append the style tag directly.
            words = description.split()
            if len(words) <= 12:
                scene["image_description"] = f"{description}, {genre_style}"
                print(f"  📝 Scene {scene.get('scene_number', '?')} (Stylized): '{scene['image_description']}'")
                continue

            # If it's long, use Ollama to fuse the style and content into something concise (< 15-20 words)
            full_description_with_style = f"{description}, {genre_style}"
            
            try:
                condense_request = f"""You are a Stable Diffusion prompt optimizer. Convert the following scene description into a SHORT visual prompt.

Rules:
- Output ONLY the condensed prompt, nothing else
- Maximum 20 words
- Keep the style keywords: {genre_style}
- Focus on: character appearance, action, setting
- Use comma-separated visual tags

Description: {full_description_with_style}

Short visual prompt:"""
                from backend.utils.bedrock_client import invoke_bedrock
                condensed = invoke_bedrock(
                    prompt=condense_request,
                    system="You are an image prompt optimizer. Output ONLY the condensed visual prompt, nothing else.",
                    model_id=IMAGE_PROMPT_CONDENSER_MODEL,
                    temperature=0.3,
                    max_tokens=100,
                )
                if condensed:
                    condensed = condensed.strip('"\' `').replace("```", "").strip()
                    condensed = condensed.split('\n')[0].strip()
                    if len(condensed) >= 5:
                        scene["image_description"] = condensed
                        print(f"  📝 Scene {scene.get('scene_number', '?')} (Condensed): '{condensed}'")
                        continue
            except Exception as e:
                print(f"  ⚠️ Condensation failed for scene {scene.get('scene_number', '?')}: {e}")
            
            # Fallback
            scene["image_description"] = " ".join(words[:20]) + f", {genre_style}"
            print(f"  📝 Scene {scene.get('scene_number', '?')} (Fallback): '{scene['image_description']}'")

    # --- Step 3: ImageAgent (if enabled) ---
    image_status = "Images not generated."
    if generate_images:
        try:
            print("🖼 Starting image generation...")
            try:
                # Determine which image agent to use
                use_personal_agent = (
                    use_personalized and
                    user_photo_data and
                    PERSONALIZED_AGENT_AVAILABLE
                )
                
                # --- OVERARCHING PRE-ANALYSIS BEFORE OLLAMA PAUSES ---
                # We must count characters using the LLM before Ollama goes offline
                global_scene_analysis_cache = {}
                story_characters = final_story.get("characters", [])
                main_character = story_characters[0] if story_characters else ""
                
                if PERSONALIZED_AGENT_AVAILABLE:
                    print("🧠 Pre-analyzing scenes for character counts while LLM is active...")
                    try:
                        pre_analyzer = PersonalizedImageAgent()
                        pre_analyzer.analyze_story_scenes(
                            scenes=final_story.get("scenes", []),
                            characters=story_characters,
                            main_character=main_character
                        )
                        global_scene_analysis_cache = pre_analyzer.scene_analysis_cache
                        del pre_analyzer
                    except Exception as e:
                        print(f"⚠️ Pre-analysis failed: {e}")

                # Pause Ollama to free GPU memory for faster image generation
                from backend.utils.ollama_manager import OllamaManager
                ollama_was_running = OllamaManager.pause_ollama()

                if use_personal_agent:
                    print("🎭 Using PersonalizedImageAgent with user photo...")

                    import base64
                    import io
                    try:
                        photo_bytes = base64.b64decode(user_photo_data.split(',')[1] if ',' in user_photo_data else user_photo_data)
                        user_photo = PILImage.open(io.BytesIO(photo_bytes)).convert("RGB")

                        # Initialize PersonalizedImageAgent
                        from backend.model_config import ENABLE_VISION_FEATURES
                        image_agent = PersonalizedImageAgent()
                        image_agent.set_user_photo(user_photo, use_vision=ENABLE_VISION_FEATURES)
                        # Inject pre-computed character counts so we avoid hitting paused Ollama
                        image_agent.scene_analysis_cache = global_scene_analysis_cache

                        print(f"🎭 Main character: '{main_character}', All characters: {story_characters}")

                        # --- Memory Clearance: Auto-reload VRAM for Image Generation ---
                        print("🧹 Preparing memory for image generation by reloading WebUI models...")
                        try:
                            import requests
                            for port in [7860, 7861]:
                                try:
                                    requests.post(f"http://127.0.0.1:{port}/sdapi/v1/reload-checkpoint", timeout=30)
                                    print(f"🧹 Successfully requested WebUI (port {port}) to reload models into VRAM")
                                except:
                                    pass
                        except Exception as e:
                            print(f"⚠️ Could not reload WebUI models: {e}")

                        scenes = final_story.get("scenes", [])
                        first_frame_reference_set = False
    
                        for scene in scenes:
                            description = scene.get("image_description") or scene.get("text", "")
                            # Style already injected in Step 2.5
                            scene_number = scene.get("scene_number", 0)
                            filename = f"{sanitize_filename(story_title)}_{timestamp}_scene_{scene_number}.png"
    
                            # --- "Continue Anyway" mode ---
                            # If user's photo had no face, generate scenes without reference
                            # until we find a face, then extract it for all subsequent scenes!
                            if use_first_frame_as_reference and not first_frame_reference_set:
                                print(f"🖼 [first-frame mode] Generating Scene {scene_number} without face reference (searching for a face)...")
                                # Temporarily clear user_photo so no face is injected for this scene
                                temp_photo = image_agent.user_photo
                                image_agent.user_photo = None
                                image_path = image_agent._generate_without_face(description, filename)
                                image_agent.user_photo = temp_photo
                                scene["image_path"] = image_path
    
                                # Attempt to extract face from CURRENT Scene for use in subsequent scenes
                                try:
                                    scene_pil = PILImage.open(image_path).convert("RGB")
                                    if image_agent.set_first_frame_reference(scene_pil):
                                        first_frame_reference_set = True
                                        print(f"✅ [first-frame mode] Face extracted from Scene {scene_number} — will use for remaining scenes")
                                    else:
                                        print(f"⚠️ [first-frame mode] No face found in Scene {scene_number} — will try again next scene")
                                except Exception as ex:
                                    print(f"⚠️ [first-frame mode] Could not extract face from Scene {scene_number}: {ex}")
                                continue  # Scene already saved
    
                            print(f"Generating personalized image for scene {scene_number}...")
                            image_path = image_agent.generate_personalized_image(
                                prompt_text=description,
                                filename=filename,
                                characters=story_characters,
                                main_character=main_character,
                                scene_number=scene_number,
                                condense=False
                            )
                            scene["image_path"] = image_path
    
                        image_status = "Personalized images generated successfully! 🎭✅"
    
                    except Exception as e:
                        print(f"❌ Personalized generation failed: {e}")
                        print("Falling back to standard image generation...")
                        use_personal_agent = False
                    finally:
                        # Clean up personalized agent to free memory
                        if 'image_agent' in dir() and hasattr(image_agent, 'cleanup'):
                            try:
                                image_agent.cleanup()
                            except Exception:
                                pass

                if not use_personal_agent:
                    # Standard / simple mode generation
                    if PERSONALIZED_AGENT_AVAILABLE:
                        print("🖼 Using WebUI for standard generation (ensuring resource consistency)...")
                        image_agent = PersonalizedImageAgent()
                        # Inject pre-computed character counts
                        image_agent.scene_analysis_cache = global_scene_analysis_cache
                        
                        # Fix Device Mismatch Error: Reload WebUI models before starting simple mode
                        print("🧹 Reloading WebUI models for simple mode generation...")
                        try:
                            import requests
                            for port in [7860, 7861]:
                                try:
                                    requests.post(f"http://127.0.0.1:{port}/sdapi/v1/reload-checkpoint", timeout=30)
                                    print(f"🧹 Successfully requested WebUI (port {port}) to reload models into VRAM")
                                except: pass
                        except: pass
                    else:
                        print("🖼 Using local diffusers ImageAgent...")
                        image_agent = ImageAgent()

                    scenes = final_story.get("scenes", [])
                    consistency_agent = None
                    reference_face_found = False
                    
                    # For simple mode, if we're using WebUI, we don't need a separate consistency_agent instance
                    # we can just use the SAME image_agent we just created!
                    if PERSONALIZED_AGENT_AVAILABLE:
                        consistency_agent = image_agent
                        # Set default character attributes since we are using WebUI agent manually
                        consistency_agent.main_character = main_character
                        consistency_agent.all_characters = story_characters

                    for idx, scene in enumerate(scenes):
                        description = scene.get("image_description") or scene.get("text", "")
                        # Style already injected in Step 2.5
                        words = description.split()
                        if len(words) > 70:
                            description = " ".join(words[:70])
                            print(f"[Safety] ⚠️ Truncated long image prompt for scene {scene.get('scene_number', '?')}")
    
                        scene_number = scene.get("scene_number", 0)
                        filename = f"{sanitize_filename(story_title)}_{timestamp}_scene_{scene_number}.png"
    
                        # If we already found a face in an earlier scene, generate this one with consistency agent
                        if reference_face_found and consistency_agent:
                            print(f"🎭 [simple mode] Generating scene {scene_number} with character consistency...")
                            try:
                                # We already injected character into consistency_agent above if it's WebUI
                                image_path = consistency_agent.generate_personalized_image(
                                    prompt_text=description,
                                    filename=filename,
                                    characters=story_characters,
                                    main_character=main_character,
                                    scene_number=scene_number,
                                    condense=False
                                )
                                scene["image_path"] = image_path
                                continue # Done with this scene!
                            except Exception as e:
                                print(f"⚠️ Consistency gen failed for scene {scene_number}: {e} — falling back to standard gen")
                                # Fall through to standard generation
    
                        # Standard generation (either it's before we found a face, or consistency failed)
                        print(f"Generating image for scene {scene_number} (standard mode)...")
                        if PERSONALIZED_AGENT_AVAILABLE:
                            # Use WebUI's non-face injection method to match Scene 1 quality with Scene 2
                            image_path = image_agent._generate_without_face(description, filename)
                        else:
                            # Use local diffusers agent
                            image_path = image_agent.generate_image(prompt_text=description, filename=filename)
                        
                        scene["image_path"] = image_path
    
                        # If we haven't found a face yet, try to extract one from this newly generated standard image
                        if not reference_face_found and PERSONALIZED_AGENT_AVAILABLE and idx < len(scenes) - 1:
                            try:
                                scene_pil = PILImage.open(image_path).convert("RGB")
                                # If it's WebUI, our image_agent IS the consistency agent, so we just set reference on it!
                                if image_agent.set_first_frame_reference(scene_pil):
                                    reference_face_found = True
                                    print(f"✅ [simple mode] Face extracted from Scene {scene_number} — will use for remaining scenes")
                                else:
                                    print(f"ℹ️ [simple mode] No face found in Scene {scene_number} — will try again next scene")
                            except Exception as e:
                                print(f"⚠️ [simple mode] Face extraction attempt failed: {e}")
    
                    if consistency_agent and hasattr(consistency_agent, 'cleanup'):
                        try:
                            consistency_agent.cleanup()
                        except:
                            pass
    
                    image_status = "Images generated successfully. ✅"


            
            finally:
                # Unload WebUI models from VRAM AND RAM to free GPU and System memory
                try:
                    import requests as req
                    for port in [7860, 7861]:
                        try:
                            # Force WebUI to dump cached checkpoints from System RAM and VRAM
                            req.post(
                                f"http://127.0.0.1:{port}/sdapi/v1/options", 
                                json={
                                    "control_net_model_cache_size": 0,
                                    "sd_checkpoint_cache": 0
                                }, 
                                timeout=10
                            )
                            req.post(f"http://127.0.0.1:{port}/sdapi/v1/unload-checkpoint", timeout=10)
                        except Exception as e:
                            print(f"⚠️ WebUI flush timed out/failed on port {port}: {e}")
                            pass
                    print("🧹 WebUI base models AND ControlNet cache fully unloaded from VRAM and System RAM")

                except Exception:
                    pass
                
                # Clear GPU memory
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
                except Exception:
                    pass
                
                import gc
                gc.collect()
                print("🧹 GPU memory cleaned after image generation")
                
                # Resume Ollama after image generation
                if ollama_was_running:
                    OllamaManager.resume_ollama()
                
        except Exception as e:
            traceback.print_exc()
            image_status = f"❌ Image generation failed: {e}"

    # --- Step 4: PDF Export ---
    safe_title = sanitize_filename(final_story.get("title", "untitled_story"))
    pdf_filename = f"{safe_title}_{timestamp}.pdf"
    pdf_path = export_pdf(final_story, pdf_filename)
    print(f"📘 Final PDF available at: {pdf_path}")

    # --- Step 5: Add image URLs for frontend ---
    for scene in final_story.get("scenes", []):
        path = scene.get("image_path")
        if generate_images and path:
            fname = os.path.basename(path)
            scene["image_url"] = f"/generated/images/{fname}"
        else:
            scene["image_url"] = None

    # --- Step 6: Save final story JSON ---
    save_agent_output("story", story_title, timestamp, final_story)

    # --- Step 7: Save final story JSON (inject mode for evaluation agent) ---
    final_story["mode"] = mode  # Used by evaluation_agent.py to determine character consistency checks
    STORIES_DIR = os.path.join(GENERATED_DIR, "stories")
    os.makedirs(STORIES_DIR, exist_ok=True)
    story_file = os.path.join(STORIES_DIR, f"{safe_title}_{timestamp}.json")
    with open(story_file, "w", encoding="utf-8") as f:
        json.dump(final_story, f, indent=2, ensure_ascii=False)
    print(f"✅ Story saved successfully at {story_file}")

    # --- Save story to database ---
    story_id = None
    try:
        db_story = Story(
            user_id=current_user.id if current_user else None,
            title=story_title,
            mode=mode,
            story_data=final_story
        )
        db.add(db_story)
        db.commit()
        db.refresh(db_story)
        story_id = db_story.id
        print(f"✅ Story saved to database with ID: {story_id}")
    except Exception as e:
        print(f"⚠️ Warning: Failed to save story to database: {e}")
        db.rollback()

    # -----------------------------------------------------------------
    # --- TRIGGER EVALUATION AGENT IN THE BACKGROUND ---
    # -----------------------------------------------------------------
    try:
        evaluator_script_path = os.path.join(BASE_DIR, "agents", "evaluation_agent.py")
        if os.path.exists(evaluator_script_path):
            print(f"🚀 Kicking off background evaluation for Story ID {story_id}...")
            # Pass story_file and story_id to the evaluator
            import subprocess as subp
            command = [sys.executable, evaluator_script_path, story_file, str(story_id or 0)]
            subp.Popen(command)
        else:
            print(f"⚠ Warning: Evaluation agent script not found at {evaluator_script_path}")
    except Exception as e:
        print(f"❌ Failed to start evaluation agent process: {e}")

    # -----------------------------------------------------------------
    # --- TRIGGER BACKGROUND TTS PRE-GENERATION (default voice) ---
    # -----------------------------------------------------------------
    try:
        if story_id and final_story and final_story.get("scenes"):
            import threading
            def _pregenerate_tts(sid, scenes_data):
                """Pre-generate TTS audio for all scenes using the default voice."""
                try:
                    tts = get_tts_manager()
                    default_voice = "female"
                    for scene in scenes_data:
                        scene_num = scene.get("scene_number")
                        text = scene.get("text", "")
                        if text and scene_num:
                            tts.generate_audio(text, sid, scene_num, default_voice)
                    print(f"🔊 Background TTS pre-generation complete for story {sid} ({len(scenes_data)} scenes)")
                except Exception as tts_err:
                    print(f"⚠️ Background TTS pre-generation failed: {tts_err}")

            tts_thread = threading.Thread(
                target=_pregenerate_tts,
                args=(story_id, final_story["scenes"]),
                daemon=True
            )
            tts_thread.start()
            print(f"🔊 Background TTS pre-generation started for story {story_id}...")
    except Exception as e:
        print(f"⚠️ Could not start background TTS: {e}")

    # --- Final combined status ---
    status_msg = image_status or story_status

    # Clear GPU cache before returning
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            print("🧹 GPU cache cleared after story generation")
    except Exception as e:
        print(f"⚠️ Could not clear GPU cache: {e}")

    return JSONResponse({
        "status": status_msg, 
        "story": final_story,
        "story_id": story_id  # Return story ID for chat reference
    })


# -------------------------
# Evaluation endpoints
# -------------------------
@app.post("/api/stories/{story_id}/evaluate")
async def evaluate_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluate an existing story manually.
    """
    # Fetch story from DB
    db_story = db.query(Story).filter(Story.id == story_id).first()
    if not db_story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    # Check ownership
    if db_story.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to evaluate this story")
        
    story_data = db_story.story_data
    
    # Get image paths from story_data
    image_paths = []
    for scene in story_data.get("scenes", []):
        img_url = scene.get("image_url")
        if img_url and img_url.startswith("/generated/images/"):
            filename = img_url.split("/")[-1]
            img_path = os.path.join(IMAGES_DIR, filename)
            if os.path.exists(img_path):
                image_paths.append(img_path)
    
    # Run evaluation
    try:
        eval_manager = get_evaluation_manager()
        results = eval_manager.evaluate_story(
            story_id=story_id,
            story_dict=story_data,
            image_paths=image_paths,
            mode=db_story.mode or "simple"
        )
        return results
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e}")

@app.get("/api/stories/{story_id}/evaluation")
async def get_story_evaluation(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get existing evaluation results for a story.
    """
    # Fetch story from DB to check permission
    db_story = db.query(Story).filter(Story.id == story_id).first()
    if not db_story:
        raise HTTPException(status_code=404, detail="Story not found")
        
    if db_story.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to view this evaluation")
        
    # Check if evaluation file exists
    eval_file = os.path.join(GENERATED_DIR, "evaluations", f"story_{story_id}_evaluation.json")
    if not os.path.exists(eval_file):
        raise HTTPException(status_code=404, detail="Evaluation not found for this story")
        
    with open(eval_file, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------
# Chatbot endpoints
# -------------------------
@app.post("/api/chat")
async def api_chat(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Handle character chatbot conversations (STATELESS - no conversation history saved)
    Request body: {story_id, character_name, user_message}
    """
    try:
        body = await request.json()
        story_id = body.get("story_id")
        character_name = body.get("character_name")
        user_message = body.get("user_message")
        
        # Validation
        if not story_id or not character_name or not user_message:
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields: story_id, character_name, user_message"
            )
        
        # Load story from database
        db_story = db.query(Story).filter(Story.id == story_id).first()
        if not db_story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        story_data = db_story.story_data
        
        # Validate character exists in story
        characters = story_data.get("characters", [])
        if character_name not in characters:
            raise HTTPException(
                status_code=400,
                detail=f"Character '{character_name}' not found in story. Available: {characters}"
            )
        
        # Generate response using ChatbotAgent (no conversation history)
        chatbot = ChatbotAgent(story_data, character_name)
        character_response = chatbot.chat(user_message)
        
        # Return response without saving anything to database
        return JSONResponse({
            "response": character_response,
            "character": character_name
        })
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")




# -------------------------
# Idea Workshop endpoints
# -------------------------
@app.post("/api/workshop/start")
async def start_workshop(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Start a new workshop session
    Request body: {mode: 'improvement' | 'new_idea'}
    """
    try:
        body = await request.json()
        mode = body.get("mode")
        
        if mode not in ['improvement', 'new_idea']:
            raise HTTPException(status_code=400, detail="Mode must be 'improvement' or 'new_idea'")
        
        # Create new session
        session = WorkshopSession(
            user_id=current_user.id if current_user else None,
            mode=mode,
            status='active'
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Generate initial message based on mode
        if mode == 'improvement':
            initial_message = "Welcome to Story Improvement Mode! Please paste your story below (maximum 300 words)."
        else:
            initial_message = "Welcome to New Idea Mode! Tell me about your story idea, and I'll help you build it!"
        
        # Save initial assistant message
        initial_msg = WorkshopMessage(
            session_id=session.id,
            role='assistant',
            message=initial_message
        )
        db.add(initial_msg)
        db.commit()
        
        return JSONResponse({
            "session_id": session.id,
            "mode": mode,
            "initial_message": initial_message
        })
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error starting workshop: {str(e)}")


@app.post("/api/workshop/chat")
async def workshop_chat(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Handle workshop conversation
    Request body: {session_id, user_message}
    """
    try:
        body = await request.json()
        session_id = body.get("session_id")
        user_message = body.get("user_message")
        
        if not session_id or not user_message:
            raise HTTPException(status_code=400, detail="Missing session_id or user_message")
        
        # Load session
        session = db.query(WorkshopSession).filter(WorkshopSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Load conversation history
        messages = db.query(WorkshopMessage).filter(
            WorkshopMessage.session_id == session_id
        ).order_by(WorkshopMessage.created_at).all()
        
        history = [{
            "role": msg.role,
            "message": msg.message,
            "metadata": msg.message_metadata or {}
        } for msg in messages]
        
        # Create agent and process message
        agent = IdeaWorkshopAgent(session.mode, history)
        response, metadata = agent.process_message(user_message)
        
        # CRITICAL FIX: Save metadata on USER message too (not just assistant)
        # This allows the next agent instance to find requirements from history
        user_msg = WorkshopMessage(
            session_id=session_id,
            role='user',
            message=user_message,
            message_metadata=metadata  # Save extracted requirements
        )
        db.add(user_msg)
        db.commit()
        
        # Save assistant response
        assistant_msg = WorkshopMessage(
            session_id=session_id,
            role='assistant',
            message=response,
            message_metadata=metadata
        )
        db.add(assistant_msg)
        db.commit()
        
        # Check if ready to generate
        ready_to_generate = agent.should_generate_story(user_message)
        
        return JSONResponse({
            "response": response,
            "ready_to_generate": ready_to_generate,
            "metadata": metadata
        })
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Workshop chat error: {str(e)}")


@app.get("/api/workshop/history/{session_id}")
async def get_workshop_history(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    Load full workshop conversation history
    """
    try:
        # Load session
        session = db.query(WorkshopSession).filter(WorkshopSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Load messages
        messages = db.query(WorkshopMessage).filter(
            WorkshopMessage.session_id == session_id
        ).order_by(WorkshopMessage.created_at).all()
        
        # Load stories if any
        stories = db.query(WorkshopStory).filter(
            WorkshopStory.session_id == session_id
        ).order_by(WorkshopStory.version).all()
        
        return JSONResponse({
            "session_id": session_id,
            "mode": session.mode,
            "status": session.status,
            "messages": [{
                "role": msg.role,
                "message": msg.message,
                "metadata": msg.message_metadata,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            } for msg in messages],
            "stories": [{
                "version": story.version,
                "story_text": story.story_text,
                "created_at": story.created_at.isoformat() if story.created_at else None
            } for story in stories]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error loading history: {str(e)}")


@app.post("/api/workshop/generate")
async def generate_workshop_story(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate story from workshop session
    Request body: {session_id}
    """
    try:
        body = await request.json()
        session_id = body.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session_id")
        
        # Load session
        session = db.query(WorkshopSession).filter(WorkshopSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Load conversation history
        messages = db.query(WorkshopMessage).filter(
            WorkshopMessage.session_id == session_id
        ).order_by(WorkshopMessage.created_at).all()
        
        history = [{
            "role": msg.role,
            "message": msg.message,
            "metadata": msg.message_metadata or {}
        } for msg in messages]
        
        # Create agent and generate story
        agent = IdeaWorkshopAgent(session.mode, history)
        story_text = agent.generate_story()
        
        # Get current version
        existing_stories = db.query(WorkshopStory).filter(
            WorkshopStory.session_id == session_id
        ).order_by(WorkshopStory.version.desc()).first()
        
        next_version = (existing_stories.version + 1) if existing_stories else 1
        
        # Save generated story
        workshop_story = WorkshopStory(
            session_id=session_id,
            version=next_version,
            story_text=story_text,
            user_story_text=agent.user_story  # For improvement mode
        )
        db.add(workshop_story)
        db.commit()
        db.refresh(workshop_story)
        
        return JSONResponse({
            "story_text": story_text,
            "version": next_version,
            "story_id": workshop_story.id
        })
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Story generation error: {str(e)}")


# -------------------------
# Workshop Library endpoints  (separate from Simple/Personalized story library)
# -------------------------

@app.post("/api/workshop/save")
async def save_workshop_story(
    request: Request,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Mark a generated workshop story as 'loved' by the user.
    Request body: { story_id, story_text, mode, session_id }
    """
    try:
        body = await request.json()
        story_id = body.get("story_id")
        story_text = body.get("story_text", "")
        mode = body.get("mode", "new_idea")
        session_id = body.get("session_id")

        print(f"[Workshop Save] story_id={story_id}, session_id={session_id}, user={current_user.id if current_user else 'guest'}, mode={mode}")

        # Generate a short title from the first non-empty line
        first_line = next((line.strip() for line in story_text.split("\n") if line.strip()), "Workshop Story")
        title = first_line[:60] + ("..." if len(first_line) > 60 else "")

        ws = None

        # 1. Look up by story_id (the row created by /api/workshop/generate)
        if story_id:
            ws = db.query(WorkshopStory).filter(WorkshopStory.id == story_id).first()
            print(f"[Workshop Save] Found by story_id: {ws is not None}")

        # 2. Fallback: find the latest story for this session
        if ws is None and session_id:
            ws = db.query(WorkshopStory).filter(
                WorkshopStory.session_id == session_id
            ).order_by(WorkshopStory.created_at.desc()).first()
            print(f"[Workshop Save] Found by session_id fallback: {ws is not None}")

        if ws is not None:
            ws.saved_by_user = True
            ws.user_id = current_user.id if current_user else None
            ws.title = title
            ws.mode = mode
            db.commit()
            db.refresh(ws)
            print(f"[Workshop Save] Saved successfully. library_id={ws.id}")
            return JSONResponse({"saved": True, "library_id": ws.id, "title": title})

        # 3. Last resort: create a brand new row only if we have a valid session
        if session_id:
            session = db.query(WorkshopSession).filter(WorkshopSession.id == session_id).first()
            if session:
                ws = WorkshopStory(
                    session_id=session_id,
                    user_id=current_user.id if current_user else None,
                    version=1,
                    story_text=story_text,
                    title=title,
                    mode=mode,
                    saved_by_user=True
                )
                db.add(ws)
                db.commit()
                db.refresh(ws)
                print(f"[Workshop Save] Created new row. library_id={ws.id}")
                return JSONResponse({"saved": True, "library_id": ws.id, "title": title})

        print("[Workshop Save] ERROR: Could not find or create a WorkshopStory row.")
        raise HTTPException(status_code=400, detail="Could not save story: session or story not found.")

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving workshop story: {str(e)}")


@app.get("/api/workshop/saved")
async def list_saved_workshop_stories(
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    List workshop library stories for the current user (saved_by_user=True only).
    Completely separate from /api/stories.
    """
    if not current_user:
        return JSONResponse([])
    try:
        saved = db.query(WorkshopStory).filter(
            WorkshopStory.user_id == current_user.id,
            WorkshopStory.saved_by_user.is_(True)
        ).order_by(WorkshopStory.created_at.desc()).all()

        print(f"[Workshop Saved] user={current_user.id}, found {len(saved)} stories")

        return JSONResponse([{
            "id": s.id,
            "title": s.title or "Untitled Workshop Story",
            "mode": s.mode or "workshop",
            "story_text": s.story_text,
            "created_at": s.created_at.isoformat() if s.created_at else None
        } for s in saved])
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing workshop library: {str(e)}")


# -------------------------
# Story History endpoints
# -------------------------
@app.get("/api/stories")
async def list_stories(
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    List all stories for the current user
    """
    if not current_user:
        return JSONResponse([])
    
    try:
        stories = db.query(Story).filter(Story.user_id == current_user.id).order_by(Story.created_at.desc()).all()
        
        return JSONResponse([{
            "id": s.id,
            "title": s.title,
            "mode": s.mode,
            "created_at": s.created_at.isoformat() if s.created_at else None
        } for s in stories])
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing stories: {str(e)}")


@app.get("/api/stories/{story_id}")
async def get_story_detail(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full story data for a specific story
    """
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
            
        # Require authentication and verify ownership
        if story.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this story"
            )
        
        return JSONResponse({
            "id": story.id,
            "title": story.title,
            "mode": story.mode,
            "story_data": story.story_data,
            "created_at": story.created_at.isoformat() if story.created_at else None
        })
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving story: {str(e)}")


@app.get("/api/stories/{story_id}/download")
async def download_story_pdf(
    story_id: int,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Generate and download the PDF for a specific story.
    """
    try:
        story = db.query(Story).filter(Story.id == story_id).first()
        
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
            
        # Optional: Check ownership
        if story.user_id and (not current_user or story.user_id != current_user.id):
             raise HTTPException(status_code=403, detail="You do not have permission to download this story")
        
        # Regenerate PDF to ensure it has the latest styling/content
        story_data = story.story_data
        safe_title = sanitize_filename(story.title or "untitled_story")
        timestamp = int(time.time())
        pdf_filename = f"{safe_title}_{timestamp}.pdf"
        
        pdf_path = export_pdf(story_data, pdf_filename)
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="Failed to generate PDF")
            
        return FileResponse(
            path=pdf_path,
            filename=pdf_filename,
            media_type="application/pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")


# -------------------------
# TTS Audio Download (ZIP)
# -------------------------
@app.get("/api/stories/{story_id}/download-audio")
async def download_audio(
    story_id: int,
    voice: str = "female",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download all TTS audio files for a story as a ZIP archive.
    Generates audio if not already cached.
    """
    import zipfile
    
    try:
        # Fetch story from DB
        db_story = db.query(Story).filter(Story.id == story_id).first()
        if not db_story:
            raise HTTPException(status_code=404, detail="Story not found")
        
        if db_story.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to download this audio")
        
        story_data = db_story.story_data
        scenes = story_data.get("scenes", [])
        
        if not scenes:
            raise HTTPException(status_code=400, detail="Story has no scenes")
        
        # Generate TTS for all scenes
        tts_manager = get_tts_manager()
        audio_files = []
        
        for scene in scenes:
            scene_num = scene.get("scene_number")
            text = scene.get("text", "")
            if text and scene_num:
                audio_url = tts_manager.generate_audio(text, story_id, scene_num, voice)
                # audio_url is like /generated/audio/story_X_scene_Y_voice.wav
                audio_filename = os.path.basename(audio_url)
                audio_path = os.path.join(AUDIO_DIR, audio_filename)
                if os.path.exists(audio_path):
                    audio_files.append((audio_path, f"scene_{scene_num}_{voice}.wav"))
        
        if not audio_files:
            raise HTTPException(status_code=404, detail="No audio files could be generated")
        
        # Create ZIP file
        safe_title = sanitize_filename(story_data.get("title", "untitled"))
        zip_filename = f"{safe_title}_audio_{voice}.zip"
        zip_path = os.path.join(GENERATED_DIR, "exports", zip_filename)
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for audio_path, archive_name in audio_files:
                zf.write(audio_path, archive_name)
        
        print(f"🔊 Created audio ZIP: {zip_path} ({len(audio_files)} files)")
        
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Audio download error: {str(e)}")


# -------------------------
# TTS endpoints
# -------------------------
@app.get("/api/tts/{story_id}/{scene_number}")
async def api_tts(
    story_id: int,
    scene_number: int,
    voice: str = "female",
    db: Session = Depends(get_db)
):
    """
    Generate or get cached audio for a specific scene
    """
    try:
        # Load story from database
        story = db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
            
        story_data = story.story_data
        scenes = story_data.get("scenes", [])
        
        # Find the requested scene
        target_scene = None
        for scene in scenes:
            if scene.get("scene_number") == scene_number:
                target_scene = scene
                break
                
        if not target_scene:
            raise HTTPException(status_code=404, detail=f"Scene {scene_number} not found in story")
            
        text = target_scene.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Scene has no text to synthesize")
            
        # Generate audio
        tts_manager = get_tts_manager()
        audio_url = tts_manager.generate_audio(text, story_id, scene_number, voice)
        
        return JSONResponse({
            "story_id": story_id,
            "scene_number": scene_number,
            "voice": voice,
            "audio_url": audio_url
        })
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


# -------------------------
# STT (Speech-to-Text) endpoint
# -------------------------
@app.post("/api/stt")
async def api_stt(
    audio: UploadFile = File(...),
    language: str = "en"
):
    """
    Transcribe audio to text using Whisper (offline)
    Accepts: audio file (wav, mp3, webm, etc.)
    Returns: {"text": "transcribed text", "language": "en"}
    """
    try:
        from backend.utils.stt_manager import get_stt_manager
        
        # Read audio bytes
        audio_bytes = await audio.read()
        
        # Get STT manager and transcribe
        stt_manager = get_stt_manager()
        result = stt_manager.transcribe_audio_bytes(audio_bytes, language)
        
        return JSONResponse({
            "text": result["text"],
            "language": result["language"]
        })
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
