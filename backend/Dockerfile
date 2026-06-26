# ==================== 后端 Dockerfile ====================
# 使用 Python 3.11 + uv 包管理器

FROM python:3.11-slim

WORKDIR /app

# 安装 uv（快速的 Python 包管理器）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先复制依赖文件（利用 Docker 缓存层，代码改了不用重新装依赖）
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY . .

# 创建上传目录
RUN mkdir -p uploads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
