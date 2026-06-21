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
        task = self._extract_task(context)
        
        # 提取之前的分析
        previous_content = ""
        for msg in context:
            if msg.sender == Role.SYNTHESIZER:
                if isinstance(msg.content, dict):
                    previous_content = msg.content.get("final_synthesis", "")
        
        # 构建执行评估提示词
        prompt = f"""请对以下合同审核结果进行执行评估和合规验证：

{task}

已有分析：
{previous_content}

请从以下角度进行评估：
1. 合同修改建议的可执行性
2. 合规验证结果
3. 后续行动建议
4. 风险防范措施

请给出具体的执行建议和合规验证结论。"""

        # 调用LLM生成响应
        response_content = await self.call_llm(prompt=prompt)
        
        return Message(
            sender=self.role,
            content={
                "type": "execution_assessment",
                "feasibility": {"score": 0.85, "assessment": response_content},
                "execution_plan": response_content,
                "compliance_check": response_content,
                "recommendations": response_content,
            },
            metadata={"confidence": 0.9, "phase": "execution"}
        )
    
    def _extract_task(self, context: list[Message]) -> str:
        """从上下文提取任务"""
        for msg in context:
            if msg.sender is None:
                return msg.content.get("task", "") if isinstance(msg.content, dict) else str(msg.content)
        return ""