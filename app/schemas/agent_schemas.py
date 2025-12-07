"""
Request and response schemas for agent endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.agent import AgentStatus


class ChatRequest(BaseModel):
    """Request schema for chatting with an agent"""
    message: str = Field(..., description="The message to send to the agent", min_length=1)
    thread_id: Optional[str] = Field(None, description="Optional thread ID to continue a conversation")
    buffer_by_sentence: bool = Field(
        True, 
        description="For streaming: buffer and send complete sentences/phrases instead of individual words"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What information do you have about machine learning?",
                "thread_id": None,
                "buffer_by_sentence": True
            }
        }


class InitializeAgentsResponse(BaseModel):
    """Response schema after initializing agents"""
    message: str
    agents_created: int
    shared_vector_store_id: Optional[str] = Field(None, description="Always None (no vector store)")
    agents: List[AgentStatus]

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Agents initialized successfully",
                "agents_created": 10,
                "shared_vector_store_id": None,
                "agents": []
            }
        }

