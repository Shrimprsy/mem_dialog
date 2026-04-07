import streamlit as st
import os
from dotenv import load_dotenv
from memory import MemoryManager
from llm_client import chat_completion
from config import BUFFER_LIMIT

# 加载环境变量
load_dotenv()

st.set_page_config(page_title="AI 长期记忆 Demo (LightMem版)", page_icon="🧠", layout="wide")
st.title("🧠 具备长期记忆的 AI 助手 (LightMem增强版)")

if "memory_manager" not in st.session_state:
    st.session_state.memory_manager = MemoryManager(buffer_limit=BUFFER_LIMIT)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 侧边栏 - 记忆状态监控
with st.sidebar:
    st.header("🗂️ 记忆状态监控")
    st.markdown("---")

    # 记忆统计
    stats = st.session_state.memory_manager.get_memory_stats()
    st.subheader("📊 统计信息")
    col1, col2 = st.columns(2)
    col1.metric("总记忆数", stats["total_memories"])
    col2.metric("短期缓冲", f"{stats['buffer_turns']}/{stats['buffer_limit']}")

    st.markdown("---")

    # 长期记忆库
    st.subheader("📚 长期记忆库")
    mem_manager = st.session_state.memory_manager

    # 搜索框
    search_query = st.text_input("🔍 搜索记忆", placeholder="输入关键词查找记忆...")
    search_button = st.button("搜索")

    # 显示记忆
    memories_to_show = []
    if search_button and search_query:
        memories_to_show = mem_manager.retrieve(search_query, top_k=5)
        st.success(f"找到 {len(memories_to_show)} 条相关记忆")
    elif not mem_manager.long_term_db:
        st.info("空空如也，多聊几句试试吧。")
    else:
        mem_manager.retrieve(search_query, top_k=5)  # 只是为了显示

        # 滚动显示记忆
        with st.container():
            for mem in mem_manager.long_term_db:
                with st.expander(f"📅 {mem.timestamp}"):
                    st.write(mem.content)

                    # 显示元数据
                    if mem.keywords:
                        st.caption(f"🏷️ 关键词: {', '.join(mem.keywords)}")
                    if mem.entities:
                        # entities 是字典列表，需要转成字符串
                        entity_names = [e.get('name', e) if isinstance(e, dict) else str(e) for e in mem.entities]
                        st.caption(f"👤 实体: {', '.join(entity_names)}")

    st.markdown("---")

    # 缓冲区状态
    current_turns = len(mem_manager.short_term_buffer) // 2
    limit = mem_manager.buffer_limit

    st.subheader("⏱️ 短期缓存区")
    progress = current_turns / limit if limit > 0 else 0
    st.progress(progress, text=f"当前对话轮数: {current_turns} / {limit}")

    if current_turns >= limit:
        st.warning("即将触发记忆压缩机制...")

    st.markdown("---")

    # 操作按钮
    st.subheader("⚙️ 操作")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📋 复制记忆"):
            memory_list = [f"[{mem.timestamp}] {mem.content}" for mem in mem_manager.long_term_db]
            st.session_state.copied_memories = "\n\n".join(memory_list)

    with col2:
        if st.button("🗑️ 清空记忆"):
            mem_manager.long_term_db = []
            mem_manager.short_term_buffer = []
            mem_manager.save_vector_store()
            st.rerun()

    # 复制的内容
    if "copied_memories" in st.session_state:
        st.info(st.session_state.copied_memories)
        st.button("关闭", on_click=lambda: st.session_state.pop("copied_memories"))


# 主对话区
st.markdown("---")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("输入你想探讨的内容..."):
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 获取上下文
    system_prompt = mem_manager.get_context_for_llm(user_input)
    api_messages = [{"role": "system", "content": system_prompt}]
    api_messages.extend(mem_manager.short_term_buffer)
    api_messages.append({"role": "user", "content": user_input})

    # 显示思考中
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 检索记忆与思考中...")

        try:
            # 调用LLM
            real_response = chat_completion(api_messages)
            message_placeholder.markdown(real_response)

            # 添加到消息历史
            st.session_state.messages.append({"role": "assistant", "content": real_response})

            # 保存到记忆
            mem_manager.add_interaction(user_input, real_response)

        except Exception as e:
            error_msg = f"⚠️ 调用出错: {e}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

    st.rerun()


# 底部信息
st.markdown("---")
st.caption("💡 **提示**: AI会自动记住你的偏好和重要信息。尝试问一些个性化问题，比如 '我的爱好是什么？' 或 '我喜欢什么颜色？'")
