"""
Collectigent 可视化调试工具模块

提供实时可视化调试功能，包括：
- CLI可视化：实时显示Agent沟通过程
- 流程可视化：显示消息流转图
- 指标仪表盘：显示涌现指标变化
"""

from typing import Optional, Callable, Any
from dataclasses import dataclass

from .cli import CLIVisualizer, CLIConfig
from .flow import FlowVisualizer
from .dashboard import MetricsDashboard


@dataclass
class DebugConfig:
    """调试配置"""
    enable_cli: bool = True  # 启用CLI可视化
    enable_flow: bool = False  # 启用流程可视化
    enable_dashboard: bool = False  # 启用指标仪表盘
    show_messages: bool = True  # 显示消息内容
    show_metrics: bool = True  # 显示指标
    max_content_length: int = 200  # 最大内容长度
    theme: str = "default"  # 主题样式


class Debugger:
    """
    可视化调试器
    
    提供统一的调试接口，支持多种可视化方式
    """
    
    def __init__(self, config: Optional[DebugConfig] = None):
        self.config = config or DebugConfig()
        self._cli: Optional[CLIVisualizer] = None
        self._flow: Optional[FlowVisualizer] = None
        self._dashboard: Optional[MetricsDashboard] = None
        self._init_components()
    
    def _init_components(self):
        """初始化可视化组件"""
        if self.config.enable_cli:
            cli_config = CLIConfig(
                show_messages=self.config.show_messages,
                max_content_length=self.config.max_content_length,
                theme=self.config.theme,
            )
            self._cli = CLIVisualizer(cli_config)
        
        if self.config.enable_flow:
            self._flow = FlowVisualizer()
        
        if self.config.enable_dashboard:
            self._dashboard = MetricsDashboard()
    
    def on_event(self, event: str, data: dict):
        """处理调试事件"""
        if self._cli:
            self._cli.handle_event(event, data)
        
        if self._flow and event == "agent_response":
            self._flow.add_message(data)
        
        if self._dashboard and event in ["agent_response", "task_complete"]:
            self._dashboard.update(data)
    
    def on_agent_thinking(self, agent_id: str, role: str, step: int):
        """Agent开始思考"""
        if self._cli:
            self._cli.show_thinking(agent_id, role, step)
    
    def on_agent_response(self, agent_id: str, role: str, content: str, content_type: str):
        """Agent响应"""
        if self._cli:
            self._cli.show_response(agent_id, role, content, content_type)
    
    def on_metrics_update(self, metrics: dict):
        """更新指标"""
        if self._dashboard:
            self._dashboard.update_metrics(metrics)
    
    def start(self, task: str):
        """开始调试会话"""
        if self._cli:
            self._cli.start_session(task)
        
        if self._flow:
            self._flow.start_session()
        
        if self._dashboard:
            self._dashboard.start_session()
    
    def end(self, result: str, metrics: dict):
        """结束调试会话"""
        if self._cli:
            self._cli.end_session(result)
        
        if self._flow:
            self._flow.end_session()
        
        if self._dashboard:
            self._dashboard.end_session(metrics)
    
    def print_summary(self):
        """打印调试摘要"""
        if self._cli:
            self._cli.print_summary()
        
        if self._flow:
            self._flow.print_flow_diagram()
        
        if self._dashboard:
            self._dashboard.print_metrics()


def create_debugger(
    enable_cli: bool = True,
    enable_flow: bool = False,
    enable_dashboard: bool = False,
    **kwargs
) -> Debugger:
    """创建调试器的便捷函数"""
    config = DebugConfig(
        enable_cli=enable_cli,
        enable_flow=enable_flow,
        enable_dashboard=enable_dashboard,
        **kwargs
    )
    return Debugger(config)


# 便捷函数：创建进度回调
def create_progress_callback(
    show_messages: bool = True,
    max_content_length: int = 200,
) -> Callable[[str, dict], None]:
    """创建进度回调函数，用于集成到Swarm"""
    cli = CLIVisualizer(CLIConfig(
        show_messages=show_messages,
        max_content_length=max_content_length,
    ))
    return cli.handle_event


__all__ = [
    "Debugger",
    "DebugConfig",
    "CLIVisualizer",
    "CLIConfig",
    "FlowVisualizer",
    "MetricsDashboard",
    "create_debugger",
    "create_progress_callback",
]
