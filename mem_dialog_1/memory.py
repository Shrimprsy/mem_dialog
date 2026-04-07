import time
from dataclasses import dataclass
from typing import List, Dict, Optional
import json
import pickle
import os

from llm_client import generate_summary, extract_metadata, get_embedding
from config import (
    BUFFER_LIMIT, DEFAULT_MEMORY_CONFIG, VECTOR_STORE_PATH,
    COLLECTION_NAME, MemoryConfig
)


@dataclass
class MemoryEntry:
    """单个记忆条目"""
    content: str
    timestamp: str
    metadata: Dict = None
    keywords: List[str] = None
    entities: List[str] = None
    embedding: List[float] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = []
        if self.embedding is None:
            self.embedding = []


class MemoryManager:
    """
    LightMem增强版记忆管理器

    核心特性：
    1. 短期缓冲区：管理最近对话
    2. 长期记忆库：存储压缩的摘要
    3. 向量检索：语义相似度搜索
    4. 元数据提取：自动提取关键词和实体
    """

    def __init__(self, buffer_limit: int = BUFFER_LIMIT, config: MemoryConfig = None):
        self.short_term_buffer: List[Dict] = []
        self.buffer_limit = buffer_limit
        self.long_term_db: List[MemoryEntry] = []
        self.config = config or DEFAULT_MEMORY_CONFIG

        # 加载或创建向量存储
        self._init_vector_store()

    def _init_vector_store(self):
        """初始化向量存储"""
        if self.config.use_vector_store:
            try:
                self.vector_store = {}
                if os.path.exists(VECTOR_STORE_PATH):
                    with open(VECTOR_STORE_PATH, 'rb') as f:
                        self.vector_store = pickle.load(f)
            except Exception as e:
                print(f"Warning: Failed to load vector store: {e}")
                self.vector_store = {}

    def save_vector_store(self):
        """保存向量存储到磁盘"""
        if self.config.use_vector_store and self.vector_store:
            try:
                with open(VECTOR_STORE_PATH, 'wb') as f:
                    pickle.dump(self.vector_store, f)
            except Exception as e:
                print(f"Warning: Failed to save vector store: {e}")

    def add_interaction(self, user_msg: str, ai_msg: str) -> None:
        """
        添加对话交互并管理记忆

        核心流程：
        1. 添加到短期缓冲区
        2. 检查是否需要压缩
        3. 生成摘要和元数据
        4. 提取向量并存储
        """
        self.short_term_buffer.append({"role": "user", "content": user_msg})
        self.short_term_buffer.append({"role": "assistant", "content": ai_msg})

        # 检查是否达到缓冲区限制
        if len(self.short_term_buffer) / 2 >= self.buffer_limit:
            self._compress_and_store()

    def _compress_and_store(self) -> None:
        """压缩短期记忆并存储到长期库"""
        if not self.short_term_buffer:
            return

        # 生成摘要
        conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in self.short_term_buffer])
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            summary = generate_summary(conversation_text)
        except Exception as e:
            summary = f"[摘要生成失败] 时间: {timestamp}, 错误: {str(e)}"
            print(f"Warning: {e}")

        # 提取元数据
        metadata = extract_metadata(self.short_term_buffer, self.config.extract_threshold)

        # 创建记忆条目
        memory_entry = MemoryEntry(
            content=summary,
            timestamp=timestamp,
            metadata=metadata,
            keywords=metadata.get("keywords", []),
            entities=metadata.get("entities", [])
        )

        # 提取向量用于检索
        if self.config.use_vector_store:
            try:
                memory_entry.embedding = get_embedding(summary)
                # 存储向量
                self.vector_store[len(self.long_term_db)] = {
                    "embedding": memory_entry.embedding,
                    "entry": memory_entry
                }
            except Exception as e:
                print(f"Warning: Failed to generate embedding: {e}")
                memory_entry.embedding = None

        self.long_term_db.append(memory_entry)
        self.short_term_buffer = []

        # 保存向量存储
        if self.config.use_vector_store:
            self.save_vector_store()

    def retrieve(self, query: str, top_k: int = None) -> List[MemoryEntry]:
        """
        语义检索相关记忆

        核心特性：
        1. 将查询转换为向量
        2. 计算相似度
        3. 返回最相关的记忆
        """
        if not self.long_term_db:
            return []

        top_k = top_k or self.config.top_k

        if not self.config.use_vector_store or not self.long_term_db[0].embedding:
            # 回退到基于文本的检索
            return self._text_based_retrieve(query, top_k)

        # 向量相似度检索
        query_embedding = get_embedding(query)
        similarities = []

        for idx, entry in enumerate(self.long_term_db):
            if entry.embedding:
                sim = self._cosine_similarity(query_embedding, entry.embedding)
                similarities.append((idx, sim))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        # 返回top_k个
        top_indices = [idx for idx, _ in similarities[:top_k]]
        return [self.long_term_db[i] for i in top_indices if i in top_indices]

    def _text_based_retrieve(self, query: str, top_k: int) -> List[MemoryEntry]:
        """基于文本的简单检索（回退方案）"""
        query_lower = query.lower()
        scores = []

        for entry in self.long_term_db:
            score = self._text_similarity(query_lower, entry.content.lower())
            scores.append((entry, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in scores[:top_k]]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _text_similarity(self, text1: str, text2: str) -> float:
        """基于文本的相似度计算"""
        import re
        # 移除标点符号
        text1 = re.sub(r'[^\w\s]', '', text1)
        text2 = re.sub(r'[^\w\s]', '', text2)

        # 计算关键词重叠
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def get_context_for_llm(self, query: str = None) -> str:
        """
        为LLM生成上下文

        核心特性：
        1. 检索相关记忆
        2. 生成系统提示
        3. 融合短期和长期记忆
        """
        # 如果提供了查询，先检索相关记忆
        relevant_memories = []
        if query:
            relevant_memories = self.retrieve(query, top_k=3)

        # 构建上下文
        context_parts = []

        if relevant_memories:
            context_parts.append("【检索到的相关记忆】：")
            for mem in relevant_memories:
                context_parts.append(f"- {mem.content} (时间: {mem.timestamp})")

        # 添加所有长期记忆（可选）
        if len(relevant_memories) < len(self.long_term_db):
            context_parts.append("\n【其他历史记忆】：")
            for mem in self.long_term_db[len(relevant_memories):]:
                context_parts.append(f"- {mem.content}")

        long_term_context = "\n".join(context_parts)

        system_prompt = (
            "你是一个具备长期记忆能力的个性化AI助手。\n"
            "你的核心能力是理解用户的历史偏好，并结合上下文给出自然的回答。\n"
            "====================\n"
            f"【关于该用户的长期记忆和偏好画像】：\n{long_term_context}\n"
            "====================\n"
            "请严格结合上述长期记忆进行回复。不要暴露你的记忆处理过程。"
        )
        return system_prompt

    def get_relevant_memories_for_display(self, query: str = None) -> List[str]:
        """获取用于显示的相关记忆列表"""
        if query:
            memories = self.retrieve(query, top_k=5)
        else:
            memories = self.long_term_db[:5]

        return [f"[{mem.timestamp}] {mem.content}" for mem in memories]

    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        return {
            "total_memories": len(self.long_term_db),
            "buffer_turns": len(self.short_term_buffer) // 2,
            "buffer_limit": self.buffer_limit,
            "use_vector_store": self.config.use_vector_store,
            "vector_count": len(self.vector_store)
        }
