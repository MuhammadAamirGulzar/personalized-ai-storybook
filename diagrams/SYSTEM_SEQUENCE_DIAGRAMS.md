# personalized-ai-storybook - System Sequence Diagrams (SSDs)

## 📋 Overview

This folder contains **5 System Sequence Diagrams (SSDs)** for the personalized-ai-storybook system. Each SSD represents **ONE specific use case scenario** with the system treated as a **BLACK BOX**.

According to UML guidelines, SSDs are created during **requirements analysis** to show **WHAT the system does** from a user perspective, without showing **HOW it works internally**.

---

## 🎯 System Sequence Diagrams

### 1. **Generate Story** (`14_ssd_story_generation.puml`)
**Use Case**: Generate Story from Prompt  
**Scenario**: Main Success - Text or Image Generation

**System Operations**:
- `makeNewStory()`
- `enterPrompt(prompt_text)`
- `selectOptions(generate_images, mode)`
- `generateStory()`
- `viewPage(page_number)`

**Key Flow**:
1. User initiates new story
2. User enters story prompt
3. System validates prompt
4. User selects generation options
5. System generates story (with or without images)
6. User views story pages

---

### 2. **Character Chat** (`15_ssd_character_chat.puml`)
**Use Case**: Chat with Story Characters  
**Scenario**: Main Success - Interactive Character Conversation

**System Operations**:
- `selectStory(story_id)`
- `selectCharacter(character_name)`
- `sendMessage(message_text)`
- `endChat()`

**Key Flow**:
1. User selects a story
2. User selects character to chat with
3. System initiates chat
4. User sends messages in loop
5. System responds as character
6. User ends chat

---

### 3. **Idea Workshop** (`16_ssd_idea_workshop.puml`)
**Use Case**: Collaborative Story Ideation  
**Scenario**: Main Success - Guided Story Creation

**System Operations**:
- `startWorkshop(mode)`
- `provideInput(user_input)`
- `requestStoryGeneration()`
- `endWorkshop()`

**Key Flow**:
1. User starts workshop session
2. System asks questions
3. User provides story ideas/requirements
4. System collects requirements (loop)
5. User requests story generation
6. System generates story from requirements
7. User ends workshop

---

### 4. **Export to PDF** (`17_ssd_export_pdf.puml`)
**Use Case**: Export Story to PDF  
**Scenario**: Main Success - Download Story as PDF

**System Operations**:
- `selectStory(story_id)`
- `requestPDFExport()`
- `downloadPDF()`

**Key Flow**:
1. User selects story to export
2. User requests PDF export
3. System generates PDF
4. System provides download link
5. User downloads PDF file

---

### 5. **Voice Input** (`18_ssd_voice_input.puml`)
**Use Case**: Generate Story from Voice Input  
**Scenario**: Main Success - Voice-to-Story Generation

**System Operations**:
- `makeNewStory()`
- `recordVoiceInput()`
- `stopRecording(audio_data)`
- `confirmPrompt(confirmed_text)`
- `selectOptions(generate_images, mode)`
- `generateStory()`

**Key Flow**:
1. User initiates new story
2. User records voice input
3. System transcribes to text
4. User confirms/edits transcription
5. User selects options
6. System generates story

---

## 🔑 Key Characteristics of SSDs

All SSDs in this project follow these principles:

### ✅ **System as Black Box**
- Only 2 participants: User (Actor) and :System
- No internal objects shown (no Frontend, Backend, Agents, etc.)
- Focus on external interface

### ✅ **High-Level Operations**
- System operations are public interface methods
- No implementation details
- Clear, descriptive operation names

### ✅ **One Scenario Per Diagram**
- Each SSD shows ONE use case scenario
- Typically the "Main Success" scenario
- Alternative scenarios can have separate SSDs

### ✅ **Requirements-Level**
- Created during analysis phase
- Shows WHAT system does
- Used as input for design-level sequence diagrams

---

## 📊 SSD vs Sequence Diagram

| Aspect | System Sequence Diagram | Sequence Diagram |
|--------|------------------------|------------------|
| **Files** | 14-18 (SSDs) | 03-05 (Design) |
| **Purpose** | Requirements | Design |
| **View** | Black-box | White-box |
| **Participants** | User + :System | Multiple objects |
| **Shows** | WHAT | HOW |
| **Phase** | Analysis | Design |

---

## 📚 From Documentation

According to `UML-artifacts-material.txt`:

> "An SSD shows – for one particular scenario of a use case –
> the events that external actors generate, their order, and
> inter-system events. The system is treated as a black-box."

> "SSDs are derived from use cases; SSDs are often drawn for
> the main success scenarios of each use case and frequent or
> complex alternative scenarios."

> "SSDs are used as input for object design"

---

## 🎯 Coverage

These 5 SSDs cover the main use cases from the Use Case Diagram:

- ✅ Generate Story from Prompt
- ✅ Generate Story from Voice Input
- ✅ Chat with Story Characters
- ✅ Idea Workshop (Story Ideation)
- ✅ Export Story to PDF

Additional use cases (like Audio Narration) can have SSDs added as needed.

---

## 📁 File Locations

**PlantUML versions**: `diagrams/14-18_ssd_*.puml`  
**Mermaid versions**: `diagrams/mermaid/14-18_ssd_*.mmd`

---

**Created**: December 5, 2025  
**Total SSDs**: 5  
**Format**: PlantUML + Mermaid  
**Project**: personalized-ai-storybook FYP
