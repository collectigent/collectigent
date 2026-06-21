"""LLM提供商基类 - 定义统一接口"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


class ProviderType(Enum):
    """LLM提供商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GLM = "glm"          # 智谱AI
    DEEPSEEK = "deepseek"
    DOUBAO = "doubao"    # 字节跳动豆包
    QWEN = "qwen"        # 阿里云通义千问
    KIMI = "kimi"        # Moonshot月之暗面
    MINIMAX = "minimax"  # MiniMax


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: ProviderType
    model: str = ""  # 默认为空，会自动填充
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    timeout: float = 60.0
    extra_params: dict[str, Any] = field(default_factory=dict)
    
    # 各提供商默认模型
    DEFAULT_MODELS: dict[ProviderType, str] = field(default_factory=lambda: {
        ProviderType.OPENAI: "gpt-4o",
        ProviderType.ANTHROPIC: "claude-3-5-sonnet-20241022",
        ProviderType.GLM: "glm-4",
        ProviderType.DEEPSEEK: "deepseek-chat",
        ProviderType.DOUBAO: "doubao-pro-32k",
        ProviderType.QWEN: "qwen-turbo",
        ProviderType.KIMI: "moonshot-v1-8k",
        ProviderType.MINIMAX: "abab6-chat",
    })
    
    def __post_init__(self):
        if not self.model:
            self.model = self.DEFAULT_MODELS.get(self.provider, "")
    
    @classmethod
    def for_openai(cls, model: str = "gpt-4o", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.OPENAI, model=model, **kwargs)
    
    @classmethod
    def for_anthropic(cls, model: str = "claude-3-5-sonnet-20241022", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.ANTHROPIC, model=model, **kwargs)
    
    @classmethod
    def for_glm(cls, model: str = "glm-4", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.GLM, model=model, **kwargs)
    
    @classmethod
    def for_deepseek(cls, model: str = "deepseek-chat", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.DEEPSEEK, model=model, **kwargs)
    
    @classmethod
    def for_doubao(cls, model: str = "doubao-pro-32k", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.DOUBAO, model=model, **kwargs)
    
    @classmethod
    def for_qwen(cls, model: str = "qwen-turbo", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.QWEN, model=model, **kwargs)
    
    @classmethod
    def for_kimi(cls, model: str = "moonshot-v1-8k", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.KIMI, model=model, **kwargs)
    
    @classmethod
    def for_minimax(cls, model: str = "abab6-chat", **kwargs) -> LLMConfig:
        return cls(provider=ProviderType.MINIMAX, model=model, **kwargs)


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    provider: ProviderType
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    raw_response: Any = None
    success: bool = True
    error: Optional[str] = None
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)
    
    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)
    
    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)


class LLMProvider(ABC):
    """LLM提供商基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本响应
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            **kwargs: 额外参数
            
        Returns:
            LLM响应
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ):
        """
        流式生成文本响应
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            history: 对话历史
            
        Yields:
            文本片段
        """
        pass
    
    def _build_messages(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None
    ) -> list[dict[str, str]]:
        """构建消息列表"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _merge_kwargs(self, **kwargs) -> dict[str, Any]:
        """合并配置参数和额外参数"""
        merged = {
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }
        merged.update(self.config.extra_params)
        merged.update(kwargs)
        return merged
    
    @property
    def provider_type(self) -> ProviderType:
        return self.config.provider
    
    @property
    def model(self) -> str:
        return self.config.model