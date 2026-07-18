# Understanding Sequence Diagrams vs System Sequence Diagrams

## 🎯 Key Difference

### **System Sequence Diagram (SSD)**
- **Purpose**: Requirements analysis - shows WHAT the system does
- **Level**: Black-box view
- **Participants**: Actor + System (as single black box)
- **Shows**: External events and system responses
- **Phase**: Used during requirements/analysis phase
- **Example**: Diagram #14 in this project

### **Sequence Diagram (Design-level)**
- **Purpose**: Design - shows HOW the system works internally
- **Level**: White-box view  
- **Participants**: Multiple internal objects (Frontend, Backend, Agents, Database, etc.)
- **Shows**: Internal object interactions and implementation details
- **Phase**: Used during design/implementation phase
- **Examples**: Diagrams #3, #4, #5 in this project

---

## 📊 Comparison Table

| Aspect | System Sequence Diagram (SSD) | Sequence Diagram |
|--------|-------------------------------|------------------|
| **Abstraction Level** | High (Black-box) | Low (White-box) |
| **System View** | External | Internal |
| **Participants** | Actor + :System | Multiple objects |
| **Operations** | System operations | Object methods |
| **Detail Level** | Simple, focused | Complex, detailed |
| **Use Case** | ONE scenario | Multiple interactions |
| **Purpose** | Requirements | Design |
| **Shows** | WHAT system does | HOW system does it |

---

## 📝 From Documentation

According to `UML-artifacts-material.txt`:

> **System Sequence Diagram**
> - An SSD shows – for one particular scenario of a use case –
>   - the events that external actors generate,
>   - their order, and
>   - inter-system events
> - The system is treated as a **black-box** (no implementation details).
> - A description of "What" system does with some time aspects.
> - SSDs are derived from use cases
> - SSDs are used as **input for object design**

---

## 🔍 Examples from personalized-ai-storybook

### System Sequence Diagram (Diagram #14)
```
User -> :System : makeNewStory()
User -> :System : enterPrompt(prompt_text)
:System --> User : validation_result
User -> :System : generateStory()
:System --> User : story_with_images(title, scenes[], images[])
```

**Notice:**
- Only 2 participants: User and :System
- System is black box
- High-level operations
- No implementation details

### Design Sequence Diagram (Diagram #3)
```
User -> Frontend : Enter prompt
Frontend -> Backend : POST /api/generate
Backend -> PromptAgent : validate_and_enhance()
PromptAgent -> LLM : Classify prompt
LLM --> PromptAgent : Enhanced prompt
Backend -> DirectorAgent : orchestrate_pipeline()
DirectorAgent -> WriterAgent : generate_story()
...
```

**Notice:**
- Many participants: Frontend, Backend, Agents, LLM, Database
- Shows internal implementation
- Detailed method calls
- Shows HOW the system works

---

## ✅ Correct Usage in This Project

### Diagram #14: System Sequence Diagram ✅
- **Correct**: Shows ONE scenario (Generate Story)
- **Correct**: System as black box
- **Correct**: High-level operations only
- **Correct**: Used for requirements analysis
- **Purpose**: Show external view for stakeholders

### Diagrams #3, #4, #5: Design Sequence Diagrams ✅
- **Correct**: Show internal objects
- **Correct**: Implementation details
- **Correct**: Multiple participants
- **Correct**: Used for design/development
- **Purpose**: Show how developers should implement the system

---

## 🎓 Academic Guidelines

According to UML standards:

1. **System Sequence Diagrams** are created during:
   - Requirements analysis
   - Use case modeling
   - Before design phase

2. **Sequence Diagrams** are created during:
   - Object-oriented design
   - After SSDs are complete
   - To show implementation

3. **Relationship**:
   - SSDs → Input for creating Sequence Diagrams
   - SSD shows "what" → Sequence Diagram shows "how"

---

## 📌 Summary

**System Sequence Diagram (SSD)**:
- ✅ Simple
- ✅ Black-box
- ✅ Requirements-level
- ✅ ONE scenario
- ✅ External view

**Sequence Diagram**:
- ✅ Complex
- ✅ White-box
- ✅ Design-level
- ✅ Multiple interactions
- ✅ Internal view

Both are important and serve different purposes in the software development lifecycle!

---

**Created**: December 5, 2025  
**Reference**: UML-artifacts-material.txt (lines 1146-1400)  
**Project**: personalized-ai-storybook FYP
