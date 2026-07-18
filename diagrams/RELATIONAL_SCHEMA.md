# personalized-ai-storybook - Relational Schema

## 📊 Database Schema Overview

This relational schema represents the complete database structure for the personalized-ai-storybook system based on the SQLAlchemy models.

### **4 Entities**

1. **USER** - User accounts
2. **STORY** - Generated stories
3. **CHAT_CONVERSATION** - Character chat sessions
4. **CHAT_MESSAGE** - Individual chat messages
5. **WORKSHOP_SESSION** - Idea workshop sessions
6. **WORKSHOP_MESSAGE** - Workshop conversation messages
7. **WORKSHOP_STORY** - Stories generated from workshop sessions

---

## 🔑 Key Relationships

### **User-centered**
- User **creates** Stories (1:N)
- User **participates** in Chat Conversations (1:N)
- User **initiates** Workshop Sessions (1:N)

### **Story-centered**
- Story **enables** Chat Conversations (1:N)
- Chat Conversation **contains** Chat Messages (1:N)

### **Workshop-centered**
- Workshop Session **contains** Workshop Messages (1:N)
- Workshop Session **generates** Workshop Stories (1:N, versioned)

---

## 📝 Entity Details

### USER
```
id (PK)
email (UNIQUE)
username (UNIQUE)
hashed_password
is_active
created_at
updated_at
```

### STORY
```
id (PK)
user_id (FK → USER) [NULLABLE for guests]
title
mode (simple/personalized)
story_data (JSON)
created_at
```

### CHAT_CONVERSATION
```
id (PK)
story_id (FK → STORY)
user_id (FK → USER) [NULLABLE for guests]
character_name
started_at
last_message_at
```

### CHAT_MESSAGE
```
id (PK)
conversation_id (FK → CHAT_CONVERSATION)
role (user/character)
message
created_at
```

### WORKSHOP_SESSION
```
id (PK)
user_id (FK → USER) [NULLABLE for guests]
mode (improvement/new_idea)
status (active/completed/abandoned)
created_at
updated_at
```

### WORKSHOP_MESSAGE
```
id (PK)
session_id (FK → WORKSHOP_SESSION)
role (user/assistant)
message
message_metadata (JSON)
created_at
```

### WORKSHOP_STORY
```
id (PK)
session_id (FK → WORKSHOP_SESSION)
version (1, 2, 3...)
story_text
user_story_text (for improvement mode)
created_at
```

---

## 🎯 Cardinality Notation

- `||--o{` = One-to-Many (1:N)
- `||--|{` = One-to-Many (mandatory)
- `PK` = Primary Key
- `FK` = Foreign Key
- `NULLABLE` = Optional relationship (for guest users)

---

## 📁 File Locations

**PlantUML**: `diagrams/19_er_diagram.puml`  
**Mermaid**: `diagrams/mermaid/19_er_diagram.mmd`

---

**Created**: December 6, 2025  
**Source**: backend/auth/models.py, backend/auth/db_models.py
