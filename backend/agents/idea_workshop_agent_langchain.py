# backend/agents/idea_workshop_agent_langchain.py
import json
from typing import Dict, List, Tuple, Optional
from langchain_aws import ChatBedrock

from backend.model_config import IDEA_WORKSHOP_AGENT_MODEL, BEDROCK_MODEL_ID

# Custom simple memory to avoid import errors
class SimpleMemory:
    def __init__(self):
        self.messages = []
    
    def add_user_message(self, message: str):
        self.messages.append({"role": "user", "content": message})
        
    def add_ai_message(self, message: str):
        self.messages.append({"role": "assistant", "content": message})
        
    def get_history_string(self) -> str:
        return "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in self.messages])

class IdeaWorkshopAgentLangChain:
    """
    LangChain-based Workshop Agent with advanced conversation rules
    Handles: new_idea and improvement modes with multi-turn conversations
    """
    
    def __init__(self, mode: str, conversation_history: List[Dict], llm_model: str = IDEA_WORKSHOP_AGENT_MODEL):
        """
        Initialize LangChain-powered workshop agent
        
        Args:
            mode: 'improvement' or 'new_idea'
            conversation_history: List of {role, message, metadata} dicts
            llm_model: Ollama model to use
        """
        self.mode = mode
        self.conversation_history = conversation_history
        self.llm_model = llm_model
        
        # State management
        self.collected_requirements = {}
        self.skipped_fields = []
        self.in_update_mode = False
        self.fields_being_updated = [] # Track fields currently being updated
        
        self.user_story = None  # For improvement mode
        self.last_question_field = None
        
        # Required fields mapping
        self.required_fields_questions = {
            'genre': "What type or genre of story do you want? (e.g., adventure, fantasy, mystery, etc.)",
            'characters': "What characters should be included in your story? (Tell me about them)",
            'setting': "What theme or world should the story take place in?",
            'beginning': "What kind of beginning do you prefer for your story?",
            'climax': "What type of climax should the story have?",
            'ending': "What ending do you want for your story?",
            'scenes': "Are there any specific scenes or moments you'd like to include?",
            'moral': "Is there a moral or lesson you'd like the story to convey?"
        }
        
        # Initialize LangChain LLM (Amazon Bedrock — Claude Sonnet 4.5)
        self.llm = ChatBedrock(
            model_id=BEDROCK_MODEL_ID,
            region_name="us-east-1",
            model_kwargs={"temperature": 0.7, "max_tokens": 2048},
        )
        
        # Initialize custom memory
        self.memory = SimpleMemory()
        
        # Restore conversation history
        self._restore_conversation_history()
        self._extract_requirements_from_history()
    
    def _create_tool_prompt(self, user_message: str) -> str:
        """Create prompt with tool descriptions for LLM"""
        
        # Check current status
        missing_fields = self._get_missing_fields()
        is_all_collected = len(missing_fields) == 0

        # Context construction
        display_requirements = self.collected_requirements.copy()
        
        # Consolidate characters for context
        character_details = []
        for k, v in list(display_requirements.items()):
            if k == 'characters' or k.startswith('character'):
                 character_details.append(f"{k}: {v}")
        if character_details:
             display_requirements['characters'] = "; ".join(character_details)
        
        context_items = []
        for k, v in display_requirements.items():
            if k == 'characters':
                context_items.append(f"{k}: {v}")
            elif not k.startswith('character') and v and v != "__SKIP__":
                context_items.append(f"{k}: {v}")
        
        context_str = ", ".join(context_items)

        # Extract the last assistant message to give the LLM conversational context
        last_assistant_message = ""
        for msg in reversed(self.memory.messages):
            if msg.get('role') == 'assistant':
                last_assistant_message = msg.get('content', '')
                break

        # =================================================================================
        # MODE 1: CONFIRMATION PHASE (All fields collected)
        # =================================================================================
        if is_all_collected:
            prompt = f"""You are a Story Workshop Assistant. 
Status: ALL STORY FIELDS HAVE BEEN COLLECTED.
Current Context: {context_str}

**YOUR GOAL**: Wait for the user to either CONFIRM (to generate) or REQUEST CHANGES.

**INPUT VALIDATION RULES**:
If the user's input is a greeting ("hi", "hello"), gibberish ("asdfgh"), math ("9+9"), only numbers, symbols, or a URL — it is INVALID.
For INVALID input → respond ONLY with: "I have all your details. If you want any changes in the field, tell me, otherwise write 'generate story'."
Do NOT save or confirm anything for invalid input.

**LOGIC RULES:**

1. **DEFAULT / CONFIRMATION**: 
   - If the user has NOT explicitly asked to generate or change something yet (or just finished the last field).
   - RESPONSE MUST BE EXACTLY: "I have all your details. If you want any changes in the field, tell me, otherwise write 'generate story'."
   - Action: `none` or just simple response.
   
2. **GENERATE REQUEST**: 
   - Triggers ONLY if user says: "generate", "generate story", "create story", "make story", "go ahead", "start".
   - Action: `generate_story`
   
3. **SPECIFIC FIELD CHANGE**:
   - if user says "I want changes in [field]" or "change [field]" (e.g., "change genre", "modify characters").
   - Action: `prepare_changes` with `fields=["genre"]`
   - Response: "What would you like the new genre to be?"
   
4. **MULTI-FIELD CHANGE**:
   - If user says "Change characters and theme".
   - Action: `prepare_changes` with `fields=["characters", "setting"]`
   - Response: "You want to change the characters and the setting. Please provide the updated characters and setting." (Combine them in one question).
   
5. **UNSPECIFIED CHANGE**:
   - If user says "I want changes" but doesn't say which field.
   - Action: `ask_which_field`
   - Response: "Which field do you want to change?"

6. **PROVIDING UPDATE DIRECTLY**:
   - If user says "Change genre to Horror".
   - Action: `save_field` (field="genre", value="Horror")
   - Response: "Updated genre to Horror. I have all your details. If you want any changes in the field, tell me, otherwise write 'generate story'."

**User Input**: "{user_message}"

**Available Actions**:
- `generate_story`: {{ "action": "generate_story", "response": "Generating..." }}
- `prepare_changes`: {{ "action": "prepare_changes", "fields": ["field1", "field2"], "response": "..." }}
- `ask_which_field`: {{ "action": "ask_which_field", "response": "Which field do you want to change?" }}
- `save_field`: {{ "action": "save_field", "field": "...", "value": "...", "response": "..." }}

Respond with VALID JSON only.
"""
            return prompt

        # =================================================================================
        # MODE 2: COLLECTION / UPDATE PHASE (Missing fields exist)
        # =================================================================================
        
        # Logic for what to ask next
        if self.in_update_mode and self.fields_being_updated:
            # We are specifically looking for the fields likely cleared recently
            # Prioritize fields in 'fields_being_updated' that are currently missing
            target_fields = [f for f in self.fields_being_updated if f in missing_fields]
            if not target_fields:
                # Fallback if something got out of sync, just use standard missing
                target_fields = missing_fields
        else:
            target_fields = missing_fields

        next_field = target_fields[0]
        question = self.required_fields_questions.get(next_field)
        
        # If multiple fields are targeted in update mode, we can try to ask for all,
        # but the tools generally handle one Save at a time or Save Multiple. 
        # The PROMPT should encourage the user to provide them.
        
        prompt = f"""You are a Story Workshop Assistant. 
Status: COLLECTING DETAILS.
Missing Fields: {target_fields}
Collected So Far: {context_str}

**GOAL**: Collect the missing information from the user.

**SUGGESTION CONFIRMATION RULE (Highest Priority — check this FIRST):**
Look at the "Previous Assistant Message" below.
If that message presented a generated/suggested value for the current field AND asked the user whether it's acceptable
(e.g. "Here's one: '...' Does that work for you?", "How about '...'?", "I've chosen '...' for you. Is that okay?"),
AND the user's current input is an affirmative reply such as:
"yes", "yeah", "yep", "ok", "okay", "sure", "fine", "that works", "looks good", "great", "perfect", "sounds good", "go ahead", "that's fine", "i like it", "accepted", "correct", "right", "good"
→ Extract the suggested VALUE from the previous assistant message and use `save_field` to save it.
→ Do NOT mark this as invalid. Do NOT ask the question again.

**Previous Assistant Message**: "{last_assistant_message}"

**INPUT VALIDATION RULES (Apply AFTER the confirmation check above):**
Before saving a value, you MUST validate whether the user's input is a genuine, meaningful answer to the question being asked.
A response is INVALID if it is any of the following:
- A greeting or social filler (e.g. "hi", "hello", "hey", "how are you", "good morning", "what's up")
- Only numbers or a math expression (e.g. "9+9=?", "123-123", "42", "100")
- Only symbols or special characters (e.g. "@@##", "!!??", "---", "***")
- A URL or web address (e.g. "http://...", "www.example.com")
- Random letters with no meaning (e.g. "asdfgh", "qwerty", "asa45sjsa")
- Completely off-topic question unrelated to story creation (e.g. "what is 2+2", "who won the world cup")
- For the VERY FIRST field (no fields collected yet): a response shorter than 3 meaningful words is ALSO invalid.
If the input is INVALID → use `invalid_input` action, include the SAME question in the response.
If the input IS a valid story-related answer (even a single word like "horror" or "fantasy" or character names like "john and jack") → save it.

**INSTRUCTIONS**:
1. **Focus**: Ask for **{next_field}**.
   - Question: "{question}"
2. **Update Mode**: If user was asked to provide multiple things (e.g. chars and theme), and provided one, ensure you ASK for the remaining one ({target_fields}).
   - Example: "You still haven't provided the updated theme. Please give the new theme."
3. **Auto-Fill**: "pick yourself", "random" → `auto_fill_field`
4. **Skip**: "skip", "pass" → `skip_field`
5. **Save**: If user provides a valid answer → `save_field`.
6. **Multi-Save**: If user provides multiple valid values → `save_multiple`.
7. **Invalid Input**: If input fails validation rules above → `invalid_input`.

**User Input**: "{user_message}"

**Available Actions**:
- `save_field`: {{ "action": "save_field", "field": "{next_field}", "value": "...", "response": "Confirmed.\n\n<next question or completion message>" }}
- `save_multiple`: {{ "action": "save_multiple", "detected_fields": {{ "field": "val" }}, "response": "..." }}
- `auto_fill_field`: {{ "action": "auto_fill_field", "field": "{next_field}", "response": "..." }}
- `skip_field`: {{ "action": "skip_field", "field": "{next_field}", "response": "..." }}
- `invalid_input`: {{ "action": "invalid_input", "response": "<friendly explanation of why it was invalid + repeat the EXACT same question>" }}

Respond with VALID JSON only.
"""
        return prompt

    def _get_fields_status_string(self) -> str:
        """Get status string of all required fields"""
        status = []
        for field in self.required_fields_questions.keys():
            val = self.collected_requirements.get(field)
            if val == "__SKIP__":
                status.append(f"- {field}: [SKIPPED]")
            elif val:
                status.append(f"- {field}: [COLLECTED]")
            else:
                 # Check if we have gathered this requirement via other keys (e.g. character_*)
                 if field == 'characters' and any(k.startswith('character') for k in self.collected_requirements):
                      status.append(f"- {field}: [COLLECTED (Derived)]")
                 else:
                      status.append(f"- {field}: [MISSING]")
        return "\n".join(status)
    
    def _extract_requirements_from_history(self):
        """Extract collected requirements from conversation history"""
        for msg in self.conversation_history:
            metadata = msg.get('metadata', {})
            if 'requirements' in metadata:
                self.collected_requirements.update(metadata['requirements'])
                
            # Restore state if present
            if 'in_update_mode' in metadata:
                self.in_update_mode = metadata['in_update_mode']
            if 'fields_being_updated' in metadata:
                self.fields_being_updated = metadata['fields_being_updated']
            
            # Restore last_question_field
            if msg.get('role') == 'assistant':
                message_text = msg.get('message', '').lower()
                for field, question in self.required_fields_questions.items():
                    if question.lower() in message_text:
                        self.last_question_field = field
                        break
    
    # ==================== TOOL IMPLEMENTATIONS ====================
    
    def _normalize_field_name(self, field: str) -> str:
        """Normalize field names to match required keys"""
        field = field.lower().strip()
        
        # Mappings for common LLM hallucinations
        mappings = {
            'character_type': 'characters',
            'character_name': 'characters',
            'character_details': 'characters',
            'climax_type': 'climax',
            'climax_description': 'climax',
            'setting_description': 'setting',
            'story_beginning': 'beginning',
            'story_ending': 'ending',
            'moral_lesson': 'moral',
            'genre_type': 'genre'
        }
        
        # Key prefix matching
        if field.startswith('character'):
            return 'characters'
        
        return mappings.get(field, field)

    def _save_field_tool(self, field: str, value: str) -> str:
        """Save a field value"""
        if field and value:
            norm_field = self._normalize_field_name(field)
            
            # Special handling for clarification requests
            if value == "CLARIFICATION_NEEDED":
                print(f"[LangChain] User requested clarification for {norm_field}")
                return f"User needs clarification for {norm_field}"
            
            # Special handling for characters: only append if NOT in update mode (overwrite in update mode)
            # Or if user explicitly says "add character". 
            # Simplified: In update mode, we usually want to replace usage or add? 
            # Requirement says "Ask for updated value... Update it". Implies overwrite.
            # But the 'characters' field often accumulates. 
            # Strategy: If in update mode, overwrite. If in new_story mode, append?
            # Safer: Just Overwrite for now as per "Change" semantic.
            
            if norm_field == 'characters' and self.collected_requirements.get('characters') and not self.in_update_mode:
                current = self.collected_requirements['characters']
                if isinstance(current, str) and value not in current:
                    self.collected_requirements['characters'] = f"{current}; {value}"
                else:
                    self.collected_requirements['characters'] = value
            else:
                self.collected_requirements[norm_field] = value
                
            # Clear from fields_being_updated if present
            if norm_field in self.fields_being_updated:
                self.fields_being_updated.remove(norm_field)
                
            print(f"[LangChain] Saved '{value}' to {norm_field} (orig: {field})")
            return f"Successfully saved '{value}' to {norm_field}"
        return "Error: Missing field or value"
    
    def _skip_field_tool(self, field: str) -> str:
        """Mark field as skipped"""
        if field:
            norm_field = self._normalize_field_name(field)
            self.skipped_fields.append(norm_field)
            self.collected_requirements[norm_field] = "__SKIP__"
            
            if norm_field in self.fields_being_updated:
                self.fields_being_updated.remove(norm_field)

            print(f"[LangChain] Skipped {norm_field} (orig: {field})")
            return f"Field '{norm_field}' marked as skipped"
        return "Error: Missing field name"
    
    def _auto_fill_field_tool(self, field: str) -> str:
        """Auto-fill a field with contextual value"""
        if not field:
            field = self.last_question_field
            
        if field:
            norm_field = self._normalize_field_name(field)
            value = self._generate_auto_fill_value(norm_field)
            self.collected_requirements[norm_field] = value
            
            if norm_field in self.fields_being_updated:
                self.fields_being_updated.remove(norm_field)

            print(f"[LangChain] Auto-filled {norm_field} with '{value}'")
            return f"Auto-generated '{value}' for {norm_field}"
        return "Error: Missing field name"
    
    def _save_multiple_fields(self, detected_fields: Dict) -> str:
        """Save multiple detected fields"""
        normalized_data = {}
        for k, v in detected_fields.items():
            norm_k = self._normalize_field_name(k)
            normalized_data[norm_k] = v
            # Also clear from pending updates
            if norm_k in self.fields_being_updated:
                self.fields_being_updated.remove(norm_k)
            
        self.collected_requirements.update(normalized_data)
        self.all_fields_detected = True
        summary = ", ".join([f"{k}={v}" for k, v in normalized_data.items()])
        print(f"[LangChain] Saved multiple fields: {summary}")
        return f"Saved {len(normalized_data)} fields"

    def _prepare_changes_tool(self, fields: List[str]) -> str:
        """Prepare for updating specific fields"""
        self.in_update_mode = True
        normalized_fields = [self._normalize_field_name(f) for f in fields]
        self.fields_being_updated.extend(normalized_fields)
        
        # CLEAR the values so they become 'missing'
        for f in normalized_fields:
            if f in self.collected_requirements:
                del self.collected_requirements[f]
                
        return f"Cleared fields {normalized_fields} for update."

    # ==================== HELPER METHODS ====================
    
    def _generate_auto_fill_value(self, field: str) -> str:
        """Generate contextual auto-fill value"""
        defaults = {
            'genre': 'adventure',
            'characters': 'brave hero',
            'setting': 'magical kingdom',
            'beginning': 'unexpected discovery',
            'climax': 'thrilling challenge',
            'ending': 'happy resolution',
            'scenes': 'exciting moments',
            'moral': 'courage and friendship'
        }
        return defaults.get(field, 'something wonderful')
    
    def _get_missing_fields(self) -> List[str]:
        """Get list of missing fields with character consolidation logic"""
        required = ['genre', 'characters', 'setting', 'beginning', 'climax', 'ending', 'scenes', 'moral']
        missing = []
        
        # Check if we have any character info stored in other keys
        has_character_info = self.collected_requirements.get('characters')
        if not has_character_info:
             # If ANY key starts with 'character', consider the 'characters' requirement met
             # BUT NOT if we are in update mode and explicitly looking for 'characters'
             if not (self.in_update_mode and 'characters' in self.fields_being_updated):
                 for k in self.collected_requirements:
                     if k.startswith('character'):
                         has_character_info = True
                         break
        
        for field in required:
            # Special handling for characters
            if field == 'characters' and has_character_info:
                continue
                
            value = self.collected_requirements.get(field, '')
            if value == '__SKIP__':
                continue
            if not value:
                missing.append(field)
        return missing
    
    def _get_next_missing_field(self) -> Optional[str]:
        """Get next missing field"""
        missing = self._get_missing_fields()
        return missing[0] if missing else None
    
    def _restore_conversation_history(self):
        """Restore conversation from history"""
        for msg in self.conversation_history:
            role = msg.get('role')
            content = msg.get('message', '')
            if role == 'user':
                self.memory.add_user_message(content)
            elif role == 'assistant':
                self.memory.add_ai_message(content)
    
    # ==================== PUBLIC API ====================
    
    def process_message(self, user_message: str) -> Tuple[str, Dict]:
        """
        Process user message using LangChain LLM with tool calling
        """
        try:
            # Create tool prompt
            prompt = self._create_tool_prompt(user_message)
            
            # Get LLM response
            llm_response = self.llm.invoke(prompt)
            print(f"[LangChain] LLM Response: {llm_response[:200]}...")
            
            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}')
                if json_start != -1 and json_end != -1:
                    json_str = llm_response[json_start:json_end+1]
                    action_data = json.loads(json_str, strict=False)
                else:
                     # Fallback: if no JSON, treat as direct response but might be broken
                     print("No JSON found, raw response")
                     action_data = {}
                
                # Execute action
                action = action_data.get('action', '')
                initial_response = action_data.get('response', '')
                
                # Default response if empty
                if not initial_response:
                    initial_response = "Confirmed."

                story_generated_flag = False
                
                if action == 'save_field':
                    field = action_data.get('field')
                    value = action_data.get('value')
                    self._save_field_tool(field, value)
                    
                elif action == 'save_multiple':
                    detected_fields = action_data.get('detected_fields', {})
                    self._save_multiple_fields(detected_fields)
                    
                elif action == 'skip_field':
                    field = action_data.get('field', self.last_question_field)
                    self._skip_field_tool(field)
                    
                elif action == 'auto_fill_field':
                    field = action_data.get('field', self.last_question_field)
                    self._auto_fill_field_tool(field)
                
                elif action == 'prepare_changes':
                    fields = action_data.get('fields', [])
                    self._prepare_changes_tool(fields)
                    
                elif action == 'ask_which_field':
                    # Just passing through the response "Which field?"
                    pass
                
                elif action == 'invalid_input':
                    # User gave invalid/nonsensical input — just return the re-ask response, save nothing
                    pass

                elif action == 'generate_story':
                     # The decision to generate is now explicit from the LLM
                     # Double check if everything is actually ready?
                     if not self._get_missing_fields():
                         return self.generate_story(), {'story_generated': True}
                     else:
                         initial_response = "I can't generate the story yet. Some details are missing."

                # Recalculate missing fields after action
                missing_fields = self._get_missing_fields()
                
                # Turn off update mode if all fields are back
                if not missing_fields and self.in_update_mode:
                    self.in_update_mode = False

                final_response = initial_response

                # STORY LOGIC: If fields are missing (and LLM didn't ask), force the next question
                # But if we are in CONFIRMATION mode (no missing fields), we rely on LLM's confirm msg
                
                if missing_fields:
                    next_field = missing_fields[0]
                    question = self.required_fields_questions.get(next_field)
                    
                    llm_asked_question = ('?' in final_response or 
                                         any(q in final_response.lower() for q in ['what ', 'how ', 'which ', 'tell me']))
                    
                    if question and not llm_asked_question:
                        final_response += f"\n\n{question}"
                else: 
                     # If we just finished collecting (missing became empty this turn),
                     # AND the action wasn't generate, we might want to ensure the confirmation msg is there.
                     # But the LLM prompt rule 6 (PROVIDING UPDATE DIRECTLY) says it should output it.
                     # Loop: The NEXT turn will hit the CONFIRMATION MODE prompt anyway. 
                     # However, if this was the last `save_field`, the response might not have the confirmation msg if the LLM followed the COLLECTION prompt.
                     # We can append it if missing.
                     confirm_msg = "I have all your details. If you want any changes in the field, tell me, otherwise write 'generate story'."
                     if confirm_msg not in final_response and not action == 'generate_story':
                         final_response += f"\n\n{confirm_msg}"

                
                # Build metadata
                metadata = {
                    'requirements': self.collected_requirements.copy(),
                    'skipped_fields': self.skipped_fields.copy(),
                    'in_update_mode': self.in_update_mode,
                    'fields_being_updated': self.fields_being_updated.copy()
                }
                
                # Add to memory
                self.memory.add_user_message(user_message)
                self.memory.add_ai_message(final_response)
                
                return final_response, metadata
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"[LangChain] JSON parsing error: {e}")
                return llm_response, {}
            
        except Exception as e:
            print(f"[LangChain Agent Error]: {e}")
            import traceback
            traceback.print_exc()
            return "I encountered an error. Could you try rephrasing your message?", {}
    
    def should_generate_story(self, user_message: str) -> bool:
        """Check if ready to generate story"""
        return not self._get_missing_fields()
    
    def generate_story(self) -> str:
        """Generate story with word count logic"""
        # Mock story generation logic
        detected_word_count = "300" # Default
        
        story_prompt = f"""Write a story based on these details:
{json.dumps(self.collected_requirements, indent=2)}

IMPORTANT: The story must be approximately 300 words long.
"""
        # Call LLM to generate story
        story = self.llm.invoke(story_prompt)
        
        return story
