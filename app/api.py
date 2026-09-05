"""FastAPI 应用：聊天、流式聊天、会话管理和知识库管理接口。"""
import json
import os
from contextlib import asynccontextmanager
from typing import Iterator

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .mock_client import MockLLMClient
from .rag import RAGSystem

# 设置 MOCK=1 可启用本地伪向量和伪流式输出，无需 API Key 联调。
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


app = FastAPI(title="RAG 智能客服对话系统", version="1.1.0", lifespan=lifespan)
rag = RAGSystem(
    llm_client=MockLLMClient() if USE_MOCK else None,
    embedding_client=MockLLMClient() if USE_MOCK else None,
)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=10)


class KnowledgeBaseRequest(BaseModel):
    content: str = Field(min_length=1, max_length=200000)


def ensure_admin(x_admin_token: str | None):
    """管理员接口默认关闭；配置 ADMIN_TOKEN 后才允许写入。"""
    if not config.ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="管理员功能未启用，请先配置 ADMIN_TOKEN")
    if x_admin_token != config.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="管理员密钥无效")


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "index_loaded": rag.store is not None,
        "mock": USE_MOCK,
        "admin_enabled": bool(config.ADMIN_TOKEN),
    }


@app.post("/chat")
def chat(req: ChatRequest):
    if rag.store is None:
        return {
            "answer": "知识库索引尚未构建，请先运行 `python scripts/ingest.py`。",
            "sources": [],
        }
    try:
        return rag.answer(req.query, req.top_k)
    except Exception as e:  # noqa: BLE001
        return {"answer": f"调用模型时出错：{e}", "sources": []}


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """通过 Server-Sent Events 返回 sources、token、done/error 事件。"""
    if rag.store is None:
        return StreamingResponse(
            iter([sse("error", {"message": "知识库索引尚未构建，请先运行 ingest.py。"})]),
            media_type="text/event-stream",
        )

    def generate() -> Iterator[str]:
        try:
            contexts, stream = rag.stream_answer(req.query, req.top_k)
            yield sse("sources", {"sources": contexts})
            for chunk in stream:
                if isinstance(chunk, str):
                    text = chunk
                else:
                    text = getattr(chunk.choices[0].delta, "content", None) or ""
                if text:
                    yield sse("token", {"text": text})
            yield sse("done", {})
        except Exception as e:  # noqa: BLE001
            yield sse("error", {"message": f"调用模型时出错：{e}"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/admin/knowledge-base")
def get_knowledge_base(x_admin_token: str | None = Header(default=None)):
    ensure_admin(x_admin_token)
    with open(config.KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as file:
        return {"content": file.read()}


@app.put("/admin/knowledge-base")
def update_knowledge_base(
    req: KnowledgeBaseRequest,
    x_admin_token: str | None = Header(default=None),
):
    ensure_admin(x_admin_token)
    with open(config.KNOWLEDGE_BASE_PATH, "w", encoding="utf-8", newline="\n") as file:
        file.write(req.content.strip() + "\n")
    try:
        count = rag.build_index()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"知识库已保存，但索引重建失败：{e}") from e
    return {"message": "知识库已保存并重建索引", "chunks": count}


# 静态资源放最后，确保 API 路由优先匹配。
app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
