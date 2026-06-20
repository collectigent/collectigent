"""任务编排器 - Agent调度、消息路由、状态管理"""

from __future__ import annotations

import asyncio
from typing import Optional, Callable, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..agents.base import Agent, Message

from dataclasses import dataclass, field

from ..agents.base import Agent, Role, Message
from ..memory import Memory, ShortTermMemory
from ..engine import DebateEngine, ConsensusProtocol
from ..metrics import EmergenceMetrics


@dataclass
class SwarmConfig:
    """Swarm配置"""
    max_iterations: int = 10
    convergence_threshold: float = 0.8
    debate_rounds: int = 3
    enable_memory: bool = True
    # 可视化配置
    verbose: bool = False  # 是否输出详细日志
    show_process: bool = False  # 是否显示处理过程
    progress_callback: Optional[Callable[[str, dict], None]] = None  # 进度回调函数


class Swarm:
    """
    群体智能编排器
    
    负责：
    - 注册和管理Agent
    - 协调Agent间的消息传递
    - 管理辩论流程
    - 计算涌现指标
    """
    
    def __init__(self, config: SwarmConfig = None):
        self.config = config or SwarmConfig()
        self._agents: dict[Role, Agent] = {}
        self._memory: Optional[Memory] = None
        self._debate_engine: Optional[DebateEngine] = None
        self._metrics: EmergenceMetrics = EmergenceMetrics()
        self._state: dict = field(default_factory=dict)
        self._conversation_history: list[Message] = []
        self._step = 0  # 步骤计数器
    
    def _log(self, message: str, level: str = "info") -> None:
        """输出日志"""
        if self.config.verbose or self.config.show_process:
            prefix = {
                "info": "📝",
                "agent": "🤖",
                "debate": "💬",
                "success": "✅",
                "warning": "⚠️",
            }.get(level, "📝")
            print(f"{prefix} {message}")
    
    def _emit(self, event: str, data: dict = None) -> None:
        """发送进度事件"""
        if self.config.progress_callback:
            self.config.progress_callback(event, data or {})
        if self.config.verbose:
            print(f"📡 Event: {event} | Data: {data}")
    
    def register(self, agent: Agent) -> None:
        """注册Agent"""
        if agent.role in self._agents:
            raise ValueError(f"Agent with role {agent.role.value} already registered")
        
        self._agents[agent.role] = agent
        
        # 挂载记忆系统
        if self._memory and self.config.enable_memory:
            agent.attach_memory(self._memory)
    
    def set_memory(self, memory: Memory) -> None:
        """设置记忆系统"""
        self._memory = memory
        for agent in self._agents.values():
            agent.attach_memory(memory)
    
    def set_debate_engine(self, engine: DebateEngine) -> None:
        """设置辩论引擎"""
        self._debate_engine = engine
    
    @property
    def agents(self) -> dict[Role, Agent]:
        return self._agents
    
    @property
    def metrics(self) -> EmergenceMetrics:
        return self._metrics
    
    @property
    def conversation_history(self) -> list[Message]:
        return self._conversation_history
    
    async def run(self, task: str, initial_plan: str = None) -> dict:
        """
        执行群体智能任务
        
        Args:
            task: 用户任务描述
            initial_plan: 可选的初始计划
            
        Returns:
            执行结果
        """
        # 初始化
        self._conversation_history = []
        self._state = {"phase": "start", "iteration": 0}
        self._step = 0
        
        # 添加用户消息
        user_msg = Message(
            sender=None,  # 用户消息
            content={"task": task, "plan": initial_plan}
        )
        self._conversation_history.append(user_msg)
        
        self._log(f"开始处理任务: {task[:50]}...", "info")
        self._emit("task_start", {"task": task})
        
        # 触发Leader进行任务分解
        if Role.LEADER in self._agents:
            self._step += 1
            self._log(f"[{self._step}] Leader 进行任务分解", "agent")
            self._emit("agent_thinking", {"role": "leader", "step": self._step})
            
            leader_msg = await self._agents[Role.LEADER].think(self._conversation_history)
            self._conversation_history.append(leader_msg)
            
            self._emit("agent_response", {
                "role": "leader",
                "step": self._step,
                "content_type": leader_msg.content.get("type") if isinstance(leader_msg.content, dict) else "text"
            })
        
        # 执行辩论流程
        await self._run_debate()
        
        # 最终综合
        self._step += 1
        self._log(f"[{self._step}] Synthesizer 综合各方观点", "agent")
        self._emit("synthesis_start", {"step": self._step})
        
        final_result = await self._finalize()
        
        # 更新指标
        self._metrics.record_run(self._conversation_history)
        
        self._log(f"处理完成! 共 {len(self._conversation_history)} 条消息", "success")
        self._emit("task_complete", {
            "message_count": len(self._conversation_history),
            "metrics": self._metrics.get_summary()
        })
        
        return {
            "result": final_result,
            "metrics": self._metrics.get_summary(),
            "history": [m.to_dict() for m in self._conversation_history],
        }
    
    async def _run_debate(self) -> None:
        """运行辩论流程"""
        self._log(f"开始辩论流程 (最多 {self.config.max_iterations} 轮)", "debate")
        self._emit("debate_start", {"max_iterations": self.config.max_iterations})
        
        for iteration in range(self.config.max_iterations):
            self._state["iteration"] = iteration
            self._state["phase"] = f"debate_{iteration}"
            
            # 选择发言者
            speaker = self._select_next_speaker()
            if speaker is None:
                break
            
            # 发言
            self._step += 1
            role_display = speaker.name or speaker.role.value
            self._log(f"[{self._step}] {role_display} 发言...", "agent")
            self._emit("agent_thinking", {"role": speaker.role.value, "step": self._step, "iteration": iteration})
            
            # 获取Agent思考
            response = await speaker.think(self._conversation_history)
            self._conversation_history.append(response)
            
            # 提取响应摘要
            if isinstance(response.content, dict):
                content_type = response.content.get("type", "unknown")
                content_preview = str(response.content)[:80]
            else:
                content_type = "text"
                content_preview = str(response.content)[:80]
            
            self._log(f"    → {content_type}: {content_preview}...", "debate")
            self._emit("agent_response", {
                "role": speaker.role.value,
                "step": self._step,
                "content_type": content_type,
                "iteration": iteration
            })
            
            # 检查收敛
            if self._check_convergence():
                self._state["phase"] = "converged"
                self._log("检测到收敛，辩论结束", "success")
                self._emit("debate_converged", {"iteration": iteration})
                break
        
        self._log(f"辩论流程结束，共 {iteration + 1} 轮", "debate")
    
    def _select_next_speaker(self) -> Optional[Agent]:
        """选择下一个发言的Agent"""
        spoke_recently = {m.sender for m in self._conversation_history[-len(self._agents):]}
        
        # 按优先级选择
        priority_order = [
            Role.RESEARCHER,
            Role.CRITIC,
            Role.INNOVATOR,
            Role.SYNTHESIZER,
            Role.EXECUTOR,
        ]
        
        for role in priority_order:
            if role in self._agents and role not in spoke_recently:
                return self._agents[role]
        
        # 如果都说过话了，从头开始
        if priority_order[0] in self._agents:
            return self._agents[priority_order[0]]
        
        return None
    
    def _check_convergence(self) -> bool:
        """检查是否收敛"""
        if not self._debate_engine:
            # 默认收敛检查
            recent = self._conversation_history[-5:]
            critics = [m for m in recent if m.sender == Role.CRITIC]
            
            if len(critics) >= 2:
                # 连续无异议则收敛
                no_objections = all(
                    not m.content.get("has_objection", True) 
                    for m in critics
                )
                return no_objections
        else:
            return self._debate_engine.check_convergence(self._conversation_history)
        
        return False
    
    async def _finalize(self) -> dict:
        """最终综合"""
        if Role.SYNTHESIZER in self._agents:
            synthesis = await self._agents[Role.SYNTHESIZER].think(self._conversation_history)
            self._conversation_history.append(synthesis)
            return synthesis.content
        
        return {"status": "completed", "messages": len(self._conversation_history)}
    
    def get_metrics(self) -> dict:
        """获取涌现指标"""
        return self._metrics.get_summary()
    
    def get_state(self) -> dict:
        """获取当前状态"""
        return {
            "swarm_state": self._state,
            "agent_states": {
                role.value: agent.get_state("status") 
                for role, agent in self._agents.items()
            },
            "message_count": len(self._conversation_history),
        }
