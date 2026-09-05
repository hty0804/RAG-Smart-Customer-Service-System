"""向量库：基于 NumPy 的余弦相似度检索（零额外依赖，适合 demo）。

如需更大规模 / 更高性能，可替换为 FAISS：
    import faiss
    index = faiss.IndexFlatIP(dim)  # 配合归一化向量即余弦相似度
其余接口保持一致即可，仅需改 add / search / save / load 的实现。
"""
import json
import numpy as np
from . import config


class VectorStore:
    def __init__(self, dim):
        self.dim = dim
        self.vectors = np.zeros((0, dim), dtype="float32")
        self.chunks = []

    def add(self, vectors, chunks):
        arr = np.array(vectors, dtype="float32")
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.vectors = arr / norms  # 归一化，便于用点积计算余弦
        self.chunks = chunks

    def search(self, vector, top_k):
        v = np.array(vector, dtype="float32")
        nv = np.linalg.norm(v)
        if nv > 0:
            v = v / nv
        sims = self.vectors @ v  # 余弦相似度
        k = min(top_k, len(self.chunks))
        top_idx = np.argsort(-sims)[:k]
        return [self.chunks[i] for i in top_idx]

    def save(self, index_path=None, chunks_path=None):
        index_path = index_path or config.INDEX_PATH
        chunks_path = chunks_path or config.CHUNKS_PATH
        np.save(index_path, self.vectors)
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, index_path=None, chunks_path=None):
        index_path = index_path or config.INDEX_PATH
        chunks_path = chunks_path or config.CHUNKS_PATH
        arr = np.load(index_path)
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        store = cls(arr.shape[1])
        store.vectors = arr
        store.chunks = chunks
        return store
