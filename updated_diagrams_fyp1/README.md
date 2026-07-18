# Updated Diagrams for FYP-1 Report (Current Iteration Only)

This folder contains updated diagrams that reflect the **current iteration** of the personalized-ai-storybook project, as required by the FYP-1 report instructions.

## Changes from Mid-Report Diagrams

### Key Updates Made:
1. **Added stable-diffusion-webui local API** as the primary image generation method
2. **Added PostgreSQL database** with 7 tables for data persistence  
3. **Updated model** from DreamShaper 8 to Realistic Vision
4. **Removed TTS/STT features** (moved to future work - not currently implemented)
5. **Added Ollama pause/resume logic** during image generation
6. **Showed database save operations** in sequence diagram

## Diagrams Included

### 1. Deployment Diagram (Updated)
**Files:**
- `deployment_diagram_updated.puml` (PlantUML)
- `deployment_diagram_updated.mmd` (Mermaid)

**Shows:**
- Client Browser (Next.js Frontend)
- Application Server (FastAPI + Multi-Agent System)
- AI Processing Engine (Ollama + stable-diffusion-webui)
- PostgreSQL Database (7 tables)
- File System Storage

**Key Changes:**
- Added stable-diffusion-webui with /sdapi/v1/txt2img and /sdapi/v1/img2img endpoints
- Added PostgreSQL database node with all 7 tables listed
- Updated to show Realistic Vision model instead of DreamShaper 8
- Added note about Ollama pausing during image generation

### 2. Sequence Diagram - Story Generation (Updated)
**Files:**
- `sequence_story_generation_updated.puml` (PlantUML)
- `sequence_story_generation_updated.mmd` (Mermaid)

**Shows:**
- Complete story generation workflow from user input to final delivery
- Multi-agent pipeline (Prompt → Writer → Reviewer → Editor)
- Image generation via PersonalizedImageAgent calling WebUI API
- Two-pass image generation (txt2img + img2img refinement)
- Database save operation
- Ollama pause/resume logic

**Key Changes:**
- Changed from local ImageAgent to PersonalizedImageAgent calling WebUI API
- Added WebUI API Server as separate participant
- Showed POST /sdapi/v1/txt2img and /sdapi/v1/img2img calls
- Added IP-Adapter embedding injection step
- Showed Realistic Vision model loading
- Added database save operation
- Added Ollama pause/resume for GPU memory management

## Diagrams NOT Updated (Still Valid from Mid-Report)

The following diagrams from mid-report are still accurate for current iteration:
- **Use Case Diagram** - Core use cases unchanged
- **Class Diagram** - May need minor updates but structure is valid
- **Data Flow Diagram** - General flow still accurate  
- **Domain Model** - Core entities unchanged
- **Relational Schema** - Already shows current 7-table structure
- **Sequence: Character Chat** - Still accurate
- **Sequence: Idea Workshop** - Still accurate

## Usage

### For PlantUML (.puml files):
1. Use PlantUML online editor: http://www.plantuml.com/plantuml/
2. Or install PlantUML extension in VS Code
3. Copy-paste the code to generate diagrams
4. Export as PNG for the report

### For Mermaid (.mmd files):
1. Use Mermaid Live Editor: https://mermaid.live/
2. Or use Mermaid extension in VS Code
3. Copy-paste the code to generate diagrams  
4. Export as PNG for the report

## Integration with Report

These updated diagrams should replace:
1. **deployment diagram.png** in `diagram_images/` folder
2. **sequence_story_generation.png** in `diagram_images/` folder

The other diagrams from mid-report can remain unchanged as they still accurately represent the current iteration.

## Features Removed (Future Work)

As per FYP-1 instructions to document "CURRENT ITERATION ONLY", the following features have been removed from the current report and marked as future work:

- **Text-to-Speech (TTS)** - Not fully implemented
- **Speech-to-Text (STT)** - Not fully implemented
- **Audio Narration** - Not fully implemented
- **Voice Input Processing** - Not fully implemented

These will be mentioned in a "Future Work" or "Conclusions" section.
