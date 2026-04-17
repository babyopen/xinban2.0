# www.xboyi.cn 宝塔面板部署指南

## 📋 部署前准备

### 需要上传到宝塔的文件

```
✅ 必需上传：
├── index.html              # 主页面（使用根目录的，不是frontend/的）
├── style.css              # 样式文件
├── api/
│   └── index.py          # 后端API服务
├── python/
│   ├── ml_api_server.py  # ML模型API服务
│   └── zodiac_ml_predictor.py
├── zodiac_model.pkl       # ML模型文件
├── lottery_history.csv    # 历史数据
└── docs/                  # 文档（可选，推荐上传）
    └── DEPLOY_XBOYI_CN.md

❌ 不需要上传：
├── frontend/              # 旧版本备份
├── .git/                 # Git版本控制
└── venv/                 # 本地虚拟环境（已删除）
```

---

## 🎯 步骤1：修改前端API地址（重要！）

在上传文件前，需要修改 `index.html` 中的两个地方，将 localhost 改为相对路径。

### 修改位置1：ML服务健康检查（第6001行）

**修改前**:
```javascript
const response = await fetch('http://localhost:5001/api/health', {
```

**修改后**:
```javascript
const response = await fetch('/ml-api/api/health', {
```

### 修改位置2：ML预测接口（第6160行）

**修改前**:
```javascript
const response = await fetch('http://localhost:5001/api/predict', {
```

**修改后**:
```javascript
const response = await fetch('/ml-api/api/predict', {
```

---

## 🚀 步骤2：在宝塔面板中创建网站

### 2.1 添加站点

1. 登录宝塔面板
2. 点击左侧菜单 **网站**
3. 点击 **添加站点**
4. 填写以下信息：

| 配置项 | 值 |
|--------|-----|
| 域名 | `www.xboyi.cn` |
| 根目录 | `/www/wwwroot/新版2.0` |
| FTP | 不创建 |
| 数据库 | 不创建 |
| PHP版本 | 纯静态 |

5. 点击 **提交**

---

## 📁 步骤3：上传文件

### 3.1 进入文件管理器

1. 宝塔面板 → 文件
2. 进入 `/www/wwwroot/` 目录
3. 创建文件夹 `新版2.0`（如果不存在）
4. 进入 `/www/wwwroot/新版2.0/` 目录

### 3.2 上传文件

上传以下文件和文件夹：

```
/www/wwwroot/新版2.0/
├── index.html          ✅ （修改过API地址的版本）
├── style.css          ✅
├── api/               ✅
│   └── index.py
├── python/            ✅
│   ├── ml_api_server.py
│   └── zodiac_ml_predictor.py
├── zodiac_model.pkl   ✅
└── lottery_history.csv ✅
```

**注意**:
- 使用根目录的 `index.html`，**不要**使用 `frontend/` 目录下的旧版本
- 确保文件权限正确（755）

---

## 🐍 步骤4：配置Python环境

### 4.1 安装Python项目管理器

1. 宝塔面板 → 软件商店
2. 搜索 **Python项目管理器**
3. 安装（如果还没安装）

### 4.2 安装Python 3.9+

1. 在Python项目管理器中
2. 点击 **版本管理**
3. 安装 Python 3.9 或更高版本

### 4.3 安装依赖包

在宝塔终端中执行：

```bash
cd /www/wwwroot/新版2.0
pip install flask numpy scikit-learn
```

或者使用Python项目管理器安装。

---

## 🔧 步骤5：配置后端服务

### 5.1 配置API服务（端口8000）

#### 方法A：使用Python项目管理器（推荐）

1. 宝塔面板 → Python项目管理器
2. 点击 **添加项目**
3. 填写：

| 配置项 | 值 |
|--------|-----|
| 项目名称 | `小摇筛选-API` |
| 路径 | `/www/wwwroot/新版2.0/api` |
| 启动文件 | `index.py` |
| 端口 | `8000` |
| Python版本 | 3.9+ |

4. 点击 **确定**
5. 点击 **安装模块依赖**（如果需要）
6. 点击 **启动**

#### 方法B：使用命令行（备用）

在宝塔终端中执行：

```bash
cd /www/wwwroot/新版2.0
nohup python3 api/index.py > api.log 2>&1 &
```

### 5.2 配置ML服务（端口5001）

#### 方法A：使用Python项目管理器（推荐）

1. 宝塔面板 → Python项目管理器
2. 点击 **添加项目**
3. 填写：

| 配置项 | 值 |
|--------|-----|
| 项目名称 | `小摇筛选-ML` |
| 路径 | `/www/wwwroot/新版2.0/python` |
| 启动文件 | `ml_api_server.py` |
| 端口 | `5001` |
| Python版本 | 3.9+ |

4. 点击 **确定**
5. 点击 **安装模块依赖**（如果需要）
6. 点击 **启动**

#### 方法B：使用命令行（备用）

在宝塔终端中执行：

```bash
cd /www/wwwroot/新版2.0
nohup python3 python/ml_api_server.py > ml.log 2>&1 &
```

---

## 🌐 步骤6：配置Nginx反向代理

### 6.1 修改网站配置

1. 宝塔面板 → 网站 → 找到 `www.xboyi.cn`
2. 点击 **设置**
3. 点击 **配置文件**
4. 用以下配置替换或添加：

```nginx
server {
    listen 80;
    server_name www.xboyi.cn xboyi.cn;
    root /www/wwwroot/新版2.0;
    index index.html;
    
    # 启用gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
    
    # 前端静态文件
    location / {
        try_files $uri $uri/ /index.html;
        
        # 静态资源缓存
        location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 后端API代理（端口8000）
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # ML API代理（端口5001）
    location /ml-api/ {
        # 移除 /ml-api 前缀，转发到后端
        rewrite ^/ml-api/(.*) /$1 break;
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 禁止访问敏感文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~* \.(py|pkl|csv|log)$ {
        deny all;
        access_log off;
    }
    
    # 日志配置
    access_log /www/wwwlogs/www.xboyi.cn-access.log;
    error_log /www/wwwlogs/www.xboyi.cn-error.log;
}
```

5. 点击 **保存**

---

## 🔒 步骤7：配置HTTPS（推荐）

### 7.1 申请SSL证书

1. 宝塔面板 → 网站 → www.xboyi.cn → 设置
2. 点击 **SSL**
3. 选择 **Let's Encrypt**
4. 勾选域名：`www.xboyi.cn` 和 `xboyi.cn`
5. 点击 **申请**

### 7.2 强制HTTPS

1. 在SSL设置页面
2. 勾选 **强制HTTPS**
3. 点击 **保存**

---

## 🔧 步骤8：配置防火墙

### 8.1 开放端口

在宝塔面板 → 安全中，确保以下端口开放：

| 端口 | 用途 | 状态 |
|------|------|------|
| 80 | HTTP | ✅ 必需 |
| 443 | HTTPS | ✅ 推荐 |
| 8000 | API服务 | ❌ 不需要（通过Nginx代理） |
| 5001 | ML服务 | ❌ 不需要（通过Nginx代理） |

**重要**：不要在防火墙中开放8000和5001端口，它们通过Nginx反向代理访问，更安全。

### 8.2 目录权限

在宝塔终端中执行：

```bash
cd /www/wwwroot/新版2.0
chmod -R 755 .
chown -R www:www .
```

---

## ✅ 步骤9：检查和测试

### 9.1 检查服务状态

在宝塔面板中检查：
- Python项目管理器中两个服务是否都在运行
- 网站设置中Nginx配置是否正确

### 9.2 功能测试清单

- [ ] 访问 http://www.xboyi.cn 能正常打开
- [ ] 访问 https://www.xboyi.cn 能正常打开（如果配置了HTTPS）
- [ ] 页面所有功能正常
- [ ] 记录页面能正常显示
- [ ] 点击「启动服务」按钮显示说明
- [ ] ML服务状态指示器显示正常
- [ ] （如果ML服务已启动）能执行ML预测
- [ ] 无 JavaScript 错误（按F12查看控制台）

### 9.3 查看日志

如果遇到问题，查看日志：

```bash
# API服务日志
tail -f /www/wwwroot/新版2.0/api.log

# ML服务日志
tail -f /www/wwwroot/新版2.0/ml.log

# Nginx访问日志
tail -f /www/wwwlogs/www.xboyi.cn-access.log

# Nginx错误日志
tail -f /www/wwwlogs/www.xboyi.cn-error.log
```

---

## 🔄 服务管理命令

### 在宝塔终端中执行

```bash
# 进入项目目录
cd /www/wwwroot/新版2.0

# 查看Python进程
ps aux | grep python

# 停止API服务（如果用nohup启动）
pkill -f "api/index.py"

# 停止ML服务（如果用nohup启动）
pkill -f "ml_api_server.py"

# 重启API服务
pkill -f "api/index.py"
nohup python3 api/index.py > api.log 2>&1 &

# 重启ML服务
pkill -f "ml_api_server.py"
nohup python3 python/ml_api_server.py > ml.log 2>&1 &
```

---

## 📊 性能优化建议

### 已在Nginx配置中启用

1. ✅ Gzip压缩
2. ✅ 静态资源缓存（30天）
3. ✅ 禁止访问敏感文件
4. ✅ 反向代理（8000、5001端口不对外暴露）

### 额外优化（可选）

1. 配置 CDN 加速
2. 启用 Redis 缓存（如果需要）
3. 配置图片懒加载
4. 添加 Service Worker（PWA支持）

---

## 🚨 常见问题排查

### 问题1：页面打不开

**检查**:
- Nginx是否运行
- 网站根目录是否正确
- 文件权限是否正确

### 问题2：ML预测不工作

**检查**:
- ML服务是否启动（端口5001）
- index.html中的API地址是否已修改为 `/ml-api/api/...`
- Nginx反向代理配置是否正确
- zodiac_model.pkl 文件是否存在

### 问题3：API不工作

**检查**:
- API服务是否启动（端口8000）
- lottery_history.csv 文件是否存在
- Nginx反向代理配置是否正确

### 问题4：500错误

**检查**:
- 查看Nginx错误日志
- 查看Python服务日志
- 检查Python依赖是否安装完整

---

## ✅ 部署完成检查清单

- [ ] 所有文件已上传到正确位置
- [ ] index.html中的API地址已修改为相对路径
- [ ] Python环境已配置
- [ ] 依赖包已安装
- [ ] API服务已启动（端口8000）
- [ ] ML服务已启动（端口5001）
- [ ] Nginx配置已更新
- [ ] 防火墙已配置（只开放80/443）
- [ ] 目录权限已设置（755）
- [ ] HTTPS已配置（推荐）
- [ ] 网站能正常访问
- [ ] 所有功能测试通过
- [ ] 无JavaScript错误
- [ ] 日志检查无异常

---

## 📞 需要帮助？

如果遇到问题：
1. 查看本文档的「常见问题排查」部分
2. 查看日志文件
3. 检查宝塔面板的「安全」和「软件商店」设置

---

*部署指南版本: 1.0*
*创建日期: 2026-04-05*
*域名: www.xboyi.cn*
