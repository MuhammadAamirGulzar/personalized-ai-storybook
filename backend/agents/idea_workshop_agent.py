# backend/agents/idea_workshop_agent.py
import json
import subprocess
from typing import Dict, List, Tuple, Optional

from backend.model_config import IDEA_WORKSHOP_AGENT_MODEL


class IdeaWorkshopAgent:
    """
    IdeaWorkshopAgent: Guides users through story improvement or new idea creation
    Maintains conversation context and asks structured questions
    """

    def __init__(self, mode: str, conversation_history: List[Dict], llm_model: str = IDEA_WORKSHOP_AGENT_MODEL):
        """
        Initialize workshop agent
        
        Args:
            mode: 'improvement' or 'new_idea'
            conversation_history: List of {role, message, metadata} dicts
            llm_model: Ollama model to use
        """
        self.mode = mode
        self.conversation_history = conversation_history
        self.llm_model = llm_model
        
        # Track what's been collected
        self.collected_requirements = {}
        self.user_story = None  # For improvement mode
        self.last_question_field = None  # Track which field we just asked about
        
        # Define questions mapping for state restoration
        self.required_fields_questions = {
            'genre': "What type or genre of story do you want? (e.g., adventure, fantasy, mystery, etc.)",
            'characters': "What characters should be included in your story?",
            'setting': "What theme or world should the story take place in?",
            'beginning': "What kind of beginning do you prefer for your story?",
            'climax': "What type of climax should the story have?",
            'ending': "What ending do you want for your story?",
            'scenes': "Are there any specific scenes or moments you'd like to include?",
            'moral': "Is there a moral or lesson you'd like the story to convey?"
        }
        
        # Extract from conversation history
        self._extract_requirements_from_history()

    def _ask_ollama(self, prompt: str) -> str:
        """Send prompt to Ollama and return response"""
        try:
            proc = subprocess.run(
                ["ollama", "run", self.llm_model],
                input=prompt.encode("utf-8"),
                capture_output=True,
                check=False,
            )
            return proc.stdout.decode("utf-8").strip()
        except Exception as e:
            print(f"[IdeaWorkshopAgent] Error calling Ollama: {e}")
            return "I'm having trouble processing right now. Could you try again?"

    def validate_story_length(self, text: str) -> Tuple[bool, str, int]:
        """
        Validate story length for improvement mode
        
        Returns:
            (is_valid, error_message, word_count)
        """
        text = text.strip()
        if not text:
            return False, "Story cannot be empty. Please paste your story.", 0
        
        words = text.split()
        word_count = len(words)
        
        if word_count > 300:
            return False, f"Story is too long ({word_count} words). Maximum is 300 words. Please shorten it.", word_count
        
        return True, "", word_count

    def _extract_requirements_from_history(self):
        """Extract requirements already mentioned in conversation"""
        print(f"[IdeaWorkshopAgent] Extracting from {len(self.conversation_history)} messages")
        
        # For improvement mode: find the original story
        if self.mode == 'improvement':
            # Look for user story in metadata first
            for msg in self.conversation_history:
                if msg.get('role') == 'user':
                    metadata = msg.get('metadata', {})
                    if 'user_story' in metadata:
                        self.user_story = metadata['user_story']
                        print(f"[IdeaWorkshopAgent] Found story in metadata: {len(self.user_story.split())} words")
                        break
            
            # Fallback: look for first substantial user message (likely the pasted story)
            if not self.user_story:
                for i, msg in enumerate(self.conversation_history):
                    if msg.get('role') == 'user':
                        message_text = msg.get('message', '')
                        word_count = len(message_text.split())
                        # First user message with >20 words is likely the story
                        if word_count > 20:
                            self.user_story = message_text
                            print(f"[IdeaWorkshopAgent] Extracted story from message: {word_count} words")
                            break
        
        # Extract requirements from ALL messages (both user and assistant)
        for msg in self.conversation_history:
            metadata = msg.get('metadata', {})
            
            # Extract from metadata if stored
            if metadata and 'requirements' in metadata:
                self.collected_requirements.update(metadata['requirements'])
                print(f"[IdeaWorkshopAgent] Loaded requirements from {msg.get('role')} message: {list(metadata['requirements'].keys())}")

        # Restore last_question_field from the last assistant message
        if self.conversation_history:
            last_msg = self.conversation_history[-1]
            if last_msg.get('role') == 'assistant':
                last_text = last_msg.get('message', '').strip()
                # Check if this text matches any of our questions
                for field, question in self.required_fields_questions.items():
                    # Check for partial match since there might be "I'll decide..." prefixes
                    if question in last_text:
                        self.last_question_field = field
                        print(f"[IdeaWorkshopAgent] Restored last_question_field: {field}")
                        break

    def get_next_question(self) -> Optional[str]:
        """
        Determine the next question to ask based on mode and collected requirements
        
        Returns:
            Next question string, or None if ready to generate
        """
        if self.mode == 'improvement':
            return self._get_next_improvement_question()
        else:
            return self._get_next_new_idea_question()

    def _get_next_improvement_question(self) -> Optional[str]:
        """Get next question for improvement mode"""
        # Step 1: Get the story
        if not self.user_story:
            return "Please paste your story below (maximum 300 words)."
        
        # Step 2: Ask about improvement types
        if 'improvement_type' not in self.collected_requirements:
            return "What type of improvements do you want? (e.g., more exciting, better pacing, stronger ending, etc.)"
        
        # Step 3: Character adjustments
        if 'characters' not in self.collected_requirements:
            return "Do you want to adjust the characters? If yes, please specify how."
        
        # Step 4: Scenes/theme
        if 'scenes_theme' not in self.collected_requirements:
            return "Do you want to adjust the scenes or theme? Please describe any changes."
        
        # Step 5: Structure changes
        if 'structure' not in self.collected_requirements:
            return "Would you like to modify the beginning, climax, or ending? Please specify."
        
        # Step 6: Tone/pacing
        if 'tone_pacing' not in self.collected_requirements:
            return "Any specific changes in tone, pacing, storyline, or lesson you'd like to include?"
        
        # All requirements collected
        return None

    def _get_next_new_idea_question(self) -> Optional[str]:
        """Get next question for new idea mode (smart questioning - skip provided details)"""
        # Use the shared mapping
        required_fields = self.required_fields_questions
        
        # Check which fields are missing or empty (but not intentionally skipped)
        
        # Check which fields are missing or empty (but not intentionally skipped)
        for field, question in required_fields.items():
            value = self.collected_requirements.get(field, '')
            # Skip if field is marked as intentionally skipped
            if value == "__SKIP__":
                continue
            # Consider field missing if: not in dict, empty string, empty list, or None
            if not value or value == '' or value == [] or value == {}:
                self.last_question_field = field  # Track what we're asking
                print(f"[IdeaWorkshopAgent] Asking about missing field: {field}")
                return question
        
        # All requirements collected with actual values
        self.last_question_field = None
        return None

    def _get_next_missing_field(self) -> Optional[str]:
        """Get the next missing field name (for auto-fill logic)"""
        required_fields = ['genre', 'characters', 'setting', 'beginning', 'climax', 'ending', 'scenes', 'moral']
        
        for field in required_fields:
            value = self.collected_requirements.get(field, '')
            # Field is missing if: not in dict, empty, or intentionally skipped
            if value == "__SKIP__":
                continue
            if not value or value == '' or value == [] or value == {}:
                return field
        
        return None

    def process_message(self, user_message: str) -> Tuple[str, Dict]:
        """
        Process user message and return response with metadata
        
        Returns:
            (response_message, metadata_dict)
        """
        user_message = user_message.strip()
        
        # Handle empty messages
        if not user_message:
            return "Please provide your input so I can help you better!", {}
        
        metadata = {}
        
        # Mode-specific processing
        if self.mode == 'improvement':
            return self._process_improvement_message(user_message)
        else:
            return self._process_new_idea_message(user_message)

    def _process_improvement_message(self, user_message: str) -> Tuple[str, Dict]:
        """Process message in improvement mode"""
        metadata = {}
        
        # Check if this is the initial story paste
        if not self.user_story:
            is_valid, error_msg, word_count = self.validate_story_length(user_message)
            
            if not is_valid:
                return error_msg, {}
            
            # Store the story
            self.user_story = user_message
            metadata['user_story'] = user_message
            metadata['word_count'] = word_count
            
            return f"Great! I've got your story ({word_count} words). What type of improvements do you want?", metadata
        
        # Process improvement requirements
        next_question = self.get_next_question()
        
        # Store the answer to current question
        if 'improvement_type' not in self.collected_requirements:
            self.collected_requirements['improvement_type'] = user_message
            metadata['requirements'] = self.collected_requirements.copy()
            next_q = self.get_next_question()
            if next_q:
                return next_q, metadata
            else:
                return self._generate_confirmation(), metadata
        
        elif 'characters' not in self.collected_requirements:
            self.collected_requirements['characters'] = user_message
            metadata['requirements'] = self.collected_requirements.copy()
            next_q = self.get_next_question()
            if next_q:
                return next_q, metadata
            else:
                return self._generate_confirmation(), metadata
        
        elif 'scenes_theme' not in self.collected_requirements:
            self.collected_requirements['scenes_theme'] = user_message
            metadata['requirements'] = self.collected_requirements.copy()
            next_q = self.get_next_question()
            if next_q:
                return next_q, metadata
            else:
                return self._generate_confirmation(), metadata
        
        elif 'structure' not in self.collected_requirements:
            self.collected_requirements['structure'] = user_message
            metadata['requirements'] = self.collected_requirements.copy()
            next_q = self.get_next_question()
            if next_q:
                return next_q, metadata
            else:
                return self._generate_confirmation(), metadata
        
        elif 'tone_pacing' not in self.collected_requirements:
            self.collected_requirements['tone_pacing'] = user_message
            metadata['requirements'] = self.collected_requirements.copy()
            return self._generate_confirmation(), metadata
        
        # If all collected - confirm generation
        return self._generate_confirmation(), metadata

    def _process_new_idea_message(self, user_message: str) -> Tuple[str, Dict]:
        """
        Process message in new idea mode using unified LLM analysis.
        Handles: answers, skips, auto-fills, premature generation, and invalid inputs.
        """
        metadata = {}
        
        # 1. Determine what we are currently asking about
        current_field = self.last_question_field
        
        # 2. Analyze the input using LLM
        analysis = self._analyze_input_with_llm(user_message, current_field, self.collected_requirements)
        
        action = analysis.get('action')
        value = analysis.get('value')
        feedback = analysis.get('feedback')
        
        print(f"[IdeaWorkshopAgent] Analysis Result: Action={action}, Value='{value}', Feedback='{feedback}'")

        # 3. Handle Actions
        
        # CASE A: SAVE VALUE (Valid Answer)
        if action == 'save_value':
            # If we were asking about a specific field, save to that field
            if current_field:
                self.collected_requirements[current_field] = value
                print(f"[IdeaWorkshopAgent] Saved '{value}' to {current_field}")
            else:
                # Fallback: If current_field is None (e.g. state lost), try to save to the next missing field
                next_field = self._get_next_missing_field()
                if next_field:
                    self.collected_requirements[next_field] = value
                    print(f"[IdeaWorkshopAgent] Fallback: Saved '{value}' to inferred field {next_field}")
                else:
                    print(f"[IdeaWorkshopAgent] Warning: Could not save '{value}' - no current or missing field found") 
                
            metadata['requirements'] = self.collected_requirements.copy()
            next_q = self.get_next_question()
            if next_q:
                return next_q, metadata
            else:
                return self._generate_confirmation(), metadata

        # CASE A.2: SAVE MULTIPLE (Full Story Extraction)
        elif action == 'save_multiple':
            if isinstance(value, dict):
                print(f"[IdeaWorkshopAgent] Processing multi-field update: {list(value.keys())}")
                for k, v in value.items():
                    # Normalize key to lowercase just in case
                    k = k.lower()
                    if k in self.required_fields_questions:
                        self.collected_requirements[k] = v
                        print(f"[IdeaWorkshopAgent] Multi-save: '{v}' to {k}")
            
            metadata['requirements'] = self.collected_requirements.copy()
            next_q = self.get_next_question()
            if next_q:
                # If we extracted a lot, acknowledge it
                extracted_count = len(value) if isinstance(value, dict) else 0
                if extracted_count > 2:
                    return f"Wow, that's a great start! I've noted down all those details. {next_q}", metadata
                return f"Got it. {next_q}", metadata
            else:
                return self._generate_confirmation(), metadata

        # CASE B: SKIP
        elif action == 'skip':
            if current_field:
                self.collected_requirements[current_field] = "__SKIP__"
                print(f"[IdeaWorkshopAgent] Skipped {current_field}")
                
            metadata['requirements'] = self.collected_requirements.copy()
            next_q = self.get_next_question()
            if next_q:
                return f"Okay, skipping that. {next_q}", metadata
            else:
                return self._generate_confirmation(), metadata

        # CASE C: AUTO-FILL
        elif action == 'auto_fill':
            # CRITICAL FIX: current_field might be outdated or None
            # Get the NEXT missing field that needs auto-filling
            field_to_fill = current_field if current_field else self._get_next_missing_field()
            
            if field_to_fill:
                auto_value = self._generate_auto_fill_value(field_to_fill)
                self.collected_requirements[field_to_fill] = auto_value
                print(f"[IdeaWorkshopAgent] Auto-filled {field_to_fill} with '{auto_value}'")
                
                metadata['requirements'] = self.collected_requirements.copy()
                next_q = self.get_next_question()
                if next_q:
                    return f"I'll decide that for you! Let's go with: {auto_value}. {next_q}", metadata
                else:
                    return self._generate_confirmation(), metadata
            else:
                # No field to auto-fill (all filled already)
                return self._generate_confirmation(), metadata

        # CASE D: GENERATE REQUEST (Premature or Valid)
        elif action == 'generate_request':
            # Check if we are actually ready
            if self.should_generate_story(""):
                return self._generate_confirmation(), metadata
            else:
                # Not ready yet - explain what's missing
                next_q = self.get_next_question()
                missing = self.last_question_field or "some details"
                return f"I'd love to start writing, but I still need to know about the **{missing}**. {next_q}", metadata

        # CASE E: REJECT / CLARIFY (Gibberish, off-topic, or unclear)
        elif action == 'reject':
            return feedback or "I'm not sure I understood that. Could you clarify?", metadata

        # Fallback
        return "I'm having trouble understanding. Could you try rephrasing?", metadata

    def _analyze_input_with_llm(self, user_message: str, current_field: str, collected_data: Dict) -> Dict:
        """
        Unified Input Analyzer using ReAct (Reasoning + Acting) framework.
        Returns JSON: { "action": "...", "value": "...", "feedback": "..." }
        """
        print(f"[IdeaWorkshopAgent] Analyzing input: '{user_message}' for field: '{current_field}'")
        
        field_description = current_field if current_field else "this story element"
        
        context_str = ", ".join([f"{k}: {v}" for k, v in collected_data.items() if v and v != "__SKIP__"])
        collected_json = json.dumps(collected_data, indent=2) if collected_data else "{}"

        # Extract last assistant message to give the LLM conversational context
        last_assistant_message = ""
        for msg in reversed(self.conversation_history):
            if msg.get('role') == 'assistant':
                last_assistant_message = msg.get('message', '')
                break

        prompt = f"""You are an intelligent Story Workshop Assistant using the ReAct (Reasoning + Acting) framework.

**Available Actions:**
1. save_value - Save user's answer to current field (SHORT ANSWERS & STORIES VALID!)
2. save_multiple - Extract MULTIPLE fields from a detailed description
3. skip - User wants to skip this field
4. auto_fill - User wants YOU to decide
5. generate_request - User wants to generate story NOW
6. reject - Use when input is invalid (see rules below)

**Story Fields:** genre, characters, setting, beginning, climax, ending, scenes, moral

**Current Context:**
- Current Question Field: {current_field or "None (initial message — first thing the user says about their story idea)"}
- Already Collected: {context_str or "nothing yet"}

**SUGGESTION CONFIRMATION RULE (Highest Priority — check this FIRST):**
Look at the "Previous Assistant Message" below.
If that message presented a generated/suggested value for the current field AND asked the user whether it's acceptable
(e.g. "Here's one: '...' Does that work for you?", "How about '...'?", "I'll decide that for you! Let's go with: '...'", "I've chosen '...' for you. Is that okay?"),
AND the user's current input is an affirmative reply such as:
"yes", "yeah", "yep", "ok", "okay", "sure", "fine", "that works", "looks good", "great", "perfect", "sounds good", "go ahead", "that's fine", "i like it", "accepted", "correct", "right", "good"
→ Extract the suggested VALUE from the previous assistant message and use `save_value` to save it.
→ Do NOT mark this as invalid. Do NOT ask the question again.

**Previous Assistant Message**: "{last_assistant_message}"

**INPUT VALIDATION RULES — Read carefully before deciding (Apply AFTER the confirmation check above):**
You must judge whether the user's input is a genuine, meaningful answer to the question being asked.
Mark input as INVALID (use `reject`) if it is:
- A greeting or social filler: "hi", "hello", "hey", "good morning", "how are you", "what's up", "sup"
- Only numbers or a math expression: "9+9=?", "123-123=0", "42", "1000", "2+2"
- Only symbols or special characters: "@@##", "!!", "---", "***", "????"
- A URL or web link: anything starting with http, https, www, or ending in .com/.net
- Meaningless random characters: "asa45sjsa", "asdfgh", "qwerty123", "zzzzz"
- Completely off-topic, unrelated to story creation: "what is the capital of France", "who won the world cup"
- For the VERY FIRST message (current_field is None, nothing collected yet): fewer than 3 meaningful words is ALSO invalid. "hi" alone is not a story idea.

If input is INVALID → Action: reject, and in the feedback field, write a friendly explanation AND re-ask the exact same question.

A response is VALID if it genuinely answers the asked question, including:
- Single story-relevant words: "horror", "fantasy", "adventure"
- Character names: "john and jack", "a brave girl named Lily"
- Short but real answers: "haunted house", "happy ending", "no moral"
- Narrative descriptions, even if brief

**User Input:** "{user_message}"

**Instructions:**
Use this EXACT format:
Thought: [FIRST check if this is a confirmation of a previous suggestion. THEN check if input is valid. Apply the rules above.]
Action: [ONE of: save_value, save_multiple, skip, auto_fill, generate_request, reject]
Action Input: [JSON object with action details]

**Action Input Formats:**
- save_value: {{"value": "extracted text"}}
- save_multiple: {{"genre": "...", "characters": "...", "setting": "..."}} (extract ALL possible fields)
- skip: {{}}
- auto_fill: {{}}
- generate_request: {{}}
- reject: {{"feedback": "friendly explanation of why it was invalid + re-ask the EXACT same question word for word"}}

Begin!

Thought:"""

        try:
            response = self._ask_ollama(prompt)
            print(f"[IdeaWorkshopAgent] ReAct Response:\n{response[:300]}...")  # Log first 300 chars
            
            # Parse ReAct output
            return self._parse_react_output(response, field_description)
            
        except Exception as e:
            print(f"[IdeaWorkshopAgent] Error in ReAct analysis: {e}")
            return {"action": "reject", "value": "", "feedback": "I had trouble understanding. Could you rephrase?"}
    
    def _parse_react_output(self, response: str, field_description: str) -> Dict:
        """
        Parse ReAct format output into action dictionary.
        Expects format: Thought: ... Action: ... Action Input: {...}
        """
        try:
            # Extract Action
            action_match = response.lower().find("action:")
            if action_match == -1:
                raise ValueError("No Action found in response")
            
            # Extract the action name
            action_line = response[action_match:].split('\n')[0]
            action = None
            for possible_action in ['save_multiple', 'save_value', 'auto_fill', 'generate_request', 'skip', 'reject']:
                if possible_action in action_line.lower():
                    action = possible_action
                    break
            
            if not action:
                raise ValueError(f"Could not identify action in: {action_line}")
            
            # Extract Action Input JSON
            input_start = response.find("action input:", action_match)
            if input_start == -1:
                input_start = response.find("action input", action_match)
            
            if input_start != -1:
                # Remove markdown code blocks if present
                input_section = response[input_start:]
                input_section = input_section.replace('```json', '').replace('```', '')
                
                # Find JSON in the Action Input section
                json_start = input_section.find('{')
                if json_start != -1:
                    # Find matching closing brace using brace counting
                    brace_count = 0
                    json_end = -1
                    for i in range(json_start, len(input_section)):
                        if input_section[i] == '{':
                            brace_count += 1
                        elif input_section[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_end = i
                                break
                    
                    if json_end != -1:
                        json_str = input_section[json_start:json_end+1]
                        try:
                            action_input = json.loads(json_str, strict=False)
                        except json.JSONDecodeError:
                            print(f"[IdeaWorkshopAgent] JSON parse error: {json_str}")
                            action_input = {}
                    else:
                        action_input = {}
                else:
                    action_input = {}
            else:
                action_input = {}
            
            # Debug logging
            print(f"[IdeaWorkshopAgent] Parsed Action: {action}, Input: {action_input}")
            
            # Build return dict based on action type
            if action == "save_value":
                return {
                    "action": "save_value",
                    "value": action_input.get("value", ""),
                    "feedback": ""
                }
            elif action == "save_multiple":
                return {
                    "action": "save_multiple",
                    "value": action_input,  # Keep the whole dict
                    "feedback": ""
                }
            elif action == "skip":
                return {"action": "skip", "value": "", "feedback": ""}
            elif action == "auto_fill":
                return {"action": "auto_fill", "value": "", "feedback": ""}
            elif action == "generate_request":
                return {"action": "generate_request", "value": "", "feedback": ""}
            elif action == "reject":
                feedback = action_input.get("feedback", f"I didn't catch that. Could you tell me about {field_description}, or say 'skip'?")
                return {"action": "reject", "value": "", "feedback": feedback}
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            print(f"[IdeaWorkshopAgent] ReAct parsing error: {e}")
            print(f"[IdeaWorkshopAgent] Raw response: {response}")
            # Fallback to save_value if we can't parse (lenient)
            return {
                "action": "save_value",
                "value": user_message,  # Use raw input
                "feedback": ""
            }

    def _generate_confirmation(self) -> str:
        """Generate confirmation message before story generation"""
        if self.mode == 'improvement':
            improvements = []
            if 'improvement_type' in self.collected_requirements:
                improvements.append(self.collected_requirements['improvement_type'])
            if 'characters' in self.collected_requirements:
                improvements.append(f"character changes: {self.collected_requirements['characters']}")
            if 'scenes_theme' in self.collected_requirements:
                improvements.append(f"scene/theme changes: {self.collected_requirements['scenes_theme']}")
            if 'structure' in self.collected_requirements:
                improvements.append(f"structure changes: {self.collected_requirements['structure']}")
            if 'tone_pacing' in self.collected_requirements:
                improvements.append(f"tone/pacing: {self.collected_requirements['tone_pacing']}")
            
            improvements_str = ", ".join(improvements)
            return f"Perfect! I'll improve your story with: {improvements_str}. Type 'generate' to create the improved version!"
        
        else:
            return "Great! I have all the details for your story. Type 'generate' to create it!"

    def should_generate_story(self, user_message: str) -> bool:
        """
        Check if we are ready to generate the story.
        Returns True ONLY if all required fields are collected.
        """
        # If there are still questions to ask, we are NOT ready
        if self.get_next_question() is not None:
            return False
            
        # If all fields are collected, we are ready
        return True

    def generate_story(self) -> str:
        """Generate improved or new story based on collected requirements"""
        if self.mode == 'improvement':
            return self._generate_improved_story()
        else:
            return self._generate_new_story()

    def _generate_improved_story(self) -> str:
        """Generate improved version of user's story"""
        if not self.user_story:
            return "Error: No original story provided."
        
        # Build improvement prompt
        improvements_text = "\n".join([
            f"- {key}: {value}" for key, value in self.collected_requirements.items()
        ])
        
        prompt = f"""You are a creative writing assistant for children's stories (ages 7-10).

**Original Story:**
{self.user_story}

**Requested Improvements:**
{improvements_text}

Please rewrite this story incorporating all the requested improvements. Keep it:
- Child-friendly and engaging
- Around the same length as the original
- Clear and easy to understand
- Fun and magical

**Improved Story:**"""
        
        return self._ask_ollama(prompt)

    def _generate_auto_fill_value(self, field: str) -> str:
        """Generate contextually appropriate auto-fill value based on existing requirements"""
        print(f"[IdeaWorkshopAgent] Generating auto-fill for: {field}")
        
        # Build context from existing requirements
        context_items = [f"{k}: {v}" for k, v in self.collected_requirements.items() if v and v != "__SKIP__"]
        context = ", ".join(context_items) if context_items else "no context yet"
        
        # If we have context, use LLM to generate a fitting value
        if len(context_items) > 0:
            prompt = f"""Given these story elements: {context}

What would be a good {field} for this children's story? Provide ONE brief, fitting suggestion (2-5 words only).

{field.capitalize()}:"""
            
            response = self._ask_ollama(prompt).strip()
            # Take first line, clean it up
            suggestion = response.split('\n')[0].strip()
            if 2 <= len(suggestion.split()) <= 10 and suggestion:  # Reasonable length
                print(f"[IdeaWorkshopAgent] Auto-filled {field} with: {suggestion}")
                return suggestion
        
        # Fallback to sensible defaults
        defaults = {
            'genre': 'adventure',
            'characters': 'a brave hero',
            'setting': 'a magical kingdom',
            'beginning': 'an unexpected discovery',
            'climax': 'a thrilling challenge',
            'ending': 'a happy resolution',
            'scenes': 'exciting moments of growth',
            'moral': 'courage and friendship'
        }
        
        default_value = defaults.get(field, 'something wonderful')
        print(f"[IdeaWorkshopAgent] Using default for {field}: {default_value}")
        return default_value

    def _summarize_description(self, description: str, field: str) -> str:
        """Summarize long user descriptions while preserving key details"""
        print(f"[IdeaWorkshopAgent] Summarizing description for {field} ({len(description.split())} words)...")
        
        prompt = f"""Summarize this {field} description for a children's story. Keep it concise (under 20 words) but preserve the most important details.

Description: {description}

Brief summary:"""
        
        response = self._ask_ollama(prompt).strip()
        summary = response.split('\n')[0].strip()  # Take first line
        
        # Validate summary
        if not summary or len(summary.split()) > 25:
            # Fallback: use first 15 words of original
            words = description.split()[:15]
            summary = ' '.join(words) + ('...' if len(description.split()) > 15 else '')
        
        print(f"[IdeaWorkshopAgent] Summarized to: {summary}")
        return summary

    def _review_metadata_consistency(self):
        """
        Review collected requirements for consistency and alignment.
        Uses LLM to adjust fields that clash (e.g. genre vs setting).
        """
        print("[IdeaWorkshopAgent] Reviewing metadata for consistency...")
        
        # Prepare context
        requirements_json = json.dumps(self.collected_requirements, indent=2)
        
        prompt = f"""You are a Story Logic Editor. Your job is to ensure the story requirements are consistent.

**Current Requirements:**
{requirements_json}

**Instructions:**
1. Check if all fields align with the main Genre and Theme.
2. If there are contradictions (e.g. Genre="Horror" but Setting="Happy Candy Land"), adjust the conflicting field to match the Genre.
3. If fields are vague (e.g. "something cool"), make them specific and fitting.
4. DO NOT change fields that are already specific and consistent.
5. Return the CLEANED JSON object.

**Output:** JSON ONLY."""

        response = self._ask_ollama(prompt)
        
        try:
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response[start:end]
                aligned_requirements = json.loads(json_str, strict=False)
                
                # Update our requirements with the aligned ones
                changes = []
                for k, v in aligned_requirements.items():
                    old_v = self.collected_requirements.get(k)
                    if old_v != v:
                        changes.append(f"{k}: '{old_v}' -> '{v}'")
                        self.collected_requirements[k] = v
                
                if changes:
                    print(f"[IdeaWorkshopAgent] Consistency Check Applied Changes:\n" + "\n".join(changes))
                else:
                    print("[IdeaWorkshopAgent] Consistency Check Passed (No changes needed).")
            else:
                print("[IdeaWorkshopAgent] Warning: Could not parse consistency check JSON.")
        except Exception as e:
            print(f"[IdeaWorkshopAgent] Error in consistency check: {e}")

    def _generate_new_story(self) -> str:
        """Generate new story from collected requirements"""
        
        # Step 1: Review and Align Metadata
        self._review_metadata_consistency()
        
        requirements_text = "\n".join([
            f"- {key}: {value}" for key, value in self.collected_requirements.items()
        ])
        
        prompt = f"""You are a creative writing assistant for children's stories (ages 7-10).

Create a complete, engaging story based on these requirements:
{requirements_text}

Requirements:
- Write a full story (around 300-500 words)
- Make it magical and engaging for children
- Include a clear beginning, middle, and end
- Make characters relatable and fun
- Keep language simple and appropriate for ages 7-10

**Story:**"""
        
        return self._ask_ollama(prompt)
