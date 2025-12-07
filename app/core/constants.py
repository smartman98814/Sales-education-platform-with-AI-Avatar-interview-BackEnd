"""
Application constants and configuration values

Optimized for fastest responses with conversational agents
"""
from typing import Final

# OpenAI Configuration - Speed Optimized
DEFAULT_MODEL: Final[str] = "gpt-4o-mini"
DEFAULT_TEMPERATURE: Final[float] = 0.3
MAX_THREADPOOL_WORKERS: Final[int] = 10
MAX_COMPLETION_TOKENS: Final[int] = 150

# Streaming Configuration
MAX_BUFFER_SIZE: Final[int] = 30

