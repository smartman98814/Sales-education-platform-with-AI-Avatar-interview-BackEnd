"""
Conversation and message database models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Conversation(Base):
    """Conversation/interview session"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, nullable=False)
    agent_name = Column(String, nullable=False)
    agent_role = Column(String, nullable=True)
    room_name = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Scoring data
    final_score = Column(Float, nullable=True)  # 0-100
    tier = Column(String, nullable=True)  # "Excellent", "Strong", etc.
    pre_deduction_total = Column(Float, nullable=True)
    
    # JSON fields for detailed scoring (stored as text, parse as JSON)
    raw_scores_json = Column(Text, nullable=True)  # JSON string
    weighted_points_json = Column(Text, nullable=True)  # JSON string
    deductions_json = Column(Text, nullable=True)  # JSON string
    strengths_json = Column(Text, nullable=True)  # JSON array string
    coaching_items_json = Column(Text, nullable=True)  # JSON array string
    detailed_feedback = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to messages
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMessage(Base):
    """Individual message in a conversation"""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'agent'
    text = Column(Text, nullable=False)
    timestamp_ms = Column(Integer, nullable=False)
    participant_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship back to conversation
    conversation = relationship("Conversation", back_populates="messages")

