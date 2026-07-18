# backend/agents/chatbot_agent.py
from typing import Dict, List, Tuple

from backend.model_config import CHATBOT_AGENT_MODEL
from backend.utils.bedrock_client import invoke_bedrock


class ChatbotAgent:
    """
    ChatbotAgent: Impersonates story characters using Ollama LLM
    Maintains context of the story and conversation history
    """

    def __init__(self, story_data: Dict, character_name: str, llm_model: str = CHATBOT_AGENT_MODEL):
        """
        Initialize chatbot with story context and character
        
        Args:
            story_data: Full story dictionary with title, characters, scenes, setting
            character_name: Name of character to impersonate
            llm_model: Ollama model to use for generation
        """
        self.story_data = story_data
        self.character_name = character_name
        self.llm_model = llm_model
        
        # Extract story context
        self.title = story_data.get("title", "Unknown Story")
        self.setting = story_data.get("setting", "")
        self.characters = story_data.get("characters", [])
        self.scenes = story_data.get("scenes", [])
        
        # Validate character exists in story
        if character_name not in self.characters:
            raise ValueError(f"Character '{character_name}' not found in story. Available: {self.characters}")

    def _ask_bedrock(self, prompt: str) -> str:
        """Call Amazon Bedrock (Claude Sonnet 4.5) for character impersonation responses."""
        result = invoke_bedrock(
            prompt=prompt,
            system=f"You are {self.character_name}, a character from a children's story. Stay in character at all times. Keep responses to 2-4 sentences. Never mention being an AI.",
            model_id=self.llm_model,
            temperature=0.8,
            max_tokens=512,
        )
        return result if result else "I'm having trouble responding right now. Can you try again?"

    def _build_character_prompt(self, user_message: str) -> str:
        """
        Build system prompt for character impersonation using ReAct framework
        
        Args:
            user_message: The current user message
            
        Returns:
            Full prompt for Ollama including system instructions and current message
        """
        # Compile story context
        story_summary = f"Story Title: {self.title}\n"
        story_summary += f"Setting: {self.setting}\n"
        story_summary += f"Characters: {', '.join(self.characters)}\n\n"
        story_summary += "Story Events:\n"
        
        for i, scene in enumerate(self.scenes, 1):
            scene_text = scene.get("text", "")
            story_summary += f"Scene {i}: {scene_text}\n"
        
        # Build ReAct prompt for character impersonation
        system_instruction = f"""You are a character impersonation system using the ReAct (Reasoning + Acting) framework.

**Your Character:** {self.character_name} from the story "{self.title}"

**Story Context:**
{story_summary}

**Your Task:** Respond to the child's message AS {self.character_name}.

**Available Response Strategies:**
1. in_character_answer - Answer their question staying fully in character
2. story_redirect - Politely redirect off-topic questions back to the story
3. gentle_decline - Refuse inappropriate/impossible questions warmly

**Guidelines:**
- Keep responses 2-4 sentences maximum
- Use first person ("I", "my")
- Reference story events naturally
- Stay child-friendly (ages 7-10)
- NEVER break character or mention being an AI

**Child's Message:** "{user_message}"

**Instructions:**
Use this EXACT format:
Thought: [Analyze the question and decide how to respond]
Response Strategy: [ONE of: in_character_answer, story_redirect, gentle_decline]
Response: [Your actual response as {self.character_name}]

Begin!

Thought:"""
        
        return system_instruction

    def chat(self, user_message: str) -> str:
        """
        Generate character response to user message using ReAct reasoning
        
        Args:
            user_message: The child's current message
            
        Returns:
            Character's response as a string
        """
        # Build prompt with ReAct format
        prompt = self._build_character_prompt(user_message)
        
        # Get response from Ollama
        ollama_output = self._ask_bedrock(prompt)
        
        # Parse ReAct output to extract final response
        response = self._parse_chatbot_react(ollama_output)
        
        return response
    
    def _parse_chatbot_react(self, output: str) -> str:
        """
        Parse ReAct output from chatbot to extract final response.
        Expects format: Thought: ... Response Strategy: ... Response: ...
        """
        try:
            # Find the Response section
            response_marker = output.lower().find("response:")
            if response_marker == -1:
                # Fallback: try to find any response-like content
                lines = output.strip().split('\n')
                for line in reversed(lines):  # Check from bottom up
                    if line.strip() and not line.lower().startswith(('thought:', 'response strategy:')):
                        return line.strip()
                return output.strip()  # Return whole output as fallback
            
            # Extract everything after "Response:"
            response_text = output[response_marker + len("response:"):].strip()
            
            # Clean up (remove character name prefix if LLM added it)
            if response_text.startswith(f"{self.character_name}:"):
                response_text = response_text[len(f"{self.character_name}:"):].strip()
            
            # Take first paragraph (in case LLM added extra text)
            response_text = response_text.split('\n\n')[0].strip()
            
            return response_text if response_text else output.strip()
            
        except Exception as e:
            print(f"[ChatbotAgent] ReAct parsing error: {e}")
            # Return the whole output if parsing fails
            return output.strip()


# Test the agent if run directly
if __name__ == "__main__":
    # Example story data
    test_story = {
        "title": "The Brave Little Cat",
        "setting": "A magical garden",
        "characters": ["Milo the Cat", "Wise Owl"],
        "scenes": [
            {"scene_number": 1, "text": "Milo the Cat lived in a cozy house near a magical garden. One day, he heard mysterious sounds coming from beyond the fence."},
            {"scene_number": 2, "text": "Milo bravely ventured into the garden and met a Wise Owl sitting on a tree branch. The owl told him about a hidden treasure."},
            {"scene_number": 3, "text": "Together, Milo and the Wise Owl found a sparkling crystal that brought joy to the entire neighborhood."}
        ]
    }
    
    try:
        # Test chatbot (STATELESS - no conversation history)
        chatbot = ChatbotAgent(test_story, "Milo the Cat")
        print("✅ ChatbotAgent initialized successfully\n")
        
        # Test message 1 (independent)
        response1 = chatbot.chat("Hello! What's your name?")
        print(f"User: Hello! What's your name?")
        print(f"Milo: {response1}\n")
        
        # Test message 2 (independent - no memory of previous message)
        response2 = chatbot.chat("What did you find in the garden?")
        print(f"User: What did you find in the garden?")
        print(f"Milo: {response2}\n")
        
        # Test edge case (off-topic question)
        response3 = chatbot.chat("What's 5 + 7?")
        print(f"User: What's 5 + 7?")
        print(f"Milo: {response3}")
        
    except Exception as e:
        print(f"❌ Error testing ChatbotAgent: {e}")
