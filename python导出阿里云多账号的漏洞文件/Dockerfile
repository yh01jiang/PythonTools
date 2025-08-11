FROM python:3.10-slim

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置工作目录
WORKDIR /app

# 创建目录
RUN mkdir -p /app/log
RUN apt update && apt install -y vim

# 复制当前目录下的所有文件到工作目录
COPY . .

# 安装所需的依赖
RUN pip install -r requirements.txt  # 如果有依赖文件的话，将其命名为 requirements.txt

# 指定容器启动时运行的命令
CMD ["bash", "date.sh"]
