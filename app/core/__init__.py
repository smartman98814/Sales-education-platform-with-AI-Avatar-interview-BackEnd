"""
Core application components - exceptions and constants
"""
from app.core.exceptions import (
    AgentError,
    AgentNotFoundError,
    AgentNotInitializedError,
    OpenAIKeyNotConfiguredError,
    AgentRunFailedError
)
from app.core.constants import (
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_THREADPOOL_WORKERS,
    MAX_COMPLETION_TOKENS,
    MAX_BUFFER_SIZE,
)

__all__ = [
    # Exceptions
    "AgentError",
    "AgentNotFoundError",
    "AgentNotInitializedError",
    "OpenAIKeyNotConfiguredError",
    "AgentRunFailedError",
    # Constants
    "DEFAULT_MODEL",
    "DEFAULT_TEMPERATURE",
    "MAX_THREADPOOL_WORKERS",
    "MAX_COMPLETION_TOKENS",
    "MAX_BUFFER_SIZE",
]

