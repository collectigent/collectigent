"""Agent基类 - 定义6角色的通用接口"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from ..llm import LLMProvider, LLMConfig


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
    
    def __init__(self, role: Role, name: str = None, llm: "LLMProvider" = None):
        self.role = role
        self.name = name or role.value.capitalize()
        self._llm = llm
        self._temperature = 0.7
        self._tools = []
        self._memory = None
        self._state = {}
    
    @property
    def llm(self) -> Optional["LLMProvider"]:
        """获取LLM提供商"""
        return self._llm
    
    @llm.setter
    def llm(self, provider: "LLMProvider"):
        """设置LLM提供商"""
        self._llm = provider
    
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
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        调用LLM生成响应
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词（默认使用角色提示词）
            history: 对话历史
            **kwargs: 额外参数
            
        Returns:
            LLM生成的文本
        """
        if not self._llm:
            raise RuntimeError(f"Agent {self.name} 未配置LLM提供商")
        
        if system_prompt is None:
            system_prompt = self.get_system_prompt()
        
        response = await self._llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            temperature=kwargs.get("temperature", self._temperature),
            **kwargs
        )
        
        # 记录到记忆系统
        if self._memory:
            self._memory.remember(f"llm_call_{self.role.value}", {
                "prompt": prompt,
                "response": response.content,
                "usage": response.usage,
            })
        
        return response.content
    
    async def call_llm_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ):
        """
        流式调用LLM生成响应
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            **kwargs: 额外参数
            
        Yields:
            文本片段
        """
        if not self._llm:
            raise RuntimeError(f"Agent {self.name} 未配置LLM提供商")
        
        if system_prompt is None:
            system_prompt = self.get_system_prompt()
        
        async for chunk in self._llm.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            history=history,
            temperature=kwargs.get("temperature", self._temperature),
            **kwargs
        ):
            yield chunk
    
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
