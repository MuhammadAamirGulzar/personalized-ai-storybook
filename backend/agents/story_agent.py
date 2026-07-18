# backend/agents/story_agent.py
from typing import Dict, Any, Tuple
from backend.agents.director_agent import DirectorAgent
from backend.model_config import STORY_AGENT_MODEL


class StoryAgent:
    """
    StoryAgent facade kept for backward compatibility.
    It delegates to DirectorAgent (multi-agent pipeline).
    """

    def __init__(self, llm_model: str = STORY_AGENT_MODEL, writer_max_scenes: int = 3, max_retries: int = 2, genre: str = "Fantasy"):
        self.director = DirectorAgent(llm_model=llm_model, writer_max_scenes=writer_max_scenes, genre=genre)
        self.max_retries = max_retries

    def generate_story(self, prompt: str, generate_images: bool = False) -> Tuple[Dict[str, Any], str]:
        # Director now returns a dictionary with story, status, and intermediate outputs
        result = self.director.create_story(prompt, generate_images=generate_images)
        
        status = result.get("status", {})
        
        # Format a friendly status string
        if isinstance(status, dict):
            status_str = " | ".join(f"{k}:{v}" for k, v in status.items())
        else:
            status_str = str(status)
            
        # Return the entire result dictionary, not just the story
        return result, status_str