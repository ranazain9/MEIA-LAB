"""
Base Agent Abstract Class
=========================

Defines the contract that all MEIA agents must implement.
Provides lifecycle hooks, health checks, and standardized I/O.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.agents.base.schemas import AgentInput, AgentOutput, AgentStatus


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all MEIA agents.

    Every agent follows a consistent lifecycle:
        1. initialize() — load models, warm up resources
        2. process()    — execute the agent's core logic
        3. shutdown()   — release resources gracefully

    Subclasses must implement:
        - _process_impl(): Core processing logic
        - agent_name property: Unique identifier for the agent
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._status = AgentStatus.IDLE
        self._initialized = False
        self._logger = logging.getLogger(f"meia.agent.{self.agent_name}")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique identifier for this agent."""
        ...

    @property
    def status(self) -> AgentStatus:
        """Current agent status."""
        return self._status

    @property
    def is_ready(self) -> bool:
        """Whether the agent is initialized and ready to process."""
        return self._initialized and self._status != AgentStatus.ERROR

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Load models, allocate GPU memory, and prepare the agent."""
        self._logger.info("Initializing agent: %s", self.agent_name)
        self._status = AgentStatus.INITIALIZING
        try:
            await self._initialize_impl()
            self._initialized = True
            self._status = AgentStatus.IDLE
            self._logger.info("Agent %s initialized successfully.", self.agent_name)
        except Exception as exc:
            self._status = AgentStatus.ERROR
            self._logger.exception("Failed to initialize agent %s", self.agent_name)
            raise exc

    async def process(self, agent_input: AgentInput) -> AgentOutput:
        """
        Run the agent's processing pipeline with timing and error handling.

        Args:
            agent_input: Standardized input payload.

        Returns:
            AgentOutput with results and metadata.
        """
        if not self._initialized:
            raise RuntimeError(f"Agent '{self.agent_name}' has not been initialized.")

        self._status = AgentStatus.PROCESSING
        self._logger.info("Processing started for agent: %s", self.agent_name)
        start = time.perf_counter()

        try:
            result = await self._process_impl(agent_input)
            elapsed = time.perf_counter() - start
            result.metadata["processing_time_seconds"] = round(elapsed, 4)
            self._status = AgentStatus.IDLE
            self._logger.info(
                "Agent %s finished in %.2fs", self.agent_name, elapsed
            )
            return result
        except Exception as exc:
            self._status = AgentStatus.ERROR
            self._logger.exception("Agent %s processing failed", self.agent_name)
            raise exc

    async def shutdown(self) -> None:
        """Release resources, unload models, and clean up."""
        self._logger.info("Shutting down agent: %s", self.agent_name)
        await self._shutdown_impl()
        self._initialized = False
        self._status = AgentStatus.IDLE

    async def health_check(self) -> Dict[str, Any]:
        """Return a health-check payload for monitoring."""
        return {
            "agent": self.agent_name,
            "status": self._status.value,
            "initialized": self._initialized,
        }

    # ------------------------------------------------------------------
    # Hooks for subclasses
    # ------------------------------------------------------------------

    async def _initialize_impl(self) -> None:
        """Override to add custom initialization logic."""

    @abstractmethod
    async def _process_impl(self, agent_input: AgentInput) -> AgentOutput:
        """Core processing logic — must be implemented by every agent."""
        ...

    async def _shutdown_impl(self) -> None:
        """Override to add custom teardown logic."""

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.agent_name!r} status={self._status.value}>"
