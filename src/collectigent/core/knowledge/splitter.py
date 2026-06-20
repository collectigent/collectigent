"""文本分块器 - 将长文档切分为小片段"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Any

from .loader import Document


@dataclass
class Chunk:
    """文档块"""
    
    content: str
    source: str
    chunk_index: int
    total_chunks: int
    metadata: dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def __len__(self) -> int:
        return len(self.content)
    
    def __repr__(self) -> str:
        return f"Chunk(index={self.chunk_index}/{self.total_chunks}, length={len(self)})"


@dataclass
class ChunkConfig:
    """分块配置"""
    chunk_size: int = 512
    chunk_overlap: int = 64
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", "。", "！", "？", "；", " ", ""])
    preserve_separator: bool = True


class TextSplitter(ABC):
    """文本分块器基类"""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
    
    @abstractmethod
    def split(self, document: Document) -> List[Chunk]:
        """将文档分割为块"""
        pass
    
    def split_documents(self, documents: List[Document]) -> List[Chunk]:
        """分割多个文档"""
        all_chunks = []
        for doc in documents:
            chunks = self.split(doc)
            all_chunks.extend(chunks)
        return all_chunks


class RecursiveCharacterTextSplitter(TextSplitter):
    """递归字符分块器 - 按分隔符递归分割"""
    
    def split(self, document: Document) -> List[Chunk]:
        """分割文档"""
        chunks = self._split_text(document.content, document.source)
        return chunks
    
    def _split_text(self, text: str, source: str, chunk_index: int = 0) -> List[Chunk]:
        """递归分割文本"""
        chunks = []
        
        if len(text) <= self.config.chunk_size:
            chunks.append(Chunk(
                content=text,
                source=source,
                chunk_index=chunk_index,
                total_chunks=1,
            ))
            return chunks
        
        # 按分隔符尝试分割
        for separator in self.config.separators:
            if separator in text:
                parts = self._split_with_separator(text, separator)
                if len(parts) > 1:
                    current_index = chunk_index
                    total_parts = len(parts)
                    
                    for i, part in enumerate(parts):
                        sub_chunks = self._split_text(part, source, current_index)
                        # 更新total_chunks
                        for chunk in sub_chunks:
                            chunk.total_chunks = total_parts
                        chunks.extend(sub_chunks)
                        current_index += len(sub_chunks)
                    return chunks
        
        # 如果没有分隔符，直接按字符数分割
        chunks = self._split_by_characters(text, source)
        return chunks
    
    def _split_with_separator(self, text: str, separator: str) -> List[str]:
        """按分隔符分割"""
        parts = text.split(separator)
        
        if self.config.preserve_separator and separator:
            # 在每个部分后添加分隔符（除了最后一个）
            result = []
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    result.append(part + separator)
                else:
                    result.append(part)
            return result
        
        return parts
    
    def _split_by_characters(self, text: str, source: str) -> List[Chunk]:
        """按字符数直接分割"""
        chunks = []
        text_len = len(text)
        start = 0
        
        while start < text_len:
            end = start + self.config.chunk_size
            
            # 如果不是最后一块，预留重叠部分
            if end < text_len:
                end -= self.config.chunk_overlap
            
            chunk_text = text[start:end]
            chunks.append(Chunk(
                content=chunk_text,
                source=source,
                chunk_index=len(chunks),
                total_chunks=self._estimate_total_chunks(text_len),
            ))
            
            start = end - self.config.chunk_overlap
        
        # 更新total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _estimate_total_chunks(self, text_len: int) -> int:
        """估算总块数"""
        if text_len <= self.config.chunk_size:
            return 1
        effective_size = self.config.chunk_size - self.config.chunk_overlap
        return max(1, (text_len + effective_size - 1) // effective_size)


class SentenceTextSplitter(TextSplitter):
    """句子级分块器 - 保持句子完整性"""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        super().__init__(config)
        self._import_nltk()
    
    def _import_nltk(self):
        """导入NLTK依赖"""
        try:
            import nltk
            from nltk.tokenize import sent_tokenize
            self._sent_tokenize = sent_tokenize
        except ImportError:
            raise ImportError("请安装nltk: pip install nltk")
    
    def split(self, document: Document) -> List[Chunk]:
        """按句子分割"""
        sentences = self._sent_tokenize(document.content)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.config.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [
            Chunk(
                content=chunk,
                source=document.source,
                chunk_index=i,
                total_chunks=len(chunks),
            )
            for i, chunk in enumerate(chunks)
        ]


class MarkdownTextSplitter(TextSplitter):
    """Markdown分块器 - 按Markdown结构分割"""
    
    def split(self, document: Document) -> List[Chunk]:
        """按Markdown结构分割"""
        lines = document.content.split("\n")
        chunks = []
        current_chunk = []
        current_heading = ""
        
        for line in lines:
            # 检测标题
            if line.startswith("#"):
                # 保存当前块
                if current_chunk:
                    chunks.append(self._create_chunk(
                        "\n".join(current_chunk),
                        document.source,
                        current_heading
                    ))
                    current_chunk = []
                
                current_heading = line.strip()
                current_chunk.append(line)
            else:
                # 检查添加后是否超过大小限制
                temp_chunk = current_chunk + [line]
                temp_text = "\n".join(temp_chunk)
                
                if len(temp_text) <= self.config.chunk_size:
                    current_chunk = temp_chunk
                else:
                    if current_chunk:
                        chunks.append(self._create_chunk(
                            "\n".join(current_chunk),
                            document.source,
                            current_heading
                        ))
                    current_chunk = [line]
        
        # 保存最后一块
        if current_chunk:
            chunks.append(self._create_chunk(
                "\n".join(current_chunk),
                document.source,
                current_heading
            ))
        
        # 更新total_chunks
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _create_chunk(self, content: str, source: str, heading: str) -> Chunk:
        """创建块"""
        metadata = {"heading": heading} if heading else {}
        return Chunk(
            content=content,
            source=source,
            chunk_index=0,
            total_chunks=1,
            metadata=metadata,
        )