# backend/agents/reviewer_agent.py
import re
from typing import Dict, Tuple
from backend.models.story_schema import Story


class ReviewerAgent:
    """
    ReviewerAgent: lightweight checks + per-scene metrics
    """

    def __init__(self, min_words_per_scene: int = 40):
        self.min_words_per_scene = min_words_per_scene

    def _count_words(self, text: str) -> int:
        return len(re.findall(r"\w+", text or ""))

    def _validate_schema(self, story_dict: Dict) -> Tuple[bool, str]:
        try:
            Story(**story_dict)
            return True, "schema_ok"
        except Exception as e:
            return False, f"schema_error: {str(e)}"

    def review_story(self, story_dict: Dict) -> Tuple[Dict, str]:
        valid, msg = self._validate_schema(story_dict)
        if not valid:
            return story_dict, f"Review failed: {msg}"

        story = Story(**story_dict)

        per_scene = {}
        for scene in story.scenes:
            sn = scene.scene_number
            wc = self._count_words(scene.text or "")
            per_scene[sn] = {
                "scene_number": sn,
                "word_count": wc,
                "length_score": min(1.0, wc / max(1, self.min_words_per_scene)),
                "has_image": bool(scene.image_description or scene.image_path),
            }

        n = len(per_scene) or 1
        overall = {
            "avg_length_score": round(sum(p["length_score"] for p in per_scene.values()) / n, 3),
            "image_coverage": round(sum(1 for p in per_scene.values() if p["has_image"]) / n, 3),
        }

        story_out = story.model_dump()
        story_out["consistency_report"] = {"per_scene": per_scene, "overall": overall}
        status = "approved" if overall["avg_length_score"] >= 0.5 else "needs_improvement"

        return story_out, f"Review complete: {status}"
