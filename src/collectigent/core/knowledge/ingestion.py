"""文件预处理层 - Ingestion Pipeline"""

from __future__ import annotations

import os
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from pathlib import Path


class FileType(Enum):
    """文件类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    XLSX = "xlsx"
    XLS = "xls"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"
    JSON = "json"
    HTML = "html"
    JPG = "jpg"
    PNG = "png"
    WEBP = "webp"
    MP3 = "mp3"
    MP4 = "mp4"
    OTHER = "other"


class FileStatus(Enum):
    """文件处理状态"""
    UPLOADED = "uploaded"
    PARSED = "parsed"
    OCR_COMPLETED = "ocr_completed"
    METADATA_EXTRACTED = "metadata_extracted"
    VALIDATED = "validated"
    DEDUPLICATED = "deduplicated"
    PROCESSED = "processed"
    ERROR = "error"


@dataclass
class FileMetadata:
    """文件元数据"""
    file_id: str
    filename: str
    file_type: FileType
    size: int
    hash: str
    created_at: float
    modified_at: float
    source_path: str
    status: FileStatus = FileStatus.UPLOADED
    title: Optional[str] = None
    author: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    language: Optional[str] = None
    page_count: Optional[int] = None
    version: int = 1
    parent_file_id: Optional[str] = None
    chunks: List[str] = field(default_factory=list)


@dataclass
class ProcessedChunk:
    """处理后的文本块"""
    chunk_id: str
    file_id: str
    content: str
    chunk_index: int
    total_chunks: int
    start_page: int
    end_page: int
    section_title: Optional[str] = None
    context: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FileIngestionPipeline:
    """文件预处理管道"""
    
    def __init__(self, storage_dir: str = "data/processed"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._processed_files: Dict[str, FileMetadata] = {}
        self._file_hashes: Set[str] = set()
        self._version_map: Dict[str, List[str]] = {}
    
    def _compute_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _detect_file_type(self, filename: str) -> FileType:
        """检测文件类型"""
        ext = filename.lower().split(".")[-1]
        type_map = {
            "pdf": FileType.PDF,
            "docx": FileType.DOCX,
            "doc": FileType.DOC,
            "xlsx": FileType.XLSX,
            "xls": FileType.XLS,
            "pptx": FileType.PPTX,
            "txt": FileType.TXT,
            "md": FileType.MD,
            "json": FileType.JSON,
            "html": FileType.HTML,
            "jpg": FileType.JPG,
            "jpeg": FileType.JPG,
            "png": FileType.PNG,
            "webp": FileType.WEBP,
            "mp3": FileType.MP3,
            "mp4": FileType.MP4,
        }
        return type_map.get(ext, FileType.OTHER)
    
    def upload_file(self, file_path: str) -> Tuple[bool, str, Optional[FileMetadata]]:
        """上传文件"""
        if not os.path.exists(file_path):
            return False, "文件不存在", None
        
        file_stat = os.stat(file_path)
        file_hash = self._compute_file_hash(file_path)
        filename = os.path.basename(file_path)
        file_type = self._detect_file_type(filename)
        
        if file_hash in self._file_hashes:
            return False, "文件已存在（重复）", None
        
        file_id = f"{file_type.value}_{int(time.time())}_{hash(filename) % 10000}"
        metadata = FileMetadata(
            file_id=file_id,
            filename=filename,
            file_type=file_type,
            size=file_stat.st_size,
            hash=file_hash,
            created_at=file_stat.st_ctime,
            modified_at=file_stat.st_mtime,
            source_path=file_path,
            status=FileStatus.UPLOADED
        )
        
        self._processed_files[file_id] = metadata
        self._file_hashes.add(file_hash)
        
        if filename not in self._version_map:
            self._version_map[filename] = []
        self._version_map[filename].append(file_id)
        
        return True, "文件上传成功", metadata
    
    def parse_file(self, file_id: str) -> Tuple[bool, str, Optional[str]]:
        """解析文件内容"""
        if file_id not in self._processed_files:
            return False, "文件不存在", None
        
        metadata = self._processed_files[file_id]
        
        try:
            content = self._parse_by_type(metadata.source_path, metadata.file_type, file_id)
            metadata.status = FileStatus.PARSED
            return True, "文件解析成功", content
        except Exception as e:
            metadata.status = FileStatus.ERROR
            return False, f"文件解析失败: {str(e)}", None
    
    def _parse_by_type(self, file_path: str, file_type: FileType, file_id: str = None) -> str:
        """根据文件类型解析内容"""
        content = ""
        
        if file_type == FileType.TXT:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        
        elif file_type == FileType.MD:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        
        elif file_type == FileType.JSON:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                content = json.dumps(data, ensure_ascii=False, indent=2)
        
        elif file_type == FileType.HTML:
            try:
                from bs4 import BeautifulSoup
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                    content = soup.get_text(separator="\n")
            except ImportError:
                content = "需要安装 beautifulsoup4 库"
        
        elif file_type == FileType.PDF:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                content = "\n".join([page.extract_text() for page in reader.pages])
                if file_id and (metadata := self._processed_files.get(file_id)):
                    metadata.page_count = len(reader.pages)
            except ImportError:
                content = self._ocr_file(file_path)
        
        elif file_type == FileType.DOCX:
            try:
                from docx import Document
                doc = Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            except ImportError:
                content = "需要安装 python-docx 库"
        
        elif file_type in [FileType.JPG, FileType.PNG, FileType.WEBP]:
            content = self._ocr_file(file_path)
        
        else:
            content = f"未支持的文件类型: {file_type.value}"
        
        return content
    
    def _ocr_file(self, file_path: str) -> str:
        """OCR识别图片内容"""
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(file_path)
            return pytesseract.image_to_string(img, lang="chi_sim+eng")
        except Exception as e:
            return f"OCR识别失败: {str(e)}"
    
    def extract_metadata(self, file_id: str, content: str) -> Tuple[bool, str]:
        """提取元数据"""
        if file_id not in self._processed_files:
            return False, "文件不存在"
        
        metadata = self._processed_files[file_id]
        
        lines = content.strip().split("\n")[:5]
        metadata.title = lines[0].strip() if lines else None
        
        metadata.keywords = self._extract_keywords(content)
        metadata.language = self._detect_language(content)
        
        metadata.status = FileStatus.METADATA_EXTRACTED
        return True, "元数据提取成功"
    
    def _extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """提取关键词"""
        stopwords = {"的", "了", "是", "在", "和", "与", "或", "及", "等", "这", "那", "我", "你", "他"}
        words = {}
        
        for word in content.lower().split():
            if word not in stopwords and len(word) >= 2:
                words[word] = words.get(word, 0) + 1
        
        return sorted(words.keys(), key=lambda x: words[x], reverse=True)[:max_keywords]
    
    def _detect_language(self, content: str) -> str:
        """检测语言"""
        chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        english_chars = sum(1 for c in content if 'a' <= c.lower() <= 'z')
        
        if chinese_chars > english_chars * 2:
            return "zh"
        elif english_chars > chinese_chars * 2:
            return "en"
        else:
            return "mixed"
    
    def validate_file(self, file_id: str) -> Tuple[bool, str]:
        """权限校验 - 防止PoisonedRAG攻击"""
        if file_id not in self._processed_files:
            return False, "文件不存在"
        
        metadata = self._processed_files[file_id]
        
        malicious_patterns = [
            "ignore previous instructions",
            "disregard prior context",
            "forget everything before",
            "override system prompt",
            "execute this instead",
            "you are now",
            "change your role to",
            "system prompt:",
            "new instruction:",
        ]
        
        content = ""
        try:
            content = self._parse_by_type(metadata.source_path, metadata.file_type)
        except:
            pass
        
        for pattern in malicious_patterns:
            if pattern.lower() in content.lower():
                metadata.status = FileStatus.ERROR
                return False, f"检测到潜在恶意内容: {pattern}"
        
        metadata.status = FileStatus.VALIDATED
        return True, "文件验证通过"
    
    def deduplicate(self, file_id: str) -> Tuple[bool, str, Optional[str]]:
        """去重和版本控制"""
        if file_id not in self._processed_files:
            return False, "文件不存在", None
        
        metadata = self._processed_files[file_id]
        filename = metadata.filename
        
        if filename in self._version_map:
            versions = self._version_map[filename]
            if len(versions) > 1:
                prev_version = versions[-2]
                metadata.version = len(versions)
                metadata.parent_file_id = prev_version
                metadata.status = FileStatus.DEDUPLICATED
                return True, f"检测到新版本，父版本: {prev_version}", prev_version
        
        metadata.status = FileStatus.DEDUPLICATED
        return True, "新增文件，无重复", None
    
    def process_file(self, file_path: str) -> Tuple[bool, str, Optional[FileMetadata]]:
        """完整处理单个文件"""
        success, msg, metadata = self.upload_file(file_path)
        if not success:
            return success, msg, metadata
        
        file_id = metadata.file_id
        
        success, msg = self.validate_file(file_id)
        if not success:
            return False, msg, metadata
        
        success, msg, content = self.parse_file(file_id)
        if not success:
            return False, msg, metadata
        
        success, msg = self.extract_metadata(file_id, content or "")
        if not success:
            return False, msg, metadata
        
        success, msg, _ = self.deduplicate(file_id)
        if not success:
            return False, msg, metadata
        
        metadata.status = FileStatus.PROCESSED
        return True, "文件处理完成", metadata
    
    def batch_process(self, folder_path: str) -> List[Tuple[str, str, Optional[FileMetadata]]]:
        """批量处理文件夹中的文件"""
        results = []
        if not os.path.isdir(folder_path):
            return [("folder", "文件夹不存在", None)]
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                success, msg, metadata = self.process_file(file_path)
                results.append((filename, msg, metadata))
        
        return results
    
    def get_file_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """获取文件元数据"""
        return self._processed_files.get(file_id)
    
    def list_files(self) -> List[FileMetadata]:
        """列出所有已处理文件"""
        return list(self._processed_files.values())
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "total_files": len(self._processed_files),
            "pending_files": sum(1 for f in self._processed_files.values() if f.status != FileStatus.PROCESSED),
            "processed_files": sum(1 for f in self._processed_files.values() if f.status == FileStatus.PROCESSED),
            "error_files": sum(1 for f in self._processed_files.values() if f.status == FileStatus.ERROR),
        }
