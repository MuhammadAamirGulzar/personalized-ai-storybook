# backend/model_config.py
"""
CENTRALIZED MODEL CONFIGURATION
================================
Change any model name here and it will be used by the corresponding agent.
All agents import from this file instead of hardcoding model names.

DEPLOYMENT NOTE:
  - LLM inference is handled by Amazon Bedrock (Claude Sonnet 4.6).
  - Image generation is handled by Stable Diffusion WebUI running on AWS EC2.
  - WEBUI_URL is read from the WEBUI_URL environment variable so it can be
    updated in Render.com when the EC2 instance IP changes.
"""

import os

# ============================================
# LLM MODELS (Amazon Bedrock — Claude Sonnet 4.6)
# ============================================

# Bedrock cross-region inference profile for Claude Sonnet 4.6.
# To verify your exact model ID: AWS Console → Bedrock → Model access → copy Model ID.
BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-6"

PROMPT_AGENT_MODEL = BEDROCK_MODEL_ID            # PromptAgent: classifies & enhances user prompts
WRITER_AGENT_MODEL = BEDROCK_MODEL_ID            # WriterAgent: generates structured story JSON
CHATBOT_AGENT_MODEL = BEDROCK_MODEL_ID           # ChatbotAgent: character impersonation chatbot
IDEA_WORKSHOP_AGENT_MODEL = BEDROCK_MODEL_ID     # IdeaWorkshopAgent: story brainstorming assistant
DIRECTOR_AGENT_MODEL = BEDROCK_MODEL_ID          # DirectorAgent: orchestrates the pipeline (passes to sub-agents)
STORY_AGENT_MODEL = BEDROCK_MODEL_ID             # StoryAgent: facade for DirectorAgent
IMAGE_PROMPT_CONDENSER_MODEL = BEDROCK_MODEL_ID  # Condenses long scene descriptions into short SD prompts (main.py + personalized agent)
CHARACTER_COUNT_JUDGE_MODEL = BEDROCK_MODEL_ID   # LLM judge for counting characters in scenes (personalized agent)

# Vision model: Claude Sonnet 4.6 supports multimodal image inputs natively via Bedrock.
# No local Llava model needed. The same BEDROCK_MODEL_ID handles image + text together.
VISION_AGENT_MODEL = BEDROCK_MODEL_ID            # Used by personalized_image_agent to extract hair/skin/glasses features
ENABLE_VISION_FEATURES = True                     # Claude 4.6 handles vision — no local GPU needed

# ============================================
# IMAGE GENERATION (Stable Diffusion WebUI on AWS EC2)
# ============================================

# WEBUI_URL: set WEBUI_URL env var on Render to point to your EC2 instance IP.
# Example: http://54.123.45.67:7860
WEBUI_URL = os.getenv("WEBUI_URL", "http://127.0.0.1:7861")

SD_WEBUI_CHECKPOINT = "dreamshaper_8.safetensors"          # Checkpoint to use in WebUI
SD_CHECKPOINT_PATH = "backend/pretrained/dreamshaper_8.safetensors"  # Local SD model path (for diffusers ImageAgent fallback)
LORA_NAME = "ip-adapter-faceid-plusv2_sd15_lora"            # LoRA for IP-Adapter FaceID face consistency
IP_ADAPTER_BASE_MODEL = "SG161222/Realistic_Vision_V4.0_noVAE" # Used by ip_adapter_downloader
IP_ADAPTER_IMAGE_ENCODER = "openai/clip-vit-large-patch14" # Used by ip_adapter_downloader

# ============================================
# EVALUATION MODELS
# ============================================

EVAL_CLIP_MODEL = "openai/clip-vit-base-patch32"           # Used by EvaluationManager for image-text similarity
EVAL_SENTENCE_MODEL = "all-MiniLM-L6-v2"                   # Used by EvaluationManager for text coherence

# ============================================
# TTS / STT
# ============================================

TTS_DEFAULT_VOICE = "female"                       # Default TTS voice: "female" or "male"
STT_WHISPER_MODEL_SIZE = "base"                    # Whisper model size: "tiny", "base", "small", "medium", "large"
