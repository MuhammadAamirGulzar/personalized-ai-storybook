import json
from typing import Dict, Any, Tuple, Optional

from backend.models.story_schema import Story
from backend.model_config import WRITER_AGENT_MODEL
from backend.utils.bedrock_client import invoke_bedrock


class WriterAgent:
    """
    WriterAgent
    - Calls Ollama to produce a structured story JSON.
    - Ensures short, visual `image_description` prompts for compatibility with CLIP (≤77 tokens).
    - Validates with Story pydantic model.
    """

    def __init__(
        self,
        llm_model: str = WRITER_AGENT_MODEL,
        max_retries: int = 2,
        max_scenes: Optional[int] = 3,
        genre: str = "Fantasy",
    ):
        self.llm_model = llm_model
        self.max_retries = max_retries
        self.max_scenes = max_scenes
        self.genre = genre

    def _ask_bedrock(self, prompt: str) -> str:
        """Call Amazon Bedrock (Claude Sonnet 4.5) for clean text output."""
        result = invoke_bedrock(
            prompt=prompt,
            system="You are a professional children's story writer. Always respond with valid JSON only. No markdown, no commentary.",
            model_id=self.llm_model,
            temperature=0.7,
            max_tokens=8192,
        )
        if not result:
            raise RuntimeError("Bedrock returned an empty response")
        return result


    def _build_system_prompt(self, max_scenes: int, genre: str) -> str:
        # Define story structure based on page count
        structure_map = {
            3: "Scene 1: Beginning (introduction), Scene 2: Climax (main conflict/action), Scene 3: Ending (resolution)",
            4: "Scene 1: Beginning (introduction), Scene 2: Rising Action, Scene 3: Climax (peak conflict), Scene 4: Ending (resolution)",
            5: "Scene 1: Beginning (introduction), Scene 2: Rising Action, Scene 3: Climax (peak conflict), Scene 4: Falling Action, Scene 5: Ending (resolution)",
            6: "Scene 1: Beginning (introduction), Scene 2: Rising Action, Scene 3: First Obstacle, Scene 4: Climax (peak conflict), Scene 5: Falling Action, Scene 6: Ending (resolution)",
        }
        structure = structure_map.get(max_scenes, structure_map[4])  # fallback to 4-scene
        
        return f"""
You are a professional children's story writer and illustrator prompt designer.

Your task:
Generate a COMPLETE story as a **VALID JSON object** using the following schema:

{{
  "title": "<string>",
  "setting": "<string>",
  "characters": ["name1","name2"],
  "scenes": [
    {{
      "scene_number": 1,
      "text": "<string - full page paragraph>",
      "image_description": "<short, vivid visual prompt for AI image generation>"
    }}
  ]
}}

Rules:
- **GENRE**: Write the story in the **{genre}** genre. Make sure the tone, themes, and style match this genre.
- Limit scenes to EXACTLY {max_scenes} scenes (one scene per page).
- **STORY STRUCTURE** (CRITICAL): Follow this exact structure for {max_scenes} pages:
  {structure}
  
- **Beginning**: Introduce characters, setting, and initial situation
- **Climax**: The most exciting/important moment with the main conflict or challenge
- **Ending**: Resolve the story with a satisfying conclusion
- **AGE-APPROPRIATE**: The story MUST be wholesome and suitable for young children. Strictly NO romance, kissing, dating, violence, or scary themes.

- **IMPORTANT**: Each scene's "text" MUST be a FULL PAGE of content - at least 8-12 sentences long (150-200 words per scene). Include rich descriptions, character emotions, dialogue, and engaging storytelling. Make each page feel complete and immersive for children ages 7-10.
- Each scene's "image_description" must be a **single short descriptive phrase (max 15 words)** focusing on visual elements only:
  ✅ Describe what should appear visually (characters, actions, setting, emotions, colors).
  🚫 Do NOT include inner thoughts, dialogue, or long storytelling.
  🚫 Do NOT exceed one concise sentence.
- Example of a good image_description:
  - "Two boys building a small treehouse under bright sunlight, surrounded by green leaves and laughter"
  - "A happy dog and a child playing hide and seek behind a large oak tree"
- Output ONLY valid JSON. No markdown, no commentary, no backticks.
"""

    def generate_story(self, enhanced_prompt: str) -> Tuple[Dict[str, Any], str]:
        """Generate story JSON using Ollama and validate via Story model."""
        last_raw = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                system_prompt = self._build_system_prompt(self.max_scenes or 3, self.genre)
                full_prompt = (
                    f"{system_prompt}\nUser prompt: {enhanced_prompt}\n\nRespond with JSON only."
                )
                raw = self._ask_bedrock(full_prompt)
                last_raw = raw

                # Remove accidental markdown fences (handles ```json, ```JSON, preamble text, etc.)
                # First: if there's a JSON block anywhere, extract it
                if "```" in raw:
                    parts = raw.split("```")
                    for p in parts:
                        stripped = p.strip()
                        # Skip the language tag (e.g. "json") that may prefix the block
                        if stripped.lower().startswith("json"):
                            stripped = stripped[4:].strip()
                        if stripped.startswith("{"):
                            raw = stripped
                            break
                    else:
                        raw = raw.replace("```", "")
                # If no fences but there's preamble text before the JSON object
                elif not raw.startswith("{"):
                    brace_idx = raw.find("{")
                    if brace_idx != -1:
                        raw = raw[brace_idx:]

                # Parse JSON with strict=False to allow control characters
                # (LLMs word-wrap output at ~76 chars, inserting literal \n inside strings)
                story_dict = json.loads(raw, strict=False)

                # Truncate excessive scenes if needed
                if self.max_scenes and "scenes" in story_dict:
                    story_dict["scenes"] = story_dict["scenes"][: self.max_scenes]

                # Safety filter: truncate overly long image prompts
                for scene in story_dict.get("scenes", []):
                    if "image_description" in scene and isinstance(scene["image_description"], str):
                        words = scene["image_description"].split()
                        if len(words) > 20:
                            scene["image_description"] = " ".join(words[:20])

                # Validate schema
                _ = Story(**story_dict)

                return story_dict, f"Story generated ✅ ({len(story_dict.get('scenes', []))} scenes)"

            except Exception as e:
                print(f"[WriterAgent] ⚠️ Attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt >= self.max_retries:
                    raise ValueError(
                        f"WriterAgent failed after {self.max_retries} attempts. "
                        f"Last raw output:\n{last_raw}\n\nError: {e}"
                    )
                print(f"[WriterAgent] 🔄 Retrying...")

        return {}, "Failed to generate story"
