"""研究者(Researcher) - 信息收集与深度分析"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Agent, Role, Message

if TYPE_CHECKING:
    from ..llm import LLMProvider


class Researcher(Agent):
    """研究者 - 负责信息收集和深度分析"""
    
    def __init__(self, name: str = None, llm: "LLMProvider" = None):
        super().__init__(Role.RESEARCHER, name, llm=llm)
        self._temperature = 0.8  # 研究者温度较高，更具创造性
        self._findings = []
    
    async def think(self, context: list[Message]) -> Message:
        """
        基于任务进行信息收集和分析
        
        Args:
            context: 对话上下文
            
        Returns:
            研究发现消息
        """
        task = self._extract_task(context)
        findings = await self._gather_information(task)
        
        return Message(
            sender=self.role,
            content={
                "type": "research_findings",
                "task": task,
                "findings": findings,
                "sources": self._findings,
                "knowledge_gaps": self._identify_gaps(findings),
            },
            metadata={"confidence": 0.85, "phase": "research"}
        )
    
    def _extract_task(self, context: list[Message]) -> str:
        """从上下文提取研究任务"""
        for msg in context:
            if msg.sender == Role.LEADER:
                data = msg.content
                if isinstance(data, dict):
                    return data.get("main_task", "")
        # 尝试从用户消息获取
        for msg in context:
            if msg.sender is None:
                return msg.content.get("task", "") if isinstance(msg.content, dict) else str(msg.content)
        return ""
    
    async def _gather_information(self, task: str) -> list[dict]:
        """
        收集信息（模拟实现）
        
        实际应用中应接入搜索API或知识库
        """
        # 模拟研究发现
        return [
            {
                "aspect": "背景",
                "facts": [f"{task}的相关背景信息"],
                "reliability": 0.9,
            },
            {
                "aspect": "现状",
                "facts": ["当前行业状况分析"],
                "reliability": 0.85,
            },
            {
                "aspect": "趋势",
                "facts": ["未来发展趋势预测"],
                "reliability": 0.75,
            },
        ]
    
    def _identify_gaps(self, findings: list[dict]) -> list[str]:
        """识别知识盲区"""
        gaps = []
        if len(findings) < 3:
            gaps.append("信息收集不够全面")
        for f in findings:
            if f.get("reliability", 1) < 0.8:
                gaps.append(f"'{f['aspect']}'的可靠性待验证")
        return gaps
    
    def add_source(self, source: dict):
        """添加信息源"""
        self._findings.append(source)
