"""智能分块与向量化层 - Chunking & Embedding"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class ChunkGranularity(Enum):
    """分块粒度"""
    SENTENCE = "sentence"      # 句子级
    PARAGRAPH = "paragraph"    # 段落级
    SECTION = "section"        # 章节级


@dataclass
class Chunk:
    """文本块"""
    chunk_id: str
    content: str
    file_id: str
    filename: str
    granularity: ChunkGranularity
    chunk_index: int
    total_chunks: int
    start_position: int
    end_position: int
    start_page: int = 1
    end_page: int = 1
    section_title: Optional[str] = None
    context: Optional[str] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SemanticChunking:
    """语义分块器"""
    
    def __init__(
        self,
        min_chunk_size: int = 200,
        max_chunk_size: int = 500,
        overlap_ratio: float = 0.15,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_ratio = overlap_ratio
    
    def _compute_chunk_id(self, content: str, index: int) -> str:
        """计算块ID"""
        return f"chunk_{hash(content) % 1000000}_{index}"
    
    def _count_tokens(self, text: str) -> int:
        """估算Token数量"""
        return int(len(text) / 3.5)
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        sentences = re.split(r'(?<=[。！？\?])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """将文本分割为段落"""
        paragraphs = re.split(r'\n\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_into_sections(self, text: str) -> List[Tuple[str, str]]:
        """将文本分割为章节"""
        sections = []
        pattern = r'(第[一二三四五六七八九十]+[章节部分篇].*?)(?=\n第[一二三四五六七八九十]+[章节部分篇]|$)'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            title = match.group(1).split('\n')[0].strip()
            content = match.group(1).strip()
            sections.append((title, content))
        
        if not sections:
            paragraphs = self._split_into_paragraphs(text)
            if len(paragraphs) > 5:
                chunk_size = (len(paragraphs) + 2) // 3
                for i in range(0, len(paragraphs), chunk_size):
                    section_content = '\n\n'.join(paragraphs[i:i+chunk_size])
                    sections.append((f"章节{i//chunk_size + 1}", section_content))
        
        return sections
    
    def chunk_by_sentence(self, text: str, file_id: str, filename: str) -> List[Chunk]:
        """句子级分块"""
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self._count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.max_chunk_size and current_chunk:
                content = ''.join(current_chunk)
                chunk = Chunk(
                    chunk_id=self._compute_chunk_id(content, len(chunks)),
                    content=content,
                    file_id=file_id,
                    filename=filename,
                    granularity=ChunkGranularity.SENTENCE,
                    chunk_index=len(chunks),
                    total_chunks=0,
                    start_position=0,
                    end_position=0,
                )
                chunks.append(chunk)
                
                overlap_size = int(len(current_chunk) * self.overlap_ratio)
                current_chunk = current_chunk[-overlap_size:] if overlap_size > 0 else []
                current_tokens = sum(self._count_tokens(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        if current_chunk:
            content = ''.join(current_chunk)
            chunk = Chunk(
                chunk_id=self._compute_chunk_id(content, len(chunks)),
                content=content,
                file_id=file_id,
                filename=filename,
                granularity=ChunkGranularity.SENTENCE,
                chunk_index=len(chunks),
                total_chunks=0,
                start_position=0,
                end_position=0,
            )
            chunks.append(chunk)
        
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def chunk_by_paragraph(self, text: str, file_id: str, filename: str) -> List[Chunk]:
        """段落级分块"""
        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for i, paragraph in enumerate(paragraphs):
            para_tokens = self._count_tokens(paragraph)
            
            if current_tokens + para_tokens > self.max_chunk_size and current_chunk:
                content = '\n\n'.join(current_chunk)
                chunk = Chunk(
                    chunk_id=self._compute_chunk_id(content, len(chunks)),
                    content=content,
                    file_id=file_id,
                    filename=filename,
                    granularity=ChunkGranularity.PARAGRAPH,
                    chunk_index=len(chunks),
                    total_chunks=0,
                    start_position=0,
                    end_position=0,
                )
                chunks.append(chunk)
                
                overlap_size = int(len(current_chunk) * self.overlap_ratio)
                current_chunk = current_chunk[-overlap_size:] if overlap_size > 0 else []
                current_tokens = sum(self._count_tokens(p) for p in current_chunk)
            
            current_chunk.append(paragraph)
            current_tokens += para_tokens
        
        if current_chunk:
            content = '\n\n'.join(current_chunk)
            chunk = Chunk(
                chunk_id=self._compute_chunk_id(content, len(chunks)),
                content=content,
                file_id=file_id,
                filename=filename,
                granularity=ChunkGranularity.PARAGRAPH,
                chunk_index=len(chunks),
                total_chunks=0,
                start_position=0,
                end_position=0,
            )
            chunks.append(chunk)
        
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def chunk_by_section(self, text: str, file_id: str, filename: str) -> List[Chunk]:
        """章节级分块"""
        sections = self._split_into_sections(text)
        chunks = []
        
        for i, (title, content) in enumerate(sections):
            chunk = Chunk(
                chunk_id=self._compute_chunk_id(content, i),
                content=content,
                file_id=file_id,
                filename=filename,
                granularity=ChunkGranularity.SECTION,
                chunk_index=i,
                total_chunks=len(sections),
                start_position=0,
                end_position=0,
                section_title=title,
            )
            chunks.append(chunk)
        
        return chunks
    
    def multi_granularity_chunking(self, text: str, file_id: str, filename: str) -> List[Chunk]:
        """多粒度分块"""
        sentence_chunks = self.chunk_by_sentence(text, file_id, filename)
        paragraph_chunks = self.chunk_by_paragraph(text, file_id, filename)
        section_chunks = self.chunk_by_section(text, file_id, filename)
        
        return sentence_chunks + paragraph_chunks + section_chunks
    
    def add_context_enhancement(self, chunks: List[Chunk], document_title: str) -> List[Chunk]:
        """为块添加上下文增强"""
        for chunk in chunks:
            context_parts = [f"本块来自《{document_title}》"]
            if chunk.section_title:
                context_parts.append(f"第{chunk.section_title}")
            if chunk.granularity == ChunkGranularity.SENTENCE:
                context_parts.append("句子级摘要")
            elif chunk.granularity == ChunkGranularity.PARAGRAPH:
                context_parts.append("段落级摘要")
            elif chunk.granularity == ChunkGranularity.SECTION:
                context_parts.append("章节级摘要")
            
            chunk.context = "，".join(context_parts)
        
        return chunks


class ChunkEmbedding:
    """向量化器"""
    
    def __init__(self, embedding_model: str = "bge-m3"):
        self.embedding_model = embedding_model
        self._model = None
    
    def _init_model(self):
        """初始化嵌入模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('BAAI/bge-m3')
            except ImportError:
                try:
                    from langchain.embeddings import HuggingFaceEmbeddings
                    self._model = HuggingFaceEmbeddings(model_name='BAAI/bge-m3')
                except:
                    self._model = None
    
    def embed_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """为块添加向量化"""
        self._init_model()
        
        if self._model is None:
            return chunks
        
        for chunk in chunks:
            text_to_embed = chunk.content
            if chunk.context:
                text_to_embed = f"{chunk.context}\n\n{chunk.content}"
            
            try:
                if hasattr(self._model, 'encode'):
                    chunk.embedding = self._model.encode(text_to_embed).tolist()
                else:
                    chunk.embedding = self._model.embed_query(text_to_embed)
            except Exception as e:
                print(f"向量化失败: {str(e)}")
        
        return chunks
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """向量化单个文本"""
        self._init_model()
        
        if self._model is None:
            return None
        
        try:
            if hasattr(self._model, 'encode'):
                return self._model.encode(text).tolist()
            else:
                return self._model.embed_query(text)
        except Exception as e:
            print(f"向量化失败: {str(e)}")
            return None
