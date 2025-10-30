# 使用 Python 3.10 作为基础镜像
FROM python:3.10-slim-bookworm

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY start.py .

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash agent

# 设置文件权限
RUN chown -R agent:agent /app

# 切换到非 root 用户
USER agent

# 暴露端口 (如果需要)
# EXPOSE 8080

# 启动命令
CMD ["python", "src/simple_conversation_agent.py", "dev"]