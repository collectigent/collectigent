"""执行者(Executor) - 可行性评估与落地路径"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Agent, Role, Message

if TYPE_CHECKING:
    from ..llm import LLMProvider


class Executor(Agent):
    """执行者 - 负责评估可行性和制定执行计划"""
    
    def __init__(self, name: str = None, llm: "LLMProvider" = None):
        super().__init__(Role.EXECUTOR, name, llm=llm)
        self._temperature = 0.5  # 执行者温度较低，注重实际
    
    async def think(self, context: list[Message]) -> Message:
        """
        评估方案可行性并制定执行路径
        
        Args:
            context: 对话上下文（包含综合结论）
            
        Returns:
            执行评估消息
        """
        synthesis = self._extract_synthesis(context)
        feasibility = self._evaluate_feasibility(synthesis)
        execution_plan = self._create_execution_plan(synthesis, feasibility)
        risks = self._identify_execution_risks(synthesis)
        
        return Message(
            sender=self.role,
            content={
                "type": "execution_assessment",
                "feasibility": feasibility,
                "execution_plan": execution_plan,
                "resource_requirements": self._estimate_resources(synthesis),
                "timeline": self._estimate_timeline(synthesis),
                "risks": risks,
                "recommendations": self._get_recommendations(feasibility, risks),
            },
            metadata={"confidence": 0.9, "phase": "execution"}
        )
    
    def _extract_synthesis(self, context: list[Message]) -> dict:
        """提取综合结论"""
        for msg in context:
            if msg.sender == Role.SYNTHESIZER:
                return msg.content
        return {}
    
    def _evaluate_feasibility(self, synthesis: dict) -> dict:
        """评估可行性"""
        final = synthesis.get("final_synthesis", {})
        
        return {
            "overall_score": 0.75,
            "technical": {
                "score": 0.8,
                "concerns": ["技术实现难度中等"],
            },
            "resource": {
                "score": 0.7,
                "concerns": ["需要额外资源投入"],
            },
            "timeline": {
                "score": 0.75,
                "concerns": ["时间窗口紧张"],
            },
        }
    
    def _create_execution_plan(self, synthesis: dict, feasibility: dict) -> list[dict]:
        """创建执行计划"""
        return [
            {
                "phase": 1,
                "title": "准备阶段",
                "tasks": ["资源调配", "团队组建"],
                "duration": "1周",
            },
            {
                "phase": 2,
                "title": "实施阶段",
                "tasks": ["方案细化", "原型开发", "测试验证"],
                "duration": "2周",
            },
            {
                "phase": 3,
                "title": "部署阶段",
                "tasks": ["上线部署", "监控跟踪", "优化迭代"],
                "duration": "1周",
            },
        ]
    
    def _estimate_resources(self, synthesis: dict) -> dict:
        """估算资源需求"""
        return {
            "human": "3-5人",
            "compute": "中等规模",
            "budget": "待详细评估",
        }
    
    def _estimate_timeline(self, synthesis: dict) -> dict:
        """估算时间线"""
        return {
            "total": "4周",
            "milestones": {
                "planning": "1周",
                "implementation": "2周",
                "deployment": "1周",
            }
        }
    
    def _identify_execution_risks(self, synthesis: dict) -> list[dict]:
        """识别执行风险"""
        return [
            {
                "risk": "资源不足",
                "probability": "medium",
                "impact": "high",
                "mitigation": "提前锁定资源",
            },
            {
                "risk": "技术难题",
                "probability": "low",
                "impact": "medium",
                "mitigation": "预留技术攻关时间",
            },
        ]
    
    def _get_recommendations(self, feasibility: dict, risks: list) -> list[str]:
        """获取执行建议"""
        recs = []
        if feasibility.get("overall_score", 0) < 0.7:
            recs.append("建议进一步优化方案再执行")
        high_impact_risks = [r for r in risks if r.get("impact") == "high"]
        if high_impact_risks:
            recs.append(f"重点关注{len(high_impact_risks)}个高风险项")
        return recs
