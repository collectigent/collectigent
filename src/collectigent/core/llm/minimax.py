"""MiniMax LLM 提供者"""

import json
from typing import Dict, List, Optional
from .base import LLMProvider, LLMConfig, LLMResponse


class MiniMaxProvider(LLMProvider):
    """MiniMax 模型提供者"""
    
    PROVIDER_NAME = "minimax"
    BASE_URL = "https://api.minimax.chat/v1"
    
    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                provider=ProviderType.MINIMAX,
                model="abab6-chat",
                api_key="",  # 需要从环境变量 MINIMAX_API_KEY 获取
            )
        super().__init__(config)
    
    @property
    def provider_name(self) -> str:
        return self.PROVIDER_NAME
    
    @property
    def default_model(self) -> str:
        return "abab6-chat"
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "abab6-chat",
            "abab5.5-chat",
            "abab5-chat",
        ]
    
    def _prepare_messages(self, messages: List[Dict]) -> List[Dict]:
        """准备MiniMax格式的消息"""
        mm_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "assistant":
                role = "assistant"
            elif role == "system":
                role = "system"
            else:
                role = "user"
            
            mm_messages.append({
                "role": role,
                "content": msg.get("content", ""),
            })
        return mm_messages
    
    async def generate(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """生成回复"""
        import aiohttp
        
        # 获取API Key和Group ID
        import os
        api_key = self.config.api_key
        if not api_key:
            api_key = os.environ.get("MINIMAX_API_KEY", "")
            if not api_key:
                return LLMResponse(
                    content="错误: 未设置 MINIMAX_API_KEY 环境变量",
                    success=False,
                    error="Missing API Key",
                )
        
        group_id = os.environ.get("MINIMAX_GROUP_ID", "")
        if not group_id:
            return LLMResponse(
                content="错误: 未设置 MINIMAX_GROUP_ID 环境变量",
                success=False,
                error="Missing Group ID",
            )
        
        # 准备请求
        url = f"{self.BASE_URL}/text/chatcompletion_pro?GroupId={group_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        data = {
            "model": self.config.model or self.default_model,
            "messages": self._prepare_messages(messages),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "choices" in result and len(result["choices"]) > 0:
                            return LLMResponse(
                                content=result["choices"][0]["messages"][-1]["text"],
                                success=True,
                                model=result.get("model", self.config.model),
                                usage={
                                    "prompt_tokens": result.get("usage", {}).get("prompt_tokens", 0),
                                    "completion_tokens": result.get("usage", {}).get("completion_tokens", 0),
                                    "total_tokens": result.get("usage", {}).get("total_tokens", 0),
                                },
                            )
                        else:
                            return LLMResponse(
                                content="",
                                success=False,
                                error="MiniMax返回格式错误",
                            )
                    else:
                        error_text = await response.text()
                        return LLMResponse(
                            content="",
                            success=False,
                            error=f"MiniMax API错误: {response.status} - {error_text}",
                        )
        except Exception as e:
            return LLMResponse(
                content="",
                success=False,
                error=f"MiniMax请求失败: {str(e)}",
            )
