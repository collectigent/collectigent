"""
消息流程可视化

以ASCII图形方式显示Agent之间的消息流转
"""

from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class FlowNode:
    """流程节点"""
    role: str
    name: str
    step: int
    content_preview: str
    content_type: str


class FlowVisualizer:
    """
    流程可视化器
    
    以ASCII图形方式显示Agent之间的消息流转
    """
    
    # Agent图标
    ROLE_ICONS = {
        "leader": "👑",
        "researcher": "📚",
        "critic": "🔍",
        "innovator": "💡",
        "synthesizer": "🔮",
        "executor": "⚙️",
    }
    
    # Agent名称映射
    ROLE_NAMES = {
        "leader": "领导者",
        "researcher": "研究者",
        "critic": "批判者",
        "innovator": "创新者",
        "synthesizer": "综合者",
        "executor": "执行者",
    }
    
    def __init__(self):
        self._nodes: list[FlowNode] = []
        self._task: str = ""
        self._result: str = ""
    
    def start_session(self, task: str = ""):
        """开始会话"""
        self._nodes = []
        self._task = task
    
    def end_session(self, result: str = ""):
        """结束会话"""
        self._result = result
    
    def add_message(self, data: dict):
        """添加消息"""
        role = data.get("role", "unknown")
        name = data.get("agent_name", role)
        step = data.get("step", len(self._nodes) + 1)
        content = data.get("content", {})
        content_type = data.get("content_type", "")
        
        # 提取内容预览
        if isinstance(content, dict):
            if content_type == "task_allocation":
                preview = content.get("main_task", "")[:50]
            elif content_type == "research_findings":
                findings = content.get("findings", [])
                preview = str(findings[0])[:50] if findings else ""
            elif content_type == "critique":
                objections = content.get("objections", [])
                preview = str(objections[0])[:50] if objections else ""
            elif content_type == "innovation_ideas":
                ideas = content.get("ideas", [])
                preview = str(ideas[0])[:50] if ideas else ""
            elif content_type == "synthesis":
                preview = content.get("final_synthesis", "")[:50]
            else:
                preview = str(content)[:50]
        else:
            preview = str(content)[:50]
        
        node = FlowNode(
            role=role,
            name=name,
            step=step,
            content_preview=preview.replace("\n", " ").replace("{", "").replace("}", ""),
            content_type=content_type,
        )
        self._nodes.append(node)
    
    def _get_icon(self, role: str) -> str:
        """获取角色图标"""
        return self.ROLE_ICONS.get(role.lower(), "🎭")
    
    def _get_role_name(self, role: str) -> str:
        """获取角色中文名"""
        return self.ROLE_NAMES.get(role.lower(), role)
    
    def _draw_horizontal_flow(self) -> str:
        """绘制水平流程图"""
        lines = []
        
        # 标题
        lines.append("\n┌─────────────────────────────────────────────────────────────┐")
        lines.append("│                    消息流转流程图                            │")
        lines.append("└─────────────────────────────────────────────────────────────┘")
        
        if not self._nodes:
            lines.append("\n  (暂无消息)")
            return "\n".join(lines)
        
        # 绘制节点
        for i, node in enumerate(self._nodes):
            icon = self._get_icon(node.role)
            role_name = self._get_role_name(node.role)
            
            # 节点框
            lines.append(f"\n  {icon} 步骤 {node.step}: {role_name} ({node.name})")
            lines.append("  " + "─" * 55)
            
            # 内容预览
            content = node.content_preview[:50]
            lines.append(f"  │ {content}...")
            
            # 连接线
            if i < len(self._nodes) - 1:
                lines.append("  │")
                lines.append("  ▼")
        
        return "\n".join(lines)
    
    def _draw_vertical_flow(self) -> str:
        """绘制垂直流程图"""
        lines = []
        
        # 标题
        lines.append("\n╔═══════════════════════════════════════════════════════════════╗")
        lines.append("║                    消息流转流程图                              ║")
        lines.append("╠═══════════════════════════════════════════════════════════════╣")
        
        if not self._nodes:
            lines.append("║  (暂无消息)                                                   ║")
        else:
            for i, node in enumerate(self._nodes):
                icon = self._get_icon(node.role)
                role_name = self._get_role_name(node.role)
                content = node.content_preview[:40].ljust(40)
                
                # 节点
                lines.append(f"║  {icon} [{node.step}] {role_name}                                      ║")
                lines.append(f"║     └─ {content}    ║")
                
                # 连接线
                if i < len(self._nodes) - 1:
                    lines.append("║     │                                                     ║")
                    lines.append("║     ▼                                                     ║")
        
        lines.append("╚═══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)
    
    def _draw_simple_flow(self) -> str:
        """绘制简单流程图"""
        lines = []
        
        lines.append("\n═══════════════════════════════════════════════════════════════")
        lines.append("                     消息流转流程")
        lines.append("═══════════════════════════════════════════════════════════════")
        
        if not self._nodes:
            lines.append("\n  (暂无消息)")
            return "\n".join(lines)
        
        # 绘制节点
        for i, node in enumerate(self._nodes):
            icon = self._get_icon(node.role)
            role_name = self._get_role_name(node.role)
            
            if i == 0:
                lines.append(f"\n  ┌─ 起始")
                lines.append(f"  │")
                lines.append(f"  ├─→ {icon} {role_name}")
            elif i == len(self._nodes) - 1:
                lines.append(f"  │")
                lines.append(f"  └─→ {icon} {role_name} ─→ 结束")
            else:
                lines.append(f"  │")
                lines.append(f"  ├─→ {icon} {role_name}")
        
        # 绘制摘要
        lines.append("\n─────────────────────────────────────────────────────────────────")
        lines.append("  节点摘要:")
        
        for node in self._nodes:
            icon = self._get_icon(node.role)
            role_name = self._get_role_name(node.role)
            content = node.content_preview[:35]
            lines.append(f"  {icon} {role_name}: {content}...")
        
        return "\n".join(lines)
    
    def print_flow_diagram(self, style: str = "simple"):
        """
        打印流程图
        
        Args:
            style: 样式选择
                - "horizontal": 水平流程图
                - "vertical": 垂直流程图
                - "simple": 简单流程图
        """
        if style == "horizontal":
            print(self._draw_horizontal_flow())
        elif style == "vertical":
            print(self._draw_vertical_flow())
        else:
            print(self._draw_simple_flow())
    
    def get_flow_summary(self) -> dict:
        """获取流程摘要"""
        return {
            "total_nodes": len(self._nodes),
            "roles_involved": list(set(node.role for node in self._nodes)),
            "first_role": self._nodes[0].role if self._nodes else None,
            "last_role": self._nodes[-1].role if self._nodes else None,
        }


def create_flow_visualizer() -> FlowVisualizer:
    """创建流程可视化器"""
    return FlowVisualizer()


__all__ = [
    "FlowVisualizer",
    "FlowNode",
    "create_flow_visualizer",
]
