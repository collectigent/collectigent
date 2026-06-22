"""共享记忆系统 - 支持多Agent协作的记忆共享机制"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Set
import time
import json
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"      # 情节记忆 - 存储具体事件
    SEMANTIC = "semantic"      # 语义记忆 - 存储知识
    PROCEDURAL = "procedural"  # 过程记忆 - 存储流程


@dataclass
class MemoryEntry:
    """记忆条目"""
    key: str
    value: Any
    memory_type: MemoryType = MemoryType.SHORT_TERM
    timestamp: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # 生存时间，None表示永久
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    source_role: Optional[str] = None  # 哪个角色创建的
    references: int = 0  # 被引用次数
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "access_count": self.access_count,
            "tags": self.tags,
            "source_role": self.source_role,
            "references": self.references,
        }


class SharedMemory:
    """
    共享记忆系统
    
    功能：
    - 支持多Agent共享记忆
    - 自动管理短期/长期记忆
    - 提供记忆检索和上下文关联
    - 支持记忆引用和依赖追踪
    """
    
    def __init__(self, max_short_term_items: int = 500, short_term_ttl: float = 3600):
        self._store: Dict[str, MemoryEntry] = {}
        self._index: Dict[str, Set[str]] = {}  # 关键词索引
        self._tag_index: Dict[str, Set[str]] = {}  # 标签索引
        self._role_index: Dict[str, Set[str]] = {}  # 角色索引
        self._max_short_term_items = max_short_term_items
        self._short_term_ttl = short_term_ttl
        self._access_order: List[str] = []
    
    def _update_index(self, key: str, entry: MemoryEntry):
        """更新索引"""
        # 更新关键词索引
        text = str(entry.value)
        keywords = self._extract_keywords(text)
        for keyword in keywords:
            if keyword not in self._index:
                self._index[keyword] = set()
            self._index[keyword].add(key)
        
        # 更新标签索引
        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(key)
        
        # 更新角色索引
        if entry.source_role:
            if entry.source_role not in self._role_index:
                self._role_index[entry.source_role] = set()
            self._role_index[entry.source_role].add(key)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        stopwords = {
            "的", "了", "是", "在", "和", "与", "或", "及", "等", "这", "那",
            "我", "你", "他", "她", "它", "我们", "你们", "他们",
            "一个", "一些", "所有", "任何", "每", "每个", "各",
            "可以", "可能", "会", "将", "应该", "必须", "需要",
            "有", "没有", "不", "不是", "要", "不要", "能",
            "因为", "所以", "但是", "然而", "虽然", "如果", "那么",
            "为了", "以便", "通过", "根据", "按照", "关于", "对于",
            "with", "and", "or", "but", "if", "then", "that", "this",
            "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "will", "would", "could", "should",
            "a", "an", "the", "in", "on", "at", "to", "for", "of"
        }
        
        words = set(text.lower().split())
        return words - stopwords
    
    def _evict_expired(self):
        """清理过期的短期记忆"""
        expired_keys = []
        for key, entry in self._store.items():
            if entry.memory_type == MemoryType.SHORT_TERM and entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self.delete(key)
    
    def _evict_lru(self):
        """淘汰最久未使用的短期记忆"""
        short_term_entries = [
            (k, v) for k, v in self._store.items() 
            if v.memory_type == MemoryType.SHORT_TERM
        ]
        
        if len(short_term_entries) <= self._max_short_term_items:
            return
        
        # 按访问次数和时间排序，优先淘汰访问少、时间久的
        short_term_entries.sort(key=lambda x: (x[1].access_count, x[1].timestamp))
        
        # 需要淘汰的数量
        to_evict = len(short_term_entries) - self._max_short_term_items
        
        for key, _ in short_term_entries[:to_evict]:
            self.delete(key)
    
    def add(self, key: str, value: Any, memory_type: MemoryType = MemoryType.SHORT_TERM,
            ttl: Optional[float] = None, tags: List[str] = None, source_role: Optional[str] = None):
        """
        添加记忆
        
        Args:
            key: 记忆键
            value: 记忆内容
            memory_type: 记忆类型
            ttl: 生存时间（秒），None表示永久
            tags: 标签列表
            source_role: 来源角色
        """
        # 清理过期记忆
        self._evict_expired()
        
        # 如果是短期记忆，检查是否需要淘汰
        if memory_type == MemoryType.SHORT_TERM:
            self._evict_lru()
        
        # 创建记忆条目
        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=memory_type,
            ttl=ttl if ttl else (self._short_term_ttl if memory_type == MemoryType.SHORT_TERM else None),
            tags=tags or [],
            source_role=source_role
        )
        
        self._store[key] = entry
        self._update_index(key, entry)
        
        if key not in self._access_order:
            self._access_order.append(key)
    
    def get(self, key: str) -> Optional[Any]:
        """获取记忆"""
        entry = self._store.get(key)
        if entry is None:
            return None
        
        if entry.is_expired():
            self.delete(key)
            return None
        
        entry.access_count += 1
        return entry.value
    
    def delete(self, key: str) -> bool:
        """删除记忆"""
        if key not in self._store:
            return False
        
        # 从索引中移除
        entry = self._store[key]
        
        # 关键词索引
        text = str(entry.value)
        keywords = self._extract_keywords(text)
        for keyword in keywords:
            if keyword in self._index:
                self._index[keyword].discard(key)
        
        # 标签索引
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(key)
        
        # 角色索引
        if entry.source_role and entry.source_role in self._role_index:
            self._role_index[entry.source_role].discard(key)
        
        # 访问顺序
        if key in self._access_order:
            self._access_order.remove(key)
        
        del self._store[key]
        return True
    
    def search(self, query: str, memory_type: Optional[MemoryType] = None,
               tags: Optional[List[str]] = None, source_role: Optional[str] = None) -> List[dict]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            memory_type: 过滤记忆类型
            tags: 过滤标签
            source_role: 过滤来源角色
        
        Returns:
            匹配的记忆列表
        """
        keywords = self._extract_keywords(query)
        
        # 收集所有匹配的key
        matching_keys: Set[str] = set()
        for keyword in keywords:
            if keyword in self._index:
                matching_keys.update(self._index[keyword])
        
        # 应用过滤条件
        results = []
        for key in matching_keys:
            entry = self._store.get(key)
            if entry is None or entry.is_expired():
                continue
            
            # 类型过滤
            if memory_type and entry.memory_type != memory_type:
                continue
            
            # 标签过滤
            if tags:
                if not any(tag in entry.tags for tag in tags):
                    continue
            
            # 角色过滤
            if source_role and entry.source_role != source_role:
                continue
            
            results.append(entry.to_dict())
        
        # 按相关性排序（访问次数+时间）
        results.sort(key=lambda x: (x["access_count"], -x["timestamp"]), reverse=True)
        
        return results
    
    def recall_recent(self, max_items: int = 20, memory_type: Optional[MemoryType] = None) -> List[dict]:
        """获取最近的记忆"""
        entries = [
            entry.to_dict() for entry in self._store.values()
            if not entry.is_expired() and (memory_type is None or entry.memory_type == memory_type)
        ]
        
        # 按时间排序
        entries.sort(key=lambda x: -x["timestamp"])
        return entries[:max_items]
    
    def recall_by_role(self, role: str, max_items: int = 20) -> List[dict]:
        """获取某个角色创建的记忆"""
        if role not in self._role_index:
            return []
        
        entries = []
        for key in self._role_index[role]:
            entry = self._store.get(key)
            if entry and not entry.is_expired():
                entries.append(entry.to_dict())
        
        entries.sort(key=lambda x: -x["timestamp"])
        return entries[:max_items]
    
    def recall_by_tags(self, tags: List[str], max_items: int = 20) -> List[dict]:
        """按标签检索记忆"""
        matching_keys: Set[str] = set()
        for tag in tags:
            if tag in self._tag_index:
                matching_keys.update(self._tag_index[tag])
        
        entries = []
        for key in matching_keys:
            entry = self._store.get(key)
            if entry and not entry.is_expired():
                entries.append(entry.to_dict())
        
        entries.sort(key=lambda x: -x["timestamp"])
        return entries[:max_items]
    
    def increment_reference(self, key: str) -> bool:
        """增加引用计数"""
        entry = self._store.get(key)
        if entry:
            entry.references += 1
            return True
        return False
    
    def decrement_reference(self, key: str) -> bool:
        """减少引用计数"""
        entry = self._store.get(key)
        if entry:
            entry.references = max(0, entry.references - 1)
            return True
        return False
    
    def save_to_file(self, filepath: str):
        """保存记忆到文件"""
        data = {
            "entries": [entry.to_dict() for entry in self._store.values() if not entry.is_expired()],
            "metadata": {
                "saved_at": time.time(),
                "count": len(self._store)
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载记忆"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for entry_data in data.get("entries", []):
                entry = MemoryEntry(
                    key=entry_data["key"],
                    value=entry_data["value"],
                    memory_type=MemoryType(entry_data.get("memory_type", "short_term")),
                    timestamp=entry_data.get("timestamp", time.time()),
                    ttl=entry_data.get("ttl"),
                    access_count=entry_data.get("access_count", 0),
                    tags=entry_data.get("tags", []),
                    source_role=entry_data.get("source_role"),
                    references=entry_data.get("references", 0)
                )
                self._store[entry.key] = entry
                self._update_index(entry.key, entry)
            
            return True
        except Exception as e:
            print(f"加载记忆失败: {e}")
            return False
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        short_term_count = sum(1 for e in self._store.values() if e.memory_type == MemoryType.SHORT_TERM and not e.is_expired())
        long_term_count = sum(1 for e in self._store.values() if e.memory_type == MemoryType.LONG_TERM and not e.is_expired())
        
        return {
            "total_entries": len(self._store),
            "short_term_entries": short_term_count,
            "long_term_entries": long_term_count,
            "index_size": len(self._index),
            "tag_count": len(self._tag_index),
            "role_count": len(self._role_index)
        }
    
    def clear(self):
        """清空所有记忆"""
        self._store.clear()
        self._index.clear()
        self._tag_index.clear()
        self._role_index.clear()
        self._access_order.clear()


class MemoryContext:
    """
    记忆上下文管理器
    
    用于在辩论过程中管理记忆访问和共享
    """
    
    def __init__(self, shared_memory: SharedMemory):
        self._memory = shared_memory
        self._current_role = None
        self._session_id = str(time.time())
    
    def set_role(self, role: str):
        """设置当前角色"""
        self._current_role = role
    
    def remember(self, key: str, value: Any, memory_type: MemoryType = MemoryType.SHORT_TERM,
                 tags: List[str] = None):
        """记住信息"""
        self._memory.add(
            key=key,
            value=value,
            memory_type=memory_type,
            tags=tags,
            source_role=self._current_role
        )
    
    def recall(self, query: str) -> List[dict]:
        """回忆相关信息"""
        return self._memory.search(query)
    
    def get_recent_context(self, max_items: int = 10) -> List[dict]:
        """获取最近的上下文"""
        return self._memory.recall_recent(max_items)
    
    def get_role_context(self, role: str, max_items: int = 10) -> List[dict]:
        """获取某个角色的贡献"""
        return self._memory.recall_by_role(role, max_items)
    
    def merge_context(self, other_context: "MemoryContext"):
        """合并另一个上下文"""
        recent_entries = other_context._memory.recall_recent(100)
        for entry in recent_entries:
            if entry["key"] not in self._memory._store:
                self._memory.add(
                    key=entry["key"],
                    value=entry["value"],
                    memory_type=MemoryType(entry["memory_type"]),
                    tags=entry.get("tags", []),
                    source_role=entry.get("source_role")
                )


# 全局共享记忆实例
_global_shared_memory = None


def get_shared_memory() -> SharedMemory:
    """获取全局共享记忆实例"""
    global _global_shared_memory
    if _global_shared_memory is None:
        _global_shared_memory = SharedMemory()
    return _global_shared_memory


def init_shared_memory(config: dict = None) -> SharedMemory:
    """初始化共享记忆系统"""
    global _global_shared_memory
    
    config = config or {}
    max_items = config.get("max_short_term_items", 500)
    ttl = config.get("short_term_ttl", 3600)
    
    _global_shared_memory = SharedMemory(
        max_short_term_items=max_items,
        short_term_ttl=ttl
    )
    
    return _global_shared_memory