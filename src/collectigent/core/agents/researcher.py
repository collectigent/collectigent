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
    
    async def think(self, context: list[Message]) -> Message:
        """
        基于任务进行信息收集和分析
        
        Args:
            context: 对话上下文
            
        Returns:
            研究发现消息
        """
        task = self._extract_task(context)
        
        # 构建研究提示词
        prompt = f"""请对以下合同进行深度研究和分析：

{task}

请从以下角度进行分析：
1. 合同背景和当事人信息
2. 合同主要条款和关键内容
3. 法律合规性分析
4. 潜在风险点识别
5. 权利义务平衡分析

请以结构化的方式输出你的研究发现。"""

        # 调用LLM生成响应
        response_content = await self.call_llm(prompt=prompt)
        
        return Message(
            sender=self.role,
            content={
                "type": "research_findings",
                "task": task,
                "findings": [{"aspect": "合同分析", "content": response_content}],
                "analysis": response_content,
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