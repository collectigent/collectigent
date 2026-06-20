"""Anthropic提供商实现"""

from __future__ import annotations

import time
import os
from typing import Optional, Any

from .base import LLMProvider, LLMConfig, LLMResponse, ProviderType


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API提供商"""
    
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化Anthropic客户端"""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "请安装anthropic包: pip install anthropic"
            )
        
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("请提供Anthropic API Key或设置ANTHROPIC_API_KEY环境变量")
        
        self._client = AsyncAnthropic(
            api_key=api_key,
            base_url=self.config.base_url or self.DEFAULT_BASE_URL,
            timeout=self.config.timeout,
        )
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本响应"""
        # Anthropic API的消息格式略有不同
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        
        params = self._merge_kwargs(**kwargs)
        
        start_time = time.time()
        
        response = await self._client.messages.create(
            model=self.config.model,
            max_tokens=params["max_tokens"],
            system=system_prompt or "",
            messages=messages,
            temperature=params["temperature"],
            top_p=params["top_p"],
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Anthropic响应格式
        content = response.content[0].text if response.content else ""
        
        return LLMResponse(
            content=content,
            model=response.model,
            provider=ProviderType.ANTHROPIC,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            latency_ms=latency_ms,
            raw_response=response,
        )
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ):
        """流式生成文本响应"""
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        
        params = self._merge_kwargs(**kwargs)
        
        stream = await self._client.messages.create(
            model=self.config.model,
            max_tokens=params["max_tokens"],
            system=system_prompt or "",
            messages=messages,
            temperature=params["temperature"],
            stream=True,
        )
        
        for event in stream:
            if event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    yield event.delta.text