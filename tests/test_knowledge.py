"""知识库检索模块测试"""

import pytest
import os
import tempfile


class TestDocumentLoader:
    """文档加载器测试"""
    
    def test_load_txt(self):
        """测试加载TXT文件"""
        from collectigent.core.knowledge.loader import DocumentLoader, FileType
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("测试内容")
            temp_path = f.name
        
        try:
            loader = DocumentLoader.create(FileType.TXT)
            doc = loader.load(temp_path)
            
            assert doc.content == "测试内容"
            assert doc.source == temp_path
            assert doc.file_type == FileType.TXT
        finally:
            os.unlink(temp_path)
    
    def test_load_markdown(self):
        """测试加载Markdown文件"""
        from collectigent.core.knowledge.loader import DocumentLoader, FileType
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# 标题\n\n正文内容")
            temp_path = f.name
        
        try:
            loader = DocumentLoader.create(FileType.MARKDOWN)
            doc = loader.load(temp_path)
            
            assert "# 标题" in doc.content
            assert "正文内容" in doc.content
        finally:
            os.unlink(temp_path)
    
    def test_detect_file_type(self):
        """测试文件类型检测"""
        from collectigent.core.knowledge.loader import DocumentLoader, FileType
        
        assert DocumentLoader.detect_file_type("test.txt") == FileType.TXT
        assert DocumentLoader.detect_file_type("test.md") == FileType.MARKDOWN
        assert DocumentLoader.detect_file_type("test.pdf") == FileType.PDF
        assert DocumentLoader.detect_file_type("test.docx") == FileType.DOCX


class TestTextSplitter:
    """文本分块器测试"""
    
    def test_split_text(self):
        """测试文本分割"""
        from collectigent.core.knowledge.splitter import RecursiveCharacterTextSplitter, ChunkConfig
        from collectigent.core.knowledge.loader import Document, FileType
        
        config = ChunkConfig(chunk_size=50, chunk_overlap=10)
        splitter = RecursiveCharacterTextSplitter(config)
        
        doc = Document(
            content="这是一段测试文本，用于测试文本分块器的功能。" * 10,
            source="test.txt",
            file_type=FileType.TXT,
        )
        
        chunks = splitter.split(doc)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 50
    
    def test_chunk_properties(self):
        """测试块属性"""
        from collectigent.core.knowledge.splitter import Chunk
        
        chunk = Chunk(
            content="测试内容",
            source="test.txt",
            chunk_index=0,
            total_chunks=3,
        )
        
        assert chunk.content == "测试内容"
        assert chunk.source == "test.txt"
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 3


class TestEmbeddingProvider:
    """向量化器测试"""
    
    def test_create_local_embedding(self):
        """测试创建本地Embedding"""
        from collectigent.core.knowledge.embedding import EmbeddingConfig, EmbeddingProvider, EmbeddingProviderType
        
        config = EmbeddingConfig(
            provider=EmbeddingProviderType.LOCAL,
            model="all-MiniLM-L6-v2",
        )
        
        provider = EmbeddingProvider.create(config)
        
        assert provider is not None
        assert isinstance(provider, EmbeddingProvider)


class TestVectorStore:
    """向量存储测试"""
    
    def test_faiss_store(self):
        """测试FAISS向量存储"""
        from collectigent.core.knowledge.vector_store import VectorStoreConfig, VectorStore, VectorStoreType
        
        config = VectorStoreConfig(
            store_type=VectorStoreType.FAISS,
            dimension=384,
        )
        
        store = VectorStore.create(config)
        
        assert store is not None
        
        # 测试添加和搜索
        import asyncio
        embeddings = [[0.1] * 384, [0.2] * 384]
        texts = ["测试文本1", "测试文本2"]
        
        asyncio.run(store.add(embeddings, texts))
        count = asyncio.run(store.count())
        
        assert count == 2
        
        # 测试搜索
        results = asyncio.run(store.search([0.1] * 384, top_k=1))
        assert len(results) == 1
    
    def test_save_load_faiss(self):
        """测试FAISS保存和加载"""
        from collectigent.core.knowledge.vector_store import VectorStoreConfig, VectorStore, VectorStoreType
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config = VectorStoreConfig(
                store_type=VectorStoreType.FAISS,
                dimension=384,
                path=temp_dir,
            )
            
            store = VectorStore.create(config)
            
            # 添加向量
            import asyncio
            embeddings = [[0.1] * 384]
            texts = ["测试文本"]
            
            asyncio.run(store.add(embeddings, texts))
            
            # 保存
            asyncio.run(store.save())
            
            # 创建新实例并加载
            new_store = VectorStore.create(config)
            asyncio.run(new_store.load())
            
            count = asyncio.run(new_store.count())
            assert count == 1


class TestRetriever:
    """检索器测试"""
    
    def test_semantic_retriever(self):
        """测试语义检索器"""
        from collectigent.core.knowledge.retriever import RetrieverConfig, SemanticRetriever
        from collectigent.core.knowledge.embedding import EmbeddingConfig, EmbeddingProviderType
        from collectigent.core.knowledge.vector_store import VectorStoreConfig, VectorStoreType
        
        embed_config = EmbeddingConfig(
            provider=EmbeddingProviderType.LOCAL,
            model="all-MiniLM-L6-v2",
            dimensions=384,
        )
        
        store_config = VectorStoreConfig(
            store_type=VectorStoreType.FAISS,
            dimension=384,
        )
        
        config = RetrieverConfig(
            embedding_config=embed_config,
            vector_store_config=store_config,
            top_k=3,
        )
        
        retriever = SemanticRetriever(config)
        
        assert retriever is not None


class TestRAGSystem:
    """RAG系统测试"""
    
    def test_basic_rag(self):
        """测试基础RAG系统"""
        from collectigent.core.knowledge.rag import RAGConfig, BasicRAGSystem
        from collectigent.core.knowledge.retriever import RetrieverConfig
        from collectigent.core.knowledge.embedding import EmbeddingConfig, EmbeddingProviderType
        from collectigent.core.knowledge.vector_store import VectorStoreConfig, VectorStoreType
        
        embed_config = EmbeddingConfig(
            provider=EmbeddingProviderType.LOCAL,
            model="all-MiniLM-L6-v2",
            dimensions=384,
        )
        
        store_config = VectorStoreConfig(
            store_type=VectorStoreType.FAISS,
            dimension=384,
        )
        
        retriever_config = RetrieverConfig(
            embedding_config=embed_config,
            vector_store_config=store_config,
            top_k=3,
        )
        
        rag_config = RAGConfig(
            retriever_config=retriever_config,
            llm_config=None,  # 不使用LLM
        )
        
        rag = BasicRAGSystem(rag_config)
        
        assert rag is not None
    
    def test_add_document(self):
        """测试添加文档"""
        from collectigent.core.knowledge.rag import RAGConfig, BasicRAGSystem
        from collectigent.core.knowledge.retriever import RetrieverConfig
        from collectigent.core.knowledge.embedding import EmbeddingConfig, EmbeddingProviderType
        from collectigent.core.knowledge.vector_store import VectorStoreConfig, VectorStoreType
        
        embed_config = EmbeddingConfig(
            provider=EmbeddingProviderType.LOCAL,
            model="all-MiniLM-L6-v2",
            dimensions=384,
        )
        
        store_config = VectorStoreConfig(
            store_type=VectorStoreType.FAISS,
            dimension=384,
        )
        
        retriever_config = RetrieverConfig(
            embedding_config=embed_config,
            vector_store_config=store_config,
        )
        
        rag_config = RAGConfig(
            retriever_config=retriever_config,
            llm_config=None,
        )
        
        rag = BasicRAGSystem(rag_config)
        
        import asyncio
        asyncio.run(rag.add_document("测试知识库内容", "test_source"))
        
        stats = asyncio.run(rag.get_knowledge_base_stats())
        assert stats["vector_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
