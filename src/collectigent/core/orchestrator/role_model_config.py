"""角色模型配置 - 为不同角色设置不同的LLM提供商"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum

from ..llm import LLMProvider, LLMConfig, ProviderType, LLMFactory


class Role(Enum):
    """智能体角色"""
    LEADER = "leader"           # 领导者
    RESEARCHER = "researcher"   # 研究者
    CRITIC = "critic"          # 批判者
    INNOVATOR = "innovator"    # 创新者
    SYNTHESIZER = "synthesizer" # 综合者
    EXECUTOR = "executor"      # 执行者


@dataclass
class RoleModelConfig:
    """单个角色的模型配置"""
    provider: ProviderType
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    description: str = ""
    api_key: str = ""  # 新增API Key字段
    
    def to_llm_config(self) -> LLMConfig:
        """转换为LLMConfig"""
        return LLMConfig(
            provider=self.provider,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,  # 传递API Key
        )
    
    def create_provider(self) -> LLMProvider:
        """创建LLM提供商实例"""
        return LLMFactory.create(self.to_llm_config())


@dataclass
class MultiModelConfig:
    """多模型配置 - 管理所有角色的模型设置"""
    
    # 默认配置：所有角色使用同一模型
    default_provider: ProviderType = ProviderType.GLM
    default_model: str = "glm-4"
    
    # 各角色的具体配置
    role_configs: Dict[Role, RoleModelConfig] = field(default_factory=dict)
    
    # 默认角色配置模板
    DEFAULT_CONFIGS: Dict[Role, RoleModelConfig] = field(default_factory=lambda: {
        Role.LEADER: RoleModelConfig(
            provider=ProviderType.QWEN,
            model="qwen-turbo",
            temperature=0.7,
            description="领导者 - 负责任务分配和协调，需要较强的推理能力",
        ),
        Role.RESEARCHER: RoleModelConfig(
            provider=ProviderType.GLM,
            model="glm-4",
            temperature=0.6,
            description="研究者 - 负责信息收集和分析，需要较强的知识储备",
        ),
        Role.CRITIC: RoleModelConfig(
            provider=ProviderType.DEEPSEEK,
            model="deepseek-chat",
            temperature=0.5,
            description="批判者 - 负责发现问题和高风险，需要较强的逻辑思维",
        ),
        Role.INNOVATOR: RoleModelConfig(
            provider=ProviderType.DOUBAO,
            model="doubao-pro-32k",
            temperature=0.9,
            description="创新者 - 负责提出创意和解决方案，需要较强的创新能力",
        ),
        Role.SYNTHESIZER: RoleModelConfig(
            provider=ProviderType.KIMI,
            model="moonshot-v1-32k",
            temperature=0.6,
            description="综合者 - 负责整合观点形成结论，需要较强的综合能力",
        ),
        Role.EXECUTOR: RoleModelConfig(
            provider=ProviderType.GLM,
            model="glm-4",
            temperature=0.5,
            description="执行者 - 负责评估和最终决策，需要较强的判断能力",
        ),
    })
    
    def __post_init__(self):
        """初始化默认配置"""
        if not self.role_configs:
            self.role_configs = self.DEFAULT_CONFIGS.copy()
    
    def get_config(self, role: Role) -> RoleModelConfig:
        """获取指定角色的模型配置"""
        return self.role_configs.get(role, RoleModelConfig(
            provider=self.default_provider,
            model=self.default_model,
        ))
    
    def get_provider(self, role: Role) -> LLMProvider:
        """获取指定角色的LLM提供商"""
        config = self.get_config(role)
        return config.create_provider()
    
    def set_role_config(
        self,
        role: Role,
        provider: ProviderType,
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        api_key: str = "",  # 新增API Key参数
    ) -> None:
        """设置指定角色的模型配置"""
        self.role_configs[role] = RoleModelConfig(
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,  # 传递API Key
        )
    
    def apply_preset(self, preset_name: str) -> None:
        """应用预设配置"""
        presets = {
            "balanced": self._balanced_preset(),
            "creative": self._creative_preset(),
            "critical": self._critical_preset(),
            "fast": self._fast_preset(),
            "quality": self._quality_preset(),
        }
        
        if preset_name in presets:
            self.role_configs = presets[preset_name]
        else:
            raise ValueError(f"未知的预设: {preset_name}。可用预设: {list(presets.keys())}")
    
    def _balanced_preset(self) -> Dict[Role, RoleModelConfig]:
        """平衡预设 - 各角色使用不同模型，分担成本"""
        return {
            Role.LEADER: RoleModelConfig(
                provider=ProviderType.QWEN, model="qwen-turbo",
                temperature=0.7, description="领导者 - 通义千问",
            ),
            Role.RESEARCHER: RoleModelConfig(
                provider=ProviderType.GLM, model="glm-4",
                temperature=0.6, description="研究者 - 智谱GLM",
            ),
            Role.CRITIC: RoleModelConfig(
                provider=ProviderType.DEEPSEEK, model="deepseek-chat",
                temperature=0.5, description="批判者 - DeepSeek",
            ),
            Role.INNOVATOR: RoleModelConfig(
                provider=ProviderType.DOUBAO, model="doubao-pro-32k",
                temperature=0.9, description="创新者 - 豆包",
            ),
            Role.SYNTHESIZER: RoleModelConfig(
                provider=ProviderType.KIMI, model="moonshot-v1-32k",
                temperature=0.6, description="综合者 - KIMI",
            ),
            Role.EXECUTOR: RoleModelConfig(
                provider=ProviderType.GLM, model="glm-4",
                temperature=0.5, description="执行者 - 智谱GLM",
            ),
        }
    
    def _creative_preset(self) -> Dict[Role, RoleModelConfig]:
        """创意预设 - 创新者使用更强的创意模型"""
        return {
            Role.LEADER: RoleModelConfig(provider=ProviderType.QWEN, model="qwen-plus", temperature=0.7),
            Role.RESEARCHER: RoleModelConfig(provider=ProviderType.GLM, model="glm-4", temperature=0.6),
            Role.CRITIC: RoleModelConfig(provider=ProviderType.DEEPSEEK, model="deepseek-chat", temperature=0.5),
            Role.INNOVATOR: RoleModelConfig(provider=ProviderType.KIMI, model="moonshot-v1-128k", temperature=1.0),
            Role.SYNTHESIZER: RoleModelConfig(provider=ProviderType.KIMI, model="moonshot-v1-32k", temperature=0.6),
            Role.EXECUTOR: RoleModelConfig(provider=ProviderType.GLM, model="glm-4", temperature=0.5),
        }
    
    def _critical_preset(self) -> Dict[Role, RoleModelConfig]:
        """批判预设 - 批判者使用更强的逻辑模型"""
        return {
            Role.LEADER: RoleModelConfig(provider=ProviderType.QWEN, model="qwen-turbo", temperature=0.7),
            Role.RESEARCHER: RoleModelConfig(provider=ProviderType.GLM, model="glm-4", temperature=0.6),
            Role.CRITIC: RoleModelConfig(provider=ProviderType.DEEPSEEK, model="deepseek-coder", temperature=0.3),
            Role.INNOVATOR: RoleModelConfig(provider=ProviderType.DOUBAO, model="doubao-pro-32k", temperature=0.9),
            Role.SYNTHESIZER: RoleModelConfig(provider=ProviderType.GLM, model="glm-4", temperature=0.6),
            Role.EXECUTOR: RoleModelConfig(provider=ProviderType.GLM, model="glm-4", temperature=0.5),
        }
    
    def _fast_preset(self) -> Dict[Role, RoleModelConfig]:
        """快速预设 - 使用速度快的小模型"""
        return {
            Role.LEADER: RoleModelConfig(provider=ProviderType.QWEN, model="qwen-turbo", temperature=0.7),
            Role.RESEARCHER: RoleModelConfig(provider=ProviderType.GLM, model="glm-4-airx", temperature=0.6),
            Role.CRITIC: RoleModelConfig(provider=ProviderType.DEEPSEEK, model="deepseek-chat", temperature=0.5),
            Role.INNOVATOR: RoleModelConfig(provider=ProviderType.DOUBAO, model="doubao-lite-32k", temperature=0.9),
            Role.SYNTHESIZER: RoleModelConfig(provider=ProviderType.KIMI, model="moonshot-v1-8k", temperature=0.6),
            Role.EXECUTOR: RoleModelConfig(provider=ProviderType.GLM, model="glm-4-air", temperature=0.5),
        }
    
    def _quality_preset(self) -> Dict[Role, RoleModelConfig]:
        """质量预设 - 使用高质量大模型"""
        return {
            Role.LEADER: RoleModelConfig(provider=ProviderType.QWEN, model="qwen-plus", temperature=0.7),
            Role.RESEARCHER: RoleModelConfig(provider=ProviderType.GLM, model="glm-4-plus", temperature=0.6),
            Role.CRITIC: RoleModelConfig(provider=ProviderType.DEEPSEEK, model="deepseek-chat", temperature=0.4),
            Role.INNOVATOR: RoleModelConfig(provider=ProviderType.KIMI, model="moonshot-v1-128k", temperature=1.0),
            Role.SYNTHESIZER: RoleModelConfig(provider=ProviderType.KIMI, model="moonshot-v1-128k", temperature=0.5),
            Role.EXECUTOR: RoleModelConfig(provider=ProviderType.GLM, model="glm-4-plus", temperature=0.4),
        }
    
    def summary(self) -> str:
        """生成配置摘要"""
        lines = ["角色模型配置摘要:", "=" * 50]
        for role in Role:
            config = self.get_config(role)
            lines.append(f"  {role.value:12} | {config.provider.value:10} | {config.model:20} | T={config.temperature}")
        return "\n".join(lines)


# 便捷函数
def create_default_config() -> MultiModelConfig:
    """创建默认配置"""
    return MultiModelConfig()


def create_config_from_env() -> MultiModelConfig:
    """从环境变量创建配置"""
    import os
    
    config = MultiModelConfig()
    
    # 检查环境变量
    env_mappings = {
        "QWEN_API_KEY": (Role.LEADER, ProviderType.QWEN),
        "GLM_API_KEY": (Role.RESEARCHER, ProviderType.GLM),
        "DEEPSEEK_API_KEY": (Role.CRITIC, ProviderType.DEEPSEEK),
        "DOUBAO_API_KEY": (Role.INNOVATOR, ProviderType.DOUBAO),
        "KIMI_API_KEY": (Role.SYNTHESIZER, ProviderType.KIMI),
    }
    
    for env_var, (role, provider) in env_mappings.items():
        api_key = os.environ.get(env_var)
        if api_key:
            config.set_role_config(role, provider)
    
    return config


def create_config_from_file(config_path: str = None) -> MultiModelConfig:
    """
    从配置文件创建配置
    
    Args:
        config_path: 配置文件路径，默认为 config/model_config.yaml
        
    Returns:
        MultiModelConfig 实例
    """
    from ..config import get_config_loader
    
    loader = get_config_loader(config_path)
    role_configs = loader.create_role_configs()
    
    config = MultiModelConfig()
    
    # Role 名称映射
    role_map = {
        "leader": Role.LEADER,
        "researcher": Role.RESEARCHER,
        "critic": Role.CRITIC,
        "innovator": Role.INNOVATOR,
        "synthesizer": Role.SYNTHESIZER,
        "executor": Role.EXECUTOR,
    }
    
    for role_name, role_config in role_configs.items():
        role_enum = role_map.get(role_name)
        if role_enum:
            config.set_role_config(
                role_enum,
                provider=role_config['provider'],
                model=role_config['model'],
                temperature=role_config['temperature'],
                max_tokens=role_config.get('max_tokens', 2048),
                api_key=role_config.get('api_key', ""),  # 传递API Key
            )
    
    return config
