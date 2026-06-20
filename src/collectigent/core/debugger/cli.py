"""
CLI可视化组件

提供命令行界面的实时可视化功能
"""

from typing import Optional, Any
from dataclasses import dataclass
import sys
import time


@dataclass
class CLIConfig:
    """CLI配置"""
    show_messages: bool = True  # 显示消息内容
    max_content_length: int = 200  # 最大内容长度
    theme: str = "default"  # 主题样式
    show_timestamp: bool = True  # 显示时间戳
    animate: bool = True  # 启用动画效果


# 颜色定义
class Colors:
    """终端颜色"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # 背景色
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    
    # 角色颜色映射
    ROLE_COLORS = {
        "leader": CYAN,
        "researcher": GREEN,
        "critic": RED,
        "innovator": YELLOW,
        "synthesizer": MAGENTA,
        "executor": BLUE,
    }
    
    @classmethod
    def get_role_color(cls, role: str) -> str:
        """获取角色对应的颜色"""
        return cls.ROLE_COLORS.get(role.lower(), cls.WHITE)
    
    @classmethod
    def role(cls, role: str, text: str) -> str:
        """为角色着色"""
        return f"{cls.get_role_color(role)}{text}{cls.RESET}"
    
    @classmethod
    def header(cls, text: str) -> str:
        """标题样式"""
        return f"{cls.BOLD}{cls.CYAN}{text}{cls.RESET}"
    
    @classmethod
    def success(cls, text: str) -> str:
        """成功样式"""
        return f"{cls.GREEN}{text}{cls.RESET}"
    
    @classmethod
    def warning(cls, text: str) -> str:
        """警告样式"""
        return f"{cls.YELLOW}{text}{cls.RESET}"
    
    @classmethod
    def error(cls, text: str) -> str:
        """错误样式"""
        return f"{cls.RED}{text}{cls.RESET}"


class ProgressBar:
    """进度条"""
    
    def __init__(self, total: int = 100, width: int = 40):
        self.total = total
        self.current = 0
        self.width = width
    
    def update(self, current: int):
        """更新进度"""
        self.current = min(current, self.total)
        self.draw()
    
    def draw(self):
        """绘制进度条"""
        filled = int(self.width * self.current / self.total) if self.total > 0 else 0
        bar = "█" * filled + "░" * (self.width - filled)
        percent = int(100 * self.current / self.total) if self.total > 0 else 0
        sys.stdout.write(f"\r[{bar}] {percent}%")
        sys.stdout.flush()
    
    def complete(self):
        """完成进度条"""
        self.current = self.total
        self.draw()
        sys.stdout.write("\n")


class CLIVisualizer:
    """
    CLI可视化器
    
    在命令行中实时显示Agent沟通过程
    """
    
    def __init__(self, config: Optional[CLIConfig] = None):
        self.config = config or CLIConfig()
        self._step = 0
        self._start_time = None
        self._message_count = 0
        self._session_data = []
    
    def _print_divider(self, char: str = "─", width: int = 60):
        """打印分隔线"""
        print(char * width)
    
    def _print_header(self, title: str):
        """打印标题"""
        self._print_divider("═")
        print(Colors.header(f"  {title}"))
        self._print_divider("═")
    
    def _print_role_box(self, role: str, name: str, step: int):
        """打印角色框"""
        color = Colors.get_role_color(role)
        role_display = {
            "leader": "👑 领导者",
            "researcher": "📚 研究者",
            "critic": "🔍 批判者",
            "innovator": "💡 创新者",
            "synthesizer": "🔮 综合者",
            "executor": "⚙️ 执行者",
        }.get(role.lower(), f"🎭 {role}")
        
        print(f"\n{color}{'─' * 60}{Colors.RESET}")
        print(f"{color}│{Colors.RESET} {Colors.BOLD}[步骤 {step}]{Colors.RESET} {color}{role_display} - {name}{Colors.RESET}")
        print(f"{color}{'─' * 60}{Colors.RESET}")
    
    def _format_content(self, content: Any) -> str:
        """格式化内容"""
        if not self.config.show_messages:
            return "[消息已隐藏]"
        
        # 如果是字典，提取关键信息
        if isinstance(content, dict):
            content_type = content.get("type", "unknown")
            
            if content_type == "task_allocation":
                return content.get("main_task", "") or content.get("analysis", "")[:100]
            elif content_type == "research_findings":
                findings = content.get("findings", [])
                if findings:
                    return str(findings[0])[:self.config.max_content_length]
            elif content_type == "critique":
                objections = content.get("objections", [])
                if objections:
                    return str(objections[0])[:self.config.max_content_length]
            elif content_type == "innovation_ideas":
                ideas = content.get("ideas", [])
                if ideas:
                    return str(ideas[0])[:self.config.max_content_length]
            elif content_type == "synthesis":
                return content.get("final_synthesis", "")[:self.config.max_content_length]
            
            return str(content)[:self.config.max_content_length]
        
        # 字符串内容
        content_str = str(content)
        if len(content_str) > self.config.max_content_length:
            content_str = content_str[:self.config.max_content_length] + "..."
        
        return content_str.replace("\n", " ").replace("{", "").replace("}", "")
    
    def handle_event(self, event: str, data: dict):
        """处理调试事件"""
        if event == "task_start":
            self.start_session(data.get("task", ""))
        elif event == "agent_thinking":
            self.show_thinking(
                agent_id=data.get("role", ""),
                role=data.get("role", ""),
                step=data.get("step", 0)
            )
        elif event == "agent_response":
            self.show_response(
                agent_id=data.get("role", ""),
                role=data.get("role", ""),
                content=data.get("content", {}),
                content_type=data.get("content_type", "")
            )
        elif event == "task_complete":
            self.end_session(data.get("result", ""))
    
    def start_session(self, task: str):
        """开始会话"""
        self._start_time = time.time()
        self._step = 0
        self._message_count = 0
        
        print("\n")
        self._print_header("群体智能调试会话")
        print(f"📌 任务: {task}\n")
        print("⏳ 等待Agent响应...")
    
    def show_thinking(self, agent_id: str, role: str, step: int):
        """显示Agent思考"""
        self._step = step
        self._print_role_box(role, agent_id, step)
        
        # 模拟思考动画
        if self.config.animate:
            print("  💭 思考中", end="", flush=True)
            for _ in range(3):
                time.sleep(0.2)
                print(".", end="", flush=True)
            print(" ✓")
    
    def show_response(self, agent_id: str, role: str, content: Any, content_type: str):
        """显示Agent响应"""
        self._message_count += 1
        
        # 格式化并显示内容
        formatted_content = self._format_content(content)
        
        print(f"\n  📝 响应内容:")
        print(f"  {Colors.CYAN}{'─' * 55}{Colors.RESET}")
        
        # 分行显示内容
        lines = []
        current_line = "  │ "
        words = formatted_content.split()
        
        for word in words:
            if len(current_line) + len(word) < 58:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = "  │ " + word + " "
        lines.append(current_line)
        
        for line in lines:
            print(line)
        
        print(f"  {Colors.CYAN}{'─' * 55}{Colors.RESET}")
        
        # 记录会话数据
        self._session_data.append({
            "step": self._step,
            "role": role,
            "agent_id": agent_id,
            "content_type": content_type,
            "content": formatted_content,
        })
    
    def end_session(self, result: str):
        """结束会话"""
        elapsed = time.time() - self._start_time if self._start_time else 0
        
        print("\n")
        self._print_header("会话结束")
        
        # 显示统计信息
        print(f"\n  📊 统计信息:")
        print(f"  {Colors.YELLOW}  • 总步骤: {self._step}{Colors.RESET}")
        print(f"  {Colors.YELLOW}  • 消息数: {self._message_count}{Colors.RESET}")
        print(f"  {Colors.YELLOW}  • 耗时: {elapsed:.2f}秒{Colors.RESET}")
        
        # 显示最终结果
        if result:
            print(f"\n  📋 最终结果:")
            print(f"  {Colors.GREEN}{'─' * 55}{Colors.RESET}")
            # 分行显示结果
            words = result.split()
            current_line = "  │ "
            for word in words:
                if len(current_line) + len(word) < 55:
                    current_line += word + " "
                else:
                    print(current_line)
                    current_line = "  │ " + word + " "
            print(current_line)
            print(f"  {Colors.GREEN}{'─' * 55}{Colors.RESET}")
    
    def print_summary(self):
        """打印会话摘要"""
        if not self._session_data:
            return
        
        print("\n")
        self._print_header("会话摘要")
        
        for i, msg in enumerate(self._session_data, 1):
            role = msg["role"]
            color = Colors.get_role_color(role)
            print(f"\n  {i}. {color}[{role}]{Colors.RESET}")
            content = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            print(f"     {content}")


def create_simple_visualizer() -> CLIVisualizer:
    """创建简单的可视化器"""
    config = CLIConfig(
        show_messages=True,
        max_content_length=150,
        animate=False,
        show_timestamp=False,
    )
    return CLIVisualizer(config)


__all__ = [
    "CLIVisualizer",
    "CLIConfig",
    "Colors",
    "ProgressBar",
    "create_simple_visualizer",
]
