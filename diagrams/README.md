# personalized-ai-storybook System Diagrams

This folder contains comprehensive UML and DFD diagrams for the personalized-ai-storybook system, created according to software engineering best practices and the guidelines provided in the `diagram_documentation` folder.

## 📁 Available Formats

- **PlantUML (.puml)**: All diagrams in this folder - best for detailed documentation and print quality
- **Mermaid (.mmd)**: All diagrams in `mermaid/` subfolder - best for GitHub/GitLab rendering and web integration

Both formats contain the **same 14 diagrams** with identical content, just in different syntax.

## 📋 Diagram Index

### 1. **Use Case Diagram** (`01_use_case_diagram.puml`)
**Purpose**: Shows all actors and their interactions with the system

**Contents**:
- **Actors**: Guest User, Authenticated User, Parent/Educator, Child
- **Use Cases**: 
  - Story Generation (from prompt, from voice, with images, with audio)
  - Interactive Features (chat, idea workshop)
  - Export Features (PDF, audio)
  - Authentication (register, login, profile)
- **External Systems**: Ollama LLM, Stable Diffusion, Whisper STT, Coqui TTS
- **Relationships**: Include, extend, and dependency relationships

**Key Insights**:
- Shows distinction between guest (text-only) and authenticated users (with images)
- Demonstrates system dependencies on external AI services
- Illustrates the complete feature set available to different user types

---

### 2. **Domain Model** (`02_domain_model.puml`)
**Purpose**: Conceptual class diagram showing entities and relationships

**Contents**:
- **Core Entities**: User, Story, Scene, Character, Setting
- **Chat Entities**: ChatConversation, ChatMessage
- **Workshop Entities**: WorkshopSession, WorkshopMessage, WorkshopStory
- **Media Entities**: Image, Audio, PDFDocument
- **Relationships**: Composition, aggregation, and association with cardinality

**Key Insights**:
- Each story has exactly 3 scenes (configurable)
- Stories can have multiple characters that can be chatted with
- Workshop sessions support iterative story development
- Clear separation between metadata (database) and media files (file system)

---

### 3. **Sequence Diagram: Story Generation** (`03_sequence_story_generation.puml`)
**Purpose**: Shows the complete story generation workflow with **internal implementation details**

**Type**: Design-level Sequence Diagram (shows HOW the system works internally)

**Contents**:
- **Participants**: User, Frontend, Backend, All AI Agents, LLM, Stable Diffusion, Database
- **Flow**: 
  1. User submits prompt
  2. PromptAgent validates and enhances
  3. DirectorAgent orchestrates pipeline
  4. WriterAgent generates draft
  5. ReviewerAgent provides feedback
  6. EditorAgent finalizes story
  7. ImageAgent generates illustrations (optional)
  8. Database stores results
  9. Frontend displays story

**Key Insights**:
- Shows the multi-agent pipeline in action
- Demonstrates two-pass image generation (txt2img → img2img)
- Illustrates optional image generation based on user preference
- Shows database persistence and frontend rendering
- **This is NOT a System Sequence Diagram** - it shows internal objects and implementation

---

### 4. **Sequence Diagram: Character Chat** (`04_sequence_character_chat.puml`)
**Purpose**: Shows character chat interaction workflow

**Contents**:
- **Participants**: User, Frontend, Backend, ChatbotAgent, LLM, Database
- **Flow**:
  1. User selects character
  2. System retrieves story context
  3. ChatbotAgent generates character-specific response
  4. Conversation saved to database
  5. Response displayed to user

**Key Insights**:
- ChatbotAgent uses story context for accurate character portrayal
- Conversations are persisted for history tracking
- Responses are child-friendly (2-4 sentences)

---

### 5. **Sequence Diagram: Idea Workshop** (`05_sequence_idea_workshop.puml`)
**Purpose**: Shows the interactive story ideation process

**Contents**:
- **Participants**: User, Frontend, Backend, IdeaWorkshopAgent, LLM, Database
- **Flow**:
  1. User starts workshop session
  2. Interactive conversation loop
  3. Agent extracts requirements (characters, setting, themes)
  4. Requirements saved as metadata
  5. Final story generation from collected requirements

**Key Insights**:
- Multi-turn conversation with requirement extraction
- Metadata accumulation across conversation
- Supports both "new idea" and "improvement" modes
- Workshop history is preserved in database

---

### 6. **Activity Diagram** (`06_activity_diagram.puml`)
**Purpose**: Shows the complete workflow with decision points

**Contents**:
- **Swimlanes**: User, Frontend, Backend Agents
- **Activities**: 
  - Prompt validation
  - Multi-agent story generation
  - Parallel image generation for scenes
  - Background evaluation
  - Story display and navigation
  - Optional character chat
  - Optional PDF export
- **Decision Points**: Prompt validity, image generation, chat, export

**Key Insights**:
- Shows parallel processing for multiple scene images
- Demonstrates asynchronous evaluation agent
- Illustrates optional features (chat, export)
- Clear separation of responsibilities across layers

---

### 7. **State Diagram** (`07_state_diagram.puml`)
**Purpose**: Shows story generation lifecycle states

**Contents**:
- **States**: 
  - Idle
  - PromptValidation (with substates)
  - WritingDraft (with retry logic)
  - Reviewing
  - Editing
  - ImageGeneration (with two-pass substates)
  - Completed
  - DisplayingStory (with page navigation and chat substates)
- **Transitions**: Events and conditions
- **Nested States**: Complex processes broken down

**Key Insights**:
- Shows error handling and retry mechanisms
- Demonstrates nested states for complex processes
- Illustrates optional image generation path
- Shows page navigation and character chat as substates of DisplayingStory

---

### 8. **DFD Context Diagram** (`08_dfd_context.puml`)
**Purpose**: Level 0 DFD showing system as single process

**Contents**:
- **External Entities**: User, Ollama LLM, Stable Diffusion, Whisper STT, Coqui TTS
- **Data Flows**: 
  - Inputs: Story prompts, voice input, chat messages, credentials
  - Outputs: Generated stories, images, PDFs, audio, responses

**Key Insights**:
- System boundary clearly defined
- All external dependencies identified
- High-level view of system inputs and outputs

---

### 9. **DFD Level 1** (`09_dfd_level1.puml`)
**Purpose**: Decomposes system into main processes

**Contents**:
- **Processes**:
  1. Authenticate User
  2. Generate Story
  3. Generate Images
  4. Generate Audio
  5. Manage Character Chat
  6. Manage Idea Workshop
  7. Export Content
- **Data Stores**: Users, Stories, Chat Conversations, Workshop Sessions, Generated Files
- **Data Flows**: Between processes, external entities, and data stores

**Key Insights**:
- Shows data flow between major system components
- Illustrates database interactions
- Demonstrates file system storage for media
- Shows integration between different features

---

### 10. **DFD Level 2: Story Generation** (`10_dfd_level2_story_generation.puml`)
**Purpose**: Detailed breakdown of story generation process

**Contents**:
- **Sub-processes**:
  - 2.1: Validate and Enhance Prompt (PromptAgent)
  - 2.2: Orchestrate Pipeline (DirectorAgent)
  - 2.3: Write Story Draft (WriterAgent)
  - 2.4: Review Story (ReviewerAgent)
  - 2.5: Edit and Finalize (EditorAgent)
  - 2.6: Evaluate Quality (EvaluationAgent - background)
- **Data Stores**: Prompts, Drafts, Reviews, Edits, Stories
- **Data Flows**: Between agents and data stores

**Key Insights**:
- Shows multi-agent pipeline in detail
- Demonstrates intermediate storage at each stage
- Illustrates retry logic in WriterAgent
- Shows asynchronous evaluation process

---

### 11. **Class Diagram** (`11_class_diagram.puml`)
**Purpose**: Complete system architecture with classes and relationships

**Contents**:
- **Packages**:
  - Database Models (User, Story, Chat, Workshop entities)
  - Pydantic Schemas (Request/Response models)
  - AI Agents (BaseAgent and all specialized agents)
  - Services (Auth, Story, Chat, Workshop)
  - FastAPI Application (Routers)
- **Relationships**: Inheritance, composition, aggregation, dependencies

**Key Insights**:
- Shows object-oriented design structure
- Demonstrates inheritance hierarchy for agents
- Illustrates service layer pattern
- Shows separation of concerns across layers

---

### 12. **Component Diagram** (`12_component_diagram.puml`)
**Purpose**: Shows system components and their relationships

**Contents**:
- **Layers**:
  - Frontend Layer (Next.js components)
  - Backend Layer (FastAPI services)
  - AI Agent Layer (Multi-agent pipeline)
  - AI Model Layer (Ollama, Stable Diffusion, Whisper, TTS)
  - Data Layer (PostgreSQL, File System)
- **Component Relationships**: Dependencies and data flows

**Key Insights**:
- Shows layered architecture
- Demonstrates component dependencies
- Illustrates separation between services and agents
- Shows integration with external AI models

---

### 13. **Deployment Diagram** (`13_deployment_diagram.puml`)
**Purpose**: Physical deployment architecture

**Contents**:
- **Nodes**:
  - User Device (Web Browser with Next.js)
  - Application Server (FastAPI, AI Agents)
  - AI Model Server (Ollama, Stable Diffusion, Whisper, TTS)
  - Database Server (PostgreSQL)
  - File Storage (Generated content)
- **Communication**: Protocols and ports
- **System Requirements**: Hardware and software specifications

**Key Insights**:
- Shows physical deployment topology
- Demonstrates local deployment (no cloud dependencies)
- Illustrates GPU acceleration for AI models
- Shows file system organization

---

### 14. **System Sequence Diagram** (`14_system_sequence_diagram.puml`)
**Purpose**: Black-box view of system interactions for **ONE specific scenario**

**Type**: Requirements-level System Sequence Diagram (shows WHAT the system does, not HOW)

**Contents**:
- **Actors**: User
- **System**: Treated as black box (no internal objects shown)
- **Scenario**: Generate Story (Main Success)
- **System Operations**: 
  - makeNewStory()
  - enterPrompt(prompt_text)
  - selectOptions(generate_images, mode)
  - generateStory()
  - viewPage(page_number)
- **Interactions**: Simple user-system message exchange

**Key Insights**:
- Shows system from user perspective
- **System treated as BLACK BOX** - no implementation details
- Shows **high-level system operations** only
- Focuses on **external events** and **system responses**
- Used for **requirements analysis**, not design
- **This IS a proper System Sequence Diagram** per UML guidelines

---

## 🔧 How to Use These Diagrams

### Viewing PlantUML Diagrams

**Option 1: Online Viewer**
1. Go to [PlantUML Online Server](http://www.plantuml.com/plantuml/uml/)
2. Copy the content of any `.puml` file
3. Paste and view the rendered diagram

**Option 2: VS Code Extension**
1. Install "PlantUML" extension in VS Code
2. Open any `.puml` file
3. Press `Alt+D` to preview

**Option 3: Local PlantUML**
1. Install Java and Graphviz
2. Download PlantUML JAR
3. Run: `java -jar plantuml.jar diagram_file.puml`

### Exporting Diagrams

**To PNG:**
```bash
java -jar plantuml.jar -tpng *.puml
```

**To SVG:**
```bash
java -jar plantuml.jar -tsvg *.puml
```

**To PDF:**
```bash
java -jar plantuml.jar -tpdf *.puml
```

---

## 📚 Diagram Guidelines Followed

These diagrams were created according to the guidelines in `diagram_documentation/`:

### From `UML-artifacts-material.txt`:
✅ Use Case Diagrams with proper actor relationships
✅ Domain Model showing conceptual classes (not software artifacts)
✅ Sequence Diagrams with proper message syntax
✅ Activity Diagrams with swimlanes and decision points
✅ State Diagrams with nested states and transitions
✅ Class Diagrams with proper relationships and multiplicity
✅ Component Diagrams showing system architecture
✅ Deployment Diagrams showing physical architecture
✅ System Sequence Diagrams treating system as black box

### From `Data-Flow-Diagrams-_DFD_.txt`:
✅ Context Diagram (Level 0) showing system boundary
✅ Level 1 DFD with 7 main processes
✅ Level 2 DFD for Story Generation (most complex process)
✅ Proper process naming (verb phrases)
✅ Data stores with plural nouns
✅ External entities clearly marked
✅ Data flows with descriptive names
✅ No direct connections between data stores or external entities

### From `System-Modeling-State-Diagram.txt`:
✅ State names as adjectives or present continuous verbs
✅ Transitions with events and guards
✅ Nested states for complex processes
✅ Initial and final states marked
✅ Self-transitions where appropriate
✅ Alternative entry/exit points for substates

---

## 🎯 Diagram Coverage

| Aspect | Diagrams |
|--------|----------|
| **User Interactions** | Use Case, System Sequence |
| **Data Structure** | Domain Model, Class Diagram |
| **Workflows** | Sequence Diagrams (3), Activity Diagram |
| **System States** | State Diagram |
| **Data Flow** | DFD Context, Level 1, Level 2 |
| **Architecture** | Class, Component, Deployment |

---

## 📝 Notes

- All diagrams are in **PlantUML** format for easy editing and version control
- Diagrams follow **UML 2.0** standards
- DFDs follow **Gane-Sarson** notation
- Diagrams are consistent with project documentation in `memory_bank/`
- Each diagram includes explanatory notes for clarity
- Diagrams are organized by complexity and purpose

---

## 🔄 Updating Diagrams

When updating the system, update relevant diagrams:

**Code Changes** → Update:
- Class Diagram
- Component Diagram
- Sequence Diagrams

**New Features** → Update:
- Use Case Diagram
- Activity Diagram
- DFD Level 1

**Database Changes** → Update:
- Domain Model
- Class Diagram
- DFD diagrams

**Deployment Changes** → Update:
- Deployment Diagram
- Component Diagram

---

**Created**: December 5, 2025  
**Total Diagrams**: 14  
**Format**: PlantUML (.puml)  
**Maintained by**: Development Team

---

## 📞 Questions?

For questions about these diagrams:
1. Review the diagram documentation in `diagram_documentation/`
2. Check the memory bank in `memory_bank/`
3. Refer to the main project README
4. Contact the development team
