"""
Unit tests for main API endpoints
Tests story generation, chat, and workshop endpoints
"""

import pytest
from fastapi import status
from unittest.mock import patch, Mock


# ============================================================================
# TEST: Device Info Endpoint
# ============================================================================

@pytest.mark.unit
def test_device_info(client):
    """Should return device information"""
    response = client.get("/device")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "device" in data
    assert data["device"] in ["cuda", "cpu"]


# ============================================================================
# TEST: Story Generation - Guest User
# ============================================================================

@pytest.mark.unit
class TestStoryGenerationGuest:
    """Test story generation for guest users"""
    
    @patch('backend.agents.story_agent.StoryAgent.generate_story')
    def test_guest_text_only_story(self, mock_generate, client, sample_story_data):
        """Guest users should be able to generate text-only stories"""
        mock_generate.return_value = ({"story": sample_story_data, "outputs": {}, "status": {}}, "success")
        
        response = client.post(
            "/api/generate",
            json={
                "prompt": "A brave little mouse",
                "generate_images": False
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "story" in data
        assert data["story"]["title"] == "The Brave Little Mouse"
    
    def test_guest_cannot_generate_images(self, client):
        """Guest users should not be able to generate images"""
        response = client.post(
            "/api/generate",
            json={
                "prompt": "A brave little mouse",
                "generate_images": True
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "login to generate images" in response.json()["detail"].lower()


# ============================================================================
# TEST: Story Generation - Authenticated User
# ============================================================================

@pytest.mark.unit
class TestStoryGenerationAuthenticated:
    """Test story generation for authenticated users"""
    
    @patch('backend.agents.story_agent.StoryAgent.generate_story')
    @patch('backend.agents.image_agent.ImageAgent.generate_image')
    @patch('backend.utils.ollama_manager.OllamaManager')
    def test_authenticated_with_images(self, mock_ollama, mock_image, mock_story, client, auth_headers, sample_story_data):
        """Authenticated users should be able to generate stories with images"""
        mock_story.return_value = ({"story": sample_story_data, "outputs": {}, "status": {}}, "success")
        mock_image.return_value = "/path/to/image.png"
        mock_ollama.pause_ollama.return_value = True
        
        response = client.post(
            "/api/generate",
            headers=auth_headers,
            json={
                "prompt": "A brave little mouse",
                "generate_images": True,
                "use_personalized_images": False,
                "mode": "simple"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "story" in data
        assert "story_id" in data


# ============================================================================
# TEST: Invalid Prompt Handling
# ============================================================================

@pytest.mark.unit
class TestInvalidPrompts:
    """Test handling of invalid prompts"""
    
    @patch('backend.agents.prompt_agent.PromptAgent.process_prompt')
    def test_invalid_prompt_rejection(self, mock_process, client):
        """Should reject invalid prompts"""
        mock_process.return_value = (None, "invalid")
        
        response = client.post(
            "/api/generate",
            json={"prompt": "https://example.com"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["error"].lower()
    
    @patch('backend.agents.prompt_agent.PromptAgent.process_prompt')
    def test_nonsense_prompt_rejection(self, mock_process, client):
        """Should reject nonsense prompts"""
        mock_process.return_value = (None, "nonsense")
        
        response = client.post(
            "/api/generate",
            json={"prompt": "asdfghjkl"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_missing_prompt(self, client):
        """Should reject request without prompt"""
        response = client.post("/api/generate", json={})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "missing 'prompt'" in response.json()["detail"].lower()


# ============================================================================
# TEST: Chat Endpoint
# ============================================================================

@pytest.mark.unit
class TestChatEndpoint:
    """Test character chatbot endpoint"""
    
    @patch('backend.agents.chatbot_agent.ChatbotAgent.chat')
    def test_chat_success(self, mock_chat, client, db_session, test_user, sample_story_data):
        """Should successfully chat with character"""
        # Create a story in database
        from backend.auth.db_models import Story
        story = Story(
            user_id=test_user.id,
            title="Test Story",
            mode="simple",
            story_data=sample_story_data
        )
        db_session.add(story)
        db_session.commit()
        db_session.refresh(story)
        
        mock_chat.return_value = "Hello! I'm the brave mouse!"
        
        response = client.post(
            "/api/chat",
            json={
                "story_id": story.id,
                "character_name": "brave mouse",
                "user_message": "Hello!"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert data["character"] == "brave mouse"
    
    def test_chat_missing_fields(self, client):
        """Should reject chat request with missing fields"""
        response = client.post(
            "/api/chat",
            json={"story_id": 1}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_chat_story_not_found(self, client):
        """Should return 404 for non-existent story"""
        response = client.post(
            "/api/chat",
            json={
                "story_id": 99999,
                "character_name": "test",
                "user_message": "hello"
            }
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# TEST: Workshop Endpoints
# ============================================================================

@pytest.mark.unit
class TestWorkshopEndpoints:
    """Test idea workshop endpoints"""
    
    def test_start_workshop_new_idea(self, client):
        """Should start workshop session in new_idea mode"""
        response = client.post(
            "/api/workshop/start",
            json={"mode": "new_idea"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
        assert data["mode"] == "new_idea"
        assert "initial_message" in data
    
    def test_start_workshop_improvement(self, client):
        """Should start workshop session in improvement mode"""
        response = client.post(
            "/api/workshop/start",
            json={"mode": "improvement"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["mode"] == "improvement"
    
    def test_start_workshop_invalid_mode(self, client):
        """Should reject invalid workshop mode"""
        response = client.post(
            "/api/workshop/start",
            json={"mode": "invalid_mode"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('backend.agents.idea_workshop_agent_langchain.IdeaWorkshopAgentLangChain.process_message')
    def test_workshop_chat(self, mock_process, client, db_session):
        """Should handle workshop chat messages"""
        # Create workshop session
        from backend.auth.db_models import WorkshopSession, WorkshopMessage
        session = WorkshopSession(mode="new_idea", status="active")
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        # Add initial message
        initial_msg = WorkshopMessage(
            session_id=session.id,
            role="assistant",
            message="Welcome!"
        )
        db_session.add(initial_msg)
        db_session.commit()
        
        mock_process.return_value = ("Great idea! Tell me more.", {"requirements": []})
        
        response = client.post(
            "/api/workshop/chat",
            json={
                "session_id": session.id,
                "user_message": "I want a story about dragons"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert "ready_to_generate" in data


# ============================================================================
# TEST: Error Handling
# ============================================================================

@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in API endpoints"""
    
    @patch('backend.agents.story_agent.StoryAgent.generate_story')
    def test_story_generation_error(self, mock_generate, client):
        """Should handle story generation errors gracefully"""
        mock_generate.side_effect = Exception("Story generation failed")
        
        response = client.post(
            "/api/generate",
            json={
                "prompt": "A test story",
                "generate_images": False
            }
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "story generation failed" in response.json()["detail"].lower()
