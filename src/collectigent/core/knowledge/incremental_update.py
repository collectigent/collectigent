"""增量更新与持续优化层 - Incremental Update"""

from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import json


class ChangeType(Enum):
    """变更类型"""
    ADD = "add"           # 新增
    MODIFY = "modify"     # 修改
    DELETE = "delete"     # 删除
    RENAME = "rename"     # 重命名


@dataclass
class FileChange:
    """文件变更信息"""
    file_id: str
    filename: str
    change_type: ChangeType
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None
    timestamp: float = 0.0


@dataclass
class ImpactAnalysisResult:
    """影响分析结果"""
    file_id: str
    affected_files: List[str]
    affected_agents: List[str]
    severity: str  # high, medium, low
    description: str


@dataclass
class IncrementalUpdate:
    """增量更新信息"""
    update_id: str
    changes: List[FileChange]
    impact_results: List[ImpactAnalysisResult]
    timestamp: float
    processed: bool = False


class ChangeDetector:
    """变更检测器"""
    
    def __init__(self):
        self._file_hashes: Dict[str, str] = {}
    
    def _compute_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def scan_directory(self, directory: str) -> Dict[str, str]:
        """扫描目录获取文件哈希"""
        current_hashes = {}
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                current_hashes[filename] = self._compute_hash(file_path)
        
        return current_hashes
    
    def detect_changes(self, directory: str) -> List[FileChange]:
        """检测目录中的文件变更"""
        current_hashes = self.scan_directory(directory)
        changes = []
        timestamp = hash(str(os.listdir(directory)))
        
        # 检测新增和修改
        for filename, current_hash in current_hashes.items():
            if filename not in self._file_hashes:
                changes.append(FileChange(
                    file_id=f"file_{hash(filename) % 10000}",
                    filename=filename,
                    change_type=ChangeType.ADD,
                    current_hash=current_hash,
                    timestamp=timestamp
                ))
            elif self._file_hashes[filename] != current_hash:
                changes.append(FileChange(
                    file_id=f"file_{hash(filename) % 10000}",
                    filename=filename,
                    change_type=ChangeType.MODIFY,
                    previous_hash=self._file_hashes[filename],
                    current_hash=current_hash,
                    timestamp=timestamp
                ))
        
        # 检测删除
        for filename in self._file_hashes:
            if filename not in current_hashes:
                changes.append(FileChange(
                    file_id=f"file_{hash(filename) % 10000}",
                    filename=filename,
                    change_type=ChangeType.DELETE,
                    previous_hash=self._file_hashes[filename],
                    timestamp=timestamp
                ))
        
        # 更新哈希记录
        self._file_hashes = current_hashes
        
        return changes


class ImpactAnalyzer:
    """影响分析器"""
    
    def __init__(self):
        self._agent_dependencies: Dict[str, List[str]] = {
            "合同分析师": ["合同", "协议"],
            "变更分析师": ["补充", "变更"],
            "财务分析师": ["财务", "报表"],
            "行业分析师": ["行业", "市场"],
            "舆情分析师": ["新闻", "舆情"],
            "沟通分析师": ["邮件"],
        }
    
    def _determine_severity(self, affected_count: int) -> str:
        """确定影响严重程度"""
        if affected_count >= 5:
            return "high"
        elif affected_count >= 2:
            return "medium"
        else:
            return "low"
    
    def analyze_impact(self, file_change: FileChange, related_files: List[str]) -> ImpactAnalysisResult:
        """分析单个文件变更的影响"""
        affected_files = []
        affected_agents = []
        
        # 确定受影响的文件
        for related_file in related_files:
            if file_change.filename in related_file or related_file in file_change.filename:
                affected_files.append(related_file)
        
        # 确定受影响的Agent
        for agent, keywords in self._agent_dependencies.items():
            for keyword in keywords:
                if keyword in file_change.filename.lower():
                    affected_agents.append(agent)
                    break
        
        severity = self._determine_severity(len(affected_files) + len(affected_agents))
        
        description = f"{file_change.change_type.value}文件 {file_change.filename}"
        if affected_files:
            description += f"，影响{len(affected_files)}个关联文件"
        if affected_agents:
            description += f"，影响{len(affected_agents)}个分析Agent"
        
        return ImpactAnalysisResult(
            file_id=file_change.file_id,
            affected_files=affected_files,
            affected_agents=affected_agents,
            severity=severity,
            description=description
        )
    
    def batch_analyze_impact(self, changes: List[FileChange], all_files: List[str]) -> List[ImpactAnalysisResult]:
        """批量分析变更影响"""
        results = []
        
        for change in changes:
            result = self.analyze_impact(change, all_files)
            results.append(result)
        
        return results


class IncrementalProcessor:
    """增量处理器"""
    
    def __init__(self):
        self.change_detector = ChangeDetector()
        self.impact_analyzer = ImpactAnalyzer()
        self._updates: List[IncrementalUpdate] = []
    
    def detect_and_analyze(self, directory: str) -> Optional[IncrementalUpdate]:
        """检测变更并分析影响"""
        changes = self.change_detector.detect_changes(directory)
        
        if not changes:
            return None
        
        # 获取所有文件列表
        all_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        
        # 分析影响
        impact_results = self.impact_analyzer.batch_analyze_impact(changes, all_files)
        
        # 创建增量更新记录
        update = IncrementalUpdate(
            update_id=f"update_{int(hash(str(changes))) % 1000000}",
            changes=changes,
            impact_results=impact_results,
            timestamp=hash(str(changes))
        )
        
        self._updates.append(update)
        
        return update
    
    def process_incremental(self, update: IncrementalUpdate, processing_callback: Optional[Callable] = None):
        """处理增量更新"""
        # 只处理受影响的Agent和路径
        affected_agents = set()
        for result in update.impact_results:
            affected_agents.update(result.affected_agents)
        
        if processing_callback:
            processing_callback(update, affected_agents)
        
        update.processed = True
    
    def get_update_history(self) -> List[IncrementalUpdate]:
        """获取更新历史"""
        return sorted(self._updates, key=lambda x: x.timestamp, reverse=True)
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "total_updates": len(self._updates),
            "processed_updates": sum(1 for u in self._updates if u.processed),
            "pending_updates": sum(1 for u in self._updates if not u.processed),
        }


class ContinuousOptimizer:
    """持续优化器"""
    
    def __init__(self):
        self._performance_history: List[Dict[str, float]] = []
        self._optimization_threshold = 0.8  # 性能阈值
    
    def record_performance(self, metrics: Dict[str, float]):
        """记录性能指标"""
        self._performance_history.append(metrics)
        
        # 保留最近100条记录
        if len(self._performance_history) > 100:
            self._performance_history = self._performance_history[-100:]
    
    def _calculate_average(self, key: str) -> float:
        """计算平均值"""
        values = [m[key] for m in self._performance_history if key in m]
        return sum(values) / len(values) if values else 0.0
    
    def suggest_optimizations(self) -> List[str]:
        """建议优化措施"""
        suggestions = []
        
        if len(self._performance_history) < 5:
            return suggestions
        
        # 分析检索精度
        avg_precision = self._calculate_average("retrieval_precision")
        if avg_precision < self._optimization_threshold:
            suggestions.append("建议调整分块策略，增加上下文增强")
        
        # 分析处理速度
        avg_speed = self._calculate_average("processing_speed")
        if avg_speed < 10:  # 每秒处理文件数
            suggestions.append("建议增加并行处理数量")
        
        # 分析冲突检测率
        avg_conflict_rate = self._calculate_average("conflict_detection_rate")
        if avg_conflict_rate < 0.9:
            suggestions.append("建议增加冲突检测规则")
        
        return suggestions
    
    def optimize_chunking(self, current_params: Dict[str, Any]) -> Dict[str, Any]:
        """优化分块参数"""
        avg_precision = self._calculate_average("retrieval_precision")
        
        if avg_precision < 0.7:
            return {
                **current_params,
                "min_chunk_size": max(100, current_params.get("min_chunk_size", 200) - 50),
                "overlap_ratio": min(0.3, current_params.get("overlap_ratio", 0.15) + 0.05),
                "optimization_note": "降低分块大小，增加重叠率以提高检索精度"
            }
        
        return current_params
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计"""
        return {
            "history_length": len(self._performance_history),
            "avg_retrieval_precision": self._calculate_average("retrieval_precision"),
            "avg_processing_speed": self._calculate_average("processing_speed"),
            "suggestions": self.suggest_optimizations()
        }
