"""创新者(Innovator) - 突破性想法产生"""

from .base import Agent, Role, Message


class Innovator(Agent):
    """创新者 - 负责产生突破性想法"""
    
    def __init__(self, name: str = None):
        super().__init__(Role.INNOVATOR, name)
        self._temperature = 1.0  # 创新者温度最高，最大创造性
        self._ideas = []
    
    async def think(self, context: list[Message]) -> Message:
        """
        基于任务产生创新方案
        
        Args:
            context: 对话上下文
            
        Returns:
            创新想法消息
        """
        task = self._extract_task(context)
        existing_views = self._extract_existing_views(context)
        
        # 生成创新方案
        ideas = await self._generate_ideas(task, existing_views)
        
        return Message(
            sender=self.role,
            content={
                "type": "innovation_ideas",
                "task": task,
                "ideas": ideas,
                "cross_domain_insights": self._get_cross_domain_insights(ideas),
            },
            metadata={"confidence": 0.7, "phase": "innovation"}
        )
    
    def _extract_task(self, context: list[Message]) -> str:
        """提取任务"""
        for msg in context:
            if msg.sender == Role.LEADER:
                data = msg.content
                if isinstance(data, dict):
                    return data.get("main_task", "")
        return ""
    
    def _extract_existing_views(self, context: list[Message]) -> list[dict]:
        """提取现有观点用于参考"""
        views = []
        for msg in context:
            if msg.sender in [Role.RESEARCHER, Role.CRITIC]:
                views.append(msg.content)
        return views
    
    async def _generate_ideas(self, task: str, existing_views: list[dict]) -> list[dict]:
        """
        生成创新方案
        
        实际应用中应接入LLM进行创意生成
        """
        # 模拟创新方案
        ideas = [
            {
                "title": f"颠覆性方案A",
                "description": "基于跨领域技术的创新方法",
                "novelty": 0.9,
                "feasibility": 0.6,
                "impact": 0.85,
                "risks": ["实施难度高", "需要新技术"],
            },
            {
                "title": f"渐进改进方案B",
                "description": "在现有基础上的优化路径",
                "novelty": 0.5,
                "feasibility": 0.85,
                "impact": 0.6,
                "risks": ["创新性不足"],
            },
            {
                "title": f"风险对冲方案C",
                "description": "多元化策略降低风险",
                "novelty": 0.6,
                "feasibility": 0.75,
                "impact": 0.7,
                "risks": ["复杂度高"],
            },
        ]
        return ideas
    
    def _get_cross_domain_insights(self, ideas: list[dict]) -> list[str]:
        """获取跨界洞察"""
        return [
            "借鉴生物界的自适应机制",
            "应用复杂系统理论",
            "引入博弈论激励机制",
        ]
    
    def add_idea(self, idea: dict):
        """添加想法"""
        self._ideas.append(idea)
