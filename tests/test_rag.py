"""无 Key 自测：用 Mock 客户端验证切分 / 建库 / 检索 / HTTP 接口全链路。"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag import RAGSystem, chunk_text
from app.mock_client import MockLLMClient
from app import api
from fastapi.testclient import TestClient


def test_chunk_text():
    chunks = chunk_text(
        "第一句。第二句很长很长很长很长很长很长很长很长很长很长。第三句。", 20, 5
    )
    assert len(chunks) >= 1
    assert all(isinstance(c, str) and c for c in chunks)


def test_rag_build_and_retrieve():
    rag = RAGSystem(llm_client=MockLLMClient())
    n = rag.build_index()
    assert n > 0
    assert os.path.exists(api.config.CHUNKS_PATH)

    rag2 = RAGSystem(llm_client=MockLLMClient())
    rag2.load_index()
    res = rag2.answer("怎么退款")
    assert res["answer"]
    assert len(res["sources"]) > 0
    # 检索结果中应包含与“退款”相关的片段
    assert any("退款" in s for s in res["sources"])


def test_api_endpoint():
    rag = RAGSystem(llm_client=MockLLMClient())
    rag.build_index()
    api.rag = rag  # 注入已构建索引的实例
    client = TestClient(api.app)

    r = client.get("/health")
    assert r.status_code == 200

    r = client.post("/chat", json={"query": "退款政策是什么"})
    assert r.status_code == 200
    body = r.json()
    assert "answer" in body and body["answer"]
