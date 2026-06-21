"""创新者(Innovator) - 突破性想法产生"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Agent, Role, Message

if TYPE_CHECKING:
    from ..llm import LLMProvider


class Innovator(Agent):
    """创新者 - 负责产生突破性想法"""
    
    def __init__(self, name: str = None, llm: "LLMProvider" = None):
        super().__init__(Role.INNOVATOR, name, llm=llm)
        self._temperature = 1.0  # 创新者温度最高，最大创造性
    
    async def think(self, context: list[Message]) -> Message:
        """
        基于任务产生创新方案
        
        Args:
            context: 对话上下文
            
        Returns:
            创新想法消息
        """
        task = self._extract_task(context)
        
        # 提取之前的分析
        previous_analysis = ""
        for msg in context:
            if msg.sender == Role.RESEARCHER:
                if isinstance(msg.content, dict):
                    previous_analysis = msg.content.get("analysis", "")
        
        # 构建创新提示词
        prompt = f"""请对以下合同提出创新性的优化建议和解决方案：

{task}

已有分析：
{previous_analysis}

请从以下角度提出创新方案：
1. 合同条款的创新性改进建议
2. 风险防范的创新机制
3. 权益保障的创新方案
4. 争议解决的创新方式
5. 其他创新性的优化建议

请提出具体可行的创新方案。"""

        # 调用LLM生成响应
        response_content = await self.call_llm(prompt=prompt)
        
        return Message(
            sender=self.role,
            content={
                "type": "innovation_ideas",
                "task": task,
                "ideas": [{"title": "创新方案", "description": response_content}],
                "innovation_proposals": response_content,
            },
            metadata={"confidence": 0.7, "phase": "innovation"}
        )
    
    def _extract_task(self, context: list[Message]) -> str:
        """提取任务"""
        for msg in context:
            if msg.sender is None:
                return msg.content.get("task", "") if isinstance(msg.content, dict) else str(msg.content)
        return ""