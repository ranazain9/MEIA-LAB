"""
Agent Schemas
=============

Pydantic models for standardized agent input/output and status tracking.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class AgentStatus(str, enum.Enum):
    """Lifecycle status of an agent."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    ERROR = "error"


class Severity(str, enum.Enum):
    """Severity level for flagged items."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ------------------------------------------------------------------
# Input / Output
# ------------------------------------------------------------------

class AgentInput(BaseModel):
    """Standardized input payload sent to any agent."""

    request_id: UUID = Field(default_factory=uuid4)
    session_id: Optional[UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FlaggedItem(BaseModel):
    """A single flagged insight, risk, or anomaly."""

    label: str
    description: str
    severity: Severity = Severity.LOW
    evidence: Optional[str] = None


class AgentOutput(BaseModel):
    """Standardized output returned by any agent."""

    request_id: UUID
    agent_name: str
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    flags: List[FlaggedItem] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
