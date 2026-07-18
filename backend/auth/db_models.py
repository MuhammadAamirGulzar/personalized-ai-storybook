"""
Extended database models for story and chat persistence
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.auth.database import Base


class Story(Base):
    """
    Stores generated stories with full story data
    """
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for guests
    title = Column(String, nullable=False)
    mode = Column(String, nullable=False)  # 'simple' or 'personalized'
    story_data = Column(JSON, nullable=False)  # Full story JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="stories")
    conversations = relationship("ChatConversation", back_populates="story", cascade="all, delete-orphan")


class ChatConversation(Base):
    """
    Stores chat conversations for each story-character pair
    """
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for guests
    character_name = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    story = relationship("Story", back_populates="conversations")
    user = relationship("User", backref="chat_conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    """
    Stores individual chat messages
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'character'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")


# ============================================================================
# IDEA WORKSHOP MODELS (for "Throw Your Ideas" feature)
# ============================================================================

class WorkshopSession(Base):
    """
    Stores idea workshop sessions for story improvement or new idea creation
    """
    __tablename__ = "workshop_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for guests
    mode = Column(String, nullable=False)  # 'improvement' or 'new_idea'
    status = Column(String, nullable=False, default='active')  # 'active', 'completed', 'abandoned'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="workshop_sessions")
    messages = relationship("WorkshopMessage", back_populates="session", cascade="all, delete-orphan")
    stories = relationship("WorkshopStory", back_populates="session", cascade="all, delete-orphan")


class WorkshopMessage(Base):
    """
    Stores individual messages in workshop conversations
    """
    __tablename__ = "workshop_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workshop_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' (reserved keyword)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("WorkshopSession", back_populates="messages")


class WorkshopStory(Base):
    """
    Stores generated stories from workshop sessions.
    saved_by_user=True means the user clicked 'I Love It' and it appears in the Workshop Library.
    """
    __tablename__ = "workshop_stories"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workshop_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # owner for library
    version = Column(Integer, nullable=False, default=1)
    story_text = Column(Text, nullable=False)
    user_story_text = Column(Text, nullable=True)  # Original story for improvement mode
    title = Column(String, nullable=True)           # Short title for library display
    mode = Column(String, nullable=True)            # 'new_idea' or 'improvement'
    saved_by_user = Column(Boolean, nullable=False, default=False)  # True = loved by user
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("WorkshopSession", back_populates="stories")
