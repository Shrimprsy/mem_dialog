"""
mem_dialog + LightMem 整合测试脚本

验证核心功能：
1. 摘要生成
2. 元数据提取
3. 记忆管理器
4. 上下文生成
5. 语义检索
6. 向量化
"""

import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from memory import MemoryManager
from llm_client import generate_summary, extract_metadata

print("=" * 60)
print("mem_dialog + LightMem 整合测试")
print("=" * 60)

# 1. 测试摘要生成
print("\n1. 测试摘要生成")
print("-" * 40)
test_conversation = """
User: 我最喜欢的电影是《星际穿越》，特别是黑洞的场景
Assistant: 《星际穿越》确实是一部很棒的电影，诺兰的视觉效果很震撼。
User: 我也喜欢科幻题材，特别是时间旅行相关的
Assistant: 时间旅行是科幻小说中经典的主题，有很多精彩的代表作。
"""
try:
    summary = generate_summary(test_conversation)
    print(f"✅ 摘要生成成功:")
    print(f"   {summary}")
except Exception as e:
    print(f"❌ 摘要生成失败: {e}")

# 2. 测试元数据提取
print("\n2. 测试元数据提取")
print("-" * 40)
try:
    metadata = extract_metadata(
        [{"role": "user", "content": test_conversation}],
        threshold=0.5
    )
    print(f"✅ 元数据提取成功:")
    print(f"   关键词: {metadata.get('keywords', [])}")
    print(f"   实体: {metadata.get('entities', [])}")
except Exception as e:
    print(f"❌ 元数据提取失败: {e}")

# 3. 测试记忆管理器
print("\n3. 测试记忆管理器")
print("-" * 40)
try:
    manager = MemoryManager(buffer_limit=3)

    # 添加几轮对话
    manager.add_interaction("我喜欢编程", "编程很有趣，可以创造很多东西")
    manager.add_interaction("Python是我的主要语言", "Python确实很强大，适合数据处理")
    manager.add_interaction("我也用JavaScript", "JavaScript可以用于Web开发")

    print(f"✅ 记忆添加成功")
    print(f"   长期记忆数: {len(manager.long_term_db)}")
    print(f"   短期缓冲: {len(manager.short_term_buffer) // 2}轮")

except Exception as e:
    print(f"❌ 记忆管理器测试失败: {e}")

# 4. 测试上下文生成
print("\n4. 测试上下文生成")
print("-" * 40)
try:
    manager = MemoryManager(buffer_limit=3)
    manager.add_interaction("我喜欢编程", "编程很有趣")
    manager.add_interaction("Python是我的主要语言", "Python很强大")

    context = manager.get_context_for_llm("我擅长什么？")
    print(f"✅ 上下文生成成功")
    print(f"   上下文长度: {len(context)} 字符")
    print(f"   前200字符: {context[:200]}...")

except Exception as e:
    print(f"❌ 上下文生成失败: {e}")

# 5. 测试语义检索
print("\n5. 测试语义检索")
print("-" * 40)
try:
    manager = MemoryManager(buffer_limit=3)
    manager.add_interaction("我喜欢编程", "编程很有趣")
    manager.add_interaction("Python是我的主要语言", "Python很强大")

    # 检索相关记忆
    results = manager.retrieve("编程技能", top_k=2)
    print(f"✅ 语义检索成功")
    print(f"   找到 {len(results)} 条相关记忆:")
    for i, mem in enumerate(results, 1):
        print(f"   {i}. {mem.content[:50]}...")

except Exception as e:
    print(f"❌ 语义检索失败: {e}")

# 6. 测试统计信息
print("\n6. 测试统计信息")
print("-" * 40)
try:
    manager = MemoryManager(buffer_limit=3)
    manager.add_interaction("测试消息1", "测试回复1")
    manager.add_interaction("测试消息2", "测试回复2")

    stats = manager.get_memory_stats()
    print(f"✅ 统计信息获取成功")
    print(f"   {stats}")

except Exception as e:
    print(f"❌ 统计信息失败: {e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
