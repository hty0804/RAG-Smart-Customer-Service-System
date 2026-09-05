FROM python:3.13-slim

WORKDIR /app

# 先装基础依赖，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 本地向量化依赖按需安装：DeepSeek 等无 Embedding 接口的场景，
# 可在本镜像构建时取消下面两行注释，并将 EMBEDDING_PROVIDER=local。
# COPY requirements-local-embeddings.txt .
# RUN pip install --no-cache-dir -r requirements-local-embeddings.txt

# 再拷贝源码
COPY . .

EXPOSE 8000

# 监听 0.0.0.0 以便容器外访问；API Key 通过 -e 环境变量传入，不要写进镜像
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
