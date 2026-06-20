"""阿里云通义千问 (Qwen) 提供商实现"""

from __future__ import annotations

import time
import os
from typing import Optional, Any

from .base import LLMProvider, LLMConfig, LLMResponse, ProviderType


class QwenProvider(LLMProvider):
    """阿里云通义千问 API提供商"""
    
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化通义千问客户端"""
        try:
            from dashscope import Generation
        except ImportError:
            raise ImportError(
                "请安装dashscope包: pip install dashscope"
            )
        
        api_key = self.config.api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("请提供DashScope API Key或设置DASHSCOPE_API_KEY环境变量")
        
        # 设置API Key
        import dashscope
        dashscope.api_key = api_key
        
        self._client = Generation
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本响应"""
        params = self._merge_kwargs(**kwargs)
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})
        
        start_time = time.time()
        
        # 调用通义千问API
        response = self._client.call(
            model=self.config.model,
            messages=messages,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            top_p=params["top_p"],
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # 解析响应
        if response.status_code == 200:
            result = response.output
            content = result.choices[0].message.content
            
            return LLMResponse(
                content=content,
                model=self.config.model,
                provider=ProviderType.QWEN,
                usage={
                    "prompt_tokens": result.usage.input_tokens,
                    "completion_tokens": result.usage.output_tokens,
                    "total_tokens": result.usage.input_tokens + result.usage.output_tokens,
                },
                finish_reason=result.choices[0].finish_reason,
                latency_ms=latency_ms,
                raw_response=response,
            )
        else:
            raise RuntimeError(f"Qwen API调用失败: {response.message}")
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ):
        """流式生成文本响应"""
        params = self._merge_kwargs(**kwargs)
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})
        
        # 流式调用
        responses = self._client.call(
            model=self.config.model,
            messages=messages,
            temperature=params["temperature"],
            max_tokens=params["max_tokens"],
            top_p=params["top_p"],
            stream=True,
        )
        
        for response in responses:
            if response.status_code == 200:
                result = response.output
                if result.choices:
                    content = result.choices[0].message.content
                    if content:
                        yield content