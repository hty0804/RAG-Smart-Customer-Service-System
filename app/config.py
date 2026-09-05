"""配置：读取 .env（API Key、模型名、参数），统一管理路径。"""
import os
from dotenv import load_dotenv

load_dotenv()

# 项目根目录（app/ 的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# 向量化后端：openai（调用 OpenAI 兼容接口）/ local（本地 sentence-transformers）
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
TOP_K = int(os.getenv("TOP_K", "3"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
# 管理员接口密钥；为空时禁用知识库写入接口（更安全）
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")

KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.txt")
INDEX_PATH = os.path.join(BASE_DIR, "data", "index.npy")
CHUNKS_PATH = os.path.join(BASE_DIR, "data", "chunks.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")
