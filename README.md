# RAG 智能客服对话系统（Demo）

一个基于 **RAG（检索增强生成）** 的本地可运行智能客服 Demo。用户提问后，系统先从知识库检索相关片段，再交给大模型生成带引用来源的答案。

## 功能特性

- 📚 **RAG 全流程**：文档切分 → 向量化 → 向量检索 → 提示词拼接 → 大模型生成
- 🔌 **OpenAI 兼容接口**：支持 OpenAI / DeepSeek / Azure / 本地 llama.cpp 等任意兼容服务
- 🧩 **零额外依赖向量库**：默认使用 NumPy 余弦检索，开箱即用（附 FAISS 升级说明）
- 💬 **网页聊天界面**：内置单页前端，可直接对话并查看参考来源
- ✅ **无 Key 自测**：内置 Mock 客户端，无需 API Key 也能跑通全链路测试

## 架构示意

```
用户提问
   │
   ▼
前端 (static/) ──POST /chat──▶ FastAPI (app/api.py)
                                   │
                                   ▼
                           文本向量化 (llm_client.embed)
                                   │
                                   ▼
                           向量检索 (vector_store, Top-K)
                                   │
                                   ▼
                   拼接 Prompt: 系统提示 + 参考资料 + 问题
                                   │
                                   ▼
                           大模型生成 (llm_client.chat)
                                   │
                                   ▼
                        答案 + 引用来源 ──▶ 前端展示
```

## 项目结构

```
rag-customer-service/
├── app/
│   ├── __init__.py
│   ├── config.py          # 配置与路径
│   ├── llm_client.py      # Embedding + Chat 客户端（兼容 OpenAI 接口）
│   ├── vector_store.py    # 向量库（NumPy 余弦检索）
│   ├── rag.py             # RAG 核心管线
│   ├── mock_client.py     # 无 Key 自测用的 Mock 客户端
│   └── api.py             # FastAPI 应用与接口
├── data/
│   └── knowledge_base.txt # 示例知识库（可替换为你自己的内容）
├── static/                # 前端页面（index.html / style.css / app.js）
├── scripts/
│   └── ingest.py          # 构建索引脚本
├── tests/
│   └── test_rag.py        # 无 Key 自测
├── main.py                # 启动入口
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 填写 API Key

```bash
cp .env.example .env
```

编辑 `.env`，填入你的密钥：

```ini
OPENAI_API_KEY=sk-你的真实key
# 可选：如果用 DeepSeek 等，改成对应 BASE_URL，例如：
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# CHAT_MODEL=deepseek-chat
```

> 只需改 `OPENAI_API_KEY` 这一行即可用 OpenAI；其余都有默认值。

### 3. 构建知识库索引

```bash
python scripts/ingest.py
```

### 4. 启动服务

```bash
python main.py
```

浏览器打开 http://127.0.0.1:8000 即可对话。

也可以一步到位（先建库再启动）：

```bash
python main.py --build
```

## 无 Key 联调（可选）

不想填 Key 也能体验前后端连通性：

```bash
MOCK=1 python main.py
```

此时使用本地伪向量，能正常检索并返回 Mock 答案，用于验证接口与界面。

## 运行自测

```bash
pytest -q
```

测试覆盖：文本切分、索引构建、向量检索、HTTP 接口，全程使用 Mock 客户端，无需任何 API Key。

## 自定义知识库

直接编辑 `data/knowledge_base.txt`，用**空行分隔不同条目**即可。改完后重新运行 `python scripts/ingest.py` 重建索引。

想换模型/参数，改 `.env` 中的 `EMBEDDING_MODEL`、`CHAT_MODEL`、`TOP_K`、`CHUNK_SIZE` 等。

## 升级到 FAISS（可选，更大规模）

`app/vector_store.py` 默认用 NumPy 余弦检索，适合中小知识库。若需更高性能，可安装 `faiss-cpu` 并将 `add / search / save / load` 替换为 FAISS 的 `IndexFlatIP`（配合归一化向量即余弦相似度），接口保持不变。

## 技术栈

- 后端：FastAPI + Uvicorn
- 向量检索：NumPy（可替换 FAISS）
- 模型调用：OpenAI Python SDK（兼容任意 OpenAI 接口服务）
- 前端：原生 HTML / CSS / JavaScript

## 许可证

[MIT](./LICENSE)
