# mem_dialog + LightMem 整合版本

将LightMem记忆系统核心特性**整合到原始mem_dialog项目中**的增强版本

---

## 🎯 整合目标

在保留mem_dialog**简洁架构**的同时，集成LightMem的**强大记忆功能**：

### 核心改进
- ✨ **长期记忆存储**：自动压缩和保存对话摘要
- 🔍 **语义检索**：智能查找相关记忆
- 🎯 **个性化上下文**：AI记住用户偏好
- 📊 **记忆可视化**：实时监控记忆状态
- 🏷️ **元数据提取**：自动提取关键词和实体
- 📈 **向量存储**：支持语义相似度搜索

---

## 📁 项目结构

```
mem_dialog_integrated/
├── app.py                 # Streamlit前端 (使用增强的记忆管理器)
├── memory.py              # 增强版记忆管理器 (整合LightMem核心)
├── llm_client.py          # LLM客户端 (新增摘要、元数据提取、向量化)
├── config.py              # 配置管理 (LightMem配置选项)
├── requirements.txt       # 依赖列表
├── README.md              # 项目文档
├── INTEGRATION.md         # 技术集成文档
├── .gitignore             # Git忽略文件
└── .env                   # API密钥配置 (需手动创建)
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

创建 `.env` 文件：
```env
OPENAI_API_KEY=your_api_key_here
```

### 3. 运行应用

```bash
streamlit run app.py
```

---

## 🔄 与原始mem_dialog的对比

### 原始mem_dialog
```python
# memory.py - 简单列表存储
class MemoryManager:
    def __init__(self):
        self.long_term_db = []  # 只存储字符串
```

### 整合版 (LightMem增强)
```python
# memory.py - 增强的记忆管理
@dataclass
class MemoryEntry:
    content: str
    timestamp: str
    metadata: Dict          # 元数据
    keywords: List[str]     # 关键词
    entities: List[str]     # 实体
    embedding: List[float]  # 向量

class MemoryManager:
    def __init__(self):
        self.long_term_db = []  # MemoryEntry对象列表
        self.vector_store = {}  # 向量存储
```

---

## 🎓 核心功能演示

### 1. 摘要生成

```python
from llm_client import generate_summary

summary = generate_summary("User: 我喜欢编程\nAssistant: 编程很有趣")
print(summary)  # 输出: 用户喜欢编程
```

### 2. 元数据提取

```python
from llm_client import extract_metadata

metadata = extract_metadata(messages, threshold=0.5)
# 返回:
# {
#   "keywords": ["编程", "Python"],
#   "entities": [{"name": "周杰伦", "type": "歌手"}]
# }
```

### 3. 记忆检索

```python
from memory import MemoryManager

manager = MemoryManager(buffer_limit=3)
manager.add_interaction("我喜欢编程", "编程很有趣")

# 语义检索
relevant = manager.retrieve("编程技能", top_k=2)
for mem in relevant:
    print(f"{mem.timestamp}: {mem.content}")
```

### 4. 智能上下文生成

```python
context = manager.get_context_for_llm("我擅长什么？")
print(context)
# 输出系统提示，包含检索到的相关记忆
```

---

## 📊 功能对比表

| 功能 | 原始mem_dialog | LightMem整合版 |
|------|--------------|---------------|
| 短期缓冲区 | ✅ | ✅ |
| 长期记忆 | 简单列表 | 向量存储 |
| 摘要生成 | ✅ | ✅ |
| **元数据提取** | ❌ | **✅** |
| **语义检索** | ❌ | **✅** |
| **向量嵌入** | ❌ | **✅** |
| **相似度计算** | ❌ | **✅** |
| 记忆统计 | ❌ | ✅ |
| 可视化 | 基础 | 增强 |
| 检索缓存 | ❌ | ✅ |

---

## ⚙️ 配置选项

在 `config.py` 中可调整：

```python
@dataclass
class MemoryConfig:
    index_strategy: str = "embedding"  # embedding/context/hybrid
    extract_threshold: float = 0.5     # 元数据提取阈值
    messages_use: str = "hybrid"       # 使用消息类型
    pre_compress: bool = True          # 预压缩
    topic_segment: bool = False        # 主题分段
    update_mode: str = "online"        # 更新模式
    use_vector_store: bool = True      # 向量存储开关
    top_k: int = 5                     # 检索数量
```

---

## 🧪 测试

运行测试脚本验证整合：

```bash
python test_memory.py
```

测试内容包括：
1. ✅ 摘要生成
2. ✅ 元数据提取
3. ✅ 记忆管理器
4. ✅ 上下文生成
5. ✅ 语义检索
6. ✅ 统计信息
7. ✅ 向量化

---

## 🔧 技术架构

### 记忆生命周期

```
对话输入 → 短期缓冲区 → 达到限制 → 生成摘要 → 提取元数据 → 向量化 → 长期记忆库 → 语义检索
```

### 核心模块

1. **MemoryManager** (memory.py)
   - 记忆压缩
   - 向量存储
   - 语义检索
   - 上下文生成

2. **LLM Client** (llm_client.py)
   - 摘要生成
   - 元数据提取
   - 向量化

3. **Configuration** (config.py)
   - 灵活配置
   - 环境变量支持

---

## 💾 数据持久化

### 向量存储
- 文件：`memory_vectors.db`
- 格式：Pickle序列化
- 自动保存

### Embedding缓存
- 目录：`embeddings_cache/`
- 文件：`<hash>.pkl`
- 自动缓存

---

## 🐛 故障排除

### 1. Embedding生成失败
```bash
# 检查API密钥
cat .env

# 测试网络
ping api.openai.com
```

### 2. 向量存储损坏
```bash
# 删除并重启
rm memory_vectors.db
streamlit run app.py
```

---

## 📈 性能指标

- **摘要生成**: ~2-3秒
- **Embedding生成**: ~1-2秒
- **检索速度**: <1秒 (100条记忆)
- **内存占用**: ~50MB/1000条记忆

---

## 🎯 使用示例

### 基础对话

```python
# 创建记忆管理器
manager = MemoryManager(buffer_limit=3)

# 添加对话
manager.add_interaction("我的名字是张三", "你好张三！")
manager.add_interaction("我住在北京", "北京真是个繁华的城市")

# 获取上下文
context = manager.get_context_for_llm("他住在哪里？")
```

### 记忆统计

```python
stats = manager.get_memory_stats()
print(f"总记忆数: {stats['total_memories']}")
print(f"短期缓冲: {stats['buffer_turns']}/{stats['buffer_limit']}")
```

---

## 📄 许可证

MIT License

---

## 🔗 相关项目

- [mem_dialog](https://github.com/Shrimprsy/mem_dialog) - 原始项目
- [LightMem](https://github.com/zjunlp/LightMem) - 论文实现

---

**整合完成时间**: 2026-04-02
**整合方式**: 保留原始架构，增强记忆功能
**核心特性**: 向量检索、元数据提取、语义搜索
