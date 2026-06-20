"""检索器 - 执行语义检索"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any

from .embedding import EmbeddingProvider, EmbeddingConfig
from .vector_store import VectorStore, VectorStoreConfig, SearchResult
from .loader import DocumentLoader
from .splitter import TextSplitter, Chunk


@dataclass
class RetrieverConfig:
    """检索器配置"""
    embedding_config: EmbeddingConfig
    vector_store_config: VectorStoreConfig
    top_k: int = 5
    score_threshold: float = 0.0
    max_tokens: Optional[int] = None


class Retriever(ABC):
    """检索器基类"""
    
    def __init__(self, config: RetrieverConfig):
        self.config = config
        self._embedding_provider = EmbeddingProvider.create(config.embedding_config)
        self._vector_store = VectorStore.create(config.vector_store_config)
    
    @abstractmethod
    async def retrieve(self, query: str) -> List[SearchResult]:
        """检索相关文档"""
        pass
    
    async def add_documents(self, documents: List[Chunk]) -> None:
        """添加文档到向量存储"""
        texts = [chunk.content for chunk in documents]
        metadatas = [
            {
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                **chunk.metadata,
            }
            for chunk in documents
        ]
        
        embeddings = await self._embedding_provider.embed_batch(texts)
        await self._vector_store.add(embeddings, texts, metadatas)
    
    async def build_index(self, docs_dir: str) -> None:
        """从目录构建索引"""
        loader = DocumentLoader.create()
        documents = loader.load_dir(docs_dir)
        
        splitter = TextSplitter()
        chunks = splitter.split_documents(documents)
        
        await self.add_documents(chunks)
    
    async def get_vector_count(self) -> int:
        """获取向量数量"""
        return await self._vector_store.count()
    
    async def save_index(self, path: Optional[str] = None) -> None:
        """保存索引"""
        await self._vector_store.save(path)
    
    async def load_index(self, path: Optional[str] = None) -> None:
        """加载索引"""
        await self._vector_store.load(path)


class SemanticRetriever(Retriever):
    """语义检索器 - 基于向量相似度"""
    
    async def retrieve(self, query: str) -> List[SearchResult]:
        """语义检索"""
        # 生成查询向量
        query_embedding = await self._embedding_provider.embed([query])
        query_embedding = query_embedding[0]
        
        # 搜索相似文档
        results = await self._vector_store.search(query_embedding, self.config.top_k)
        
        # 过滤低评分结果
        if self.config.score_threshold > 0:
            results = [r for r in results if r.score >= self.config.score_threshold]
        
        # 限制token数量
        if self.config.max_tokens:
            results = self._truncate_by_tokens(results)
        
        return results
    
    def _truncate_by_tokens(self, results: List[SearchResult]) -> List[SearchResult]:
        """按token数量截断结果"""
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            return results
        
        total_tokens = 0
        truncated = []
        
        for result in results:
            tokens = len(encoding.encode(result.content))
            if total_tokens + tokens <= self.config.max_tokens:
                truncated.append(result)
                total_tokens += tokens
            else:
                break
        
        return truncated


class BM25Retriever(Retriever):
    """BM25检索器 - 基于词频"""
    
    def __init__(self, config: RetrieverConfig):
        super().__init__(config)
        self._bm25_index = None
    
    async def retrieve(self, query: str) -> List[SearchResult]:
        """BM25检索"""
        if not self._bm25_index:
            # 先从向量存储获取所有文档构建BM25索引
            await self._build_bm25_index()
        
        # BM25搜索
        results = self._bm25_search(query)
        
        # 结合向量检索进行重排序
        semantic_results = await super().retrieve(query)
        
        return self._hybrid_rerank(results, semantic_results)
    
    async def _build_bm25_index(self):
        """构建BM25索引"""
        try:
            from rank_bm25 import BM25Okapi
            import jieba
        except ImportError:
            raise ImportError("请安装rank_bm25和jieba: pip install rank_bm25 jieba")
        
        # 获取所有文档
        # 这里简化处理，实际应该从向量存储获取所有文本
        self._bm25_index = {"texts": [], "bm25": None}
    
    def _bm25_search(self, query: str) -> List[SearchResult]:
        """BM25搜索（简化实现）"""
        return []
    
    def _hybrid_rerank(self, bm25_results: List[SearchResult], semantic_results: List[SearchResult]) -> List[SearchResult]:
        """混合重排序"""
        # 合并结果并去重
        seen = set()
        combined = []
        
        for result in semantic_results + bm25_results:
            key = (result.content, result.source)
            if key not in seen:
                seen.add(key)
                combined.append(result)
        
        return combined[:self.config.top_k]


class HybridRetriever(Retriever):
    """混合检索器 - 结合语义检索和关键词检索"""
    
    async def retrieve(self, query: str) -> List[SearchResult]:
        """混合检索"""
        # 语义检索
        semantic_results = await self._semantic_retrieve(query)
        
        # 关键词检索（简单实现）
        keyword_results = await self._keyword_retrieve(query)
        
        # 融合结果
        return self._fuse_results(semantic_results, keyword_results)
    
    async def _semantic_retrieve(self, query: str) -> List[SearchResult]:
        """语义检索"""
        query_embedding = await self._embedding_provider.embed([query])
        return await self._vector_store.search(query_embedding[0], self.config.top_k)
    
    async def _keyword_retrieve(self, query: str) -> List[SearchResult]:
        """关键词检索"""
        # 简单的关键词匹配
        # 实际实现应该从存储中查询
        return []
    
    def _fuse_results(self, semantic: List[SearchResult], keyword: List[SearchResult]) -> List[SearchResult]:
        """融合两种检索结果"""
        # 使用RRF（Reciprocal Rank Fusion）融合
        fused = {}
        
        for i, result in enumerate(semantic):
            key = (result.content, result.source)
            fused[key] = 1.0 / (i + 1)
        
        for i, result in enumerate(keyword):
            key = (result.content, result.source)
            fused[key] = fused.get(key, 0) + 1.0 / (i + 1)
        
        # 按融合分数排序
        sorted_results = sorted(fused.keys(), key=lambda k: -fused[k])
        
        # 重建SearchResult对象
        result_map = {
            (r.content, r.source): r for r in semantic + keyword
        }
        
        return [result_map[key] for key in sorted_results[:self.config.top_k]]