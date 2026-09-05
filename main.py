"""启动入口：可选先构建索引，再启动 FastAPI 服务。"""
import argparse
import uvicorn
from app.api import app


def main():
    parser = argparse.ArgumentParser(description="RAG 智能客服对话系统")
    parser.add_argument("--build", action="store_true", help="启动前先构建知识库索引")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.build:
        from app.rag import RAGSystem
        rag = RAGSystem()
        n = rag.build_index()
        print(f"✅ 索引构建完成，共 {n} 个知识片段。")

    uvicorn.run(app, host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
