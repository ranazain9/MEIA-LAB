"""
Agent Exceptions
================

Custom exception hierarchy for MEIA agents.
"""


class AgentError(Exception):
    """Base exception for all agent-related errors."""

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        super().__init__(f"[{agent_name}] {message}")


class AgentTimeoutError(AgentError):
    """Raised when an agent exceeds its processing time limit."""


class AgentProcessingError(AgentError):
    """Raised when an agent encounters an error during processing."""


class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize (model load, GPU alloc, etc.)."""


class ModelNotLoadedError(AgentError):
    """Raised when attempting to use a model that hasn't been loaded."""
