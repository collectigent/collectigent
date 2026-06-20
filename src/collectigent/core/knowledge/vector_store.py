"""向量存储 - 管理和检索向量数据"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Any, Tuple
import os


class VectorStoreType(Enum):
    """向量存储类型"""
    FAISS = "faiss"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    CHROMA = "chroma"
    MILVUS = "milvus"


@dataclass
class VectorStoreConfig:
    """向量存储配置"""
    store_type: VectorStoreType
    index_name: str = "collectigent"
    dimension: int = 1536
    metric: str = "cosine"  # cosine, euclidean, dot
    api_key: Optional[str] = None
    host: Optional[str] = None
    port: int = 0
    path: Optional[str] = None  # 本地存储路径


@dataclass
class SearchResult:
    """检索结果"""
    content: str
    source: str
    score: float
    metadata: dict = field(default_factory=dict)
    chunk_index: int = 0
    
    def __repr__(self) -> str:
        return f"SearchResult(score={self.score:.4f}, source={self.source})"


class VectorStore(ABC):
    """向量存储基类"""
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
    
    @abstractmethod
    async def add(self, embeddings: List[List[float]], texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """添加向量"""
        pass
    
    @abstractmethod
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[SearchResult]:
        """搜索相似向量"""
        pass
    
    @abstractmethod
    async def delete(self, ids: Optional[List[str]] = None) -> None:
        """删除向量"""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """获取向量数量"""
        pass
    
    @abstractmethod
    async def save(self, path: Optional[str] = None) -> None:
        """保存索引"""
        pass
    
    @abstractmethod
    async def load(self, path: Optional[str] = None) -> None:
        """加载索引"""
        pass
    
    @classmethod
    def create(cls, config: VectorStoreConfig) -> "VectorStore":
        """工厂方法创建存储"""
        stores = {
            VectorStoreType.FAISS: FAISSVectorStore,
            VectorStoreType.PINECONE: PineconeVectorStore,
            VectorStoreType.WEAVIATE: WeaviateVectorStore,
            VectorStoreType.CHROMA: ChromaVectorStore,
            VectorStoreType.MILVUS: MilvusVectorStore,
        }
        
        store_class = stores.get(config.store_type)
        if not store_class:
            raise ValueError(f"不支持的向量存储类型: {config.store_type}")
        
        return store_class(config)


class FAISSVectorStore(VectorStore):
    """FAISS向量存储 - 本地向量数据库"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._index = None
        self._texts = []
        self._metadatas = []
        self._init_index()
    
    def _init_index(self):
        """初始化FAISS索引"""
        try:
            import faiss
        except ImportError:
            raise ImportError("请安装faiss: pip install faiss-cpu")
        
        if self.config.metric == "cosine":
            self._index = faiss.IndexFlatIP(self.config.dimension)
            self._normalize = True
        else:
            self._index = faiss.IndexFlatL2(self.config.dimension)
            self._normalize = False
    
    async def add(self, embeddings: List[List[float]], texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """添加向量"""
        import numpy as np
        
        if self._normalize:
            embeddings = self._normalize_vectors(embeddings)
        
        array = np.array(embeddings, dtype=np.float32)
        self._index.add(array)
        self._texts.extend(texts)
        
        if metadatas:
            self._metadatas.extend(metadatas)
        else:
            self._metadatas.extend([{} for _ in texts])
    
    def _normalize_vectors(self, vectors: List[List[float]]) -> List[List[float]]:
        """归一化向量"""
        import numpy as np
        
        array = np.array(vectors, dtype=np.float32)
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        return (array / norms).tolist()
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[SearchResult]:
        """搜索相似向量"""
        import numpy as np
        
        query = np.array([query_embedding], dtype=np.float32)
        
        if self._normalize:
            query = self._normalize_vectors(query.tolist())[0]
            query = np.array([query], dtype=np.float32)
        
        distances, indices = self._index.search(query, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self._texts):
                # FAISS返回的是距离，转换为相似度
                if self.config.metric == "cosine":
                    score = float(distances[0][i])  # IP相似度
                else:
                    # L2距离越小越相似
                    score = 1.0 / (1.0 + float(distances[0][i]))
                
                results.append(SearchResult(
                    content=self._texts[idx],
                    source=self._metadatas[idx].get("source", ""),
                    score=score,
                    metadata=self._metadatas[idx],
                    chunk_index=self._metadatas[idx].get("chunk_index", 0),
                ))
        
        return results
    
    async def delete(self, ids: Optional[List[str]] = None) -> None:
        """删除向量（FAISS不支持高效删除）"""
        # 重新创建索引
        self._init_index()
        self._texts = []
        self._metadatas = []
    
    async def count(self) -> int:
        """获取向量数量"""
        return self._index.ntotal
    
    async def save(self, path: Optional[str] = None) -> None:
        """保存索引"""
        import faiss
        
        save_path = path or self.config.path or "./faiss_index"
        os.makedirs(save_path, exist_ok=True)
        
        faiss.write_index(self._index, os.path.join(save_path, "index.faiss"))
        
        # 保存文本和元数据
        import pickle
        with open(os.path.join(save_path, "data.pkl"), "wb") as f:
            pickle.dump({"texts": self._texts, "metadatas": self._metadatas}, f)
    
    async def load(self, path: Optional[str] = None) -> None:
        """加载索引"""
        import faiss
        import pickle
        
        load_path = path or self.config.path or "./faiss_index"
        
        self._index = faiss.read_index(os.path.join(load_path, "index.faiss"))
        
        with open(os.path.join(load_path, "data.pkl"), "rb") as f:
            data = pickle.load(f)
            self._texts = data["texts"]
            self._metadatas = data["metadatas"]


class PineconeVectorStore(VectorStore):
    """Pinecone向量存储 - 云向量数据库"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化Pinecone客户端"""
        try:
            import pinecone
        except ImportError:
            raise ImportError("请安装pinecone: pip install pinecone-client")
        
        api_key = self.config.api_key or os.environ.get("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("请提供Pinecone API Key")
        
        pinecone.init(api_key=api_key, environment="gcp-starter")
        
        # 创建或连接索引
        if self.config.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.config.index_name,
                dimension=self.config.dimension,
                metric=self.config.metric,
            )
        
        self._index = pinecone.Index(self.config.index_name)
    
    async def add(self, embeddings: List[List[float]], texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """添加向量"""
        import uuid
        
        vectors = []
        for i, (embedding, text) in enumerate(zip(embeddings, texts)):
            metadata = metadatas[i] if metadatas else {}
            metadata["text"] = text
            
            vectors.append({
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": metadata,
            })
        
        self._index.upsert(vectors=vectors)
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[SearchResult]:
        """搜索相似向量"""
        results = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )
        
        return [
            SearchResult(
                content=match["metadata"].get("text", ""),
                source=match["metadata"].get("source", ""),
                score=match["score"],
                metadata=match["metadata"],
            )
            for match in results["matches"]
        ]
    
    async def delete(self, ids: Optional[List[str]] = None) -> None:
        """删除向量"""
        if ids:
            self._index.delete(ids=ids)
        else:
            self._index.delete(delete_all=True)
    
    async def count(self) -> int:
        """获取向量数量"""
        return self._index.describe_index_stats()["total_vector_count"]
    
    async def save(self, path: Optional[str] = None) -> None:
        """Pinecone是云存储，不需要保存"""
        pass
    
    async def load(self, path: Optional[str] = None) -> None:
        """Pinecone是云存储，不需要加载"""
        pass


class WeaviateVectorStore(VectorStore):
    """Weaviate向量存储"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化Weaviate客户端"""
        try:
            import weaviate
        except ImportError:
            raise ImportError("请安装weaviate: pip install weaviate-client")
        
        auth_config = None
        if self.config.api_key:
            auth_config = weaviate.AuthApiKey(api_key=self.config.api_key)
        
        self._client = weaviate.Client(
            url=self.config.host or "http://localhost:8080",
            auth_client_secret=auth_config,
        )
        
        # 创建Schema
        class_obj = {
            "class": self.config.index_name.capitalize(),
            "vectorizer": "none",
            "properties": [
                {"name": "text", "dataType": ["string"]},
                {"name": "source", "dataType": ["string"]},
            ],
        }
        
        if not self._client.schema.exists(self.config.index_name.capitalize()):
            self._client.schema.create_class(class_obj)
    
    async def add(self, embeddings: List[List[float]], texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """添加向量"""
        import uuid
        
        with self._client.batch as batch:
            for i, (embedding, text) in enumerate(zip(embeddings, texts)):
                metadata = metadatas[i] if metadatas else {}
                
                batch.add_data_object(
                    data_object={
                        "text": text,
                        "source": metadata.get("source", ""),
                        **metadata,
                    },
                    class_name=self.config.index_name.capitalize(),
                    vector=embedding,
                    uuid=str(uuid.uuid4()),
                )
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[SearchResult]:
        """搜索相似向量"""
        results = self._client.query.get(
            self.config.index_name.capitalize(),
            ["text", "source"],
        ).with_near_vector({"vector": query_embedding}).with_limit(top_k).do()
        
        return [
            SearchResult(
                content=obj["text"],
                source=obj["source"],
                score=obj.get("_additional", {}).get("distance", 0),
            )
            for obj in results["data"]["Get"][self.config.index_name.capitalize()]
        ]
    
    async def delete(self, ids: Optional[List[str]] = None) -> None:
        """删除向量"""
        if ids:
            for id_ in ids:
                self._client.data_object.delete(uuid=id_, class_name=self.config.index_name.capitalize())
        else:
            self._client.schema.delete_class(self.config.index_name.capitalize())
    
    async def count(self) -> int:
        """获取向量数量"""
        return self._client.query.aggregate(self.config.index_name.capitalize()).with_meta_count().do()[
            "data"
        ]["Aggregate"][self.config.index_name.capitalize()][0]["meta"]["count"]
    
    async def save(self, path: Optional[str] = None) -> None:
        """Weaviate服务端存储"""
        pass
    
    async def load(self, path: Optional[str] = None) -> None:
        """Weaviate服务端存储"""
        pass


class ChromaVectorStore(VectorStore):
    """Chroma向量存储"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化Chroma客户端"""
        try:
            import chromadb
        except ImportError:
            raise ImportError("请安装chromadb: pip install chromadb")
        
        self._client = chromadb.PersistentClient(path=self.config.path or "./chroma_db")
        self._collection = self._client.get_or_create_collection(name=self.config.index_name)
    
    async def add(self, embeddings: List[List[float]], texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """添加向量"""
        import uuid
        
        ids = [str(uuid.uuid4()) for _ in texts]
        self._collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[SearchResult]:
        """搜索相似向量"""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        
        return [
            SearchResult(
                content=results["documents"][0][i],
                source=results["metadatas"][0][i].get("source", "") if results["metadatas"] else "",
                score=1.0 - results["distances"][0][i],  # 转换为相似度
                metadata=results["metadatas"][0][i] if results["metadatas"] else {},
            )
            for i in range(len(results["documents"][0]))
        ]
    
    async def delete(self, ids: Optional[List[str]] = None) -> None:
        """删除向量"""
        if ids:
            self._collection.delete(ids=ids)
        else:
            self._client.delete_collection(name=self.config.index_name)
            self._collection = self._client.get_or_create_collection(name=self.config.index_name)
    
    async def count(self) -> int:
        """获取向量数量"""
        return self._collection.count()
    
    async def save(self, path: Optional[str] = None) -> None:
        """Chroma自动持久化"""
        pass
    
    async def load(self, path: Optional[str] = None) -> None:
        """Chroma自动加载"""
        pass


class MilvusVectorStore(VectorStore):
    """Milvus向量存储"""
    
    def __init__(self, config: VectorStoreConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化Milvus客户端"""
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
        except ImportError:
            raise ImportError("请安装pymilvus: pip install pymilvus")
        
        connections.connect(
            alias="default",
            host=self.config.host or "localhost",
            port=self.config.port or 19530,
        )
        
        # 创建集合
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.config.dimension),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=255),
        ]
        
        schema = CollectionSchema(fields=fields)
        self._collection = Collection(name=self.config.index_name, schema=schema, using="default")
        
        # 创建索引
        index_params = {
            "metric_type": self.config.metric.upper(),
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128},
        }
        self._collection.create_index(field_name="embedding", index_params=index_params)
        self._collection.load()
    
    async def add(self, embeddings: List[List[float]], texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """添加向量"""
        entities = [
            embeddings,
            texts,
            [m.get("source", "") if m else "" for m in (metadatas or [])],
        ]
        self._collection.insert(entities)
        self._collection.flush()
    
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[SearchResult]:
        """搜索相似向量"""
        search_params = {
            "metric_type": self.config.metric.upper(),
            "params": {"nprobe": 10},
        }
        
        results = self._collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source"],
        )
        
        return [
            SearchResult(
                content=hit.entity.get("text", ""),
                source=hit.entity.get("source", ""),
                score=hit.score,
            )
            for hit in results[0]
        ]
    
    async def delete(self, ids: Optional[List[str]] = None) -> None:
        """删除向量"""
        if ids:
            self._collection.delete(f"id in {ids}")
        else:
            self._collection.drop()
    
    async def count(self) -> int:
        """获取向量数量"""
        return self._collection.num_entities
    
    async def save(self, path: Optional[str] = None) -> None:
        """Milvus服务端存储"""
        pass
    
    async def load(self, path: Optional[str] = None) -> None:
        """Milvus服务端存储"""
        self._collection.load()