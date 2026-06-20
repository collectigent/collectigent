"""批判者(Critic) - 挑战假设与风险识别"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Agent, Role, Message

if TYPE_CHECKING:
    from ..llm import LLMProvider


class Critic(Agent):
    """批判者 - 负责挑战假设和识别风险"""
    
    def __init__(self, name: str = None, llm: "LLMProvider" = None):
        super().__init__(Role.CRITIC, name, llm=llm)
        self._temperature = 0.5  # 批判者温度较低，更理性
        self._objections = []
    
    async def think(self, context: list[Message]) -> Message:
        """
        对已有观点进行批判性分析
        
        Args:
            context: 对话上下文（包含其他角色的观点）
            
        Returns:
            批判性反馈消息
        """
        target_views = self._extract_views(context)
        objections = self._analyze_critically(target_views)
        has_objection = len(objections) > 0
        
        return Message(
            sender=self.role,
            content={
                "type": "critique",
                "target_views": target_views,
                "objections": objections,
                "has_objection": has_objection,
                "risk_assessment": self._assess_risks(target_views),
            },
            metadata={
                "confidence": 0.8,
                "phase": "critique",
                "objection_count": len(objections),
            }
        )
    
    def _extract_views(self, context: list[Message]) -> list[dict]:
        """提取需要批判的观点"""
        views = []
        for msg in context:
            if msg.sender in [Role.RESEARCHER, Role.INNOVATOR]:
                if isinstance(msg.content, dict):
                    views.append({
                        "source": msg.sender.value,
                        "content": msg.content,
                    })
        return views
    
    def _analyze_critically(self, views: list[dict]) -> list[dict]:
        """
        批判性分析
        
        Returns:
            异议列表
        """
        objections = []
        for view in views:
            content = view.get("content", {})
            
            # 检查逻辑漏洞
            if content.get("type") == "research_findings":
                gaps = content.get("knowledge_gaps", [])
                if gaps:
                    objections.append({
                        "type": "knowledge_gap",
                        "severity": "high",
                        "description": f"研究存在知识盲区: {', '.join(gaps)}",
                    })
                
                # 检查可靠性
                for finding in content.get("findings", []):
                    if finding.get("reliability", 1) < 0.8:
                        objections.append({
                            "type": "reliability_issue",
                            "severity": "medium",
                            "description": f"'{finding['aspect']}'的可靠性仅为{finding['reliability']}",
                        })
            
            # 检查创新方案的可行性
            if content.get("type") == "innovation_ideas":
                for idea in content.get("ideas", []):
                    if not idea.get("feasibility"):
                        objections.append({
                            "type": "feasibility_issue",
                            "severity": "high",
                            "description": f"创新方案'{idea.get('title')}'可行性存疑",
                        })
        
        return objections
    
    def _assess_risks(self, views: list[dict]) -> list[dict]:
        """评估潜在风险"""
        risks = []
        if len(views) < 2:
            risks.append({
                "type": "insufficient_perspectives",
                "severity": "medium",
                "description": "收集的观点数量不足，可能遗漏重要角度",
            })
        return risks
    
    def add_objection(self, objection: dict):
        """记录异议"""
        self._objections.append(objection)
