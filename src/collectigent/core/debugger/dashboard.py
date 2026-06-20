"""
涌现指标仪表盘

实时显示和分析群体智能的涌现指标
"""

from typing import Optional, Any
from dataclasses import dataclass, field
import time


@dataclass
class MetricSnapshot:
    """指标快照"""
    timestamp: float
    step: int
    group_gain: float
    diversity_index: float
    error_correction: float
    confidence: float
    message_count: int


class MetricsDashboard:
    """
    涌现指标仪表盘
    
    实时显示群体智能的涌现指标变化
    """
    
    def __init__(self):
        self._snapshots: list[MetricSnapshot] = []
        self._start_time: Optional[float] = None
        self._current_metrics: dict = {}
    
    def start_session(self):
        """开始会话"""
        self._start_time = time.time()
        self._snapshots = []
        self._current_metrics = {}
    
    def end_session(self, final_metrics: dict = None):
        """结束会话"""
        if final_metrics:
            self._current_metrics = final_metrics
    
    def update(self, data: dict):
        """更新指标"""
        step = data.get("step", len(self._snapshots) + 1)
        
        # 从数据中提取指标
        metrics = data.get("metrics", {})
        if isinstance(metrics, dict):
            group_gain = metrics.get("group_gain", 0)
            diversity = metrics.get("diversity_index", 0)
            error_correction = metrics.get("error_correction_rate", 0)
        else:
            group_gain = 0
            diversity = 0
            error_correction = 0
        
        # 获取当前置信度
        confidence_evolution = metrics.get("confidence_evolution", [])
        confidence = confidence_evolution[-1] if confidence_evolution else 0
        
        # 创建快照
        snapshot = MetricSnapshot(
            timestamp=time.time() - self._start_time if self._start_time else 0,
            step=step,
            group_gain=group_gain,
            diversity_index=diversity,
            error_correction=error_correction,
            confidence=confidence,
            message_count=step,
        )
        self._snapshots.append(snapshot)
        self._current_metrics = {
            "group_gain": group_gain,
            "diversity_index": diversity,
            "error_correction": error_correction,
            "confidence": confidence,
        }
    
    def update_metrics(self, metrics: dict):
        """更新指标（简化版）"""
        self._current_metrics = metrics
        if self._start_time:
            snapshot = MetricSnapshot(
                timestamp=time.time() - self._start_time,
                step=len(self._snapshots) + 1,
                group_gain=metrics.get("group_gain", 0),
                diversity_index=metrics.get("diversity_index", 0),
                error_correction=metrics.get("error_correction_rate", 0),
                confidence=metrics.get("confidence", 0),
                message_count=len(self._snapshots) + 1,
            )
            self._snapshots.append(snapshot)
    
    def _draw_bar(self, value: float, max_value: float = 1.0, width: int = 20) -> str:
        """绘制条形图"""
        filled = int(width * min(value, max_value) / max_value)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def _get_status_icon(self, value: float, threshold: float) -> str:
        """获取状态图标"""
        if value >= threshold:
            return "✓"
        elif value >= threshold * 0.5:
            return "~"
        else:
            return "✗"
    
    def print_metrics(self, live: bool = False):
        """
        打印指标
        
        Args:
            live: 是否实时模式
        """
        if live:
            self._print_live_metrics()
        else:
            self._print_summary_metrics()
    
    def _print_summary_metrics(self):
        """打印汇总指标"""
        print("\n" + "═" * 60)
        print("                    涌现指标仪表盘")
        print("═" * 60)
        
        if not self._snapshots:
            print("\n  (暂无数据)")
            print("═" * 60)
            return
        
        # 当前指标
        current = self._current_metrics
        group_gain = current.get("group_gain", 0)
        diversity = current.get("diversity_index", 0)
        error_correction = current.get("error_correction_rate", 0)
        
        # 群体增益
        gain_bar = self._draw_bar(group_gain, 2.0)
        gain_status = "✓" if group_gain > 1 else "✗"
        print(f"\n  📊 群体增益 (Group Gain)")
        print(f"     {gain_bar} {group_gain:.2f} {gain_status}")
        print(f"     → {'群体表现优于个体' if group_gain > 1 else '群体表现未超越个体'}")
        
        # 多样性指数
        div_bar = self._draw_bar(diversity)
        div_status = "✓" if diversity > 0.5 else "✗"
        print(f"\n  🌈 多样性指数 (Diversity)")
        print(f"     {div_bar} {diversity:.2f} {div_status}")
        print(f"     → {'高多样性带来更多创意' if diversity > 0.5 else '多样性不足'}")
        
        # 错误修正率
        err_bar = self._draw_bar(error_correction)
        err_status = "✓" if error_correction > 0.3 else "✗"
        print(f"\n  🔧 错误修正率 (Error Correction)")
        print(f"     {err_bar} {error_correction:.2%} {err_status}")
        print(f"     → {'有效识别和修正错误' if error_correction > 0.3 else '错误修正能力有限'}")
        
        # 趋势图
        if len(self._snapshots) > 1:
            print(f"\n  📈 置信度变化趋势:")
            trend = ""
            for s in self._snapshots:
                conf = s.confidence
                if conf > 0.8:
                    trend += "🟢"
                elif conf > 0.5:
                    trend += "🟡"
                else:
                    trend += "🔴"
            print(f"     {trend}")
            print(f"     {'初始' + ' ' * 10 + '最终'}")
        
        print("\n" + "═" * 60)
    
    def _print_live_metrics(self):
        """打印实时指标"""
        # 清除行并打印
        current = self._current_metrics
        
        group_gain = current.get("group_gain", 0)
        diversity = current.get("diversity_index", 0)
        error_correction = current.get("error_correction_rate", 0)
        
        gain_bar = self._draw_bar(group_gain, 2.0, 10)
        div_bar = self._draw_bar(diversity, 1.0, 10)
        err_bar = self._draw_bar(error_correction, 1.0, 10)
        
        line = f"\r  增益:{gain_bar} {group_gain:.2f} | 多样:{div_bar} {diversity:.2f} | 修正:{err_bar} {error_correction:.2%}"
        print(line)
    
    def print_evolution_chart(self):
        """打印指标演化图"""
        if len(self._snapshots) < 2:
            return
        
        print("\n  指标演化图:")
        print("  " + "─" * 50)
        
        # 获取范围
        max_gain = max(s.group_gain for s in self._snapshots) or 1
        max_div = max(s.diversity_index for s in self._snapshots) or 1
        max_conf = max(s.confidence for s in self._snapshots) or 1
        
        for i, s in enumerate(self._snapshots):
            step = f"[{s.step}]"
            
            gain_bar = self._draw_bar(s.group_gain, max_gain, 8)
            div_bar = self._draw_bar(s.diversity_index, max_div, 8)
            conf_bar = self._draw_bar(s.confidence, max_conf, 8)
            
            print(f"  {step:4s} 增益:{gain_bar}  多样:{div_bar}  置信:{conf_bar}")
        
        print("  " + "─" * 50)
        print("       增益          多样性        置信度")
    
    def get_summary(self) -> dict:
        """获取指标摘要"""
        if not self._snapshots:
            return {
                "total_steps": 0,
                "final_metrics": {},
            }
        
        return {
            "total_steps": len(self._snapshots),
            "final_metrics": self._current_metrics,
            "max_group_gain": max(s.group_gain for s in self._snapshots),
            "avg_diversity": sum(s.diversity_index for s in self._snapshots) / len(self._snapshots),
            "total_error_corrections": sum(s.error_correction for s in self._snapshots),
            "final_confidence": self._snapshots[-1].confidence if self._snapshots else 0,
        }


def create_dashboard() -> MetricsDashboard:
    """创建指标仪表盘"""
    return MetricsDashboard()


__all__ = [
    "MetricsDashboard",
    "MetricSnapshot",
    "create_dashboard",
]
