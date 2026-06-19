"""Agent基类 - 定义6角色的通用接口"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional
import uuid


class Role(Enum):
    """6角色枚举"""
    LEADER = "leader"
    RESEARCHER = "researcher"
    CRITIC = "critic"
    INNOVATOR = "innovator"
    SYNTHESIZER = "synthesizer"
    EXECUTOR = "executor"


@dataclass
class Message:
    """Agent间传递的消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: Role = None
    recipient: Optional[Role] = None  # None表示广播
    content: Any = None
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender.value if self.sender else None,
            "recipient": self.recipient.value if self.recipient else None,
            "content": self.content,
            "metadata": self.metadata,
        }


class Agent:
    """Agent基类 - 所有角色的父类"""
    
    def __init__(self, role: Role, name: str = None):
        self.role = role
        self.name = name or role.value.capitalize()
        self._temperature = 0.7
        self._tools = []
        self._memory = None
        self._state = {}
    
    @property
    def temperature(self) -> float:
        """模型温度设置"""
        return self._temperature
    
    @temperature.setter
    def temperature(self, value: float):
        if 0 <= value <= 2:
            self._temperature = value
    
    def attach_memory(self, memory: "Memory"):
        """挂载记忆系统"""
        self._memory = memory
    
    def add_tool(self, tool: callable):
        """注册工具"""
        self._tools.append(tool)
    
    def set_state(self, key: str, value: Any):
        """设置Agent状态"""
        self._state[key] = value
    
    def get_state(self, key: str) -> Any:
        """获取Agent状态"""
        return self._state.get(key)
    
    async def think(self, context: list[Message]) -> Message:
        """
        核心思考方法 - 子类必须实现
        
        Args:
            context: 对话上下文
            
        Returns:
            产生的消息
        """
        raise NotImplementedError
    
    def get_system_prompt(self) -> str:
        """
        获取角色系统提示词
        
        Returns:
            角色定义prompt
        """
        prompts = {
            Role.LEADER: """你是一个领导者(Leader)，负责任务分解、策略制定和全局协调。
你的职责：
- 理解用户需求，分解任务
- 协调各角色工作
- 监控进度，适时干预
- 最终决策或共识推进""",
            
            Role.RESEARCHER: """你是一个研究者(Researcher)，负责信息收集和深度分析。
你的职责：
- 搜集相关资料和数据
- 分析问题背景
- 提供事实依据
- 识别知识盲区""",
            
            Role.CRITIC: """你是一个批判者(Critic)，负责挑战假设和识别风险。
你的职责：
- 质疑现有观点
- 识别逻辑漏洞
- 评估潜在风险
- 提出反对意见""",
            
            Role.INNOVATOR: """你是一个创新者(Innovator)，负责产生突破性想法。
你的职责：
- 提供新颖观点
- 突破思维定式
- 产生创意方案
- 跨界联想""",
            
            Role.SYNTHESIZER: """你是一个综合者(Synthesizer)，负责整合多方观点。
你的职责：
- 归纳整理各方观点
- 寻找共识点
- 消解冲突
- 形成综合结论""",
            
            Role.EXECUTOR: """你是一个执行者(Executor)，负责评估可行性和落地路径。
你的职责：
- 评估方案可行性
- 识别资源约束
- 制定执行计划
- 风险缓解建议""",
        }
        return prompts.get(self.role, "")
