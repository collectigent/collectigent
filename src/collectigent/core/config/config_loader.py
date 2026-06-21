"""配置文件加载器"""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

from ..llm import ProviderType


@dataclass
class ModelRoleConfig:
    """单个角色的模型配置"""
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048


class ConfigLoader:
    """配置加载器"""
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "model_config.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为 config/model_config.yaml
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self.DEFAULT_CONFIG_PATH
        
        self._config: Dict[str, Any] = {}
        self._loaded = False
    
    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self._loaded:
            return self._config
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}
        
        self._loaded = True
        return self._config
    
    def get_api_keys(self) -> Dict[str, str]:
        """获取所有API Key"""
        config = self.load()
        return config.get('api_keys', {})
    
    def get_api_key(self, provider: ProviderType) -> str:
        """
        获取指定提供商的API Key
        
        优先级：环境变量 > 配置文件
        
        Args:
            provider: 提供商类型
            
        Returns:
            API Key
        """
        # 环境变量映射
        env_vars = {
            ProviderType.OPENAI: "OPENAI_API_KEY",
            ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
            ProviderType.GLM: "ZHIPU_API_KEY",
            ProviderType.DEEPSEEK: "DEEPSEEK_API_KEY",
            ProviderType.DOUBAO: "DOUBAO_API_KEY",
            ProviderType.QWEN: "QWEN_API_KEY",
            ProviderType.KIMI: "MOONSHOT_API_KEY",
            ProviderType.MINIMAX: "MINIMAX_API_KEY",
        }
        
        # 先检查环境变量
        env_var = env_vars.get(provider)
        if env_var:
            api_key = os.environ.get(env_var)
            if api_key:
                return api_key
        
        # 再从配置文件读取
        api_keys = self.get_api_keys()
        key_map = {
            ProviderType.OPENAI: "openai",
            ProviderType.ANTHROPIC: "anthropic",
            ProviderType.GLM: "glm",
            ProviderType.DEEPSEEK: "deepseek",
            ProviderType.DOUBAO: "doubao",
            ProviderType.QWEN: "qwen",
            ProviderType.KIMI: "kimi",
            ProviderType.MINIMAX: "minimax",
        }
        
        key_name = key_map.get(provider)
        if key_name and key_name in api_keys:
            return api_keys.get(key_name, "")
        
        return ""
    
    def get_active_preset(self) -> str:
        """获取当前激活的预设配置"""
        config = self.load()
        return config.get('active_preset', 'balanced')
    
    def get_preset_config(self, preset_name: Optional[str] = None) -> Dict[str, ModelRoleConfig]:
        """
        获取预设配置
        
        Args:
            preset_name: 预设名称，默认为当前激活的预设
            
        Returns:
            角色配置字典
        """
        config = self.load()
        
        if preset_name is None:
            preset_name = self.get_active_preset()
        
        presets = config.get('model_presets', {})
        preset = presets.get(preset_name, presets.get('balanced', {}))
        
        result = {}
        for role, role_config in preset.items():
            result[role] = ModelRoleConfig(
                provider=role_config.get('provider', 'glm'),
                model=role_config.get('model', 'glm-4'),
                temperature=role_config.get('temperature', 0.7),
                max_tokens=role_config.get('max_tokens', 2048),
            )
        
        return result
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        config = self.load()
        return config.get('logging', {
            'level': 'INFO',
            'verbose': False,
            'show_process': False,
        })
    
    def create_role_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        创建角色配置（包含API Key）
        
        Returns:
            角色配置字典，包含 provider 类型转换
        """
        preset = self.get_preset_config()
        
        # Provider 字符串到枚举的映射
        provider_map = {
            'openai': ProviderType.OPENAI,
            'anthropic': ProviderType.ANTHROPIC,
            'glm': ProviderType.GLM,
            'deepseek': ProviderType.DEEPSEEK,
            'doubao': ProviderType.DOUBAO,
            'qwen': ProviderType.QWEN,
            'kimi': ProviderType.KIMI,
            'minimax': ProviderType.MINIMAX,
        }
        
        result = {}
        for role, role_config in preset.items():
            provider_str = role_config.provider
            provider_enum = provider_map.get(provider_str, ProviderType.GLM)
            
            result[role] = {
                'provider': provider_enum,
                'model': role_config.model,
                'temperature': role_config.temperature,
                'max_tokens': role_config.max_tokens,
                'api_key': self.get_api_key(provider_enum),
            }
        
        return result


# 全局配置加载器实例
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_path: Optional[str] = None) -> ConfigLoader:
    """获取配置加载器实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)
    return _config_loader


def load_from_config() -> Dict[str, Dict[str, Any]]:
    """
    从配置文件加载所有角色配置
    
    Returns:
        角色配置字典
    """
    loader = get_config_loader()
    return loader.create_role_configs()
