import re
import logging
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

import tiktoken

logger = logging.getLogger(__name__)

ENCODER = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    strategy_used: str
    token_count: int
    parent_chunk_id: Optional[str] = None


def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text))


def chunk_document(text: str, strategy: str = "semantic") -> list[Chunk]:
    if strategy == "fixed":
        return _fixed_chunking(text)
    elif strategy == "semantic":
        return _semantic_chunking(text)
    elif strategy == "late":
        return _late_chunking(text)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def _fixed_chunking(text: str, chunk_size: int = 512, overlap: int = 50) -> list[Chunk]:
    tokens = ENCODER.encode(text)
    chunks = []
    
    start = 0
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = ENCODER.decode(chunk_tokens)
        
        chunks.append(Chunk(
            chunk_id=str(uuid4()),
            text=chunk_text,
            strategy_used="fixed",
            token_count=len(chunk_tokens))
        )
        
        start = end - overlap
        if start >= len(tokens):
            break
    
    logger.info(f"Fixed chunking produced {len(chunks)} chunks")
    return chunks


def _semantic_chunking(text: str, max_tokens: int = 512) -> list[Chunk]:
    paragraphs = re.split(r'\n\n+', text)
    chunks = []
    
    current_chunk_text = ""
    current_tokens = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_tokens = count_tokens(para)
        
        if para_tokens > max_tokens:
            if current_chunk_text:
                chunks.append(Chunk(
                    chunk_id=str(uuid4()),
                    text=current_chunk_text.strip(),
                    strategy_used="semantic",
                    token_count=count_tokens(current_chunk_text)
                ))
                current_chunk_text = ""
                current_tokens = 0
            
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                sentence_tokens = count_tokens(sentence)
                
                if sentence_tokens > max_tokens:
                    if current_chunk_text:
                        chunks.append(Chunk(
                            chunk_id=str(uuid4()),
                            text=current_chunk_text.strip(),
                            strategy_used="semantic",
                            token_count=count_tokens(current_chunk_text)
                        ))
                        current_chunk_text = ""
                        current_tokens = 0
                    continue
                
                if current_tokens + sentence_tokens > max_tokens:
                    chunks.append(Chunk(
                        chunk_id=str(uuid4()),
                        text=current_chunk_text.strip(),
                        strategy_used="semantic",
                        token_count=count_tokens(current_chunk_text)
                    ))
                    current_chunk_text = sentence
                    current_tokens = sentence_tokens
                else:
                    current_chunk_text += " " + sentence
                    current_tokens += sentence_tokens
        else:
            if current_tokens + para_tokens > max_tokens:
                chunks.append(Chunk(
                    chunk_id=str(uuid4()),
                    text=current_chunk_text.strip(),
                    strategy_used="semantic",
                    token_count=count_tokens(current_chunk_text)
                ))
                current_chunk_text = para
                current_tokens = para_tokens
            else:
                current_chunk_text += "\n\n" + para
                current_tokens += para_tokens
    
    if current_chunk_text:
        chunks.append(Chunk(
            chunk_id=str(uuid4()),
            text=current_chunk_text.strip(),
            strategy_used="semantic",
            token_count=count_tokens(current_chunk_text)
        ))
    
    logger.info(f"Semantic chunking produced {len(chunks)} chunks")
    return chunks


def _late_chunking(text: str, parent_tokens: int = 1500, child_tokens: int = 150) -> list[Chunk]:
    parent_chunks = _semantic_chunking(text, max_tokens=parent_tokens)
    all_chunks = []
    
    for parent in parent_chunks:
        parent_id = str(uuid4())
        all_chunks.append(Chunk(
            chunk_id=parent_id,
            text=parent.text,
            strategy_used="late",
            token_count=parent.token_count,
            parent_chunk_id=None
        ))
        
        sentences = re.split(r'(?<=[.!?])\s+', parent.text)
        child_text = ""
        child_token_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = count_tokens(sentence)
            
            if child_token_count + sentence_tokens > child_tokens:
                if child_text:
                    all_chunks.append(Chunk(
                        chunk_id=str(uuid4()),
                        text=child_text.strip(),
                        strategy_used="late",
                        token_count=child_token_count,
                        parent_chunk_id=parent_id
                    ))
                child_text = sentence
                child_token_count = sentence_tokens
            else:
                child_text += " " + sentence
                child_token_count += sentence_tokens
        
        if child_text:
            all_chunks.append(Chunk(
                chunk_id=str(uuid4()),
                text=child_text.strip(),
                strategy_used="late",
                token_count=child_token_count,
                parent_chunk_id=parent_id
            ))
    
    logger.info(f"Late chunking produced {len(all_chunks)} chunks")
    return all_chunks