import jieba
from rank_bm25 import BM25Okapi
from typing import List, Tuple

class BM25IndexManager:
    def __init__(self):
        self.corpus = []
        self.doc_ids = []
        self.index = None

    def add_document(self, doc_id: str, content: str):
        tokenized = list(jieba.cut(content))
        self.doc_ids.append(doc_id)
        self.corpus.append(tokenized)
        self._rebuild_index()

    def add_batch(self, docs: List[Tuple[str, str]]):
        for doc_id, content in docs:
            tokenized = list(jieba.cut(content))
            self.doc_ids.append(doc_id)
            self.corpus.append(tokenized)
        self._rebuild_index()

    def _rebuild_index(self):
        if self.corpus:
            self.index = BM25Okapi(self.corpus)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not self.index:
            return []
        tokenized_query = list(jieba.cut(query))
        scores = self.index.get_scores(tokenized_query)
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in indexed_scores[:top_k]:
            if score > 0:
                results.append((self.doc_ids[idx], score))
        return results