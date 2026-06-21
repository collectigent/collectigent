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
    
    async def think(self, context: list[Message]) -> Message:
        """
        对已有观点进行批判性分析
        
        Args:
            context: 对话上下文（包含其他角色的观点）
            
        Returns:
            批判性反馈消息
        """
        # 提取之前的观点
        previous_analysis = ""
        for msg in context:
            if msg.sender == Role.RESEARCHER:
                if isinstance(msg.content, dict):
                    previous_analysis = msg.content.get("analysis", "")
        
        task = self._extract_task(context)
        
        # 构建批判提示词
        prompt = f"""请对以下合同进行批判性分析和风险评估：

{task}

已有分析：
{previous_analysis}

请从以下角度进行批判性分析：
1. 合同条款的法律漏洞和风险
2. 当事人权益平衡问题
3. 违约责任条款的合理性
4. 争议解决条款的有效性
5. 潜在的法律陷阱和模糊表述

请列出具体的风险点和修改建议。"""

        # 调用LLM生成响应
        response_content = await self.call_llm(prompt=prompt)
        
        # 简单判断是否有异议（如果响应包含"风险"或"问题"等关键词）
        has_objection = any(keyword in response_content for keyword in ["风险", "问题", "漏洞", "不合理", "缺失"])
        
        return Message(
            sender=self.role,
            content={
                "type": "critique",
                "criticism": response_content,
                "objections": [{"description": response_content}],
                "has_objection": has_objection,
                "risk_assessment": response_content,
            },
            metadata={
                "confidence": 0.8,
                "phase": "critique",
            }
        )
    
    def _extract_task(self, context: list[Message]) -> str:
        """从上下文提取任务"""
        for msg in context:
            if msg.sender is None:
                return msg.content.get("task", "") if isinstance(msg.content, dict) else str(msg.content)
        return ""