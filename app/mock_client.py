"""本地自测用的 Mock 客户端：无需 API Key，用于跑通整条管线。

使用「字符 + 二元组」的确定性伪向量（基于 md5，跨进程稳定），
因此检索结果可复现，足以验证切分 / 建库 / 检索 / 接口全链路。
"""
import hashlib
import math


class MockLLMClient:
    DIM = 256

    def _vec(self, text):
        vec = [0.0] * self.DIM
        grams = list(text) + [text[i:i + 2] for i in range(len(text) - 1)]
        for g in grams:
            h = int.from_bytes(hashlib.md5(g.encode("utf-8")).digest()[:4], "big") % self.DIM
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, texts):
        return [self._vec(t) for t in texts]

    def chat(self, messages):
        last = messages[-1]["content"]
        return "（Mock 回复）我已根据知识库为您整理以下信息：\n" + last[:300]
