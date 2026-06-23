"""跨文件综合推理层 - Cross-File Synthesis"""

from __future__ import annotations

import networkx as nx
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime
import re


class RelationType(Enum):
    """关系类型"""
    REFERENCES = "references"      # 引用
    CONFLICTS_WITH = "conflicts_with"  # 冲突
    FOLLOWS = "follows"            # 时间顺序
    DEPENDS_ON = "depends_on"      # 依赖
    SIMILAR_TO = "similar_to"      # 相似


@dataclass
class Conflict:
    """冲突信息"""
    conflict_id: str
    file1_id: str
    file1_name: str
    file2_id: str
    file2_name: str
    description: str
    severity: str  # high, medium, low
    evidence1: str
    evidence2: str


@dataclass
class TimelineEvent:
    """时间线事件"""
    event_id: str
    file_id: str
    file_name: str
    date: Optional[datetime]
    description: str
    type: str  # contract_signing, payment, meeting, milestone


@dataclass
class GraphNode:
    """知识图谱节点"""
    node_id: str
    node_type: str  # file, entity, event
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """知识图谱边"""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self):
        self._graph = nx.DiGraph()
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
    
    def add_node(self, node: GraphNode):
        """添加节点"""
        self._nodes[node.node_id] = node
        self._graph.add_node(node.node_id, **node.properties)
    
    def add_edge(self, edge: GraphEdge):
        """添加边"""
        self._edges.append(edge)
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            relation_type=edge.relation_type.value,
            **edge.properties
        )
    
    def find_relations(self, node_id: str, relation_type: Optional[RelationType] = None) -> List[GraphEdge]:
        """查找节点的关系"""
        edges = []
        for edge in self._edges:
            if edge.source_id == node_id or edge.target_id == node_id:
                if relation_type is None or edge.relation_type == relation_type:
                    edges.append(edge)
        return edges
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """查找路径"""
        try:
            return nx.shortest_path(self._graph, source_id, target_id)
        except nx.NetworkXNoPath:
            return None
    
    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        """获取邻居节点"""
        neighbors = []
        for edge in self._edges:
            if edge.source_id == node_id:
                if edge.target_id in self._nodes:
                    neighbors.append(self._nodes[edge.target_id])
            elif edge.target_id == node_id:
                if edge.source_id in self._nodes:
                    neighbors.append(self._nodes[edge.source_id])
        return neighbors
    
    def get_graph_stats(self) -> Dict[str, int]:
        """获取图统计"""
        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "connected_components": nx.number_weakly_connected_components(self._graph)
        }


class ConflictDetector:
    """冲突检测器"""
    
    def __init__(self):
        self._conflict_patterns = [
            (r'违约金.*(?:[千万亿]?元|%)', '违约金金额'),
            (r'期限.*(\d+.*[天月年])', '期限'),
            (r'(?:甲方|乙方).*责任', '责任方'),
            (r'争议解决.*(?:法院|仲裁)', '争议解决方式'),
            (r'(?:生效|失效).*日期', '生效日期'),
        ]
    
    def _extract_info(self, content: str) -> Dict[str, str]:
        """提取关键信息"""
        info = {}
        for pattern, label in self._conflict_patterns:
            matches = re.findall(pattern, content)
            if matches:
                info[label] = matches[-1]
        return info
    
    def detect_conflicts(self, file1_content: str, file1_id: str, file1_name: str,
                         file2_content: str, file2_id: str, file2_name: str) -> List[Conflict]:
        """检测两个文件之间的冲突"""
        conflicts = []
        
        info1 = self._extract_info(file1_content)
        info2 = self._extract_info(file2_content)
        
        for key in info1:
            if key in info2 and info1[key] != info2[key]:
                conflict = Conflict(
                    conflict_id=f"conflict_{hash(key + info1[key] + info2[key]) % 10000}",
                    file1_id=file1_id,
                    file1_name=file1_name,
                    file2_id=file2_id,
                    file2_name=file2_name,
                    description=f"{key}不一致",
                    severity="high" if key in ["违约金金额", "生效日期"] else "medium",
                    evidence1=info1[key],
                    evidence2=info2[key]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def batch_detect_conflicts(self, files: List[Tuple[str, str, str]]) -> List[Conflict]:
        """批量检测文件间冲突"""
        conflicts = []
        
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                file1_id, file1_name, file1_content = files[i]
                file2_id, file2_name, file2_content = files[j]
                
                file_conflicts = self.detect_conflicts(
                    file1_content, file1_id, file1_name,
                    file2_content, file2_id, file2_name
                )
                conflicts.extend(file_conflicts)
        
        return conflicts


class TimelineReconstructor:
    """时间线重建器"""
    
    def __init__(self):
        self._date_patterns = [
            r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日号]?',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{2})[-/](\d{1,2})[-/](\d{1,2})',
        ]
    
    def _extract_dates(self, content: str) -> List[datetime]:
        """提取日期"""
        dates = []
        
        for pattern in self._date_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                try:
                    if len(match) == 3:
                        year, month, day = match
                        if int(year) < 100:
                            year = f"20{year}"
                        dates.append(datetime(int(year), int(month), int(day)))
                except:
                    pass
        
        return dates
    
    def _extract_events(self, content: str, file_id: str, file_name: str) -> List[TimelineEvent]:
        """提取事件"""
        events = []
        dates = self._extract_dates(content)
        
        event_patterns = [
            (r'(?:签订|签署).*合同', 'contract_signing'),
            (r'(?:支付|付款|转账)', 'payment'),
            (r'(?:会议|会谈|协商)', 'meeting'),
            (r'(?:里程碑|节点|阶段)', 'milestone'),
            (r'(?:生效|失效|终止)', 'contract_status'),
        ]
        
        for pattern, event_type in event_patterns:
            if re.search(pattern, content):
                event = TimelineEvent(
                    event_id=f"event_{file_id}_{hash(pattern) % 1000}",
                    file_id=file_id,
                    file_name=file_name,
                    date=dates[0] if dates else None,
                    description=f"{event_type}: {pattern}",
                    type=event_type
                )
                events.append(event)
        
        return events
    
    def reconstruct(self, files: List[Tuple[str, str, str]]) -> List[TimelineEvent]:
        """重建时间线"""
        all_events = []
        
        for file_id, file_name, content in files:
            events = self._extract_events(content, file_id, file_name)
            all_events.extend(events)
        
        # 按日期排序
        all_events.sort(key=lambda x: x.date if x.date else datetime.min)
        
        return all_events


class CrossFileSynthesizer:
    """跨文件综合推理器"""
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.conflict_detector = ConflictDetector()
        self.timeline_reconstructor = TimelineReconstructor()
    
    def build_knowledge_graph(self, files: List[Tuple[str, str, str]]):
        """构建知识图谱"""
        # 添加文件节点
        for file_id, file_name, content in files:
            node = GraphNode(
                node_id=file_id,
                node_type="file",
                label=file_name,
                properties={"content": content[:200]}
            )
            self.knowledge_graph.add_node(node)
        
        # 添加文件间关系
        for i in range(len(files)):
            for j in range(len(files)):
                if i != j:
                    file1_id = files[i][0]
                    file2_id = files[j][0]
                    
                    # 检查是否存在引用关系
                    if files[j][2] in files[i][2] or files[j][1] in files[i][2]:
                        edge = GraphEdge(
                            source_id=file1_id,
                            target_id=file2_id,
                            relation_type=RelationType.REFERENCES,
                            properties={"context": "文件内容引用"}
                        )
                        self.knowledge_graph.add_edge(edge)
    
    def analyze_cross_file_conflicts(self, files: List[Tuple[str, str, str]]) -> List[Conflict]:
        """分析跨文件冲突"""
        return self.conflict_detector.batch_detect_conflicts(files)
    
    def reconstruct_timeline(self, files: List[Tuple[str, str, str]]) -> List[TimelineEvent]:
        """重建时间线"""
        return self.timeline_reconstructor.reconstruct(files)
    
    def synthesize(self, files: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        """综合分析"""
        # 构建知识图谱
        self.build_knowledge_graph(files)
        
        # 检测冲突
        conflicts = self.analyze_cross_file_conflicts(files)
        
        # 重建时间线
        timeline = self.reconstruct_timeline(files)
        
        # 获取图统计
        graph_stats = self.knowledge_graph.get_graph_stats()
        
        return {
            "graph_stats": graph_stats,
            "conflicts": conflicts,
            "timeline": timeline,
            "total_files": len(files),
            "total_conflicts": len(conflicts),
            "total_events": len(timeline)
        }
