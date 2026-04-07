# 技术集成文档

## 整合概述

本文档详细说明如何将LightMem的核心记忆机制**整合到原始mem_dialog项目中**。

---

## 整合策略

### 设计原则

1. **保留原始架构** - 保持mem_dialog的简洁性
2. **模块化增强** - 新功能作为可选模块
3. **向后兼容** - 不破坏原有功能
4. **渐进式增强** - 可选启用新特性

---

## 代码修改清单

### 1. 新增文件

#### `llm_client.py` (新增)
**职责**：扩展LLM客户端功能

**新增函数**：
```python
def generate_summary(conversation_text)
    """生成对话摘要"""

def extract_metadata(messages, threshold=0.5)
    """提取元数据（关键词、实体等）"""

def get_embedding(text)
    """获取文本向量"""
```

**集成点**：
- `app.py` - 用于生成上下文
- `memory.py` - 用于记忆压缩

#### `config.py` (新增)
**职责**：集中管理配置

**新增内容**：
```python
@dataclass
class MemoryConfig:
    index_strategy: str  # 检索策略
    extract_threshold: float  # 元数据提取阈值
    use_vector_store: bool  # 向量存储开关
    top_k: int  # 检索数量
```

#### `test_memory.py` (新增)
**职责**：单元测试

**测试项**：
- 摘要生成
- 元数据提取
- 记忆管理器
- 上下文生成
- 语义检索
- 统计信息
- 向量化

### 2. 修改文件

#### `memory.py` (增强)
**修改内容**：

**之前**：
```python
class MemoryManager:
    def __init__(self):
        self.long_term_db = []  # 简单字符串列表
```

**之后**：
```python
@dataclass
class MemoryEntry:
    content: str
    timestamp: str
    metadata: Dict
    keywords: List[str]
    entities: List[str]
    embedding: List[float]  # 新增

class MemoryManager:
    def __init__(self):
        self.long_term_db = []  # MemoryEntry对象列表
        self.vector_store = {}  # 新增：向量存储
        self.config = config or DEFAULT_MEMORY_CONFIG

    def retrieve(self, query: str, top_k: int)
        # 新增：语义检索

    def get_context_for_llm(self, query: str)
        # 增强：基于查询检索相关记忆
```

**关键新增方法**：
- `_compress_and_store()`: 增强的记忆压缩
- `retrieve()`: 语义检索
- `_cosine_similarity()`: 相似度计算
- `_text_based_retrieve()`: 回退文本检索
- `get_memory_stats()`: 记忆统计

#### `app.py` (最小修改)
**修改内容**：

```python
# 之前
from memory import MemoryManager

# 之后 (相同，但MemoryManager已增强)
from memory import MemoryManager
from config import BUFFER_LIMIT

# 侧边栏增加记忆统计和搜索功能
```

**增加功能**：
- 记忆统计显示
- 记忆搜索
- 元数据展示（关键词、实体）
- 缓冲区状态监控

---

## 核心算法流程

### 记忆压缩流程

```
输入: user_msg, ai_msg
  ↓
1. 添加到短期缓冲区
  ↓
2. 检查缓冲区大小 (BUFFER_LIMIT)
  ↓
3. 生成对话摘要 (generate_summary)
  ↓
4. 提取元数据 (extract_metadata)
   - 关键词
   - 实体
   - 时间戳
  ↓
5. 计算向量 (get_embedding)
  ↓
6. 存储到长期记忆库 (MemoryEntry)
   - content
   - timestamp
   - metadata
   - keywords
   - entities
   - embedding
  ↓
7. 保存向量到向量存储
  ↓
输出: long_term_db 增加 MemoryEntry
```

### 语义检索流程

```
输入: query (用户问题)
  ↓
1. 查询向量化 (get_embedding(query))
  ↓
2. 遍历所有长期记忆
   - 获取每个记忆的向量
  ↓
3. 计算相似度
   - 余弦相似度
   - similarity = dot_product / (norm1 * norm2)
  ↓
4. 排序并筛选
   - 按相似度降序排序
   - 取前 top_k 个
  ↓
5. 返回最相关的记忆
  ↓
输出: List[MemoryEntry]
```

### 上下文生成流程

```
输入: user_msg (当前问题)
  ↓
1. 使用 user_msg 作为查询
  ↓
2. 执行语义检索
   - retrieve(user_msg, top_k=3)
  ↓
3. 构建上下文字符串
   - 【检索到的相关记忆】：每条记忆
   - 【其他历史记忆】：剩余记忆
  ↓
4. 生成系统提示
   - 包含上下文
   - 指导AI使用记忆
  ↓
输出: system_prompt
```

---

## 数据结构

### MemoryEntry 数据类

```python
@dataclass
class MemoryEntry:
    content: str           # 摘要内容
    timestamp: str         # 时间戳 (YYYY-MM-DD HH:MM:SS)
    metadata: Dict         # 元数据字典
    keywords: List[str]    # 关键词列表
    entities: List[str]    # 实体列表
    embedding: List[float] # 向量 (1536维)
```

### 向量存储结构

```python
vector_store = {
    0: {
        "embedding": [0.123, -0.456, ...],  # 1536维向量
        "entry": MemoryEntry(...)           # 对应的记忆条目
    },
    1: {
        "embedding": [...],
        "entry": MemoryEntry(...)
    }
}
```

### 配置结构

```python
@dataclass
class MemoryConfig:
    index_strategy: str = "embedding"      # embedding/context/hybrid
    extract_threshold: float = 0.5         # 元数据提取阈值
    messages_use: str = "hybrid"           # user_only/assistant_only/hybrid
    pre_compress: bool = True              # 预压缩开关
    topic_segment: bool = False            # 主题分段
    update_mode: str = "online"            # online/offline
    use_vector_store: bool = True          # 向量存储开关
    top_k: int = 5                         # 检索数量
    retrieve_strategy: str = "embedding"   # 检索策略
```

---

## 集成要点

### 1. 向后兼容

```python
# 旧的调用方式仍然有效
manager = MemoryManager()
manager.add_interaction("msg1", "reply1")
# 效果相同，但内部现在使用增强功能
```

### 2. 可选功能

```python
# 禁用向量存储
manager = MemoryManager(
    config=MemoryConfig(use_vector_store=False)
)

# 禁用元数据提取
manager = MemoryManager(
    config=MemoryConfig(extract_threshold=1.0)  # 不提取
)
```

### 3. 错误处理

```python
# Embedding生成失败时的回退
if not self.config.use_vector_store or not self.long_term_db[0].embedding:
    return self._text_based_retrieve(query, top_k)  # 回退到文本检索
```

---

## 性能优化

### 1. 向量缓存

```python
# 自动缓存已处理的文本
def get_embedding(text):
    cache_key = hash(text)
    if cache_key in cache:
        return cached_embedding
    embedding = generate_embedding(text)
    save_to_cache(cache_key, embedding)
    return embedding
```

### 2. 批量检索

```python
# 预加载所有记忆到检索器
def _preload_memories(self):
    for idx, entry in enumerate(self.long_term_db):
        retriever.add_document(f"mem_{idx}", entry.content)
```

### 3. 延迟计算

```python
# 只在需要时计算向量
if self.config.use_vector_store:
    memory_entry.embedding = get_embedding(summary)
```

---

## 测试策略

### 单元测试

```bash
python test_memory.py
```

### 测试覆盖

1. **摘要生成**
   - 输入对话
   - 输出简洁摘要

2. **元数据提取**
   - 输入对话
   - 输出关键词和实体

3. **记忆管理**
   - 添加对话
   - 压缩记忆
   - 验证存储

4. **语义检索**
   - 查询记忆
   - 验证相似度排序

5. **上下文生成**
   - 输入查询
   - 输出系统提示

### 集成测试

```python
# 完整流程测试
manager = MemoryManager(buffer_limit=3)
manager.add_interaction("我喜欢Python", "Python很好")
manager.add_interaction("我会编程", "编程很实用")

# 检索相关记忆
results = manager.retrieve("编程语言", top_k=2)
assert len(results) > 0

# 获取统计
stats = manager.get_memory_stats()
assert stats["total_memories"] == 1
```

---

## 部署建议

### 开发环境

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
echo "OPENAI_API_KEY=your_key" > .env

# 3. 运行
streamlit run app.py
```

### 生产环境

```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 设置环境变量
export OPENAI_API_KEY="your_key"

# 生产运行
streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true
```

---

## 扩展方向

### 短期扩展

1. **主题分段** - 按主题组织记忆
2. **时间衰减** - 老记忆权重降低
3. **用户分组** - 不同用户的记忆隔离

### 长期扩展

1. **多模态支持** - 图像、音频记忆
2. **图存储** - 记忆关系图谱
3. **持久化数据库** - 替代文件存储
4. **分布式检索** - 跨服务器共享

---

## 已知限制

1. **API依赖** - 需要OpenAI兼容的API
2. **向量维度** - 固定1536维（取决于embedding模型）
3. **内存占用** - 大量记忆会增加内存使用
4. **网络要求** - 需要访问API

---

## 故障排除

### 问题1: Embedding失败

**症状**: 元数据提取或检索失败

**解决**:
```bash
# 检查API密钥
cat .env

# 测试API连接
python -c "from llm_client import get_embedding; print(get_embedding('test'))"
```

### 问题2: 向量存储损坏

**症状**: 应用启动失败或功能异常

**解决**:
```bash
# 删除向量存储
rm memory_vectors.db

# 重启应用
streamlit run app.py
```

### 问题3: 性能问题

**症状**: 检索速度慢

**解决**:
```python
# 减少检索数量
manager = MemoryManager(config=MemoryConfig(top_k=3))

# 禁用向量存储（回退到文本检索）
manager = MemoryManager(config=MemoryConfig(use_vector_store=False))
```

---

**版本**: 1.0
**日期**: 2026-04-02
**作者**: Claude Code
