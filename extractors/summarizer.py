from llm_client import generate_summary as llm_generate_summary

def generate_summary(conversation_text: str) -> str:
    return llm_generate_summary(conversation_text)