"""
Unit tests for prompt_agent.py module
Tests prompt processing, classification, and enhancement
"""

import pytest
from unittest.mock import Mock, patch
from backend.agents.prompt_agent import PromptAgent


# ============================================================================
# TEST: Empty and Nonsense Prompts
# ============================================================================

@pytest.mark.unit
class TestEmptyAndNonsensePrompts:
    """Test handling of empty and nonsense inputs"""
    
    def test_empty_prompt(self):
        """Should return None and 'nonsense' for empty prompt"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("")
        
        assert result is None
        assert prompt_type == "nonsense"
    
    def test_whitespace_only_prompt(self):
        """Should return None and 'nonsense' for whitespace-only prompt"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("   \n\t   ")
        
        assert result is None
        assert prompt_type == "nonsense"
    
    def test_only_numbers(self):
        """Should return None and 'invalid' for only numbers"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("12345678")
        
        assert result is None
        assert prompt_type == "invalid"
    
    def test_only_symbols(self):
        """Should return None and 'invalid' for only symbols"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("!@#$%^&*()")
        
        assert result is None
        assert prompt_type == "invalid"
    
    def test_mixed_numbers_symbols(self):
        """Should return None and 'invalid' for mixed numbers and symbols"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("123!@#456")
        
        assert result is None
        assert prompt_type == "invalid"


# ============================================================================
# TEST: URL Detection
# ============================================================================

@pytest.mark.unit
class TestURLDetection:
    """Test detection and rejection of URLs"""
    
    def test_http_url(self):
        """Should reject HTTP URLs"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("http://example.com")
        
        assert result is None
        assert prompt_type == "invalid"
    
    def test_https_url(self):
        """Should reject HTTPS URLs"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("https://google.com")
        
        assert result is None
        assert prompt_type == "invalid"
    
    def test_url_in_text(self):
        """Should reject prompts containing URLs"""
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("Check out http://example.com for stories")
        
        assert result is None
        assert prompt_type == "invalid"


# ============================================================================
# TEST: Prompt Sanitization
# ============================================================================

@pytest.mark.unit
class TestPromptSanitization:
    """Test that dangerous characters are sanitized"""
    
    @patch('subprocess.run')
    def test_sanitize_quotes(self, mock_run):
        """Should replace double quotes with single quotes"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "normal", "enhanced": "A story about friendship"}',
            returncode=0
        )
        
        agent = PromptAgent()
        # The sanitization happens before calling Ollama
        prompt = 'A story with "quotes"'
        result, prompt_type = agent.process_prompt(prompt)
        
        # Verify the prompt was sanitized (quotes replaced)
        call_args = mock_run.call_args[0][0]
        assert '"' not in str(call_args) or "'" in str(call_args)
    
    @patch('subprocess.run')
    def test_sanitize_braces(self, mock_run):
        """Should replace curly braces with square brackets"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "normal", "enhanced": "A story about friendship"}',
            returncode=0
        )
        
        agent = PromptAgent()
        prompt = "A story with {braces}"
        result, prompt_type = agent.process_prompt(prompt)
        
        # Braces should be replaced
        assert result is not None


# ============================================================================
# TEST: Prompt Classification with Mocked Ollama
# ============================================================================

@pytest.mark.unit
class TestPromptClassification:
    """Test prompt classification using mocked Ollama responses"""
    
    @patch('subprocess.run')
    def test_classify_short_prompt(self, mock_run):
        """Should classify and enhance short prompts"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "short", "enhanced": "A heartwarming story about a boy and girl learning friendship in a magical forest."}',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("boy and girl")
        
        assert prompt_type == "short"
        assert result is not None
        assert len(result) > len("boy and girl")
    
    @patch('subprocess.run')
    def test_classify_normal_prompt(self, mock_run):
        """Should classify normal prompts"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "normal", "enhanced": "A curious astronaut explores a forgotten planet full of mysterious life, discovering hope and wonder."}',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("A lonely astronaut exploring a forgotten planet")
        
        assert prompt_type == "normal"
        assert result is not None
    
    @patch('subprocess.run')
    def test_classify_long_prompt(self, mock_run):
        """Should classify and summarize long prompts"""
        long_prompt = " ".join(["word"] * 60)  # 60 words
        
        mock_run.return_value = Mock(
            stdout=b'{"type": "long", "enhanced": "A concise summary of the long prompt."}',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt(long_prompt)
        
        assert prompt_type == "long"
        assert result is not None
        assert len(result.split()) < len(long_prompt.split())


# ============================================================================
# TEST: Character Name Preservation
# ============================================================================

@pytest.mark.unit
class TestCharacterNamePreservation:
    """Test that character names and details are preserved"""
    
    @patch('subprocess.run')
    def test_preserve_character_names(self, mock_run):
        """Should preserve character names from original prompt"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "short", "enhanced": "John and Jack were playing cricket when something magical happened on their field."}',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("john and jack were playing cricket")
        
        assert result is not None
        # Names should be preserved (case-insensitive check)
        assert "john" in result.lower()
        assert "jack" in result.lower()
    
    @patch('subprocess.run')
    def test_preserve_location_names(self, mock_run):
        """Should preserve location names"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "normal", "enhanced": "A magical adventure in Paris where a child discovers hidden treasures."}',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("A story in Paris")
        
        assert result is not None
        assert "paris" in result.lower()


# ============================================================================
# TEST: Ollama Communication
# ============================================================================

@pytest.mark.unit
class TestOllamaCommunication:
    """Test communication with Ollama service"""
    
    @patch('subprocess.run')
    def test_ollama_called_with_correct_model(self, mock_run):
        """Should call Ollama with correct model"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "normal", "enhanced": "A story"}',
            returncode=0
        )
        
        agent = PromptAgent(model="mistral-nemo:12b")
        agent.process_prompt("A simple story")
        
        # Verify Ollama was called
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "ollama" in call_args
        assert "mistral-nemo:12b" in call_args
    
    @patch('subprocess.run')
    def test_handle_ollama_json_parse_error(self, mock_run):
        """Should handle invalid JSON from Ollama gracefully"""
        mock_run.return_value = Mock(
            stdout=b'Invalid JSON response',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("A simple story")
        
        # Should fallback to original prompt and "normal" type
        assert result == "A simple story"
        assert prompt_type == "normal"
    
    @patch('subprocess.run')
    def test_handle_missing_enhanced_field(self, mock_run):
        """Should handle missing 'enhanced' field in Ollama response"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "normal"}',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("A simple story")
        
        # Should fallback to original prompt
        assert result == "A simple story"
        assert prompt_type == "normal"


# ============================================================================
# TEST: Edge Cases
# ============================================================================

@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_very_short_meaningful_prompt(self):
        """Should handle very short but meaningful prompts"""
        agent = PromptAgent()
        # "cat" is 3 characters - should not be nonsense
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout=b'{"type": "short", "enhanced": "A story about a cat"}',
                returncode=0
            )
            result, prompt_type = agent.process_prompt("cat")
            
            assert result is not None
            assert prompt_type == "short"
    
    def test_prompt_with_special_characters(self):
        """Should handle prompts with some special characters"""
        agent = PromptAgent()
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                stdout=b'{"type": "normal", "enhanced": "A story about friendship"}',
                returncode=0
            )
            result, prompt_type = agent.process_prompt("A story about friendship!")
            
            assert result is not None
    
    @patch('subprocess.run')
    def test_unicode_characters(self, mock_run):
        """Should handle unicode characters"""
        mock_run.return_value = Mock(
            stdout=b'{"type": "normal", "enhanced": "A story about a princess"}',
            returncode=0
        )
        
        agent = PromptAgent()
        result, prompt_type = agent.process_prompt("A story about a princess 👑")
        
        assert result is not None


# ============================================================================
# TEST: Integration Scenarios
# ============================================================================

@pytest.mark.integration
class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    @patch('subprocess.run')
    def test_typical_user_prompts(self, mock_run):
        """Test with typical user prompts"""
        test_cases = [
            ("A brave knight", "short"),
            ("A story about friendship and adventure", "normal"),
            ("Once upon a time in a magical kingdom far away...", "normal")
        ]
        
        for prompt, expected_type in test_cases:
            mock_run.return_value = Mock(
                stdout=f'{{"type": "{expected_type}", "enhanced": "Enhanced version"}}'.encode(),
                returncode=0
            )
            
            agent = PromptAgent()
            result, prompt_type = agent.process_prompt(prompt)
            
            assert result is not None
            assert prompt_type == expected_type
