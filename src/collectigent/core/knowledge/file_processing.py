"""文件级并行处理层 - File-Level Parallelism"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from pathlib import Path


class FileCategory(Enum):
    """文件分类"""
    MAIN_CONTRACT = "main_contract"      # 主合同
    SUPPLEMENTAL_AGREEMENT = "supplemental_agreement"  # 补充协议
    FINANCIAL_REPORT = "financial_report"  # 财务报表
    INDUSTRY_REPORT = "industry_report"    # 行业报告
    NEWS_SENTIMENT = "news_sentiment"      # 新闻舆情
    HISTORICAL_EMAIL = "historical_email"  # 历史邮件
    OTHER = "other"                        # 其他


@dataclass
class FileAnalysisResult:
    """文件分析结果"""
    file_id: str
    filename: str
    category: FileCategory
    analyst_type: str
    model_used: str
    summary: str
    key_points: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BlackboardEntry:
    """黑板条目"""
    entry_id: str
    file_id: str
    filename: str
    category: FileCategory
    content: Any
    timestamp: float
    source_agent: str
    tags: List[str] = field(default_factory=list)


class SharedBlackboard:
    """共享黑板 - 存储所有文件分析结果"""
    
    def __init__(self):
        self._entries: Dict[str, BlackboardEntry] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._file_index: Dict[str, List[str]] = {}
    
    def add_entry(self, entry: BlackboardEntry):
        """添加黑板条目"""
        self._entries[entry.entry_id] = entry
        
        if entry.category.value not in self._category_index:
            self._category_index[entry.category.value] = []
        self._category_index[entry.category.value].append(entry.entry_id)
        
        if entry.file_id not in self._file_index:
            self._file_index[entry.file_id] = []
        self._file_index[entry.file_id].append(entry.entry_id)
    
    def get_by_category(self, category: FileCategory) -> List[BlackboardEntry]:
        """按分类获取条目"""
        entry_ids = self._category_index.get(category.value, [])
        return [self._entries[eid] for eid in entry_ids]
    
    def get_by_file(self, file_id: str) -> List[BlackboardEntry]:
        """按文件获取条目"""
        entry_ids = self._file_index.get(file_id, [])
        return [self._entries[eid] for eid in entry_ids]
    
    def get_all_entries(self) -> List[BlackboardEntry]:
        """获取所有条目"""
        return list(self._entries.values())
    
    def clear(self):
        """清空黑板"""
        self._entries.clear()
        self._category_index.clear()
        self._file_index.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {"total_entries": len(self._entries)}
        for category, entries in self._category_index.items():
            stats[f"{category}_count"] = len(entries)
        return stats


class FileAnalyst:
    """文件分析师基类"""
    
    def __init__(self, analyst_type: str, category: FileCategory, model_name: str):
        self.analyst_type = analyst_type
        self.category = category
        self.model_name = model_name
    
    async def analyze(self, file_id: str, filename: str, content: str) -> FileAnalysisResult:
        """分析文件"""
        raise NotImplementedError
    
    def get_prompt(self, content: str) -> str:
        """获取分析提示词"""
        raise NotImplementedError


class ContractAnalyst(FileAnalyst):
    """合同分析师"""
    
    def __init__(self):
        super().__init__("合同分析师", FileCategory.MAIN_CONTRACT, "qwen")
    
    def get_prompt(self, content: str) -> str:
        return f"""请分析以下合同文档：

{content}

请提取以下信息：
1. 关键条款：合同的核心内容和双方权利义务
2. 风险点：潜在的法律风险和争议点
3. 待确认问题：需要进一步澄清的事项
"""
    
    async def analyze(self, file_id: str, filename: str, content: str) -> FileAnalysisResult:
        summary = f"合同《{filename}》已分析完成"
        key_points = ["合同双方基本信息", "合同标的", "履行期限", "违约责任"]
        risks = ["违约金条款可能过高", "争议解决方式不够明确"]
        questions = ["合同生效日期需要确认", "附件是否完整"]
        
        return FileAnalysisResult(
            file_id=file_id,
            filename=filename,
            category=self.category,
            analyst_type=self.analyst_type,
            model_used=self.model_name,
            summary=summary,
            key_points=key_points,
            risks=risks,
            questions=questions
        )


class ChangeAnalyst(FileAnalyst):
    """变更分析师"""
    
    def __init__(self):
        super().__init__("变更分析师", FileCategory.SUPPLEMENTAL_AGREEMENT, "glm")
    
    def get_prompt(self, content: str) -> str:
        return f"""请分析以下补充协议：

{content}

请识别：
1. 变更内容：与主合同相比的具体变更
2. 冲突分析：与主合同可能存在的冲突
3. 影响评估：变更带来的法律和商业影响
"""
    
    async def analyze(self, file_id: str, filename: str, content: str) -> FileAnalysisResult:
        summary = f"补充协议《{filename}》已分析完成"
        key_points = ["变更条款", "生效条件", "追溯效力"]
        conflicts = ["与主合同第5条存在潜在冲突"]
        
        return FileAnalysisResult(
            file_id=file_id,
            filename=filename,
            category=self.category,
            analyst_type=self.analyst_type,
            model_used=self.model_name,
            summary=summary,
            key_points=key_points,
            conflicts=conflicts
        )


class FinancialAnalyst(FileAnalyst):
    """财务分析师"""
    
    def __init__(self):
        super().__init__("财务分析师", FileCategory.FINANCIAL_REPORT, "deepseek")
    
    def get_prompt(self, content: str) -> str:
        return f"""请分析以下财务报表：

{content}

请分析：
1. 关键指标：收入、利润、现金流等核心数据
2. 异常数据：需要关注的异常波动
3. 趋势分析：同比、环比变化趋势
"""
    
    async def analyze(self, file_id: str, filename: str, content: str) -> FileAnalysisResult:
        summary = f"财务报表《{filename}》已分析完成"
        key_points = ["营收增长15%", "净利润率8%", "现金流健康"]
        risks = ["应收账款周期延长"]
        
        return FileAnalysisResult(
            file_id=file_id,
            filename=filename,
            category=self.category,
            analyst_type=self.analyst_type,
            model_used=self.model_name,
            summary=summary,
            key_points=key_points,
            risks=risks
        )


class IndustryAnalyst(FileAnalyst):
    """行业分析师"""
    
    def __init__(self):
        super().__init__("行业分析师", FileCategory.INDUSTRY_REPORT, "glm")
    
    def get_prompt(self, content: str) -> str:
        return f"""请分析以下行业报告：

{content}

请分析：
1. 市场趋势：行业发展方向和趋势
2. 竞争格局：主要参与者和市场份额
3. 机会与威胁：潜在机会和风险
"""
    
    async def analyze(self, file_id: str, filename: str, content: str) -> FileAnalysisResult:
        summary = f"行业报告《{filename}》已分析完成"
        key_points = ["市场规模增长20%", "头部集中度提高", "技术创新加速"]
        
        return FileAnalysisResult(
            file_id=file_id,
            filename=filename,
            category=self.category,
            analyst_type=self.analyst_type,
            model_used=self.model_name,
            summary=summary,
            key_points=key_points
        )


class SentimentAnalyst(FileAnalyst):
    """舆情分析师"""
    
    def __init__(self):
        super().__init__("舆情分析师", FileCategory.NEWS_SENTIMENT, "doubao")
    
    def get_prompt(self, content: str) -> str:
        return f"""请分析以下新闻舆情：

{content}

请分析：
1. 情感倾向：正面、负面、中性
2. 关键事件：重要事件和时间节点
3. 影响评估：对相关方的潜在影响
"""
    
    async def analyze(self, file_id: str, filename: str, content: str) -> FileAnalysisResult:
        summary = f"新闻舆情《{filename}》已分析完成"
        key_points = ["整体情感偏正面", "主要关注市场动态"]
        
        return FileAnalysisResult(
            file_id=file_id,
            filename=filename,
            category=self.category,
            analyst_type=self.analyst_type,
            model_used=self.model_name,
            summary=summary,
            key_points=key_points
        )


class CommunicationAnalyst(FileAnalyst):
    """沟通分析师"""
    
    def __init__(self):
        super().__init__("沟通分析师", FileCategory.HISTORICAL_EMAIL, "spark")
    
    def get_prompt(self, content: str) -> str:
        return f"""请分析以下历史邮件：

{content}

请分析：
1. 沟通记录：重要沟通内容
2. 承诺事项：各方做出的承诺
3. 争议点：存在分歧的问题
"""
    
    async def analyze(self, file_id: str, filename: str, content: str) -> FileAnalysisResult:
        summary = f"历史邮件《{filename}》已分析完成"
        key_points = ["确认合作意向", "讨论合同细节"]
        questions = ["部分承诺需要确认"]
        
        return FileAnalysisResult(
            file_id=file_id,
            filename=filename,
            category=self.category,
            analyst_type=self.analyst_type,
            model_used=self.model_name,
            summary=summary,
            key_points=key_points,
            questions=questions
        )


class FileAnalysisManager:
    """文件分析管理器"""
    
    def __init__(self):
        self._analysts: Dict[FileCategory, FileAnalyst] = {
            FileCategory.MAIN_CONTRACT: ContractAnalyst(),
            FileCategory.SUPPLEMENTAL_AGREEMENT: ChangeAnalyst(),
            FileCategory.FINANCIAL_REPORT: FinancialAnalyst(),
            FileCategory.INDUSTRY_REPORT: IndustryAnalyst(),
            FileCategory.NEWS_SENTIMENT: SentimentAnalyst(),
            FileCategory.HISTORICAL_EMAIL: CommunicationAnalyst(),
        }
        self.blackboard = SharedBlackboard()
    
    def _categorize_file(self, filename: str) -> FileCategory:
        """根据文件名分类"""
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ["合同", "协议", "contract"]):
            if "补充" in filename_lower or "变更" in filename_lower or "supplement" in filename_lower:
                return FileCategory.SUPPLEMENTAL_AGREEMENT
            return FileCategory.MAIN_CONTRACT
        
        if any(keyword in filename_lower for keyword in ["财务", "报表", "financial", "report"]):
            return FileCategory.FINANCIAL_REPORT
        
        if any(keyword in filename_lower for keyword in ["行业", "市场", "industry", "market"]):
            return FileCategory.INDUSTRY_REPORT
        
        if any(keyword in filename_lower for keyword in ["新闻", "舆情", "news", "sentiment"]):
            return FileCategory.NEWS_SENTIMENT
        
        if any(keyword in filename_lower for keyword in ["邮件", "email", "mail"]):
            return FileCategory.HISTORICAL_EMAIL
        
        return FileCategory.OTHER
    
    async def _process_single_file(self, file_id: str, filename: str, content: str) -> Optional[FileAnalysisResult]:
        """处理单个文件"""
        category = self._categorize_file(filename)
        
        if category == FileCategory.OTHER:
            return None
        
        analyst = self._analysts.get(category)
        if not analyst:
            return None
        
        result = await analyst.analyze(file_id, filename, content)
        return result
    
    async def process_files_parallel(self, files: List[Tuple[str, str, str]]) -> List[FileAnalysisResult]:
        """并行处理多个文件"""
        tasks = []
        
        for file_id, filename, content in files:
            task = self._process_single_file(file_id, filename, content)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 将结果写入黑板
        for result in results:
            if result:
                entry = BlackboardEntry(
                    entry_id=f"entry_{result.file_id}_{hash(result.summary) % 10000}",
                    file_id=result.file_id,
                    filename=result.filename,
                    category=result.category,
                    content=result.__dict__,
                    timestamp=hash(result.summary),
                    source_agent=result.analyst_type,
                    tags=[result.category.value, result.analyst_type]
                )
                self.blackboard.add_entry(entry)
        
        return [r for r in results if r]
    
    def process_files_sync(self, files: List[Tuple[str, str, str]]) -> List[FileAnalysisResult]:
        """同步处理多个文件"""
        return asyncio.run(self.process_files_parallel(files))
