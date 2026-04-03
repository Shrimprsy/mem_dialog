# mem_dialog
Research on Memory Algorithms

# 短期记忆
暂定默认存储3轮的用户和 AI 原始对话
每轮对话都会追加到短期缓冲区

# 长期记忆
当短期缓冲区达到3轮后，触发压缩：
将短期内的所有对话拼接成文本
调用 LLM（通过 generate_summary）生成摘要，提取用户偏好、事实或关键信息
将摘要（带时间戳）存入 long_term_db 列表
清空短期缓冲区，释放“工作记忆”空间

# 记忆检索与注入
每次用户发送新消息时:
从长期记忆库获取所有历史摘要（当前为全量返回，未来可升级为向量检索）
构造系统提示词，其中包含这些长期记忆
系统提示 + 短期缓冲区的历史对话 + 当前用户输入 → 发送给大模型
# 安装依赖
'pip install streamlit requests python-dotenv pip install streamlit requests python-dotenv'

# 密钥配置
在secrets.toml文件种添加你的真实密钥
在config.py种修改你的API_URL
# 运行
'streamlit run app.py'

运行失败尝试绕过PATH问题 'python -m streamlit run app.py'
