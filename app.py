# 前端
import streamlit as st
from memory import MemoryManager
from llm_client import chat_completion
from config import BUFFER_LIMIT
st.set_page_config(page_title="AI 长期记忆 Demo", page_icon="🧠", layout="wide")
st.title("🧠 具备长期记忆的 AI 助手 (模块化版)")

if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = MemoryManager(buffer_limit=BUFFER_LIMIT)
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("🗂️ 记忆状态监控")
    st.markdown("---")
    st.subheader("📚 长期记忆库")
    if not st.session_state.memory_manager.long_term_db:
        st.info("空空如也，多聊几句试试吧。")
    else:
        for i, mem in enumerate(st.session_state.memory_manager.long_term_db):
            st.success(f"记录 {i+1}: {mem}")
    st.markdown("---")
    st.subheader("⏱️ 短期缓存区")
    current_turns = len(st.session_state.memory_manager.short_term_buffer) // 2
    limit = st.session_state.memory_manager.buffer_limit
    st.progress(current_turns / limit, text=f"当前对话轮数: {current_turns} / {limit}")
    if current_turns >= limit:
        st.warning("即将触发记忆压缩机制...")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("输入你想探讨的内容..."):
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    system_prompt = st.session_state.memory_manager.get_context_for_llm()
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(st.session_state.memory_manager.short_term_buffer)
    api_messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 检索记忆与思考中...")
        try:
            real_response = chat_completion(api_messages)
            message_placeholder.markdown(real_response)
            st.session_state.messages.append({"role": "assistant", "content": real_response})
            st.session_state.memory_manager.add_interaction(user_input, real_response)
        except Exception as e:
            error_msg = f"⚠️ 调用出错: {e}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    st.rerun()