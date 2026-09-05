"""Embedding 后端：OpenAI 兼容接口 / 本地 sentence-transformers / 离线词哈希。

部分服务（如 DeepSeek）只提供对话接口、没有 Embedding 接口。
此时把 EMBEDDING_PROVIDER 设为 local（本地 sentence-transformers 向量化），
对话仍走你配置的 OPENAI_BASE_URL（DeepSeek 等）。

若运行环境无法下载模型（内网/防火墙/无外网），可设为 offline：
使用词哈希（feature hashing）在完全离线、零额外依赖下完成向量化，
适合快速演示或受限网络。检索质量以「词面相似度」为主。
"""
import hashlib
import re

from . import config


class OpenAIEmbeddingClient:
    def __init__(self, client):
        self.client = client

    def embed(self, texts):
        resp = self.client.embeddings.create(model=config.EMBEDDING_MODEL, input=texts)
        return [item.embedding for item in resp.data]


class LocalEmbeddingClient:
    def __init__(self):
        # 延迟加载：构造时不 import sentence_transformers，
        # 避免无该依赖（未安装本地向量化包）时连「导入」都失败。
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(config.EMBEDDING_MODEL)
        return self._model

    def embed(self, texts):
        vectors = self._get_model().encode(texts, normalize_embeddings=True)
        return vectors.tolist()


class HashEmbeddingClient:
    """零依赖、可离线运行的词哈希（feature hashing）向量化。

    无需下载任何模型权重，基于字符与词元的哈希特征生成向量，
    相似文本会得到相近向量（词面相似度）。适合内网环境或快速演示。
    """

    DIM = 512

    def __init__(self, dim: int = DIM):
        self.dim = dim

    def _features(self, text):
        text = (text or "").lower()
        feats = set()
        # 英文 / 数字词元
        for tok in re.findall(r"[a-z0-9]+", text):
            feats.add(tok)
        # 中文连续段：单字 + bigram + trigram
        for cjk in re.findall(r"[一-鿿]+", text):
            for ch in cjk:
                feats.add("c:" + ch)
            for n in (2, 3):
                for i in range(len(cjk) - n + 1):
                    feats.add(f"g{n}:" + cjk[i : i + n])
        return feats

    def _vector(self, text):
        vec = [0.0] * self.dim
        for f in self._features(text):
            h = hashlib.md5(f.encode("utf-8")).hexdigest()
            idx = int(h, 16) % self.dim
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, texts):
        return [self._vector(t) for t in texts]


def get_embedding_client(openai_client=None):
    """按配置返回对应的 Embedding 客户端。"""
    provider = (config.EMBEDDING_PROVIDER or "openai").lower()
    if provider in ("offline", "hash", "local_hash"):
        return HashEmbeddingClient()
    if provider == "local":
        return LocalEmbeddingClient()
    # 默认走 OpenAI 兼容接口
    if openai_client is None:
        from openai import OpenAI

        openai_client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)
    return OpenAIEmbeddingClient(openai_client)
