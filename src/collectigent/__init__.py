"""Collectigent - 群体智能涌现引擎"""

__version__ = "0.4.0"

from .core.orchestrator import Swarm
from .core.agents.base import Agent, Role
from .core.llm import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMFactory,
    ProviderType,
)
from .core.knowledge import (
    DocumentLoader,
    FileType,
    TextSplitter,
    ChunkConfig,
    EmbeddingProvider,
    EmbeddingConfig,
    VectorStore,
    VectorStoreType,
    Retriever,
    RetrieverConfig,
    RAGSystem,
    RAGConfig,
)
from .core.debugger import (
    Debugger,
    DebugConfig,
    CLIVisualizer,
    CLIConfig,
    FlowVisualizer,
    MetricsDashboard,
    create_debugger,
    create_progress_callback,
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
    "DocumentLoader",
    "FileType",
    "TextSplitter",
    "ChunkConfig",
    "EmbeddingProvider",
    "EmbeddingConfig",
    "VectorStore",
    "VectorStoreType",
    "Retriever",
    "RetrieverConfig",
    "RAGSystem",
    "RAGConfig",
    # Debugger (v0.4)
    "Debugger",
    "DebugConfig",
    "CLIVisualizer",
    "CLIConfig",
    "FlowVisualizer",
    "MetricsDashboard",
    "create_debugger",
    "create_progress_callback",
]
