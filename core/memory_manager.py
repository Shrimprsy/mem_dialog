import uuid
from typing import List, Dict
from core.storage import MemoryStorage
from core.retrieval import HybridRetriever
from extractors.entity_extractor import EntityExtractor
from extractors.summarizer import generate_summary
from utils.embedding import EmbeddingModel
from config_memory import (
    WORKING_MEMORY_MAX_MESSAGES, EPISODIC_COMPRESS_TRIGGER,
    RETRIEVAL_TOP_K
)

class MemoryManager:
    def __init__(self, user_id: str, buffer_limit=3):
        self.user_id = user_id
        self.buffer_limit = buffer_limit
        self.storage = MemoryStorage()
        self.embed_model = EmbeddingModel()
        self.retriever = HybridRetriever(self.storage, self.embed_model)
        self.extractor = EntityExtractor()

        self.working_memory = self.storage.load_working_memory(user_id)
        self.compressed_rounds = self.storage.get_compressed_rounds(user_id)

    def add_interaction(self, user_msg: str, ai_msg: str):
        self.working_memory.append({"role": "user", "content": user_msg})
        self.working_memory.append({"role": "assistant", "content": ai_msg})
        self.storage.save_working_memory(self.user_id, self.working_memory)

        if len(self.working_memory) > WORKING_MEMORY_MAX_MESSAGES:
            excess = len(self.working_memory) - WORKING_MEMORY_MAX_MESSAGES
            rounds_to_compress = (excess // 2) + 1
            self._force_compress_rounds(rounds_to_compress)
            self.working_memory = self.working_memory[-WORKING_MEMORY_MAX_MESSAGES:]
            self.storage.save_working_memory(self.user_id, self.working_memory)

        total_rounds = len(self.working_memory) // 2
        uncompressed_rounds = total_rounds - self.compressed_rounds
        if uncompressed_rounds >= self.buffer_limit:
            self._incremental_consolidate()

    def _incremental_consolidate(self):
        total_rounds = len(self.working_memory) // 2
        start_idx = self.compressed_rounds * 2
        end_idx = total_rounds * 2
        segment = self.working_memory[start_idx:end_idx]
        if not segment:
            return
        self._compress_segment(segment)
        self.compressed_rounds = total_rounds
        self.storage.set_compressed_rounds(self.user_id, self.compressed_rounds)

    def _force_compress_rounds(self, rounds: int):
        if rounds <= 0 or rounds > len(self.working_memory) // 2:
            return
        segment = self.working_memory[:rounds*2]
        if segment:
            self._compress_segment(segment)
        self.compressed_rounds = max(0, self.compressed_rounds - rounds)
        self.storage.set_compressed_rounds(self.user_id, self.compressed_rounds)

    def _compress_segment(self, segment: List[Dict]):
        conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in segment])
        summary = generate_summary(conv_text)
        metadata = self.extractor.extract_from_conversation(segment)
        embedding = self.embed_model.encode(summary)
        mem_id = str(uuid.uuid4())
        self.storage.add_episodic(self.user_id, mem_id, conv_text, summary, embedding, metadata)
        self.retriever.add_to_index(mem_id, conv_text)
        self._update_semantic_from_metadata(metadata, mem_id)

    def _update_semantic_from_metadata(self, metadata: Dict, source_id: str):
        for fact in metadata.get("key_facts", []):
            self.storage.upsert_semantic(self.user_id, "fact", fact, "", confidence=0.8, source_id=source_id)
        for pref in metadata.get("user_preferences", []):
            self.storage.upsert_semantic(self.user_id, "preference", pref, "", confidence=0.9, source_id=source_id)
        for person in metadata.get("persons", []):
            self.storage.upsert_semantic(self.user_id, "person", person, f"提及人物 {person}", confidence=0.7, source_id=source_id)
        for loc in metadata.get("locations", []):
            self.storage.upsert_semantic(self.user_id, "location", loc, f"提及地点 {loc}", confidence=0.7, source_id=source_id)

    def get_context_for_llm(self, current_query: str = "") -> str:
        retrieved = self.retriever.retrieve(self.user_id, current_query, top_k=RETRIEVAL_TOP_K)
        semantic_memories = self.storage.get_all_semantic(self.user_id)
        working_context = "\n".join([f"{m['role']}: {m['content']}" for m in self.working_memory[-10:]])

        episodic_text = ""
        if retrieved:
            episodic_text = "【相关历史片段】\n"
            for mem_id, score, data in retrieved:
                episodic_text += f"- {data['summary']} (相关度: {score:.2f})\n"

        semantic_text = ""
        if semantic_memories:
            semantic_text = "【用户长期画像】\n"
            by_type = {}
            for m in semantic_memories:
                by_type.setdefault(m['type'], []).append(m['key'])
            for t, items in by_type.items():
                semantic_text += f"- {t}: {', '.join(items[:5])}\n"

        system_prompt = f"""
你是一个具备长期记忆能力的个性化 AI 助手。

{semantic_text}

{episodic_text}

【近期对话】
{working_context}

请严格结合上述信息进行回复。如果记忆中没有相关信息，请如实说明。
"""
        return system_prompt