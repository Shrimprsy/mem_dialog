import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# API 配置
API_URL = os.getenv("API_URL", "https://api.chatanywhere.tech/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "")

# 模型参数
CHAT_MODEL = "gpt-3.5-turbo"
SUMMARY_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"

# 温度设置
TEMPERATURE = 0.7
SUMMARY_TEMPERATURE = 0.3
EMBEDDING_TEMPERATURE = 0.0

# 记忆管理参数
BUFFER_LIMIT = 3

# LightMem 配置
@dataclass
class MemoryConfig:
    """LightMem记忆系统配置"""
    index_strategy: str = "embedding"  # 'embedding', 'context', 'hybrid'
    extract_threshold: float = 0.5     # 元数据提取阈值
    messages_use: str = "hybrid"       # 'user_only', 'assistant_only', 'hybrid'
    pre_compress: bool = True          # 预压缩
    topic_segment: bool = False        # 主题分段
    update_mode: str = "online"        # 'online', 'offline'
    use_vector_store: bool = True      # 启用向量存储

    # 检索配置
    top_k: int = 5                     # 检索前k个相关记忆
    retrieve_strategy: str = "embedding"  # 检索策略

# 默认配置
DEFAULT_MEMORY_CONFIG = MemoryConfig()

# 向量存储配置
VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "memory_vectors.db")
COLLECTION_NAME = "mem_dialog_memory"
