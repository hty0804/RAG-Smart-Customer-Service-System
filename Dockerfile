FROM python:3.13-slim

WORKDIR /app

# 先装依赖，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再拷贝源码
COPY . .

EXPOSE 8000

# 监听 0.0.0.0 以便容器外访问；API Key 通过 -e 环境变量传入，不要写进镜像
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000"]
