"""基础涌现指标 - 群体增益、多样性指数、错误修正率"""

from dataclasses import dataclass, field
from typing import Optional
import math

from ..agents.base import Message, Role


@dataclass
class EmergenceMetrics:
    """
    涌现指标计算器
    
    核心指标：
    - 群体增益 (Group Gain): 群体表现 vs 最优个体
    - 多样性指数 (Diversity Index): 观点多样性
    - 错误修正率 (Error Correction Rate): 批判者修正错误的比例
    """
    
    _history: list[dict] = field(default_factory=list)
    
    def record_run(self, conversation: list[Message]) -> None:
        """记录一次运行"""
        metrics = self.calculate(conversation)
        self._history.append(metrics)
    
    def calculate(self, conversation: list[Message]) -> dict:
        """计算当前对话的涌现指标"""
        return {
            "group_gain": self.group_gain(conversation),
            "diversity_index": self.diversity_index(conversation),
            "error_correction_rate": self.error_correction_rate(conversation),
            "consensus_speed": self.consensus_speed(conversation),
            "confidence_evolution": self.confidence_evolution(conversation),
        }
    
    def group_gain(self, conversation: list[Message]) -> float:
        """
        群体增益
        
        定义：群体最终决策质量 / 最优个体决策质量
        
        实现：使用置信度作为质量代理
        """
        confidences = [
            m.metadata.get("confidence", 0)
            for m in conversation
            if m.metadata.get("confidence")
        ]
        
        if not confidences:
            return 1.0
        
        # 最终置信度 vs 初始最高置信度
        final_confidence = confidences[-1] if confidences else 0
        max_initial = confidences[0] if confidences else 0
        
        if max_initial == 0:
            return 1.0
        
        # 增益 = 最终 / 最大初始（归一化到1.0以上）
        gain = final_confidence / max_initial
        
        # 模拟群体增益因子（实际应用中需要基准测试标定）
        # 这里简化处理：当存在批判和修正时，增益 > 1
        critics = [m for m in conversation if m.sender == Role.CRITIC]
        if critics:
            corrections = sum(1 for c in critics if c.content.get("objections"))
            if corrections > 0:
                gain *= (1 + 0.1 * corrections)
        
        return round(gain, 3)
    
    def diversity_index(self, conversation: list[Message]) -> float:
        """
        多样性指数
        
        定义：衡量群体中观点的多样性
        实现：基于发言角色和内容的熵
        
        范围：0-1，0表示完全一致，1表示完全多样
        """
        # 统计各角色发言分布
        role_counts: dict[str, int] = {}
        for msg in conversation:
            if msg.sender:
                role = msg.sender.value
                role_counts[role] = role_counts.get(role, 0) + 1
        
        if not role_counts:
            return 0.0
        
        # 计算香农熵
        total = sum(role_counts.values())
        entropy = 0.0
        for count in role_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # 归一化到最大熵
        max_roles = len(Role)
        max_entropy = math.log2(max_roles)
        
        if max_entropy == 0:
            return 0.0
        
        return round(entropy / max_entropy, 3)
    
    def error_correction_rate(self, conversation: list[Message]) -> float:
        """
        错误修正率
        
        定义：批判者提出的异议被采纳/修正的比例
        
        实现：统计异议数量 vs 最终被解决的异议数量
        """
        critics = [m for m in conversation if m.sender == Role.CRITIC]
        
        if not critics:
            return 0.0
        
        # 统计异议
        total_objections = 0
        resolved_objections = 0
        
        for c in critics:
            objections = c.content.get("objections", [])
            total_objections += len(objections)
        
        # 统计被解决的异议（在后续消息中被提及或采纳）
        synthesizer_views = [
            m.content for m in conversation
            if m.sender == Role.SYNTHESIZER
        ]
        
        for sv in synthesizer_views:
            resolved = sv.get("resolved_conflicts", [])
            resolved_objections += len(resolved)
        
        if total_objections == 0:
            return 1.0  # 无异议表示正确
        
        return round(resolved_objections / total_objections, 3)
    
    def consensus_speed(self, conversation: list[Message]) -> float:
        """
        共识速度
        
        定义：达成共识所需的平均消息数
        
        实现：消息总数 / 达成共识的轮次
        """
        # 找到达成共识的点
        consensus_idx = None
        
        for i, msg in enumerate(conversation):
            if msg.sender == Role.CRITIC:
                # 找到连续无异议的位置
                if not msg.content.get("has_objection", True):
                    # 检查后续消息是否也保持无异议
                    if i + 1 < len(conversation):
                        next_msg = conversation[i + 1]
                        if next_msg.sender == Role.SYNTHESIZER:
                            consensus_idx = i
                            break
        
        if consensus_idx is None or consensus_idx == 0:
            return float(len(conversation))
        
        return round(len(conversation) / (consensus_idx + 1), 2)
    
    def confidence_evolution(self, conversation: list[Message]) -> list[float]:
        """
        置信度演化
        
        返回：各阶段的置信度变化
        """
        return [
            m.metadata.get("confidence", 0)
            for m in conversation
            if m.metadata.get("confidence")
        ]
    
    def get_summary(self) -> dict:
        """获取指标摘要"""
        if not self._history:
            return {
                "group_gain": 0.0,
                "diversity_index": 0.0,
                "error_correction_rate": 0.0,
                "total_runs": 0,
            }
        
        latest = self._history[-1]
        
        # 计算历史平均
        n = len(self._history)
        avg_gain = sum(h["group_gain"] for h in self._history) / n
        avg_diversity = sum(h["diversity_index"] for h in self._history) / n
        avg_correction = sum(h["error_correction_rate"] for h in self._history) / n
        
        return {
            "current": latest,
            "historical_avg": {
                "group_gain": round(avg_gain, 3),
                "diversity_index": round(avg_diversity, 3),
                "error_correction_rate": round(avg_correction, 3),
            },
            "total_runs": n,
        }
