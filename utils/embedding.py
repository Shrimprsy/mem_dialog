from config import USE_LOCAL_EMBEDDING, LOCAL_EMBEDDING_PATH
from llm_client import get_embedding

class EmbeddingModel:
    def __init__(self):
        self.use_local = USE_LOCAL_EMBEDDING
        if self.use_local:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(LOCAL_EMBEDDING_PATH)
            except ImportError:
                raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")
        else:
            self.model = None

    def encode(self, text: str) -> list:
        if self.use_local:
            return self.model.encode(text).tolist()
        else:
            return get_embedding(text)

    def encode_batch(self, texts: list) -> list:
        if self.use_local:
            return self.model.encode(texts).tolist()
        else:
            return [get_embedding(t) for t in texts]