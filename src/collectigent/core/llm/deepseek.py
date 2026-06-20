"""DeepSeek提供商实现"""

from __future__ import annotations

import time
import os
from typing import Optional, Any

from .base import LLMProvider, LLMConfig, LLMResponse, ProviderType


class DeepSeekProvider(LLMProvider):
    """DeepSeek API提供商"""
    
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化DeepSeek客户端"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "请安装openai包: pip install openai"
            )
        
        api_key = self.config.api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请提供DeepSeek API Key或设置DEEPSEEK_API_KEY环境变量")
        
        base_url = self.config.base_url or self.DEFAULT_BASE_URL
        
        # DeepSeek兼容OpenAI API格式
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
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
        messages = self._build_messages(prompt, system_prompt, history)
        params = self._merge_kwargs(**kwargs)
        
        start_time = time.time()
        
        response = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            top_p=params["top_p"],
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            provider=ProviderType.DEEPSEEK,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
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
        messages = self._build_messages(prompt, system_prompt, history)
        params = self._merge_kwargs(**kwargs)
        
        stream = await self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            top_p=params["top_p"],
            stream=True,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content