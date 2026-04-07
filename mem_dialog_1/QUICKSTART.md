# 快速开始指南 - 5分钟上手

## 🚀 开始使用

### 第一步：安装依赖

```bash
cd mem_dialog_integrated
pip install -r requirements.txt
```

### 第二步：配置API密钥

创建 `.env` 文件：

```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

**获取API密钥**:
1. 访问 https://platform.openai.com/api-keys
2. 登录并创建新密钥
3. 将密钥复制到 `.env` 文件

### 第三步：运行测试

```bash
python test_memory.py
```

预期输出：
```
==================================================
mem_dialog + LightMem 整合测试
==================================================

1. 测试摘要生成
--------------------------------------------------
✅ 摘要生成成功:
   用户喜欢科幻电影，特别是《星际穿越》...

2. 测试元数据提取
--------------------------------------------------
✅ 元数据提取成功:
   关键词: ['科幻', '电影', '星际穿越']
   实体: [...]

...
==================================================
测试完成
==================================================
```

### 第四步：启动应用

```bash
streamlit run app.py
```

打开浏览器访问: http://localhost:8501

---

## 🎯 核心功能演示

### 1. 基础对话

在左侧输入框输入：
```
我喜欢编程，特别是Python
```

继续对话：
```
Python有哪些优势？
```

### 2. 测试记忆

AI会自动记住你的对话：
```
我喜欢什么？
```

AI会基于对话历史回答。

### 3. 查看记忆

在侧边栏查看：
- 📚 **长期记忆库** - 所有已存储的记忆
- 📊 **统计信息** - 记忆数量和缓冲区状态
- 🔍 **搜索记忆** - 查找特定记忆

---

## 📝 代码示例

### Python脚本测试

创建 `test.py`:
```python
from memory import MemoryManager

# 创建记忆管理器
manager = MemoryManager(buffer_limit=3)

# 添加对话
manager.add_interaction("我的名字是张三", "你好张三！")
manager.add_interaction("我住在北京", "北京真繁华")

# 检索记忆
relevant = manager.retrieve("用户住在哪里？", top_k=2)
for mem in relevant:
    print(f"[{mem.timestamp}] {mem.content}")

# 获取统计
stats = manager.get_memory_stats()
print(f"总记忆数: {stats['total_memories']}")
```

运行：
```bash
python test.py
```

---

## ⚙️ 常用配置

### 修改缓冲区大小

编辑 `config.py`:
```python
BUFFER_LIMIT = 5  # 5轮对话后压缩
```

### 禁用向量存储

编辑 `config.py`:
```python
MemoryConfig(
    use_vector_store=False  # 禁用
)
```

### 切换检索策略

编辑 `config.py`:
```python
MemoryConfig(
    index_strategy="hybrid"  # embedding, context, hybrid
)
```

---

## 🔧 故障排除

### 问题1: API调用失败

**错误**: `RuntimeError: LLM API调用失败`

**解决**:
```bash
# 1. 检查.env文件
cat .env

# 2. 测试网络
ping api.openai.com

# 3. 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 问题2: Embedding失败

**错误**: `RuntimeError: Embedding生成失败`

**解决**:
```bash
# 1. 检查API密钥是否有效
echo "OPENAI_API_KEY=your_key" > .env

# 2. 清除缓存
rm -rf embeddings_cache/

# 3. 重启应用
streamlit run app.py --server.headless=true
```

### 问题3: 导入错误

**错误**: `ModuleNotFoundError`

**解决**:
```bash
# 1. 确保在正确目录
cd mem_dialog_integrated

# 2. 重新安装
pip install -r requirements.txt

# 3. 清除Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
```

---

## 📊 性能优化

### 减少API调用

编辑 `config.py`:
```python
MemoryConfig(
    use_vector_store=False  # 禁用，减少API调用
)
```

### 减少检索数量

编辑 `config.py`:
```python
MemoryConfig(
    top_k=3  # 从5减少到3
)
```

### 增大缓冲区

编辑 `config.py`:
```python
BUFFER_LIMIT = 5  # 增加到5
```

---

## 🎓 学习资源

### 文档

- **README.md** - 项目介绍
- **TECHNICAL.md** - 技术细节
- **INTEGRATION_REPORT.md** - 整合报告

### 相关项目

- [mem_dialog](https://github.com/Shrimprsy/mem_dialog)
- [LightMem](https://github.com/zjunlp/LightMem)

---

## 💡 提示

1. **首次使用**: 需要几秒钟初始化
2. **记忆压缩**: 每3轮对话自动压缩
3. **向量存储**: 自动保存在 `memory_vectors.db`
4. **嵌入缓存**: 保存在 `embeddings_cache/`
5. **错误恢复**: 删除 `memory_vectors.db` 可修复损坏

---

## ✅ 检查清单

在使用前，确保：

- [ ] 已安装Python 3.8+
- [ ] 已安装requirements.txt依赖
- [ ] 已创建.env文件
- [ ] 已配置有效的API密钥
- [ ] 已运行test_memory.py测试
- [ ] 已启动streamlit应用

---

**准备好开始了吗？**

```bash
cd mem_dialog_integrated
python test_memory.py
streamlit run app.py
```

---

**需要帮助？** 查看 `TECHNICAL.md` 获取详细技术文档
