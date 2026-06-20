"""智谱AI (GLM) 提供商实现"""

from __future__ import annotations

import time
import os
from typing import Optional, Any

from .base import LLMProvider, LLMConfig, LLMResponse, ProviderType


class GLMProvider(LLMProvider):
    """智谱AI GLM API提供商"""
    
    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化智谱客户端"""
        try:
            from zhipuai import ZhipuAI
        except ImportError:
            raise ImportError(
                "请安装zhipuai包: pip install zhipuai"
            )
        
        api_key = self.config.api_key or os.environ.get("ZHIPU_API_KEY")
        if not api_key:
            raise ValueError("请提供智谱API Key或设置ZHIPU_API_KEY环境变量")
        
        self._client = ZhipuAI(
            api_key=api_key,
            base_url=self.config.base_url or self.DEFAULT_BASE_URL,
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
        
        # 智谱API调用
        response = self._client.chat.completions.create(
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
            provider=ProviderType.GLM,
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
        
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            top_p=params["top_p"],
            stream=True,
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content