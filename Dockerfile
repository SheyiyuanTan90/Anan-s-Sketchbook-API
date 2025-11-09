FROM python:3.11-alpine

# 设置工作目录
WORKDIR /app

# 添加阿里云源配置
RUN echo "http://mirrors.aliyun.com/alpine/v3.19/main/" > /etc/apk/repositories && \
    echo "http://mirrors.aliyun.com/alpine/v3.19/community/" >> /etc/apk/repositories

# 安装系统依赖
RUN apk update && \
    apk add --no-cache \
    python3-tkinter \
    gcc \
    musl-dev \
    libjpeg-turbo-dev \
    zlib-dev \
    libffi-dev

# 添加项目文件
ADD . /app

# 设置阿里云pip源并安装Python依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 设置环境变量
ENV WORK_DIR=/app

# 暴露API端口
EXPOSE 14541

# 设置启动命令
CMD ["python3", "main.py"]