# memory算法
import time
from llm_client import generate_summary

class MemoryManager:
    def __init__(self, buffer_limit=3):
        self.short_term_buffer = []
        self.buffer_limit = buffer_limit
        self.long_term_db = []

    def add_interaction(self, user_msg, ai_msg):
        self.short_term_buffer.append({"role": "user", "content": user_msg})
        self.short_term_buffer.append({"role": "assistant", "content": ai_msg})

        if len(self.short_term_buffer) / 2 >= self.buffer_limit:
            self._compress_and_store()

    def _compress_and_store(self):
        if not self.short_term_buffer:
            return
        conversation = "\n".join([f"{m['role']}: {m['content']}" for m in self.short_term_buffer])
        try:
            summary = generate_summary(conversation)
        except Exception as e:
            summary = f"[摘要生成失败] 时间: {time.strftime('%H:%M:%S')}，错误: {e}"
        self.long_term_db.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {summary}")
        self.short_term_buffer = []

    def retrieve_relevant_memory(self):
        if not self.long_term_db:
            return "暂无长期记忆。请从零开始了解用户。"
        return "\n".join(self.long_term_db)

    def get_context_for_llm(self):
        long_term_context = self.retrieve_relevant_memory()
        system_prompt = (
            "你是一个具备长期记忆能力的个性化 AI 助手。\n"
            "你的核心能力是理解用户的历史偏好，并结合上下文给出自然的回答。\n"
            "====================\n"
            f"【关于该用户的长期记忆和偏好画像】：\n{long_term_context}\n"
            "====================\n"
            "请严格结合上述长期记忆进行回复。不要暴露你的记忆处理过程。"
        )
        return system_prompt