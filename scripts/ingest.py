"""构建知识库索引：读取 knowledge_base.txt → 切分 → 向量化 → 保存。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import config
from app.rag import RAGSystem


def main():
    rag = RAGSystem()
    n = rag.build_index()
    print(f"✅ 索引构建完成，共 {n} 个知识片段。")
    print(f"   向量文件：{config.INDEX_PATH}")
    print(f"   片段文件：{config.CHUNKS_PATH}")


if __name__ == "__main__":
    main()
