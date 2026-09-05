"""LLM 与 Embedding 客户端。

兼容任意 OpenAI 接口的云服务（OpenAI / DeepSeek / Azure / 本地 llama.cpp 等）。
只需在 .env 中填入 OPENAI_API_KEY（以及可选的 OPENAI_BASE_URL）即可。
"""
from openai import OpenAI
from . import config


class LLMClient:
    """封装 Embedding 与 Chat 两类调用。"""

    def __init__(self):
        # 延迟创建 OpenAI 客户端：构造时不校验凭据，避免无 Key 时导入即报错。
        self._api_key = config.OPENAI_API_KEY
        self._base_url = config.OPENAI_BASE_URL
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
        return self._client

    def embed(self, texts):
        """批量将文本转为向量列表，顺序与输入一致。"""
        resp = self.client.embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in resp.data]

    def chat(self, messages):
        """根据消息列表（system/user）生成回复文本。"""
        resp = self.client.chat.completions.create(
            model=config.CHAT_MODEL,
            messages=messages,
            temperature=0.3,
        )
        return resp.choices[0].message.content
