"""RAG 核心管线：文档切分 → 建库 → 检索 → 生成。"""
import re
from . import config
from .vector_store import VectorStore
from .llm_client import LLMClient
from .embeddings import get_embedding_client

SYSTEM_PROMPT = (
    "你是一个专业、友好的智能客服助手。"
    "请仅根据提供的【参考资料】回答用户问题；"
    "如果参考资料中没有相关信息，请如实说明你无法回答，不要编造内容。"
)


def chunk_text(text, size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    """将知识库文本切分为合适大小的片段。

    先按空行切分为「条目」（通常一个条目对应一个主题），
    若单条超过 size，再按句末标点切分并聚合，长片段之间保留 overlap 重叠。
    """
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return []
    entries = [e.strip() for e in re.split(r"\n\s*\n", text) if e.strip()]
    chunks = []
    for entry in entries:
        if len(entry) <= size:
            chunks.append(entry)
            continue
        units = [u for u in re.split(r"(?<=[。！？.!?])", entry) if u.strip()]
        buf = ""
        for u in units:
            if len(buf) + len(u) <= size:
                buf += u
            else:
                if buf.strip():
                    chunks.append(buf.strip())
                buf = (buf[-overlap:] if overlap > 0 and len(buf) > overlap else "") + u
        if buf.strip():
            chunks.append(buf.strip())
    return chunks


def build_prompt(query, contexts):
    ctx_block = "\n\n".join(
        f"【参考资料 {i + 1}】\n{c}" for i, c in enumerate(contexts)
    )
    return (
        f"以下是知识库中的相关参考资料：\n\n{ctx_block}\n\n"
        f"用户问题：{query}\n\n请基于上述参考资料回答用户问题。"
    )


class RAGSystem:
    def __init__(self, llm_client=None, embedding_client=None):
        # 允许注入自定义客户端（测试时注入 Mock）
        self.llm = llm_client or LLMClient()
        self.store = None
        # 嵌入客户端优先级：显式传入 > 按 EMBEDDING_PROVIDER 配置选择
        # 注意：不再回退到 self.llm.embed，否则会无视 EMBEDDING_PROVIDER 设置，
        # 在 DeepSeek（无 Embedding 接口）等场景下调错接口。
        if embedding_client is not None:
            self.embedder = embedding_client
        else:
            # 仅在 llm 暴露 OpenAI 客户端时透传（Mock 等自定义客户端无需 client）
            openai_client = getattr(self.llm, "client", None)
            self.embedder = get_embedding_client(openai_client)

    def build_index(self, kb_path=config.KNOWLEDGE_BASE_PATH):
        with open(kb_path, "r", encoding="utf-8") as f:
            text = f.read()
        chunks = chunk_text(text)
        vectors = self.embedder.embed(chunks)
        store = VectorStore(len(vectors[0]))
        store.add(vectors, chunks)
        store.save()
        self.store = store
        return len(chunks)

    def load_index(self):
        self.store = VectorStore.load()
        return self.store

    def answer(self, query):
        if self.store is None:
            self.load_index()
        qvec = self.embedder.embed([query])[0]
        contexts = self.store.search(qvec, config.TOP_K)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(query, contexts)},
        ]
        reply = self.llm.chat(messages)
        return {"answer": reply, "sources": contexts}
