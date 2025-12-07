from pydantic import BaseModel
from typing import Optional


class AgentConfig(BaseModel):
    """Configuration for a single agent"""
    id: int
    name: str
    role: str
    description: str
    system_prompt: str
    assistant_id: Optional[str] = None
    vector_store_id: Optional[str] = None
    model: str = "gpt-4o-mini"


class AgentStatus(BaseModel):
    """Status of an agent"""
    agent_id: int
    name: str
    role: str
    vector_store_id: Optional[str] = None
    assistant_id: Optional[str] = None
    is_ready: bool = False

