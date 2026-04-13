# API 配置
import os
import streamlit as st

# ========== DeepSeek API 配置 ==========
API_URL = "https://api.chatanywhere.tech/v1/chat/completions"
EMBEDDING_API_URL = "https://api.chatanywhere.tech/v1/embeddings"  # 新增
API_KEY = os.getenv("DEEPSEEK_API_KEY") or st.secrets.get("DEEPSEEK_API_KEY", "")

# ========== 模型参数 ==========
CHAT_MODEL = "deepseek-v3.2"           # 对话模型
SUMMARY_MODEL = "deepseek-v3.2"        # 摘要模型
TEMPERATURE = 0.7
SUMMARY_TEMPERATURE = 0.3
MAX_SUMMARY_TOKENS = 150

# ========== Embedding 配置 ==========
EMBEDDING_MODEL = "text-embedding-ada-002"  # DeepSeek Embedding 模型名称

# 是否使用本地 Embedding 模型（您希望使用 API，因此设为 False）
USE_LOCAL_EMBEDDING = False

# 本地模型路径（虽然您不用本地模型，但变量必须存在，此处仅作占位）
LOCAL_EMBEDDING_PATH = "paraphrase-multilingual-MiniLM-L12-v2"

# ========== 记忆管理参数 ==========
BUFFER_LIMIT = 3