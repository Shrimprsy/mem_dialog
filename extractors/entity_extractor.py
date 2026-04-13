import json
from datetime import datetime
from typing import Dict, List
from llm_client import chat_completion

class EntityExtractor:
    def __init__(self):
        pass

    def extract_from_conversation(self, messages: List[Dict]) -> Dict:
        prompt = """
请从以下对话中提取结构化信息，严格按 JSON 格式返回，包含字段：
- time_context: 对话发生的时间段（如"上午"、"下午"、"晚上"），以及对话中提及的事件时间（字符串）
- locations: 提及的城市或具体地点（数组）
- persons: 提及的人物全名（数组）
- emotions: 用户的情绪倾向，只能是 "positive", "neutral", "negative" 之一
- topics: 对话涉及的主题关键词（数组，每项不超过5字）
- key_facts: 从对话中提取的事实性陈述（数组，每条简洁）
- user_preferences: 用户表达的偏好或习惯（数组）

只返回有效的 JSON，不要有其他文字。
"""
        conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        response = chat_completion([
            {"role": "system", "content": prompt},
            {"role": "user", "content": conv_text}
        ])

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                metadata = json.loads(json_str)
            else:
                metadata = {}
        except:
            metadata = {"error": "Parse failed", "raw": response}

        tags = {}
        for field in ["locations", "persons", "topics"]:
            if field in metadata and metadata[field]:
                tags[field.rstrip('s')] = metadata[field]
        if "emotions" in metadata:
            tags["emotion"] = metadata["emotions"]

        metadata["tags"] = tags
        metadata["extracted_at"] = datetime.now().isoformat()
        return metadata