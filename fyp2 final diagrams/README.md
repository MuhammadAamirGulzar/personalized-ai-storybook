---
title: "personalized-ai-storybook FYP-2 — Diagram Files Index"
---

# personalized-ai-storybook FYP-2 — Diagrams Index

## Which Format to Use?

| Criterion | **PlantUML** (.puml) | **Mermaid** (.mmd) |
|-----------|---------------------|-------------------|
| LaTeX integration | ✅ `tikz-uml` or PNG export | ⚠️ Requires HTML/Markdown |
| GitHub / Markdown preview | ❌ Needs plugin | ✅ Native rendering |
| Academic report (LaTeX) | ✅ **Recommended** | ❌ Not native |
| Online preview | plantuml.com | mermaid.live |
| Class diagrams | ✅ Excellent | ✅ Good |
| Sequence diagrams | ✅ Excellent | ✅ Good |
| State diagrams | ✅ Excellent | ✅ Good |
| DFD (process boxes) | ✅ Using `rectangle` | ⚠️ Limited support |
| Use Case | ✅ Native syntax | ⚠️ Limited |

## **Recommendation: Use PlantUML (.puml) for the LaTeX Report**

For the formal academic FYP-2 PDF report:
1. Open each `.puml` file at **https://www.plantuml.com/plantuml/uml/**
2. Generate PNG images (click "Download PNG")
3. Save images to the `images/` folder in the report
4. Reference in LaTeX with `\includegraphics{images/diagram_name.png}`

For GitHub README or markdown documentation, use the **Mermaid (.mmd)** files with **https://mermaid.live**

---

## Available Diagrams

### PlantUML Files (.puml)

| File | Diagram Type | Chapter |
|------|-------------|---------|
| `use_case.puml` | Use Case Diagram | Chapter 2 / Chapter 3 |
| `class_diagram.puml` | Class Diagram | Chapter 3 |
| `sequence_story_generation.puml` | Sequence Diagram | Chapter 3 |
| `state_story_lifecycle.puml` | State Diagram | Chapter 3 |
| `dfd_context.puml` | DFD Context Diagram (Level 0) | Chapter 3 |
| `dfd_level1.puml` | DFD Level 1 | Chapter 3 |

### Mermaid Files (.mmd)

| File | Diagram Type | Preview at |
|------|-------------|-----------|
| `use_case.mmd` | Use Case (flowchart) | mermaid.live |
| `class_diagram.mmd` | Class Diagram | mermaid.live |
| `sequence_story_generation.mmd` | Sequence Diagram | mermaid.live |
| `state_story_lifecycle.mmd` | State Diagram | mermaid.live |
| `dfd_context.mmd` | DFD Context (flowchart) | mermaid.live |
| `dfd_level1.mmd` | DFD Level 1 (flowchart) | mermaid.live |

---

## Diagram Rules Compliance

### Use Case Diagram
- ✅ Business value test: each use case can be preceded by "the system shall" and describes a goal the actor wants to achieve
- ✅ Actors are outside the system boundary rectangle
- ✅ <<include>> used for mandatory subflows (PDF export always included in generation)
- ✅ <<extend>> used for optional extensions (voice extends text; evaluation extends metrics view)

### DFD Rules (Gane & Sarson)
- ✅ Context diagram has single central process
- ✅ Level 1 has 6 processes (within recommended 6-9 range)
- ✅ All processes numbered (1.0-6.0)
- ✅ Each process has both inputs and outputs
- ✅ All data flows are named
- ✅ Data stores use plural nouns (STORIES, IMAGES, AUDIO, EXPORTS, EVALUATIONS)
- ✅ Processes are verb phrases (Generate Story Text, Synthesize Audio, etc.)

### Class Diagram
- ✅ Aggregation used where DirectorAgent owns sub-agents
- ✅ Inheritance hierarchy from BaseAgent
- ✅ Singleton pattern documented with `{static}` methods
- ✅ Dependency relationships shown as dashed arrows

### State Diagram
- ✅ Every state has entry/exit transitions
- ✅ Guard conditions shown in brackets [...]
- ✅ Concurrent background evaluation shown
- ✅ Nested state (IMAGE_GENERATION) captures scene-level sub-states
- ✅ Error states and recovery transitions included

### Sequence Diagram
- ✅ Temporal ordering top-to-bottom
- ✅ Asynchronous messages shown with `-->>`
- ✅ Alt/loop frames used where applicable
- ✅ All major components included as lifelines
