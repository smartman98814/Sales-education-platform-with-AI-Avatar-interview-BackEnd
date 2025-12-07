"""
Custom exceptions for the application
"""


class AgentError(Exception):
    """Base exception for agent-related errors"""
    pass


class AgentNotFoundError(AgentError):
    """Raised when an agent is not found"""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        super().__init__(f"Agent {agent_id} not found")


class AgentNotInitializedError(AgentError):
    """Raised when an agent is not properly initialized"""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        super().__init__(f"Agent {agent_id} is not properly initialized")


class OpenAIKeyNotConfiguredError(AgentError):
    """Raised when OpenAI API key is not configured"""
    
    def __init__(self):
        super().__init__("OpenAI API key is not configured")


class AgentRunFailedError(AgentError):
    """Raised when an agent run fails"""
    
    def __init__(self, status: str, details: str = ""):
        self.status = status
        self.details = details
        super().__init__(f"Agent run failed with status: {status}. {details}")

