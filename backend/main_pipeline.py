# backend/main_pipeline.py
import json
from backend.agents.story_agent import StoryAgent
from backend.agents.image_agent import ImageAgent
from backend.agents.reviewer_agent import ReviewAgent


def run_pipeline(prompt: str):
    """
    Iteration 1 Pipeline:
    1. Generate a story (StoryAgent) -> (story_dict, status)
    2. Generate images (ImageAgent) -> (story_with_images, status)
    3. Review story (ReviewAgent) -> (final_story, status)
    """

    print("\n=== Step 1: StoryAgent ===")
    story_agent = StoryAgent(max_retries=2)
    story_dict, story_status = story_agent.generate_story(prompt)
    print("StoryAgent status:", story_status)

    print("\n=== Step 2: ImageAgent ===")
    image_agent = ImageAgent()
    # For faster test runs, ImageAgent.generate_images has first_only option inside it if needed.
    story_with_images, img_status = image_agent.generate_images(story_dict, first_only=True)
    print("ImageAgent status:", img_status)

    print("\n=== Step 3: ReviewAgent ===")
    review_agent = ReviewAgent(max_retries=2)
    final_story, review_status = review_agent.review_story(story_with_images)
    print("ReviewAgent status:", review_status)

    return final_story


if __name__ == "__main__":
    user_prompt = "Write a short story for kids about a curious cat exploring a magical garden."

    final_output = run_pipeline(user_prompt)

    print("\n=== Final Story JSON ===")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
