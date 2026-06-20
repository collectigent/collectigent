"""RAG系统 - 检索增强生成"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

from .retriever import Retriever, RetrieverConfig, SearchResult
from ..llm.factory import LLMFactory
from ..llm.base import LLMConfig, ProviderType


@dataclass
class RAGConfig:
    """RAG配置"""
    retriever_config: RetrieverConfig
    llm_config: Optional[LLMConfig] = None
    max_context_chunks: int = 5
    prompt_template: str = """
基于以下上下文信息回答问题。

上下文：
{context}

问题：{question}

请根据上下文信息回答问题，如果上下文没有相关信息，请明确说明。
"""


@dataclass
class RAGResult:
    """RAG结果"""
    answer: str
    sources: List[SearchResult]
    context_used: str
    llm_token_count: int = 0
    retrieval_time: float = 0.0


class RAGSystem(ABC):
    """RAG系统基类"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self._retriever = Retriever(config.retriever_config)
        
        if config.llm_config:
            self._llm = LLMFactory.create(config.llm_config)
        else:
            self._llm = None
    
    @abstractmethod
    async def query(self, question: str) -> RAGResult:
        """执行RAG查询"""
        pass
    
    async def build_knowledge_base(self, docs_dir: str) -> None:
        """从目录构建知识库"""
        await self._retriever.build_index(docs_dir)
    
    async def add_document(self, content: str, source: str = "") -> None:
        """添加单个文档"""
        from .splitter import Chunk
        chunks = [Chunk(
            content=content,
            source=source,
            chunk_index=0,
            total_chunks=1,
        )]
        await self._retriever.add_documents(chunks)
    
    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        count = await self._retriever.get_vector_count()
        return {
            "vector_count": count,
            "retriever_type": type(self._retriever).__name__,
        }


class BasicRAGSystem(RAGSystem):
    """基础RAG系统"""
    
    async def query(self, question: str) -> RAGResult:
        """执行RAG查询"""
        import time
        
        # 检索相关文档
        start_time = time.time()
        results = await self._retriever.retrieve(question)
        retrieval_time = time.time() - start_time
        
        # 构建上下文
        context = "\n\n".join([
            f"【来源: {r.source}】\n{r.content}" 
            for r in results[:self.config.max_context_chunks]
        ])
        
        # 生成回答
        if self._llm and context:
            prompt = self.config.prompt_template.format(
                context=context,
                question=question,
            )
            
            response = await self._llm.generate(prompt)
            answer = response.content
            token_count = response.token_count if hasattr(response, 'token_count') else 0
        elif context:
            answer = f"根据知识库信息，我来回答您的问题：\n\n{context}"
            token_count = 0
        else:
            answer = "知识库中没有找到相关信息。"
            token_count = 0
        
        return RAGResult(
            answer=answer,
            sources=results,
            context_used=context,
            llm_token_count=token_count,
            retrieval_time=retrieval_time,
        )


class AdvancedRAGSystem(RAGSystem):
    """高级RAG系统 - 支持多轮对话和动态检索"""
    
    def __init__(self, config: RAGConfig):
        super().__init__(config)
        self._conversation_history = []
    
    async def query(self, question: str) -> RAGResult:
        """执行RAG查询（支持对话历史）"""
        import time
        
        # 构建带历史的查询
        enhanced_question = self._enhance_query_with_history(question)
        
        # 检索相关文档
        start_time = time.time()
        results = await self._retriever.retrieve(enhanced_question)
        retrieval_time = time.time() - start_time
        
        # 动态确定上下文数量
        context_chunks = self._select_best_chunks(results, question)
        
        # 构建上下文
        context = "\n\n".join([
            f"【来源: {r.source}】\n{r.content}" 
            for r in context_chunks
        ])
        
        # 生成回答
        if self._llm:
            prompt = self._build_prompt(context, enhanced_question)
            response = await self._llm.generate(prompt)
            answer = response.content
            token_count = response.token_count if hasattr(response, 'token_count') else 0
        else:
            answer = f"根据知识库信息，我来回答您的问题：\n\n{context}"
            token_count = 0
        
        # 更新对话历史
        self._conversation_history.append({
            "question": question,
            "answer": answer,
        })
        
        # 保持历史记录数量
        if len(self._conversation_history) > 10:
            self._conversation_history = self._conversation_history[-10:]
        
        return RAGResult(
            answer=answer,
            sources=results,
            context_used=context,
            llm_token_count=token_count,
            retrieval_time=retrieval_time,
        )
    
    def _enhance_query_with_history(self, question: str) -> str:
        """结合对话历史增强查询"""
        if not self._conversation_history:
            return question
        
        history_str = "\n".join([
            f"历史问题: {h['question']}\n历史回答: {h['answer']}"
            for h in self._conversation_history[-3:]
        ])
        
        return f"""
历史对话:
{history_str}

当前问题: {question}

请根据历史对话理解当前问题的上下文，并生成一个独立的查询语句。
"""
    
    def _select_best_chunks(self, results: List[SearchResult], question: str) -> List[SearchResult]:
        """动态选择最佳上下文块"""
        # 基于评分阈值过滤
        threshold = 0.3
        filtered = [r for r in results if r.score >= threshold]
        
        # 返回最多max_context_chunks个
        return filtered[:self.config.max_context_chunks]
    
    def _build_prompt(self, context: str, question: str) -> str:
        """构建高级prompt"""
        return f"""
你是一个专业的知识库问答助手。请根据提供的上下文信息回答问题。

## 规则：
1. 优先使用上下文中的信息进行回答
2. 如果上下文没有相关信息，明确说明"知识库中没有相关信息"
3. 回答要简洁准确，不要编造信息
4. 如果问题需要结合多个上下文，请综合分析

## 上下文：
{context}

## 问题：
{question}

## 回答：
"""
    
    def clear_history(self):
        """清除对话历史"""
        self._conversation_history = []


class RAGFactory:
    """RAG工厂类"""
    
    @classmethod
    def create_basic(
        cls,
        embedding_provider: str = "openai",
        vector_store: str = "faiss",
        llm_provider: str = "openai",
        **kwargs,
    ) -> RAGSystem:
        """创建基础RAG系统"""
        from .embedding import EmbeddingConfig, EmbeddingProviderType
        from .vector_store import VectorStoreConfig, VectorStoreType
        
        # 创建Embedding配置
        embed_type = EmbeddingProviderType(embedding_provider.lower())
        embed_config = EmbeddingConfig(provider=embed_type)
        
        # 创建向量存储配置
        store_type = VectorStoreType(vector_store.lower())
        store_config = VectorStoreConfig(store_type=store_type)
        
        # 创建检索器配置
        retriever_config = RetrieverConfig(
            embedding_config=embed_config,
            vector_store_config=store_config,
            top_k=kwargs.get("top_k", 5),
        )
        
        # 创建LLM配置
        llm_type = ProviderType(llm_provider.lower())
        llm_config = LLMConfig(provider=llm_type)
        
        # 创建RAG配置
        rag_config = RAGConfig(
            retriever_config=retriever_config,
            llm_config=llm_config,
        )
        
        return BasicRAGSystem(rag_config)
    
    @classmethod
    def create_advanced(
        cls,
        embedding_provider: str = "openai",
        vector_store: str = "faiss",
        llm_provider: str = "openai",
        **kwargs,
    ) -> RAGSystem:
        """创建高级RAG系统"""
        from .embedding import EmbeddingConfig, EmbeddingProviderType
        from .vector_store import VectorStoreConfig, VectorStoreType
        
        # 创建Embedding配置
        embed_type = EmbeddingProviderType(embedding_provider.lower())
        embed_config = EmbeddingConfig(provider=embed_type)
        
        # 创建向量存储配置
        store_type = VectorStoreType(vector_store.lower())
        store_config = VectorStoreConfig(store_type=store_type)
        
        # 创建检索器配置
        retriever_config = RetrieverConfig(
            embedding_config=embed_config,
            vector_store_config=store_config,
            top_k=kwargs.get("top_k", 5),
        )
        
        # 创建LLM配置
        llm_type = ProviderType(llm_provider.lower())
        llm_config = LLMConfig(provider=llm_type)
        
        # 创建RAG配置
        rag_config = RAGConfig(
            retriever_config=retriever_config,
            llm_config=llm_config,
            max_context_chunks=kwargs.get("max_context_chunks", 5),
        )
        
        return AdvancedRAGSystem(rag_config)