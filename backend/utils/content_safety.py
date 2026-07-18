# backend/utils/content_safety.py
"""
Content Safety Utilities for Children's Storybook
Filters inappropriate content and ensures child-safe image generation
"""

import re
from typing import Tuple


class ContentSafetyFilter:
    """Filters and validates content for child safety"""
    
    # Explicit/inappropriate keywords to block
    BLOCKED_KEYWORDS = [
        # Explicit content
        'nude', 'naked', 'nsfw', 'explicit', 'sexual', 'sexy', 'erotic',
        'porn', 'xxx', 'adult', 'mature', 'provocative', 'seductive',
        'kissing', 'kissing lips', 'making out', 'romance', 'lovers', 'intimacy',
        'dating', 'boyfriend', 'girlfriend', 'valentines',
        # Violence
        'blood', 'gore', 'violent', 'brutal', 'murder', 'kill', 'death',
        'weapon', 'gun', 'knife', 'sword', 'fight', 'war', 'battle',
        # Inappropriate themes
        'drug', 'alcohol', 'cigarette', 'smoking', 'drinking',
        'horror', 'scary', 'terrifying', 'nightmare', 'demon', 'evil',
        # Deformity-related
        'deformed', 'mutated', 'grotesque', 'disfigured', 'distorted',
    ]
    
    # Warning keywords (allowed but need stronger negative prompts)
    WARNING_KEYWORDS = [
        'monster', 'creature', 'beast', 'dragon', 'witch', 'ghost',
        'dark', 'shadow', 'night', 'mysterious',
    ]
    
    @staticmethod
    def filter_prompt(prompt: str) -> Tuple[str, bool, str]:
        """
        Filter prompt for inappropriate content
        
        Returns:
            (filtered_prompt, is_safe, warning_message)
        """
        prompt_lower = prompt.lower()
        
        # Check for blocked keywords
        for keyword in ContentSafetyFilter.BLOCKED_KEYWORDS:
            if keyword in prompt_lower:
                return (
                    "",
                    False,
                    f"Prompt contains inappropriate content: '{keyword}'. Please use child-friendly descriptions."
                )
        
        # Check for warning keywords
        needs_extra_safety = False
        for keyword in ContentSafetyFilter.WARNING_KEYWORDS:
            if keyword in prompt_lower:
                needs_extra_safety = True
                break
        
        # Clean up prompt (don't modify it - let IP-Adapter work naturally)
        filtered = prompt.strip()
        
        # Safety is enforced through negative prompts, not by modifying the positive prompt
        # This preserves facial likeness while still blocking inappropriate content
        
        return (filtered, True, "extra_safety" if needs_extra_safety else "")
    
    @staticmethod
    def get_child_safe_negative_prompt(extra_safety: bool = False, include_style_blocks: bool = True) -> str:
        """
        Get comprehensive negative prompt for child-safe image generation.
        
        Args:
            extra_safety: If True, adds extra negative prompts for darker themes
            include_style_blocks: If True, adds blocks to keep the style clean
        """
        # 1. THE SAFETY CORE - Strictly blocks what NOT to draw (Always Active)
        safety_blocks = (
            # Explicit content (Stronger romance blockers)
            "nsfw, nude, naked, explicit, sexual, adult content, mature, provocative, "
            "suggestive, revealing clothing, kissing, romance, romantic, dating, "
            "intimacy, lovers, making out, "
            # Violence & scary
            "blood, gore, violence, weapon, gun, knife, sword, scary, horror, terrifying, "
            "nightmare, demon, evil, dark magic, "
            # Inappropriate themes
            "drugs, alcohol, smoking, cigarette, beer, wine, "
            "disturbing, creepy, unsettling"
        )

        # 2. THE QUALITY & ANATOMY CORE (Always Active)
        quality_blocks = (
            "(worst quality, low quality:1.4), (low resolution, blurry:1.2), "
            "(bad anatomy, bad hands:1.3), "
            "(missing fingers, extra digit, fewer digits, fused fingers, mutated hands:1.3), "
            "deformed, disfigured, mutated, mutation, extra limbs, missing limbs, "
            "bad proportions, gross proportions, malformed limbs, "
            "extra arms, extra legs, missing arms, missing legs, "
            "poorly drawn hands, poorly drawn face, "
            "ugly, duplicate, morbid, mutilated, mutated hands, "
            "cloned face, malformed, cross-eyed, lazy eye, asymmetric eyes, "
            "distorted facial features, jpeg artifacts, watermark, signature, text, error, "
            "EasyNegative, badhandv4"
        )
        
        combined = f"{safety_blocks}, {quality_blocks}"

        if extra_safety:
            # Add extra negatives for darker themes (monsters, etc.)
            extra_negative = (
                "monster, creature, beast, witch, ghost, zombie, skeleton, "
                "darkness, shadows, night scene, gloomy, ominous, threatening, "
                "sinister, menacing, aggressive"
            )
            combined += f", {extra_negative}"
        
        return combined

    @staticmethod
    def get_child_safe_positive_additions() -> str:
        """Get positive prompt additions to encourage child-friendly content (Optional Style)"""
        return (
            "child-friendly, wholesome, innocent, cheerful, happy, bright colors, "
            "safe for children, age-appropriate, family-friendly, cute, adorable, "
            "joyful, playful, colorful, vibrant, clean, pure"
        )
    
    @staticmethod
    def get_likeness_safe_positive_additions() -> str:
        """Get positive prompt additions that preserve facial likeness (Recommended for Personalized)"""
        return "vivid colors, masterpiece, clean lines, high quality, sharp focus, clear features"

    @staticmethod
    def validate_scene_description(description: str) -> Tuple[bool, str]:
        """Validate a scene description for child safety"""
        _, is_safe, warning = ContentSafetyFilter.filter_prompt(description)
        if not is_safe:
            return False, warning
        if len(description.split()) > 100:
            return False, "Scene description too complex. Please simplify."
        return True, ""


def enhance_prompt_for_children(prompt: str, mode: str = "simple") -> Tuple[str, str, bool]:
    """
    Enhance prompt for child-safe image generation.
    
    Args:
        prompt: The user's input/scene description
        mode: "simple" (adds cute style) or "personalized" (keeps likeness priority)
    
    Returns:
        (enhanced_positive_prompt, negative_prompt, is_safe)
    """
    filtered_prompt, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
    if not is_safe:
        return "", "", False
    
    # Select positive additions based on mode
    if mode == "personalized":
        # Keep it descriptive but clear. Avoid "babying" keywords that break FaceID.
        positive_additions = ContentSafetyFilter.get_likeness_safe_positive_additions()
    else:
        # Standard mode - can be more artistic/wholesome
        positive_additions = ContentSafetyFilter.get_child_safe_positive_additions()
    
    enhanced_positive = f"{positive_additions}, {filtered_prompt}"
    
    # Negative prompt always includes strict safety blocks
    extra_safety = (warning == "extra_safety")
    negative_prompt = ContentSafetyFilter.get_child_safe_negative_prompt(extra_safety)
    
    return enhanced_positive, negative_prompt, True
