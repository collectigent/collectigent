"""迭代辩论引擎 - 多轮对话循环、观点收敛机制"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Callable
import asyncio

from ..agents.base import Message, Role


class ConsensusProtocol(Enum):
    """共识协议类型"""
    PRIORITY_RULING = "priority_ruling"      # 优先级裁决
    CONFIDENCE_WEIGHTED = "confidence"       # 置信度加权
    ITERATIVE_DEBATE = "iterative"           # 迭代辩论


@dataclass
class DebateConfig:
    """辩论配置"""
    max_rounds: int = 5
    convergence_threshold: float = 0.8
    protocol: ConsensusProtocol = ConsensusProtocol.ITERATIVE_DEBATE


class DebateEngine:
    """
    迭代辩论引擎
    
    负责：
    - 管理多轮辩论流程
    - 选择合适的共识协议
    - 判断观点收敛
    """
    
    def __init__(self, config: DebateConfig = None):
        self.config = config or DebateConfig()
        self._rounds: list[list[Message]] = []
        self._protocol_selectors: dict[ConsensusProtocol, Callable] = {
            ConsensusProtocol.PRIORITY_RULING: self._priority_ruling,
            ConsensusProtocol.CONFIDENCE_WEIGHTED: self._confidence_weighted,
            ConsensusProtocol.ITERATIVE_DEBATE: self._iterative_debate,
        }
    
    async def run_debate(self, context: list[Message], agents: dict[Role, any]) -> dict:
        """
        运行辩论流程
        
        Args:
            context: 初始上下文
            agents: 可用的Agent字典
            
        Returns:
            辩论结果
        """
        self._rounds = []
        current_context = list(context)
        
        for round_num in range(self.config.max_rounds):
            self._rounds.append([])
            
            # 选择发言者
            speaker = self._select_speaker(current_context, agents)
            if speaker is None:
                break
            
            # Agent思考
            response = await speaker.think(current_context)
            current_context.append(response)
            self._rounds[-1].append(response)
            
            # 检查收敛
            if self._check_convergence(current_context):
                break
        
        # 执行裁决
        verdict = self._make_verdict(current_context)
        
        return {
            "rounds": len(self._rounds),
            "verdict": verdict,
            "final_context": current_context,
        }
    
    def _select_speaker(self, context: list[Message], agents: dict[Role, any]) -> any:
        """选择发言者"""
        # 轮询选择
        spoke = {m.sender for m in context}
        priority = [Role.CRITIC, Role.RESEARCHER, Role.INNOVATOR]
        
        for role in priority:
            if role in agents and role not in spoke:
                return agents[role]
        
        # 如果都说过，从头开始轮询
        for role in priority:
            if role in agents:
                return agents[role]
        
        return None
    
    def _check_convergence(self, context: list[Message]) -> bool:
        """
        检查是否收敛
        
        收敛条件：
        1. 批判者连续无异议
        2. 或达到最大轮次
        3. 或置信度达到阈值
        """
        recent = context[-5:]
        
        # 条件1: 批判者连续无异议
        critics = [m for m in recent if m.sender == Role.CRITIC]
        if len(critics) >= 2:
            all_no_objection = all(
                not m.content.get("has_objection", True)
                for m in critics
            )
            if all_no_objection:
                return True
        
        # 条件2: 置信度达到阈值
        confidences = [
            m.metadata.get("confidence", 0)
            for m in recent
            if m.metadata.get("confidence")
        ]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            if avg_confidence >= self.config.convergence_threshold:
                return True
        
        return False
    
    def _make_verdict(self, context: list[Message]) -> dict:
        """
        生成裁决结果
        
        根据配置的协议执行裁决
        """
        protocol = self._protocol_selectors[self.config.protocol]
        return protocol(context)
    
    def _priority_ruling(self, context: list[Message]) -> dict:
        """
        优先级裁决协议
        
        按角色优先级选择最终决策
        """
        # 优先级: Executor > Synthesizer > Leader
        priority_roles = [Role.EXECUTOR, Role.SYNTHESIZER, Role.LEADER]
        
        for role in priority_roles:
            for msg in reversed(context):
                if msg.sender == role:
                    return {
                        "protocol": "priority_ruling",
                        "winner_role": role.value,
                        "decision": msg.content,
                        "confidence": msg.metadata.get("confidence", 0),
                    }
        
        return {"protocol": "priority_ruling", "decision": None}
    
    def _confidence_weighted(self, context: list[Message]) -> dict:
        """
        置信度加权协议
        
        按置信度加权汇总各角色观点
        """
        weighted_votes = []
        total_weight = 0
        
        for msg in context:
            confidence = msg.metadata.get("confidence", 0.5)
            weight = confidence ** 2  # 置信度平方加权
            
            weighted_votes.append({
                "sender": msg.sender.value if msg.sender else "user",
                "weight": weight,
                "content": msg.content,
            })
            total_weight += weight
        
        # 选择权重最高的
        if weighted_votes:
            best = max(weighted_votes, key=lambda x: x["weight"])
            return {
                "protocol": "confidence_weighted",
                "winner": best["sender"],
                "normalized_confidence": best["weight"] / total_weight if total_weight else 0,
                "decision": best["content"],
            }
        
        return {"protocol": "confidence_weighted", "decision": None}
    
    def _iterative_debate(self, context: list[Message]) -> dict:
        """
        迭代辩论协议
        
        通过多轮辩论逐步收敛
        """
        # 分析各轮变化
        evolution = self._analyze_evolution(context)
        
        # 找出最终共识
        consensus = self._find_final_consensus(context)
        
        return {
            "protocol": "iterative_debate",
            "rounds": len(self._rounds),
            "evolution": evolution,
            "consensus": consensus,
            "dissent_remaining": self._count_remaining_dissent(context),
        }
    
    def _analyze_evolution(self, context: list[Message]) -> list[dict]:
        """分析辩论演化"""
        evolution = []
        for i, round_msgs in enumerate(self._rounds):
            evolution.append({
                "round": i,
                "speaker": round_msgs[0].sender.value if round_msgs and round_msgs[0].sender else None,
                "message_count": len(round_msgs),
            })
        return evolution
    
    def _find_final_consensus(self, context: list[Message]) -> dict:
        """找出最终共识"""
        # 找综合者的结论
        for msg in reversed(context):
            if msg.sender == Role.SYNTHESIZER:
                return {
                    "source": "synthesizer",
                    "conclusion": msg.content,
                }
        
        # 找置信度最高的结论
        best = max(
            [m for m in context if m.metadata.get("confidence")],
            key=lambda x: x.metadata.get("confidence", 0),
            default=None
        )
        
        if best:
            return {
                "source": best.sender.value if best.sender else "unknown",
                "conclusion": best.content,
            }
        
        return {"source": None, "conclusion": None}
    
    def _count_remaining_dissent(self, context: list[Message]) -> int:
        """统计剩余异议"""
        return sum(
            1 for m in context
            if m.sender == Role.CRITIC and m.content.get("has_objection", False)
        )
    
    def check_convergence(self, context: list[Message]) -> bool:
        """公开的收敛检查接口"""
        return self._check_convergence(context)
