"""KIMI (Moonshot) LLM 提供者"""

import json
from typing import Dict, List, Optional
from .base import LLMProvider, LLMConfig, LLMResponse, ProviderType


class KIMIProvider(LLMProvider):
    """KIMI (Moonshot) 模型提供者"""
    
    PROVIDER_NAME = "kimi"
    BASE_URL = "https://api.moonshot.cn/v1"
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                provider=ProviderType.KIMI,
                model="moonshot-v1-8k",
                api_key="",  # 需要从环境变量 MOONSHOT_API_KEY 获取
            )
        super().__init__(config)
    
    @property
    def provider_name(self) -> str:
        return self.PROVIDER_NAME
    
    @property
    def default_model(self) -> str:
        return "moonshot-v1-8k"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
        ]
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ) -> LLMResponse:
        """生成文本响应"""
        import aiohttp
        
        # 获取API Key
        api_key = self.config.api_key
        if not api_key:
            import os
            api_key = os.environ.get("MOONSHOT_API_KEY", "")
            if not api_key:
                return LLMResponse(
                    content="错误: 未设置 MOONSHOT_API_KEY 环境变量",
                    model=self.config.model,
                    provider=self.config.provider,
                    success=False,
                    error="Missing API Key",
                )
        
        # 准备请求
        url = f"{self.BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        messages = self._build_messages(prompt, system_prompt, history)
        
        data = {
            "model": self.config.model or self.default_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return LLMResponse(
                            content=result["choices"][0]["message"]["content"],
                            model=result.get("model", self.config.model),
                            provider=self.config.provider,
                            success=True,
                            usage={
                                "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                                "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                                "total_tokens": result.get("usage", {}).get("total_tokens", 0),
                            },
                        )
                    else:
                        error_text = await response.text()
                        return LLMResponse(
                            content="",
                            model=self.config.model,
                            provider=self.config.provider,
                            success=False,
                            error=f"KIMI API错误: {response.status} - {error_text}",
                        )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.config.model,
                provider=self.config.provider,
                success=False,
                error=f"KIMI请求失败: {str(e)}",
            )
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict[str, str]]] = None,
        **kwargs
    ):
        """流式生成文本响应"""
        import aiohttp
        
        # 获取API Key
        api_key = self.config.api_key
        if not api_key:
            import os
            api_key = os.environ.get("MOONSHOT_API_KEY", "")
            if not api_key:
                yield "错误: 未设置 MOONSHOT_API_KEY 环境变量"
                return
        
        # 准备请求
        url = f"{self.BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        messages = self._build_messages(prompt, system_prompt, history)
        
        data = {
            "model": self.config.model or self.default_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        async for chunk in response.content.iter_any():
                            if chunk:
                                try:
                                    lines = chunk.decode("utf-8").strip().split("\n")
                                    for line in lines:
                                        if line.startswith("data: "):
                                            data_str = line[6:]
                                            if data_str == "[DONE]":
                                                return
                                            try:
                                                result = json.loads(data_str)
                                                if "choices" in result and len(result["choices"]) > 0:
                                                    delta = result["choices"][0].get("delta", {})
                                                    content = delta.get("content", "")
                                                    if content:
                                                        yield content
                                            except json.JSONDecodeError:
                                                continue
                                except Exception:
                                    continue
                    else:
                        error_text = await response.text()
                        yield f"KIMI API错误: {response.status} - {error_text}"
        except Exception as e:
            yield f"KIMI请求失败: {str(e)}"
