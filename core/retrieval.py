import numpy as np
from typing import List, Dict, Tuple, Optional
from utils.bm25_utils import BM25IndexManager
from utils.embedding import EmbeddingModel
from core.storage import MemoryStorage
from config_memory import (
    BM25_WEIGHT, VECTOR_WEIGHT, META_FILTER_WEIGHT,
    RETRIEVAL_TOP_K, CANDIDATE_EXPAND_FACTOR
)

class HybridRetriever:
    def __init__(self, storage: MemoryStorage, embedding_model: EmbeddingModel):
        self.storage = storage
        self.embed_model = embedding_model
        self.bm25_index = BM25IndexManager()
        self.w_bm25 = BM25_WEIGHT
        self.w_vector = VECTOR_WEIGHT
        self.w_meta = META_FILTER_WEIGHT
        self._load_bm25_from_storage()

    def _load_bm25_from_storage(self):
        cursor = self.storage.conn.cursor()
        cursor.execute("SELECT id, content FROM episodic_memories")
        rows = cursor.fetchall()
        docs = [(row[0], row[1]) for row in rows]
        if docs:
            self.bm25_index.add_batch(docs)

    def add_to_index(self, mem_id: str, content: str):
        self.bm25_index.add_document(mem_id, content)

    def retrieve(self, user_id: str, query: str,
                 filter_tags: Optional[Dict[str, str]] = None,
                 top_k: int = RETRIEVAL_TOP_K) -> List[Tuple[str, float, Dict]]:
        candidates = self.storage.get_candidates_by_tags(user_id, filter_tags)
        if not candidates:
            return []

        query_vector = self.embed_model.encode(query)
        vector_results = self.storage.episodic_collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k * CANDIDATE_EXPAND_FACTOR, len(candidates)),
            where={"user_id": user_id}
        )

        bm25_results = self.bm25_index.search(query, top_k * CANDIDATE_EXPAND_FACTOR)
        bm25_score_map = {doc_id: score for doc_id, score in bm25_results if doc_id in candidates}

        final_scores = {}
        vec_id_to_score = {}
        if vector_results and vector_results['ids']:
            for i, mem_id in enumerate(vector_results['ids'][0]):
                distance = vector_results['distances'][0][i]
                vec_id_to_score[mem_id] = 1.0 - distance

        max_bm25 = max(bm25_score_map.values()) if bm25_score_map else 1.0
        for mem_id in candidates:
            vec_score = vec_id_to_score.get(mem_id, 0.0)
            bm25_score = bm25_score_map.get(mem_id, 0.0) / max_bm25 if max_bm25 > 0 else 0.0
            meta_score = 1.0
            final_scores[mem_id] = (
                self.w_vector * vec_score +
                self.w_bm25 * bm25_score +
                self.w_meta * meta_score
            )

        final_scores = self._apply_decay(user_id, final_scores)
        sorted_ids = sorted(final_scores.keys(), key=lambda x: final_scores[x], reverse=True)[:top_k]

        results = []
        for mem_id in sorted_ids:
            mem_data = self.storage.get_episodic_by_id(user_id, mem_id)
            if mem_data:
                results.append((mem_id, final_scores[mem_id], mem_data))

        if results:
            self.storage.update_access_stats(user_id, [r[0] for r in results])

        return results

    def _apply_decay(self, user_id: str, scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return scores
        cursor = self.storage.conn.cursor()
        placeholders = ','.join(['?'] * len(scores))
        cursor.execute(
            f"SELECT id, decay_factor FROM episodic_memories WHERE user_id = ? AND id IN ({placeholders})",
            [user_id] + list(scores.keys())
        )
        decay_map = {row[0]: row[1] for row in cursor.fetchall()}
        for mem_id in scores:
            scores[mem_id] *= decay_map.get(mem_id, 1.0)
        return scores