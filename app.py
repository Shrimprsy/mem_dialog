import streamlit as st
from core.memory_manager import MemoryManager
from core.storage import MemoryStorage
from llm_client import chat_completion
from config import BUFFER_LIMIT

st.set_page_config(page_title="AI 长期记忆 Demo", page_icon="🧠", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None

storage = MemoryStorage()

def login_page():
    st.title("🧠 长期记忆助手 - 登录")
    tab1, tab2 = st.tabs(["登录", "注册"])
    with tab1:
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        if st.button("登录"):
            user_id = storage.authenticate_user(username, password)
            if user_id:
                st.session_state.authenticated = True
                st.session_state.user_id = user_id
                st.session_state.username = username
                st.success("登录成功！")
                st.rerun()
            else:
                st.error("用户名或密码错误")
    with tab2:
        new_username = st.text_input("新用户名", key="reg_username")
        new_password = st.text_input("新密码", type="password", key="reg_password")
        confirm_password = st.text_input("确认密码", type="password", key="reg_confirm")
        if st.button("注册"):
            if new_password != confirm_password:
                st.error("两次密码输入不一致")
            elif len(new_username) < 3:
                st.error("用户名至少3位")
            else:
                user_id = storage.create_user(new_username, new_password)
                if user_id:
                    st.success("注册成功！请登录")
                else:
                    st.error("用户名已存在")

def main_app():
    st.title(f"🧠 长期记忆助手 - 欢迎 {st.session_state.username}")

    if "memory_manager" not in st.session_state:
        st.session_state.memory_manager = MemoryManager(
            user_id=st.session_state.user_id,
            buffer_limit=BUFFER_LIMIT
        )
        st.session_state.messages = st.session_state.memory_manager.working_memory.copy()
    else:
        if not st.session_state.messages:
            st.session_state.messages = st.session_state.memory_manager.working_memory.copy()

    mm = st.session_state.memory_manager

    with st.sidebar:
        st.header(f"👤 {st.session_state.username} 的记忆状态")
        if st.button("退出登录"):
            for key in ["authenticated", "user_id", "username", "memory_manager", "messages"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        st.markdown("---")
        cursor = mm.storage.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM episodic_memories WHERE user_id = ?", (st.session_state.user_id,))
        ep_count = cursor.fetchone()[0]
        st.metric("情节记忆", ep_count)
        cursor.execute("SELECT COUNT(*) FROM semantic_memories WHERE user_id = ?", (st.session_state.user_id,))
        sem_count = cursor.fetchone()[0]
        st.metric("语义记忆", sem_count)
        wm_len = len(mm.working_memory)
        st.metric("工作记忆消息数", wm_len)
        st.progress(wm_len / 50, text=f"工作记忆容量: {wm_len}/50")
        st.caption(f"已压缩轮数: {mm.compressed_rounds}")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("输入你想探讨的内容..."):
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        system_prompt = mm.get_context_for_llm(user_input)
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(mm.working_memory[-6:])
        api_messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤔 检索记忆与思考中...")
            try:
                response = chat_completion(api_messages)
                message_placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                mm.add_interaction(user_input, response)
            except Exception as e:
                error_msg = f"⚠️ 调用出错: {e}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.rerun()

if st.session_state.authenticated:
    main_app()
else:
    login_page()