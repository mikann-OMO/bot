FROM python:3.11

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    && apt-get clean

WORKDIR /app

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制启动脚本并设置权限
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# 使用启动脚本
CMD ["/app/startup.sh"]