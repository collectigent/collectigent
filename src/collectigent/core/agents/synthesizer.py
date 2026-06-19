"""综合者(Synthesizer) - 整合多方观点"""

from .base import Agent, Role, Message


class Synthesizer(Agent):
    """综合者 - 负责整合多方观点形成结论"""
    
    def __init__(self, name: str = None):
        super().__init__(Role.SYNTHESIZER, name)
        self._temperature = 0.6
    
    async def think(self, context: list[Message]) -> Message:
        """
        综合各方观点形成统一结论
        
        Args:
            context: 各角色发言的上下文
            
        Returns:
            综合结论消息
        """
        all_views = self._collect_all_views(context)
        consensus = self._find_consensus(all_views)
        conflicts = self._resolve_conflicts(all_views)
        synthesis = self._create_synthesis(all_views, consensus, conflicts)
        
        return Message(
            sender=self.role,
            content={
                "type": "synthesis",
                "consensus_points": consensus,
                "resolved_conflicts": conflicts,
                "final_synthesis": synthesis,
                "remaining_dissent": self._get_remaining_dissent(all_views),
            },
            metadata={"confidence": 0.85, "phase": "synthesis"}
        )
    
    def _collect_all_views(self, context: list[Message]) -> dict:
        """收集所有观点"""
        views = {
            Role.RESEARCHER: [],
            Role.CRITIC: [],
            Role.INNOVATOR: [],
        }
        for msg in context:
            if msg.sender in views:
                views[msg.sender].append(msg.content)
        return views
    
    def _find_consensus(self, views: dict) -> list[str]:
        """找出共识点"""
        consensus = []
        
        # 从研究者和创新者观点中找共同点
        research_views = views.get(Role.RESEARCHER, [])
        innovation_views = views.get(Role.INNOVATOR, [])
        
        if research_views and innovation_views:
            # 简单模拟：找到任务相关的共识
            consensus.append("任务目标明确，需要综合分析")
        
        return consensus
    
    def _resolve_conflicts(self, views: dict) -> list[dict]:
        """消解冲突"""
        conflicts = []
        
        # 检查批判者提出的异议
        critic_views = views.get(Role.CRITIC, [])
        for cv in critic_views:
            if isinstance(cv, dict) and cv.get("has_objection"):
                objections = cv.get("objections", [])
                for obj in objections:
                    conflicts.append({
                        "issue": obj.get("description"),
                        "resolution": f"建议进一步验证{obj.get('type')}",
                    })
        
        return conflicts
    
    def _create_synthesis(self, views: dict, consensus: list, conflicts: list) -> dict:
        """创建综合结论"""
        return {
            "summary": "综合各方观点，形成以下结论",
            "key_points": consensus[:3] if consensus else ["需要进一步讨论"],
            "resolved_issues": [c["issue"] for c in conflicts],
            "recommendation": "建议采用综合方案",
            "next_steps": ["提交执行者评估", "领导者和最终确认"],
        }
    
    def _get_remaining_dissent(self, views: dict) -> list[dict]:
        """获取未被采纳的不同意见"""
        dissent = []
        critic_views = views.get(Role.CRITIC, [])
        for cv in critic_views:
            if isinstance(cv, dict) and cv.get("has_objection"):
                dissent.append({
                    "source": "critic",
                    "dissent": cv.get("objections"),
                })
        return dissent
