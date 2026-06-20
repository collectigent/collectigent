"""字节跳动 (Doubao) 提供商实现"""

from __future__ import annotations

import time
import os
import json
from typing import Optional, Any

from .base import LLMProvider, LLMConfig, LLMResponse, ProviderType


class DoubaoProvider(LLMProvider):
    """字节跳动 Doubao API提供商"""
    
    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._init_client()
    
    def _init_client(self):
        """初始化Doubao客户端"""
        try:
            from volcengine.python.Maas import MaasService, MaasException
        except ImportError:
            raise ImportError(
                "请安装volcengine-python包: pip install volcengine-python"
            )
        
        api_key = self.config.api_key or os.environ.get("DOUBAO_API_KEY")
        if not api_key:
            raise ValueError("请提供Doubao API Key或设置DOUBAO_API_KEY环境变量")
        
        # Doubao使用火山引擎SDK
        self._client = MaasService(
            host=self.config.base_url or self.DEFAULT_BASE_URL,
            region="cn-beijing"
        )
        self._client.set_ak(os.environ.get("DOUBAO_ACCESS_KEY", ""))
        self._client.set_sk(os.environ.get("DOUBAO_SECRET_KEY", ""))
        self._api_key = api_key
    
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
        
        # Doubao API调用
        request = {
            "model": self.config.model,
            "messages": messages,
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "top_p": params["top_p"],
        }
        
        try:
            response = self._client.chat(request)
            
            latency_ms = (time.time() - start_time) * 1000
            
            return LLMResponse(
                content=response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                model=self.config.model,
                provider=ProviderType.DOUBAO,
                usage=response.get("usage", {}),
                finish_reason=response.get("choices", [{}])[0].get("finish_reason", "stop"),
                latency_ms=latency_ms,
                raw_response=response,
            )
        except Exception as e:
            raise RuntimeError(f"Doubao API调用失败: {e}")
    
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
        
        request = {
            "model": self.config.model,
            "messages": messages,
            "temperature": params["temperature"],
            "max_tokens": params["max_tokens"],
            "top_p": params["top_p"],
            "stream": True,
        }
        
        try:
            for chunk in self._client.stream_chat(request):
                if chunk:
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        yield content
        except Exception as e:
            raise RuntimeError(f"Doubao流式API调用失败: {e}")