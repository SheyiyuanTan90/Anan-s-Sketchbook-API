# 使用Python 3.10作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括可能需要的图像处理库依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建data目录和其子目录
RUN mkdir -p /app/data /app/data/log /app/data/sketchbooks

# 设置环境变量
ENV WORK_DIR=/app

# 暴露API端口（默认14541）
EXPOSE 14541

# 设置启动命令
CMD ["python", "main.py"]