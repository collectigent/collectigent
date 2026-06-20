"""向量化器 - 将文本转换为向量表示"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any
import os


class EmbeddingProviderType(Enum):
    """Embedding提供商类型"""
    OPENAI = "openai"
    TEXT_EMBEDDING_3 = "text_embedding_3"
    GLM = "glm"
    BAICHUAN = "baichuan"
    MINIMAX = "minimax"
    LOCAL = "local"  # 本地模型


@dataclass
class EmbeddingConfig:
    """Embedding配置"""
    provider: EmbeddingProviderType
    model: str = ""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    dimensions: int = 1536
    batch_size: int = 32
    
    # 默认模型映射
    DEFAULT_MODELS: dict[EmbeddingProviderType, str] = field(default_factory=lambda: {
        EmbeddingProviderType.OPENAI: "text-embedding-3-small",
        EmbeddingProviderType.TEXT_EMBEDDING_3: "text-embedding-3-large",
        EmbeddingProviderType.GLM: "embedding-2",
        EmbeddingProviderType.BAICHUAN: "Baichuan-Text-Embedding",
        EmbeddingProviderType.MINIMAX: "embo-01",
        EmbeddingProviderType.LOCAL: "all-MiniLM-L6-v2",
    })
    
    def __post_init__(self):
        if not self.model:
            self.model = self.DEFAULT_MODELS.get(self.provider, "")


class EmbeddingProvider(ABC):
    """Embedding提供商基类"""
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._client = None
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为向量"""
        pass
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """分批处理文本"""
        results = []
        
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            embeddings = await self.embed(batch)
            results.extend(embeddings)
        
        return results
    
    @classmethod
    def create(cls, config: EmbeddingConfig) -> "EmbeddingProvider":
        """工厂方法创建提供商"""
        providers = {
            EmbeddingProviderType.OPENAI: OpenAIEmbeddingProvider,
            EmbeddingProviderType.TEXT_EMBEDDING_3: OpenAIEmbeddingProvider,
            EmbeddingProviderType.GLM: GLMEmbeddingProvider,
            EmbeddingProviderType.BAICHUAN: BaichuanEmbeddingProvider,
            EmbeddingProviderType.MINIMAX: MinimaxEmbeddingProvider,
            EmbeddingProviderType.LOCAL: LocalEmbeddingProvider,
        }
        
        provider_class = providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"不支持的Embedding提供商: {config.provider}")
        
        return provider_class(config)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embedding提供商"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
        
        api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("请提供OpenAI API Key")
        
        base_url = self.config.base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成Embedding"""
        response = await self._client.embeddings.create(
            model=self.config.model,
            input=texts,
            dimensions=self.config.dimensions if self.config.provider == EmbeddingProviderType.TEXT_EMBEDDING_3 else None,
        )
        
        return [emb.embedding for emb in response.data]


class GLMEmbeddingProvider(EmbeddingProvider):
    """智谱AI Embedding提供商"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化智谱客户端"""
        try:
            from zhipuai import ZhipuAI
        except ImportError:
            raise ImportError("请安装zhipuai: pip install zhipuai")
        
        api_key = self.config.api_key or os.environ.get("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError("请提供智谱API Key")
        
        self._client = ZhipuAI(api_key=api_key)
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成Embedding"""
        results = []
        
        for text in texts:
            response = self._client.embeddings.create(
                model=self.config.model,
                input=text,
            )
            results.append(response.data[0].embedding)
        
        return results


class BaichuanEmbeddingProvider(EmbeddingProvider):
    """百川智能Embedding提供商"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化百川客户端"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
        
        api_key = self.config.api_key or os.environ.get("BAICHUAN_API_KEY")
        if not api_key:
            raise ValueError("请提供百川API Key")
        
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.baichuan-ai.com/v1",
        )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成Embedding"""
        response = await self._client.embeddings.create(
            model=self.config.model,
            input=texts,
        )
        
        return [emb.embedding for emb in response.data]


class MinimaxEmbeddingProvider(EmbeddingProvider):
    """Minimax Embedding提供商"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化Minimax客户端"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("请安装openai: pip install openai")
        
        api_key = self.config.api_key or os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            raise ValueError("请提供Minimax API Key")
        
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.minimax.chat/v1",
        )
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成Embedding"""
        response = await self._client.embeddings.create(
            model=self.config.model,
            input=texts,
        )
        
        return [emb.embedding for emb in response.data]


class LocalEmbeddingProvider(EmbeddingProvider):
    """本地Embedding模型"""
    
    def __init__(self, config: EmbeddingConfig):
        super().__init__(config)
        self._init_model()
    
    def _init_model(self):
        """初始化本地模型"""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("请安装sentence-transformers: pip install sentence-transformers")
        
        self._model = SentenceTransformer(self.config.model)
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """生成Embedding"""
        embeddings = self._model.encode(texts)
        return embeddings.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """本地模型直接处理所有文本"""
        return await self.embed(texts)