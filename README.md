# RAG 智能客服对话系统（Demo）

一个基于 **RAG（检索增强生成）** 的本地可运行智能客服 Demo。用户提问后，系统先从知识库检索相关片段，再交给大模型生成带引用来源的答案。

## 功能特性

- 📚 **RAG 全流程**：文档切分 → 向量化 → 向量检索 → 提示词拼接 → 大模型生成
- 🔌 **OpenAI 兼容接口**：支持 OpenAI / DeepSeek / Azure / 本地 llama.cpp 等任意兼容服务
- 🧩 **零额外依赖向量库**：默认使用 NumPy 余弦检索，开箱即用（附 FAISS 升级说明）
- 🔀 **双向量化后端**：OpenAI Embedding、本地 `sentence-transformers`，以及完全离线的词哈希模式
- 💬 **网页聊天界面**：内置单页前端，可直接对话并查看参考来源
- 🗂️ **多对话窗口**：支持新建、切换、自动命名、重命名、删除，并用浏览器 localStorage 保存记录
- ⚡ **流式输出**：通过 SSE 逐段显示模型回复，Mock 模式也可联调
- 📤 **聊天记录导出**：支持导出当前对话为 TXT 或 JSON
- 🛠️ **管理员知识库**：配置管理员密钥后，可在网页读取、编辑并自动重建索引
- ✅ **无 Key 自测**：内置 Mock 客户端，无需 API Key 也能跑通全链路测试

## 架构示意

```
用户提问
   │
   ▼
前端 (static/) ──POST /chat──▶ FastAPI (app/api.py)
                                   │
                                   ▼
                           文本向量化 (embeddings.py)
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
│   ├── llm_client.py      # Chat 客户端（兼容 OpenAI 接口）
│   ├── embeddings.py      # Embedding 后端（OpenAI / 本地 / 离线）
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

编辑 `.env`，填入你的密钥。

**OpenAI：**只需改这一行即可：

```ini
OPENAI_API_KEY=sk-你的真实key
```

**DeepSeek：**DeepSeek 只提供对话接口，没有 Embedding 接口，因此需要本地向量化：

```ini
OPENAI_API_KEY=sk-你的deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
CHAT_MODEL=deepseek-chat
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
```

并额外安装本地向量化依赖：

```bash
pip install -r requirements-local-embeddings.txt
```

如果当前电脑无法下载模型或不想安装大体积依赖，可使用完全离线的词哈希模式：

```ini
EMBEDDING_PROVIDER=offline
```

> `offline` 适合演示和受限网络，检索主要依据词面相似度；正式使用优先选择 `local`。

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

## 多对话窗口

网页左侧提供对话管理功能：

- 点击 **新建对话** 创建独立的聊天窗口；
- 第一次提问后，系统会自动使用问题生成对话标题；
- 点击左侧会话可随时切换，已有消息和参考来源会一并恢复；
- 支持重命名和删除对话；
- 会话记录保存在当前浏览器的 `localStorage` 中，刷新页面后仍会保留；
- 当前版本为单浏览器本地保存，不同浏览器或设备之间不会同步。

> 新对话只隔离聊天记录，所有会话仍使用同一份 RAG 知识库。

## 流式输出与聊天导出

- 发送问题后，客服回答会逐段显示，而不是等待完整结果后一次性出现；
- 点击顶部 `TXT` 或 `JSON` 按钮，可以导出当前对话及参考来源；
- 流式接口为 `POST /chat/stream`，普通客户端仍可继续使用 `POST /chat`。

## 管理员编辑知识库

1. 在 `.env` 中设置随机管理员密钥：

```ini
ADMIN_TOKEN=请替换为随机长密钥
```

2. 重启服务后，点击网页顶部的齿轮按钮；
3. 输入相同密钥，点击「读取知识库」；
4. 编辑内容后点击「保存并重建索引」。不同主题之间使用空行分隔。

管理员接口：

- `GET /admin/knowledge-base`：读取知识库；
- `PUT /admin/knowledge-base`：保存知识库并自动重建索引；
- 请求头使用 `X-Admin-Token`。

如果没有配置 `ADMIN_TOKEN`，管理接口会保持关闭。生产环境请使用 HTTPS，并且不要把管理员密钥提交到 GitHub。

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

> 如果你已经在 `.env` 中配置了 `EMBEDDING_PROVIDER=local`，测试仍会通过：测试会显式注入 Mock 向量化客户端，不会下载模型。

## 自定义知识库

直接编辑 `data/knowledge_base.txt`，用**空行分隔不同条目**即可。改完后重新运行 `python scripts/ingest.py` 重建索引。

想换模型/参数，改 `.env` 中的 `EMBEDDING_MODEL`、`CHAT_MODEL`、`TOP_K`、`CHUNK_SIZE` 等。

## 升级到 FAISS（可选，更大规模）

`app/vector_store.py` 默认用 NumPy 余弦检索，适合中小知识库。若需更高性能，可安装 `faiss-cpu` 并将 `add / search / save / load` 替换为 FAISS 的 `IndexFlatIP`（配合归一化向量即余弦相似度），接口保持不变。

## 更多文档

- [使用上手文档（给非技术同事）](docs/使用上手文档.md)：三步跑起来、如何维护知识库、常见问题对照表
- [部署指南（本地 → 云端）](docs/部署指南.md)：Docker 部署、Railway/Render/阿里云等通用步骤、上线前安全与稳定性检查

> 想用 Docker 一键部署？项目已附带 `Dockerfile` 与 `.dockerignore`，密钥通过环境变量传入，切勿写进镜像。

## 技术栈

- 后端：FastAPI + Uvicorn
- 向量检索：NumPy（可替换 FAISS）
- 模型调用：OpenAI Python SDK（兼容任意 OpenAI 接口服务）
- 前端：原生 HTML / CSS / JavaScript

## 许可证

[MIT](./LICENSE)
