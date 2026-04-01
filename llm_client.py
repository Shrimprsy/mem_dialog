import requests
import urllib3
from config import API_URL, API_KEY, CHAT_MODEL, SUMMARY_MODEL, TEMPERATURE, SUMMARY_TEMPERATURE, MAX_SUMMARY_TOKENS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _call_llm(messages, model=CHAT_MODEL, temperature=TEMPERATURE, max_tokens=None):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    try:
        response = requests.post(API_URL, headers=headers, json=payload, verify=False, timeout=15)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"LLM API 调用失败: {e}") from e

def chat_completion(messages):
    return _call_llm(messages, model=CHAT_MODEL, temperature=TEMPERATURE)

def generate_summary(conversation_text):
    system_prompt = "请用简洁的中文总结以下对话中用户的偏好、事实或关键信息，只输出总结内容，不要添加额外说明。"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": conversation_text}
    ]
    return _call_llm(messages, model=SUMMARY_MODEL, temperature=SUMMARY_TEMPERATURE, max_tokens=MAX_SUMMARY_TOKENS)