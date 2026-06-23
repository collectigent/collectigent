"""知识库检索模块 - RAG集成"""

# 原有模块
from .loader import DocumentLoader, FileType
from .splitter import TextSplitter, ChunkConfig
from .embedding import EmbeddingProvider, EmbeddingConfig
from .vector_store import VectorStore, VectorStoreType
from .retriever import Retriever, RetrieverConfig
from .rag import RAGSystem, RAGConfig, RAGFactory

# 新增大规模文件处理模块
from .ingestion import (
    FileIngestionPipeline,
    FileType as IngestionFileType,
    FileStatus,
    FileMetadata,
    ProcessedChunk,
)
from .chunking import (
    SemanticChunking,
    ChunkEmbedding,
    Chunk,
    ChunkGranularity,
)
from .file_processing import (
    FileAnalysisManager,
    SharedBlackboard,
    FileAnalyst,
    ContractAnalyst,
    ChangeAnalyst,
    FinancialAnalyst,
    IndustryAnalyst,
    SentimentAnalyst,
    CommunicationAnalyst,
    FileAnalysisResult,
    FileCategory,
)
from .cross_file_synthesis import (
    CrossFileSynthesizer,
    KnowledgeGraph,
    ConflictDetector,
    TimelineReconstructor,
    Conflict,
    TimelineEvent,
    RelationType,
)
from .incremental_update import (
    IncrementalProcessor,
    ChangeDetector,
    ImpactAnalyzer,
    ContinuousOptimizer,
    ChangeType,
    FileChange,
    ImpactAnalysisResult,
)

__all__ = [
    # 原有模块
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
    "RAGFactory",
    # 新增模块
    "FileIngestionPipeline",
    "FileStatus",
    "FileMetadata",
    "ProcessedChunk",
    "SemanticChunking",
    "ChunkEmbedding",
    "Chunk",
    "ChunkGranularity",
    "FileAnalysisManager",
    "SharedBlackboard",
    "FileAnalyst",
    "ContractAnalyst",
    "ChangeAnalyst",
    "FinancialAnalyst",
    "IndustryAnalyst",
    "SentimentAnalyst",
    "CommunicationAnalyst",
    "FileAnalysisResult",
    "FileCategory",
    "CrossFileSynthesizer",
    "KnowledgeGraph",
    "ConflictDetector",
    "TimelineReconstructor",
    "Conflict",
    "TimelineEvent",
    "RelationType",
    "IncrementalProcessor",
    "ChangeDetector",
    "ImpactAnalyzer",
    "ContinuousOptimizer",
    "ChangeType",
    "FileChange",
    "ImpactAnalysisResult",
]
