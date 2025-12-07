"""
Error handling utilities for consistent error responses.
"""
from functools import wraps
from typing import Callable
from fastapi import HTTPException
from app.core import (
    AgentNotFoundError,
    AgentNotInitializedError,
    OpenAIKeyNotConfiguredError,
    AgentRunFailedError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def handle_agent_errors(func: Callable) -> Callable:
    """
    Decorator to handle common agent-related errors consistently.
    
    Args:
        func: The endpoint function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except AgentNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except AgentNotInitializedError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except AgentRunFailedError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except OpenAIKeyNotConfiguredError:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key is not configured. Please set OPENAI_API_KEY in your environment."
            )
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred: {str(e)}"
            )
    return wrapper


def validate_agent(agent_id: int, agent, require_initialized: bool = False) -> None:
    """
    Validate agent exists and optionally check if initialized.
    
    Args:
        agent_id: Agent ID to validate
        agent: Agent object or None
        require_initialized: If True, check that agent is initialized
        
    Raises:
        HTTPException: If validation fails
    """
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent {agent_id} not found. Valid agent IDs are 1-10."
        )
    
    if require_initialized:
        if not agent.assistant_id:
            raise HTTPException(
                status_code=400,
                detail=f"Agent {agent_id} is not properly initialized. "
                       "Please initialize agents first via /api/agents/initialize"
            )

