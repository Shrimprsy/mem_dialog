import os
import streamlit as st

# API 配置
API_URL = "https://api.chatanywhere.tech/v1/chat/completions"
API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")

# 模型参数
CHAT_MODEL = "gpt-3.5-turbo"
SUMMARY_MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.7
SUMMARY_TEMPERATURE = 0.3
MAX_SUMMARY_TOKENS = 150

# 记忆管理参数
BUFFER_LIMIT = 3