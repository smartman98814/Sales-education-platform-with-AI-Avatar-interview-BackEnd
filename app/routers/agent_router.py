"""
Router for managing and interacting with OpenAI agents.

This module provides REST API endpoints for:
- Agent management (list, get, initialize)
- Agent chat interactions (streaming optimized)
"""
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.agent import AgentStatus
from app.schemas import (
    ChatRequest,
    InitializeAgentsResponse,
)
from app.services import agent_manager
from app.utils.logger import get_logger
from app.utils.error_handlers import handle_agent_errors, validate_agent

logger = get_logger(__name__)

router = APIRouter()


@router.get("/agents", response_model=List[AgentStatus], summary="List all agents")
async def get_all_agents():
    """
    Get status of all 10 agents.
    
    Returns:
        List of AgentStatus objects containing agent information
    """
    return agent_manager.get_all_agents_status()


@router.get("/agents/{agent_id}", response_model=AgentStatus, summary="Get agent by ID")
@handle_agent_errors
async def get_agent(agent_id: int):
    """
    Get status of a specific agent.
    
    Args:
        agent_id: Agent ID (1-10)
        
    Returns:
        AgentStatus object
    """
    agent = agent_manager.get_agent(agent_id)
    validate_agent(agent_id, agent)
    
    return AgentStatus(
        agent_id=agent.id,
        name=agent.name,
        role=agent.role,
        vector_store_id=None,
        assistant_id=agent.assistant_id,
        is_ready=bool(agent.assistant_id)
    )


@router.post(
    "/agents/initialize",
    response_model=InitializeAgentsResponse,
    summary="Initialize all agents"
)
@handle_agent_errors
async def initialize_agents():
    """
    Initialize all 10 conversational agents (no vector store for maximum speed).
    
    This endpoint creates or loads 10 OpenAI assistants, each with unique 
    personality and system prompt. Agents respond conversationally without 
    document search (2-3s response time).
    
    If agents are already initialized, returns their current status.
    
    Returns:
        InitializeAgentsResponse with initialization status
    """
    existing_agents = agent_manager.get_all_agents()
    if existing_agents and all(
        agent.assistant_id for agent in existing_agents.values()
    ):
        logger.info("Agents are already initialized")
        return InitializeAgentsResponse(
            message="Agents are already initialized (conversational mode)",
            agents_created=len(existing_agents),
            shared_vector_store_id=None,
            agents=agent_manager.get_all_agents_status()
        )
    
    logger.info("Initializing all agents in conversational mode...")
    await agent_manager.create_all_agents()
    
    return InitializeAgentsResponse(
        message="Agents initialized successfully (conversational mode - fast responses)",
        agents_created=len(agent_manager.get_all_agents()),
        shared_vector_store_id=None,
        agents=agent_manager.get_all_agents_status()
    )


@router.post(
    "/agents/{agent_id}/chat/stream",
    summary="Chat with specific agent (streaming)"
)
@handle_agent_errors
async def chat_with_agent_streaming(agent_id: int, request: ChatRequest):
    """
    Chat with a specific agent using streaming for real-time response.
    
    Returns response as Server-Sent Events (SSE). Can stream word-by-word
    or buffer by sentences/phrases for more readable output.
    
    Args:
        agent_id: Agent ID (1-10)
        request: ChatRequest with message, optional thread_id, and buffer_by_sentence flag
        
    Returns:
        StreamingResponse with SSE data
        
    Notes:
        - buffer_by_sentence=True (default): Sends complete sentences/phrases (recommended)
        - buffer_by_sentence=False: Sends individual word chunks (fastest but choppy)
    """
    agent = agent_manager.get_agent(agent_id)
    validate_agent(agent_id, agent, require_initialized=True)
    
    async def generate():
        """Generate SSE stream of agent response."""
        try:
            # Stream the response from agent manager
            async for chunk in agent_manager.chat_with_agent_stream(
                agent_id=agent_id,
                message=request.message,
                thread_id=request.thread_id,
                buffer_by_sentence=request.buffer_by_sentence
            ):
                # Send as Server-Sent Event
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Streaming error for agent {agent_id}: {str(e)}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
