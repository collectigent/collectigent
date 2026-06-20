"""Collectigent - 群体智能涌现引擎"""

__version__ = "0.3.0"

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
]
