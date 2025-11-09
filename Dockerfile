# 使用Python 3.10作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（使用阿里云源）
RUN apt-get update -o Acquire::Base::http::Proxy="" -o Acquire::http::Proxy::mirrors.aliyun.com="DIRECT" && \
    apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt文件
COPY requirements.txt .

# 更换为阿里云的pip源并安装Python依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

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