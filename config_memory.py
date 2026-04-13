# 记忆系统专项配置

# 分层记忆参数
WORKING_MEMORY_MAX_MESSAGES = 50       # 工作记忆最多保留消息条数
EPISODIC_COMPRESS_TRIGGER = 3          # 每 N 轮对话触发一次压缩

# 混合检索权重
BM25_WEIGHT = 0.3
VECTOR_WEIGHT = 0.6
META_FILTER_WEIGHT = 0.1

# 检索数量
RETRIEVAL_TOP_K = 5                    # 每次检索返回的记忆条数
CANDIDATE_EXPAND_FACTOR = 3            # 候选池扩大倍数

# 时间衰减参数
DECAY_HALF_LIFE_DAYS = 30.0            # 基础半衰期（天）
RECENCY_BONUS_HALF_LIFE = 7.0          # 最近访问加成半衰期
IMPORTANCE_DEFAULT = 1.0
ACCESS_BONUS_FACTOR = 0.2              # 访问次数对数加成系数

# 存储路径
SQLITE_DB_PATH = "./data/memory.db"
CHROMA_PERSIST_PATH = "./data/chroma_db"
