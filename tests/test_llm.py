"""LLM集成测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from collectigent.core.llm import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMFactory,
    ProviderType,
)
from collectigent.core.llm.base import LLMProvider as BaseLLMProvider
from collectigent.core.agents import Agent, Role, Leader


class TestLLMConfig:
    """测试LLM配置"""
    
    def test_config_creation(self):
        """测试配置创建"""
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o",
            api_key="test-key",
        )
        assert config.provider == ProviderType.OPENAI
        assert config.model == "gpt-4o"
        assert config.api_key == "test-key"
        assert config.temperature == 0.7
    
    def test_config_default_model(self):
        """测试默认模型"""
        config = LLMConfig(provider=ProviderType.OPENAI)
        assert config.model == "gpt-4o"
        
        config = LLMConfig(provider=ProviderType.ANTHROPIC)
        assert config.model == "claude-3-5-sonnet-20241022"
        
        config = LLMConfig(provider=ProviderType.GLM)
        assert config.model == "glm-4"
        
        config = LLMConfig(provider=ProviderType.DEEPSEEK)
        assert config.model == "deepseek-chat"
    
    def test_config_factory_methods(self):
        """测试工厂方法"""
        config = LLMConfig.for_openai(model="gpt-4-turbo", api_key="key1")
        assert config.provider == ProviderType.OPENAI
        assert config.model == "gpt-4-turbo"
        
        config = LLMConfig.for_anthropic(api_key="key2")
        assert config.provider == ProviderType.ANTHROPIC
        
        config = LLMConfig.for_deepseek(api_key="key3")
        assert config.provider == ProviderType.DEEPSEEK


class TestLLMResponse:
    """测试LLM响应"""
    
    def test_response_creation(self):
        """测试响应创建"""
        response = LLMResponse(
            content="Hello, world!",
            model="gpt-4o",
            provider=ProviderType.OPENAI,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert response.content == "Hello, world!"
        assert response.total_tokens == 15
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5


class TestLLMFactory:
    """测试LLM工厂"""
    
    def test_list_providers(self):
        """测试列出提供商"""
        providers = LLMFactory.list_providers()
        assert ProviderType.OPENAI in providers
        assert ProviderType.ANTHROPIC in providers
        assert ProviderType.GLM in providers
        assert ProviderType.DEEPSEEK in providers
        assert ProviderType.DOUBAO in providers
    
    def test_create_openai_provider(self):
        """测试创建OpenAI提供商"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = LLMFactory.create_openai(model="gpt-4o")
            assert provider.provider_type == ProviderType.OPENAI
            assert provider.model == "gpt-4o"
    
    def test_create_anthropic_provider(self):
        """测试创建Anthropic提供商"""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = LLMFactory.create_anthropic(model="claude-3-opus")
            assert provider.provider_type == ProviderType.ANTHROPIC
    
    def test_create_deepseek_provider(self):
        """测试创建DeepSeek提供商"""
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}):
            provider = LLMFactory.create_deepseek()
            assert provider.provider_type == ProviderType.DEEPSEEK


class TestOpenAIProvider:
    """测试OpenAI提供商"""
    
    @pytest.mark.asyncio
    async def test_generate(self):
        """测试生成"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4o"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = LLMFactory.create_openai()
            
            with patch.object(provider._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
                mock_create.return_value = mock_response
                
                response = await provider.generate("Hello")
                
                assert response.content == "Test response"
                assert response.model == "gpt-4o"
                assert response.total_tokens == 15


class TestAgentWithLLM:
    """测试Agent与LLM集成"""
    
    def test_agent_with_llm(self):
        """测试Agent配置LLM"""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            llm = LLMFactory.create_openai()
            agent = Leader(llm=llm)
            
            assert agent.llm is not None
            assert agent.llm.provider_type == ProviderType.OPENAI
    
    def test_agent_without_llm(self):
        """测试Agent未配置LLM"""
        agent = Leader()
        assert agent.llm is None
    
    @pytest.mark.asyncio
    async def test_agent_call_llm_error(self):
        """测试Agent调用LLM错误"""
        agent = Leader()
        
        with pytest.raises(RuntimeError, match="未配置LLM提供商"):
            await agent.call_llm("test prompt")
    
    @pytest.mark.asyncio
    async def test_agent_call_llm_success(self):
        """测试Agent调用LLM成功"""
        mock_response = LLMResponse(
            content="Test response",
            model="gpt-4o",
            provider=ProviderType.OPENAI,
            usage={"total_tokens": 10},
        )
        
        mock_llm = MagicMock(spec=BaseLLMProvider)
        mock_llm.generate = AsyncMock(return_value=mock_response)
        
        agent = Leader(llm=mock_llm)
        
        response = await agent.call_llm("Hello")
        assert response == "Test response"
        
        # 验证调用参数
        mock_llm.generate.assert_called_once()
        call_args = mock_llm.generate.call_args
        assert call_args.kwargs["prompt"] == "Hello"
        assert "领导者" in call_args.kwargs["system_prompt"]


class TestProviderType:
    """测试提供商类型"""
    
    def test_provider_type_values(self):
        """测试提供商类型值"""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.GLM.value == "glm"
        assert ProviderType.DEEPSEEK.value == "deepseek"
        assert ProviderType.DOUBAO.value == "doubao"