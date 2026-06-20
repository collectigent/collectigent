"""LLM工厂类 - 简化提供商创建"""

from __future__ import annotations

from typing import Optional

from .base import LLMProvider, LLMConfig, ProviderType
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .glm import GLMProvider
from .deepseek import DeepSeekProvider
from .doubao import DoubaoProvider


class LLMFactory:
    """LLM提供商工厂"""
    
    _providers: dict[ProviderType, type[LLMProvider]] = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.GLM: GLMProvider,
        ProviderType.DEEPSEEK: DeepSeekProvider,
        ProviderType.DOUBAO: DoubaoProvider,
    }
    
    @classmethod
    def create(cls, config: LLMConfig) -> LLMProvider:
        """
        根据配置创建LLM提供商
        
        Args:
            config: LLM配置
            
        Returns:
            LLM提供商实例
        """
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"不支持的提供商: {config.provider}")
        
        return provider_class(config)
    
    @classmethod
    def create_openai(
        cls,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        **kwargs
    ) -> OpenAIProvider:
        """创建OpenAI提供商"""
        config = LLMConfig.for_openai(model=model, api_key=api_key, **kwargs)
        return cls.create(config)
    
    @classmethod
    def create_anthropic(
        cls,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        **kwargs
    ) -> AnthropicProvider:
        """创建Anthropic提供商"""
        config = LLMConfig.for_anthropic(model=model, api_key=api_key, **kwargs)
        return cls.create(config)
    
    @classmethod
    def create_glm(
        cls,
        model: str = "glm-4",
        api_key: Optional[str] = None,
        **kwargs
    ) -> GLMProvider:
        """创建智谱AI提供商"""
        config = LLMConfig.for_glm(model=model, api_key=api_key, **kwargs)
        return cls.create(config)
    
    @classmethod
    def create_deepseek(
        cls,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        **kwargs
    ) -> DeepSeekProvider:
        """创建DeepSeek提供商"""
        config = LLMConfig.for_deepseek(model=model, api_key=api_key, **kwargs)
        return cls.create(config)
    
    @classmethod
    def create_doubao(
        cls,
        model: str = "doubao-pro-32k",
        api_key: Optional[str] = None,
        **kwargs
    ) -> DoubaoProvider:
        """创建字节跳动Doubao提供商"""
        config = LLMConfig.for_doubao(model=model, api_key=api_key, **kwargs)
        return cls.create(config)
    
    @classmethod
    def register_provider(cls, provider_type: ProviderType, provider_class: type[LLMProvider]) -> None:
        """注册自定义提供商"""
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def list_providers(cls) -> list[ProviderType]:
        """列出所有支持的提供商"""
        return list(cls._providers.keys())