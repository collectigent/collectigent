"""Collectigent - 群体智能涌现引擎"""

__version__ = "0.1.0"

from .core.orchestrator import Swarm
from .core.agents.base import Agent, Role

__all__ = ["Swarm", "Agent", "Role"]
