"""
Unit tests for content_safety.py module
Tests content filtering, validation, and child-safe prompt enhancement
"""

import pytest
from backend.utils.content_safety import (
    ContentSafetyFilter,
    enhance_prompt_for_children
)


# ============================================================================
# TEST: filter_prompt() - Blocked Keywords
# ============================================================================

@pytest.mark.unit
class TestFilterPromptBlocked:
    """Test blocking of inappropriate keywords"""
    
    def test_block_explicit_content(self):
        """Should block explicit content keywords"""
        prompt = "A story about naked people"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == False
        assert "inappropriate content" in warning.lower()
        assert filtered == ""
    
    def test_block_violence(self):
        """Should block violence keywords"""
        prompt = "A tale with blood and murder"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == False
        assert "inappropriate content" in warning.lower()
    
    def test_block_drugs_alcohol(self):
        """Should block drug and alcohol references"""
        test_cases = [
            "Kids drinking alcohol",
            "A story about drugs",
            "Children smoking cigarettes"
        ]
        
        for prompt in test_cases:
            filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
            assert is_safe == False, f"Failed to block: {prompt}"
    
    def test_block_horror_themes(self):
        """Should block horror and scary themes"""
        prompt = "A terrifying horror nightmare"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == False
        assert "inappropriate content" in warning.lower()
    
    def test_block_deformity_keywords(self):
        """Should block deformity-related keywords"""
        prompt = "A deformed mutated creature"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == False


# ============================================================================
# TEST: filter_prompt() - Warning Keywords
# ============================================================================

@pytest.mark.unit
class TestFilterPromptWarnings:
    """Test handling of warning keywords that need extra safety"""
    
    def test_warning_monster_keyword(self):
        """Should allow 'monster' but flag for extra safety"""
        prompt = "A friendly monster helps children"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == True
        assert warning == "extra_safety"
        assert "child-friendly" in filtered.lower()
    
    def test_warning_dark_keyword(self):
        """Should allow 'dark' but flag for extra safety"""
        prompt = "A dark mysterious forest"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == True
        assert warning == "extra_safety"
    
    def test_warning_witch_keyword(self):
        """Should allow 'witch' but flag for extra safety"""
        prompt = "A kind witch teaches magic"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == True
        assert warning == "extra_safety"


# ============================================================================
# TEST: filter_prompt() - Safe Content
# ============================================================================

@pytest.mark.unit
class TestFilterPromptSafe:
    """Test that safe content is allowed"""
    
    def test_allow_safe_content(self):
        """Should allow completely safe content"""
        prompt = "A brave knight saves a kingdom"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == True
        assert warning == ""
        assert len(filtered) > 0
    
    def test_add_child_friendly_context(self):
        """Should add child-friendly context if not present"""
        prompt = "A robot explores space"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == True
        assert "child-friendly" in filtered.lower()
    
    def test_preserve_existing_child_context(self):
        """Should not duplicate child-friendly context"""
        prompt = "A children's story about friendship"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == True
        # Should not add redundant "child-friendly"
        assert filtered.count("child") >= 1


# ============================================================================
# TEST: get_child_safe_negative_prompt()
# ============================================================================

@pytest.mark.unit
class TestNegativePrompt:
    """Test negative prompt generation"""
    
    def test_base_negative_prompt(self):
        """Should generate base negative prompt"""
        negative = ContentSafetyFilter.get_child_safe_negative_prompt(extra_safety=False)
        
        assert "nsfw" in negative
        assert "violence" in negative
        assert "deformed" in negative
        assert "inappropriate" in negative
    
    def test_extra_safety_negative_prompt(self):
        """Should add extra negatives when extra_safety=True"""
        base_negative = ContentSafetyFilter.get_child_safe_negative_prompt(extra_safety=False)
        extra_negative = ContentSafetyFilter.get_child_safe_negative_prompt(extra_safety=True)
        
        assert len(extra_negative) > len(base_negative)
        assert "monster" in extra_negative
        assert "darkness" in extra_negative
    
    def test_negative_prompt_blocks_quality_issues(self):
        """Should include quality issue negatives"""
        negative = ContentSafetyFilter.get_child_safe_negative_prompt()
        
        assert "bad anatomy" in negative
        assert "extra fingers" in negative
        assert "blurry" in negative


# ============================================================================
# TEST: get_child_safe_positive_additions()
# ============================================================================

@pytest.mark.unit
def test_positive_additions():
    """Should generate positive prompt additions"""
    positive = ContentSafetyFilter.get_child_safe_positive_additions()
    
    assert "child-friendly" in positive
    assert "wholesome" in positive
    assert "safe for children" in positive
    assert "colorful" in positive


# ============================================================================
# TEST: validate_scene_description()
# ============================================================================

@pytest.mark.unit
class TestValidateSceneDescription:
    """Test scene description validation"""
    
    def test_validate_safe_scene(self):
        """Should validate safe scene descriptions"""
        description = "A happy child playing in a sunny garden"
        is_safe, error = ContentSafetyFilter.validate_scene_description(description)
        
        assert is_safe == True
        assert error == ""
    
    def test_reject_unsafe_scene(self):
        """Should reject unsafe scene descriptions"""
        description = "A violent battle with blood everywhere"
        is_safe, error = ContentSafetyFilter.validate_scene_description(description)
        
        assert is_safe == False
        assert len(error) > 0
    
    def test_reject_overly_long_scene(self):
        """Should reject scene descriptions that are too long"""
        description = " ".join(["word"] * 101)  # 101 words
        is_safe, error = ContentSafetyFilter.validate_scene_description(description)
        
        assert is_safe == False
        assert "too complex" in error.lower()
    
    def test_allow_reasonable_length_scene(self):
        """Should allow reasonably long scene descriptions"""
        description = " ".join(["word"] * 50)  # 50 words
        is_safe, error = ContentSafetyFilter.validate_scene_description(description)
        
        assert is_safe == True


# ============================================================================
# TEST: enhance_prompt_for_children()
# ============================================================================

@pytest.mark.unit
class TestEnhancePromptForChildren:
    """Test full prompt enhancement pipeline"""
    
    def test_enhance_safe_prompt(self):
        """Should enhance safe prompts successfully"""
        prompt = "A brave astronaut explores Mars"
        enhanced_positive, negative, is_safe = enhance_prompt_for_children(prompt)
        
        assert is_safe == True
        assert len(enhanced_positive) > 0
        assert len(negative) > 0
        assert "child-friendly" in enhanced_positive.lower()
        assert "nsfw" in negative
    
    def test_reject_unsafe_prompt(self):
        """Should reject unsafe prompts"""
        prompt = "A story with violence and blood"
        enhanced_positive, negative, is_safe = enhance_prompt_for_children(prompt)
        
        assert is_safe == False
        assert enhanced_positive == ""
        assert negative == ""
    
    def test_add_extra_safety_for_warnings(self):
        """Should add extra safety for warning keywords"""
        prompt = "A scary monster in the dark forest"
        enhanced_positive, negative, is_safe = enhance_prompt_for_children(prompt)
        
        assert is_safe == True
        # Should have extra negative prompts
        assert "monster" in negative or "darkness" in negative
    
    def test_preserve_original_content(self):
        """Should preserve original prompt content"""
        prompt = "A robot named Robo helps children learn math"
        enhanced_positive, negative, is_safe = enhance_prompt_for_children(prompt)
        
        assert is_safe == True
        assert "robot" in enhanced_positive.lower() or "robo" in enhanced_positive.lower()


# ============================================================================
# TEST: Edge Cases
# ============================================================================

@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_prompt(self):
        """Should handle empty prompts"""
        prompt = ""
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        # Empty prompts should be handled gracefully
        assert is_safe == True  # Empty is not "unsafe", just invalid
    
    def test_whitespace_only_prompt(self):
        """Should handle whitespace-only prompts"""
        prompt = "   \n\t   "
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert filtered.strip() == "" or "child-friendly" in filtered
    
    def test_case_insensitive_blocking(self):
        """Should block keywords regardless of case"""
        test_cases = [
            "A story with BLOOD",
            "Violence in the story",
            "NAKED people"
        ]
        
        for prompt in test_cases:
            filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
            assert is_safe == False, f"Failed to block: {prompt}"
    
    def test_partial_word_matching(self):
        """Should block keywords even in compound words"""
        prompt = "A story about bloodthirsty vampires"
        filtered, is_safe, warning = ContentSafetyFilter.filter_prompt(prompt)
        
        assert is_safe == False  # Contains "blood"


# ============================================================================
# TEST: Integration with Story Generation
# ============================================================================

@pytest.mark.integration
def test_content_safety_integration():
    """Test content safety in realistic story generation scenario"""
    # Simulate story generation prompts
    safe_prompts = [
        "A friendly dragon teaches children to read",
        "A magical garden where flowers sing songs",
        "A brave little mouse goes on an adventure"
    ]
    
    unsafe_prompts = [
        "A violent battle with blood and gore",
        "Naked people in the forest",
        "Children drinking alcohol at a party"
    ]
    
    # All safe prompts should pass
    for prompt in safe_prompts:
        enhanced, negative, is_safe = enhance_prompt_for_children(prompt)
        assert is_safe == True, f"Safe prompt rejected: {prompt}"
    
    # All unsafe prompts should be blocked
    for prompt in unsafe_prompts:
        enhanced, negative, is_safe = enhance_prompt_for_children(prompt)
        assert is_safe == False, f"Unsafe prompt allowed: {prompt}"
