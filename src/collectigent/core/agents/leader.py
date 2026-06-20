"""领导者(Leader) - 任务分解与全局协调"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Agent, Role, Message

if TYPE_CHECKING:
    from ..llm import LLMProvider


class Leader(Agent):
    """领导者 - 负责任务分解、策略制定和全局协调"""
    
    def __init__(self, name: str = None, llm: "LLMProvider" = None):
        super().__init__(Role.LEADER, name, llm=llm)
        self._temperature = 0.6  # 领导者温度较低，更稳定
    
    async def think(self, context: list[Message]) -> Message:
        """
        分析上下文，进行任务分解和协调
        
        Args:
            context: 各角色发言的上下文
            
        Returns:
            指导性消息或任务分配
        """
        # 解析上下文中的关键信息
        user_task = self._extract_task(context)
        
        # 调用LLM进行任务分解
        json_template = '''{
    "main_task": "主要任务描述",
    "analysis": "对任务的初步分析",
    "subtasks": [
        {"role": "researcher", "task": "研究子任务"},
        {"role": "critic", "task": "批判分析子任务"},
        {"role": "innovator", "task": "创新方案子任务"}
    ]
}'''
        
        prompt = f"""作为群体智能的领导者，请分析以下任务并进行分解：

任务：{user_task}

请用JSON格式返回任务分解，格式如下：
{json_template}"""
        
        try:
            llm_response = await self.call_llm(prompt)
            import json
            # 尝试解析JSON
            result = json.loads(llm_response)
            content = {
                "type": "task_allocation",
                **result,
                "current_phase": "decomposition",
            }
        except Exception:
            # 如果解析失败，使用默认分解
            content = {
                "type": "task_allocation",
                "main_task": user_task,
                "analysis": llm_response if 'llm_response' in dir() else "需要深入分析",
                "subtasks": [
                    {"role": Role.RESEARCHER, "task": f"深入研究: {user_task}"},
                    {"role": Role.CRITIC, "task": f"批判性分析: {user_task}"},
                    {"role": Role.INNOVATOR, "task": f"提出创新方案: {user_task}"},
                ],
                "current_phase": "decomposition",
            }
        
        # 返回任务分配消息
        return Message(
            sender=self.role,
            content=content,
            metadata={"phase": "planning"}
        )
    
    def _extract_task(self, context: list[Message]) -> str:
        """从上下文提取用户任务"""
        for msg in context:
            if msg.sender is None:  # 用户消息
                return msg.content.get("task", "") if isinstance(msg.content, dict) else str(msg.content)
        return ""
    
    def _decompose_task(self, task: str) -> list[dict]:
        """分解任务为子任务"""
        return [
            {"role": Role.RESEARCHER, "task": f"研究: {task}"},
            {"role": Role.CRITIC, "task": f"批判分析: {task}"},
            {"role": Role.INNOVATOR, "task": f"创新方案: {task}"},
        ]
    
    async def coordinate(self, context: list[Message]) -> dict:
        """
        协调各角色讨论
        
        Args:
            context: 当前讨论上下文
            
        Returns:
            协调指令
        """
        return {
            "action": "continue" if not self._is_converged(context) else "finalize",
            "next_speaker": self._select_next_speaker(context),
        }
    
    def _is_converged(self, context: list[Message]) -> bool:
        """判断是否达成共识"""
        # 简化实现：连续3轮无反对意见则收敛
        recent = context[-5:]
        critics = [m for m in recent if m.sender == Role.CRITIC]
        if len(critics) >= 3:
            return all(c.content.get("has_objection", True) is False for c in critics)
        return False
    
    def _select_next_speaker(self, context: list[Message]) -> Role:
        """选择下一个发言者"""
        # 简单轮询
        spoke = {m.sender for m in context if m.sender != Role.LEADER}
        for role in [Role.RESEARCHER, Role.CRITIC, Role.INNOVATOR, Role.SYNTHESIZER, Role.EXECUTOR]:
            if role not in spoke:
                return role
        return Role.SYNTHESIZER
