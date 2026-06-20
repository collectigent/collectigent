"""共享记忆系统 - 短期记忆+长期记忆"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
import time


@dataclass
class MemoryItem:
    """记忆条目"""
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # 生存时间，None表示永久
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl


class Memory(ABC):
    """记忆基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取记忆"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """存储记忆"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除记忆"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> list[Any]:
        """搜索记忆"""
        pass


class ShortTermMemory(Memory):
    """短期记忆 - 对话上下文"""
    
    def __init__(self, max_items: int = 100):
        self._max_items = max_items
        self._store: dict[str, MemoryItem] = {}
        self._access_order: list[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        """获取记忆"""
        item = self._store.get(key)
        if item is None:
            return None
        
        if item.is_expired():
            self.delete(key)
            return None
        
        item.access_count += 1
        return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """存储记忆"""
        # LRU淘汰
        if len(self._store) >= self._max_items and key not in self._store:
            self._evict_lru()
        
        self._store[key] = MemoryItem(key=key, value=value, ttl=ttl)
        if key not in self._access_order:
            self._access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """删除记忆"""
        if key in self._store:
            del self._store[key]
            self._access_order.remove(key)
            return True
        return False
    
    def search(self, query: str) -> list[Any]:
        """搜索相关记忆（简单实现）"""
        results = []
        query_lower = query.lower()
        for item in self._store.values():
            if isinstance(item.value, str) and query_lower in item.value.lower():
                results.append(item.value)
        return results
    
    def _evict_lru(self) -> None:
        """淘汰最久未使用的条目"""
        if self._access_order:
            oldest = self._access_order.pop(0)
            self.delete(oldest)
    
    def clear(self) -> None:
        """清空短期记忆"""
        self._store.clear()
        self._access_order.clear()
    
    def get_context(self, max_items: int = 10) -> list[dict]:
        """获取最近上下文"""
        items = sorted(
            self._store.values(),
            key=lambda x: (x.access_count, -x.timestamp),
            reverse=True
        )[:max_items]
        return [{"key": i.key, "value": i.value} for i in items]


class LongTermMemory(Memory):
    """长期记忆 - 知识库检索"""
    
    def __init__(self):
        self._store: dict[str, MemoryItem] = {}
        self._index: dict[str, set[str]] = {}  # 关键词到key的索引
    
    def get(self, key: str) -> Optional[Any]:
        """获取记忆"""
        item = self._store.get(key)
        if item and not item.is_expired():
            return item.value
        elif item:
            self.delete(key)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """存储记忆"""
        self._store[key] = MemoryItem(key=key, value=value, ttl=ttl)
        
        # 更新索引
        keywords = self._extract_keywords(str(value))
        for keyword in keywords:
            if keyword not in self._index:
                self._index[keyword] = set()
            self._index[keyword].add(key)
    
    def delete(self, key: str) -> bool:
        """删除记忆"""
        if key in self._store:
            # 从索引中移除
            for keyword_keys in self._index.values():
                keyword_keys.discard(key)
            
            del self._store[key]
            return True
        return False
    
    def search(self, query: str) -> list[Any]:
        """搜索记忆"""
        keywords = self._extract_keywords(query)
        
        # 收集所有匹配的结果
        matching_keys: set[str] = set()
        for keyword in keywords:
            if keyword in self._index:
                matching_keys.update(self._index[keyword])
        
        # 获取结果
        results = []
        for key in matching_keys:
            item = self._store.get(key)
            if item and not item.is_expired():
                results.append(item.value)
        
        return results
    
    def _extract_keywords(self, text: str) -> set[str]:
        """提取关键词"""
        # 简单实现：分词并过滤停用词
        stopwords = {"的", "了", "是", "在", "和", "与", "或", "及", "等", "这", "那"}
        words = set(text.lower().split())
        return words - stopwords
    
    def store_knowledge(self, key: str, knowledge: dict, tags: list[str] = None) -> None:
        """存储结构化知识"""
        self.set(key, {
            "type": "knowledge",
            "content": knowledge,
            "tags": tags or [],
        })
    
    def retrieve_by_tags(self, tags: list[str]) -> list[Any]:
        """按标签检索"""
        results = []
        for item in self._store.values():
            if isinstance(item.value, dict) and item.value.get("type") == "knowledge":
                item_tags = item.value.get("tags", [])
                if any(tag in item_tags for tag in tags):
                    results.append(item.value)
        return results


class MemorySystem:
    """
    统一记忆系统接口
    
    整合短期记忆和长期记忆，
    自动判断从何处读取/写入
    """
    
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
    
    def remember(self, key: str, value: Any, ttl: Optional[float] = 3600) -> None:
        """存储记忆（短期）"""
        self.short_term.set(key, value, ttl)
    
    def memorize(self, key: str, value: Any, tags: list[str] = None) -> None:
        """永久记忆（长期）"""
        self.long_term.store_knowledge(key, value, tags)
    
    def recall(self, key: str) -> Optional[Any]:
        """回忆"""
        # 先查短期
        value = self.short_term.get(key)
        if value is not None:
            return value
        # 再查长期
        return self.long_term.get(key)
    
    def search_memories(self, query: str) -> dict[str, list]:
        """搜索记忆"""
        return {
            "short_term": self.short_term.search(query),
            "long_term": self.long_term.search(query),
        }
