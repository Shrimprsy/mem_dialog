import requests
import urllib3
import base64
import time
import hmac
import hashlib
import json
import ssl
from requests.adapters import HTTPAdapter
from config import (
    API_URL, API_KEY, CHAT_MODEL, SUMMARY_MODEL,
    EMBEDDING_MODEL, TEMPERATURE, SUMMARY_TEMPERATURE,
    EMBEDDING_TEMPERATURE
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局禁用SSL验证（解决某些代理平台的TLS兼容问题）
try:
    _old_create_default_https_context = ssl._create_default_https_context
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass


def generate_zhipuai_token(api_key, exp_seconds=3600):
    """
    生成智谱AI的JWT token

    Args:
        api_key: 智谱AI API Key，格式为 "id.secret"
        exp_seconds: token过期时间（秒），默认3600秒

    Returns:
        JWT token字符串
    """
    if '.' not in api_key:
        raise ValueError("Invalid ZhipuAI API key format. Expected 'id.secret' format")

    # 分离id和secret
    id_str, secret_str = api_key.split('.', 1)

    # Base64编码
    id_encoded = base64.urlsafe_b64encode(id_str.encode('utf-8')).decode('utf-8').rstrip('=')
    secret_encoded = base64.urlsafe_b64encode(secret_str.encode('utf-8')).decode('utf-8').rstrip('=')

    # 当前时间戳和过期时间戳
    now = int(time.time())
    exp = now + exp_seconds

    # 构建payload
    payload = {
        'api_key': id_encoded,
        'exp': exp,
        'timestamp': now
    }

    # JWT header
    header = {
        'alg': 'HS256',
        'sign_type': 'SIGN'
    }

    # Base64编码header和payload
    header_encoded = base64.urlsafe_b64encode(json.dumps(header, separators=(',', ':')).encode('utf-8')).decode('utf-8').rstrip('=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8')).decode('utf-8').rstrip('=')

    # 生成签名
    message = f'{header_encoded}.{payload_encoded}'.encode('utf-8')
    secret_bytes = secret_str.encode('utf-8')
    signature = hmac.new(secret_bytes, message, hashlib.sha256).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    # 拼接JWT token
    return f'{header_encoded}.{payload_encoded}.{signature_encoded}'


def _call_llm(messages, model=CHAT_MODEL, temperature=TEMPERATURE, max_tokens=None):
    """调用LLM API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    try:
        response = requests.post(
            f"{API_URL}/chat/completions",
            headers=headers,
            json=payload,
            verify=False,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        if 'error' in result:
            raise RuntimeError(f"API Error: {result['error'].get('message', 'Unknown error')}")

        return result["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"LLM API调用失败: {e}") from e


def chat_completion(messages):
    """标准对话完成"""
    return _call_llm(messages, model=CHAT_MODEL, temperature=TEMPERATURE)


def generate_summary(conversation_text):
    """生成对话摘要 - LightMem核心功能"""
    system_prompt = (
        "请用简洁的中文总结以下对话中用户的偏好、事实或关键信息，"
        "只输出总结内容，不要添加额外说明、引言或结尾。"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": conversation_text}
    ]
    return _call_llm(
        messages,
        model=SUMMARY_MODEL,
        temperature=SUMMARY_TEMPERATURE,
        max_tokens=150
    )


def extract_metadata(messages, threshold=0.5):
    """提取元数据 - LightMem核心功能"""
    # 合并消息文本
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

    system_prompt = (
        f"从以下对话中提取重要信息，提取阈值: {threshold}\n"
        "请提取以下类型的元数据：\n"
        "- 用户偏好和喜好\n"
        "- 事实性信息\n"
        "- 重要决定和目标\n"
        "- 角色关系\n"
        "- 关键技能和知识领域\n\n"
        "用JSON格式返回，格式：{{\"keywords\": [\"keyword1\", \"keyword2\"], \"entities\": [{\"name\": \"实体名\", \"type\": \"类型\"}]}}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": conversation_text}
    ]

    try:
        response = _call_llm(
            messages,
            model=SUMMARY_MODEL,
            temperature=SUMMARY_TEMPERATURE,
            max_tokens=200
        )
        # 尝试解析JSON
        import json
        return json.loads(response)
    except Exception as e:
        return {"keywords": [], "entities": []}


def get_embedding(text):
    """获取文本向量 - LightMem核心功能"""
    if not text or len(text.strip()) == 0:
        return [0.0] * 1536  # ada-002 维度

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        response = requests.post(
            f"{API_URL}/embeddings",
            headers=headers,
            json={
                "model": "text-embedding-ada-002",
                "input": text,
                "encoding_format": "float"
            },
            verify=False,
            timeout=60
        )
        response.raise_for_status()

        # 解析响应
        result = response.json()

        if 'error' in result:
            raise RuntimeError(f"Embedding API Error: {result['error'].get('message', 'Unknown error')}")

        # 提取向量
        embedding = result.get("data", [{}])[0].get("embedding", [])
        return embedding
    except Exception as e:
        raise RuntimeError(f"Embedding生成失败: {e}") from e
