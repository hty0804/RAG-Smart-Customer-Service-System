"""FastAPI 应用：提供 /chat、/health 接口，并托管前端静态页面。"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import config
from .rag import RAGSystem
from .mock_client import MockLLMClient

# 设置环境变量 MOCK=1 可启用本地伪向量，无需 API Key 即可联调前端与服务。
USE_MOCK = os.getenv("MOCK", "0") == "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if USE_MOCK:
        try:
            rag.build_index()
            print("[MOCK] 已使用本地伪向量构建索引，无需 API Key 即可联调。")
        except Exception as e:  # noqa: BLE001
            print(f"[MOCK] 构建索引失败: {e}")
        yield
        return
    try:
        rag.load_index()
        print("✅ 已加载知识库索引。")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  未检测到索引文件，请先运行 `python scripts/ingest.py`：{e}")
    yield


app = FastAPI(title="RAG 智能客服对话系统", version="1.0.0", lifespan=lifespan)
rag = RAGSystem(llm_client=MockLLMClient() if USE_MOCK else None)


class ChatRequest(BaseModel):
    query: str
    top_k: int | None = None


@app.get("/health")
def health():
    return {"status": "ok", "index_loaded": rag.store is not None, "mock": USE_MOCK}


@app.post("/chat")
def chat(req: ChatRequest):
    if rag.store is None:
        return {
            "answer": "知识库索引尚未构建，请先运行 `python scripts/ingest.py`。",
            "sources": [],
        }
    try:
        result = rag.answer(req.query)
        return result
    except Exception as e:  # noqa: BLE001
        return {"answer": f"调用模型时出错：{e}", "sources": []}


# 挂载静态资源，放在最后，确保 /chat、/health 等 API 优先匹配。
app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
