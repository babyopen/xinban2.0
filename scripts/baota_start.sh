#!/bin/bash
# 宝塔面板部署启动脚本
# 适用于小摇筛选项目

set -e  # 遇到错误立即退出

# 项目目录
PROJECT_DIR="/www/wwwroot/xboyi.cn"

# 进入项目目录
cd "$PROJECT_DIR"

# 创建必要的目录
mkdir -p logs
mkdir -p temp

# 检查依赖文件
if [ ! -f "requirements.txt" ]; then
    echo "错误: requirements.txt 文件不存在"
    exit 1
fi

# 检查模型文件
if [ ! -f "zodiac_model.pkl" ]; then
    echo "警告: zodiac_model.pkl 文件不存在"
fi

# 检查历史数据文件
if [ ! -f "lottery_history.csv" ]; then
    echo "警告: lottery_history.csv 文件不存在"
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE 'Python [0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+')
if [[ "$PYTHON_VERSION" < "3.8" ]]; then
    echo "错误: Python版本需要3.8或更高，当前版本为 $PYTHON_VERSION"
    exit 1
fi

# 检查并安装依赖
echo "检查依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "安装依赖..."
    pip3 install -r requirements.txt
else
    echo "依赖已安装"
fi

# 检查端口是否被占用
if lsof -i :8000 &> /dev/null; then
    echo "端口 8000 已被占用，尝试停止占用进程..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 检查进程是否存在
if ps aux | grep "gunicorn" | grep "api.index:app" | grep -v grep; then
    echo "发现正在运行的 Gunicorn 进程，尝试停止..."
    ps aux | grep "gunicorn" | grep "api.index:app" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# 启动 Gunicorn
echo "正在启动应用..."
echo "启动时间: $(date)"
echo "项目目录: $PROJECT_DIR"

# 使用 Gunicorn 启动应用
# --daemon 后台运行
# --workers 进程数
# --threads 线程数
# --bind 绑定地址和端口
# --timeout 超时时间
# --access-logfile 访问日志
# --error-logfile 错误日志

python3 -m gunicorn \
    --daemon \
    --workers 3 \
    --threads 2 \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    api.index:app

# 等待应用启动
sleep 3

# 检查应用是否启动成功
if ps aux | grep "gunicorn" | grep "api.index:app" | grep -v grep; then
    echo "应用启动成功！"
    echo "访问地址: http://www.xboyi.cn"
    echo "API地址: http://www.xboyi.cn/api/health"
else
    echo "应用启动失败，请检查日志文件: logs/gunicorn_error.log"
    exit 1
fi

# 输出进程信息
echo "\n进程信息:"
ps aux | grep "gunicorn" | grep "api.index:app" | grep -v grep

echo "\n部署完成！"
