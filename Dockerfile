FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 添加项目文件
ADD . /app

# 安装Python依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 设置环境变量
ENV WORK_DIR=/app

# 暴露API端口
EXPOSE 14541

# 设置启动命令
CMD ["python","main.py"]