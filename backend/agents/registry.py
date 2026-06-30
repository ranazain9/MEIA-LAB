"""
Agent Registry
==============

Central registry for discovering, registering, and managing agent instances.
Supports lazy initialization and dependency injection of configuration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Type

from backend.agents.base.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Singleton-style registry that maps agent names → agent instances.

    Usage:
        registry = AgentRegistry()
        registry.register(ASRAgent, config={...})
        asr = registry.get("asr_alignment")
        await registry.initialize_all()
    """

    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        agent_cls: Type[BaseAgent],
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseAgent:
        """Instantiate and register an agent class."""
        instance = agent_cls(config=config)
        name = instance.agent_name
        if name in self._agents:
            raise ValueError(f"Agent '{name}' is already registered.")
        self._agents[name] = instance
        logger.info("Registered agent: %s", name)
        return instance

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, name: str) -> BaseAgent:
        """Retrieve a registered agent by name."""
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' is not registered.")
        return self._agents[name]

    def list_agents(self) -> list[str]:
        """Return the names of all registered agents."""
        return list(self._agents.keys())

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    async def initialize_all(self) -> None:
        """Initialize every registered agent."""
        for name, agent in self._agents.items():
            logger.info("Initializing agent: %s", name)
            await agent.initialize()

    async def shutdown_all(self) -> None:
        """Gracefully shut down every registered agent."""
        for name, agent in self._agents.items():
            logger.info("Shutting down agent: %s", name)
            await agent.shutdown()

    async def health_check_all(self) -> Dict[str, Any]:
        """Aggregate health checks from all agents."""
        return {
            name: await agent.health_check()
            for name, agent in self._agents.items()
        }
