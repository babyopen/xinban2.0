# Gunicorn配置文件
# 适用于小摇筛选项目

# 工作进程数
workers = 3

# 线程数
threads = 2

# 绑定地址
bind = '127.0.0.1:8000'

# 超时设置
timeout = 60

# 日志配置
accesslog = 'logs/gunicorn_access.log'
errorlog = 'logs/gunicorn_error.log'
loglevel = 'info'

# 安全选项
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 进程名称
proc_name = 'xboyi_app'

# 守护进程模式
daemon = False

# 最大请求数
max_requests = 1000
max_requests_jitter = 50

# 环境变量
env = {
    'FLASK_ENV': 'production',
    'PYTHONUNBUFFERED': '1'
}
