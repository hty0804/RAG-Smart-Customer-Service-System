"""全局配置：从 .env 读取环境变量，并统一解析项目绝对路径。"""
import os
from dotenv import load_dotenv

load_dotenv()

# 项目根目录（app/ 的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 只需在这一行附近填写你的 API Key ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# 兼容 OpenAI 接口的服务地址（默认官方；可改为 DeepSeek / Azure / 本地 llama.cpp 等）
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# 模型与参数（均可选，带默认值）
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-3.5-turbo")
TOP_K = int(os.getenv("TOP_K", "3"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# 数据与静态资源路径（基于项目根目录，避免相对路径出错）
KNOWLEDGE_BASE_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.txt")
INDEX_PATH = os.path.join(BASE_DIR, "data", "index.npy")
CHUNKS_PATH = os.path.join(BASE_DIR, "data", "chunks.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")
