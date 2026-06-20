"""Collectigent - 群体智能涌现引擎"""

__version__ = "0.1.0"

from .core.orchestrator import Swarm
from .core.agents.base import Agent, Role
from .core.llm import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMFactory,
    ProviderType,
)

__all__ = [
    "Swarm",
    "Agent",
    "Role",
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "LLMFactory",
    "ProviderType",
]
