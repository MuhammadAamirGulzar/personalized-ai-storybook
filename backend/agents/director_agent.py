# backend/agents/director_agent.py
from typing import Dict, Any
from backend.agents.prompt_agent import PromptAgent
from backend.agents.writer_agent import WriterAgent
from backend.agents.reviewer_agent import ReviewerAgent
from backend.agents.editor_agent import EditorAgent
from backend.agents.image_agent import ImageAgent
from backend.model_config import DIRECTOR_AGENT_MODEL


class DirectorAgent:
    """
    DirectorAgent orchestrates the pipeline:
      PromptAgent -> WriterAgent -> (optional ImageAgent) -> ReviewerAgent -> EditorAgent
    """

    def __init__(self, llm_model: str = DIRECTOR_AGENT_MODEL, writer_max_scenes: int = 3, genre: str = "Fantasy"):
        self.prompt_agent = PromptAgent(model=llm_model)
        self.writer = WriterAgent(llm_model=llm_model, max_retries=2, max_scenes=writer_max_scenes, genre=genre)
        self.reviewer = ReviewerAgent()
        self.editor = EditorAgent()
        # ImageAgent instantiated only when images requested

    def create_story(self, user_prompt: str, generate_images: bool = False) -> Dict[str, Any]:
        # Step 0 - prompt handling (PromptAgent already enriches/validates)
        enhanced_prompt, prompt_type = self.prompt_agent.process_prompt(user_prompt)
        if prompt_type in ["invalid", "nonsense"]:
            raise ValueError("Invalid or nonsense prompt provided")

        # --- Dictionary to store intermediate outputs ---
        agent_outputs = {}

        # Step 1 - write story
        story_dict, write_status = self.writer.generate_story(enhanced_prompt)
        agent_outputs["writer"] = story_dict.copy()  # Save writer's draft

        # Step 2 - images (optional)
        image_status = "skipped"
        if generate_images:
            image_agent = ImageAgent()
            # Note: Image generation logic is handled in main.py, this is a placeholder
            # story_dict, image_status = image_agent.generate_images(story_dict)

        # Step 3 - review
        story_after_review, review_status = self.reviewer.review_story(story_dict)
        agent_outputs["reviewer"] = story_after_review.copy() # Save reviewer's output

        # Step 4 - edit/package
        final_story, edit_status = self.editor.edit_story(story_after_review)
        agent_outputs["editor"] = final_story.copy() # Save editor's final version

        # attach meta
        final_story.setdefault("meta", {})
        final_story["meta"].update({"prompt_type": prompt_type, "enhanced_prompt": enhanced_prompt})

        # Final response
        response = {
            "status": {"write": write_status, "image": image_status, "review": review_status, "edit": edit_status},
            "outputs": agent_outputs, # Include all intermediate outputs
            "story": final_story,
        }
        return response