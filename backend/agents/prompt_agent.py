import re
import json

from backend.model_config import PROMPT_AGENT_MODEL
from backend.utils.bedrock_client import invoke_bedrock

class PromptAgent:
    def __init__(self, model=PROMPT_AGENT_MODEL):
        self.model = model

    def _ask_bedrock(self, prompt: str) -> str:
        """Call Amazon Bedrock (Claude Sonnet 4.5) for clean text output."""
        result = invoke_bedrock(
            prompt=prompt,
            system="You are a highly intelligent text classifier and enhancer for a children's story generator. Always respond with valid JSON only.",
            model_id=self.model,
            temperature=0.3,
        )
        if not result:
            return '{"type": "normal", "enhanced": ""}'
        return result

    def process_prompt(self, user_prompt: str):
        """Analyze and enhance user prompt intelligently."""
        # 🧩 Guard against empty input
        if not user_prompt or not user_prompt.strip():
            return None, "nonsense"

        # 🧩 Check obvious nonsense: only symbols, numbers, or URLs
        if re.fullmatch(r"[\d\W_]+", user_prompt.strip()) or "http" in user_prompt.lower():
            return None, "invalid"
        
        # ✅ Sanitize dangerous characters
        user_prompt = user_prompt.replace('"', "'")
        user_prompt = user_prompt.replace("{", "[")
        user_prompt = user_prompt.replace("}", "]")

        # 🧠 Step 1 — Build few-shot instruction for Ollama
        system_instruction = """
You are a highly intelligent text classifier and enhancer for a children's story generator.

Your task: classify the user's prompt into one of these categories:
- "short" → meaningful, very brief idea or phrase (3+ words) suitable for a story.
- "normal" → one or two clear sentences describing a story idea.
- "long" → more than 50 words, detailed description.
- "invalid" → URLs, gibberish, only numbers/symbols/special characters.
- "nonsense" → meaningless phrases (<3 words) with no context (like "notes", "asdf", etc).

Then, return a JSON object:
{
  "type": "short|normal|long|invalid|nonsense",
  "enhanced": "<meaningful rewritten prompt for story generation>"
}

 Enhancement rules:
- ALWAYS PRESERVE any **character names, locations, or objects** exactly as they appear in the original user prompt.
- If "short" and meaningful → expand into a vivid story idea **keeping all names and details**.
- If "long" → summarize to ~50 words while keeping all names and main ideas.
- If "nonsense" → return a default generic story theme prompt about kindness and imagination.
- If "invalid" → leave "enhanced" empty ("").
- Do NOT generate a full story — only an improved prompt.
- NEVER replace or rename characters or settings given by the user.

Examples:

User: "john and jack were playing cricket"
Response: {"type": "short", "enhanced": "John and Jack were playing cricket when something magical happened on their field."}

User: "boy and girl"
Response: {"type": "short", "enhanced": "A heartwarming story about a boy and girl learning friendship in a magical forest."}

User: "98217398"
Response: {"type": "invalid", "enhanced": ""}

User: "book on a"
Response: {"type": "short", "enhanced": "A mysterious book left on a bench leads a child into a magical world of secrets."}

User: "cat cat cat"
Response: {"type": "short", "enhanced": "A silly cat who thinks he's a tiger goes on a jungle adventure in the backyard."}

User: "()/@343,,,"
Response: {"type": "invalid", "enhanced": ""}

User: "(+=||\po,"
Response: {"type": "invalid", "enhanced": ""}

User: "https://google.com"
Response: {"type": "invalid", "enhanced": ""}

User: "notes"
Response: {"type": "nonsense", "enhanced": ""}

User: "A lonely astronaut exploring a forgotten planet with strange life forms."
Response: {"type": "normal", "enhanced": "A curious astronaut explores a forgotten planet full of mysterious life, discovering hope and wonder."}

User: "A very long detailed description ..."
Response: {"type": "long", "enhanced": "A concise 50-word summary preserving all character names and key details."}
"""

        ollama_prompt = f"""{system_instruction}

User prompt: "{user_prompt}"

Respond ONLY with valid JSON.
"""

        # 🧠 Step 2 & 3 — Query Bedrock and parse JSON safely
        try:
            raw_response = self._ask_bedrock(ollama_prompt)
            result = json.loads(raw_response, strict=False)
            prompt_type = result.get("type", "normal").lower()
            enhanced_prompt = result.get("enhanced", "").strip()

            # Fallback safety
            if not enhanced_prompt and prompt_type not in ["invalid", "nonsense"]:
                enhanced_prompt = user_prompt

            return enhanced_prompt, prompt_type

        except Exception as e:
            print(f"[PromptAgent Error] Bedrock failed: {e}")
            return user_prompt, "normal"
