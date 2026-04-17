# 宝塔面板部署优化指南

## 📋 项目优化总结

### ✅ 已完成的优化

1. **文件清理**
   - ✅ 删除了 `frontend/venv/` 虚拟环境文件夹（最大冗余）
   - ✅ 保留了项目核心文件

2. **功能优化**
   - ✅ 移除了所有删除相关功能（安全考虑）
   - ✅ 添加了ML服务状态管理功能
   - ✅ 优化了用户体验

---

## 🎯 宝塔面板部署步骤

### 1. 项目结构说明

```
新版2.0/
├── index.html              # 主页面（使用此版本）
├── style.css               # 样式文件
├── api/
│   └── index.py           # 后端API服务
├── python/
│   ├── ml_api_server.py   # ML模型API服务
│   └── zodiac_ml_predictor.py
├── zodiac_model.pkl        # ML模型文件
├── lottery_history.csv     # 历史数据
├── docs/                   # 文档目录
│   └── BAOTA_DEPLOY_GUIDE.md
└── frontend/              # 备份目录（保留但不使用）
    ├── index.html         # 旧版本
    └── style.css
```

### 2. 宝塔面板部署前准备

#### 2.1 上传文件到宝塔

**需要上传的文件和目录：**
```
✅ index.html
✅ style.css
✅ api/
✅ python/
✅ zodiac_model.pkl
✅ lottery_history.csv
✅ docs/
```

**不需要上传（已删除）：**
```
❌ frontend/venv/ （已删除）
❌ .git/ （版本控制，可选）
```

### 3. 宝塔面板环境配置

#### 3.1 Python环境配置

**宝塔面板 → 软件商店 → 安装 Python 项目管理器**

1. 安装 Python 3.9 或更高版本
2. 创建虚拟环境（可选，但推荐）
3. 安装依赖包：

```bash
# 在项目根目录执行
pip install flask numpy scikit-learn
```

#### 3.2 网站配置

**宝塔面板 → 网站 → 添加站点**

| 配置项 | 值 |
|--------|-----|
| 域名 | 您的域名或IP |
| 根目录 | `/www/wwwroot/新版2.0` |
| PHP版本 | 纯静态（不需要PHP） |

### 4. 后端服务配置

#### 4.1 配置API服务（Flask）

**使用宝塔面板的「Python项目」管理器：**

1. 添加 Python 项目
   - 项目路径：`/www/wwwroot/新版2.0/api`
   - 启动文件：`index.py`
   - 端口：`8000`
   - 项目名称：`小摇筛选-API`

2. 设置 Supervisor 守护进程

**或使用命令行启动：**

```bash
cd /www/wwwroot/新版2.0
nohup python3 api/index.py > api.log 2>&1 &
```

#### 4.2 配置ML模型服务

**使用宝塔面板的「Python项目」管理器：**

1. 添加 Python 项目
   - 项目路径：`/www/wwwroot/新版2.0/python`
   - 启动文件：`ml_api_server.py`
   - 端口：`5001`
   - 项目名称：`小摇筛选-ML`

2. 设置 Supervisor 守护进程

**或使用命令行启动：**

```bash
cd /www/wwwroot/新版2.0
nohup python3 python/ml_api_server.py > ml.log 2>&1 &
```

### 5. Nginx反向代理配置

**宝塔面板 → 网站 → 设置 → 配置文件**

添加以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /www/wwwroot/新版2.0;
    index index.html;
    
    # 前端静态文件
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ML API代理
    location /ml-api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**注意：** 如果使用反向代理，需要修改前端代码中的API地址：

```javascript
// 在 index.html 中修改
// 原：http://localhost:5001/api/predict
// 改为：/ml-api/api/predict
```

### 6. 安全加固

#### 6.1 宝塔面板安全设置

1. **防火墙配置**
   - 开放端口：80, 443
   - 关闭不必要的端口：8000, 5001（通过Nginx代理访问）

2. **目录权限**
   ```bash
   chmod -R 755 /www/wwwroot/新版2.0
   chown -R www:www /www/wwwroot/新版2.0
   ```

3. **禁止访问敏感文件**
   在Nginx配置中添加：
   ```nginx
   location ~ /\. {
       deny all;
       access_log off;
       log_not_found off;
   }
   
   location ~* \.(py|pkl|csv)$ {
       deny all;
   }
   ```

#### 6.2 HTTPS配置

**宝塔面板 → 网站 → 设置 → SSL**

1. 申请Let's Encrypt免费证书
2. 强制HTTPS
3. 开启HSTS

### 7. 性能优化

#### 7.1 静态资源缓存

在Nginx配置中添加：

```nginx
location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

#### 7.2 Gzip压缩

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;
```

### 8. 监控和日志

#### 8.1 日志管理

在宝塔面板中配置：
- API服务日志：`/www/wwwroot/新版2.0/api.log`
- ML服务日志：`/www/wwwroot/新版2.0/ml.log`
- Nginx日志：默认位置

#### 8.2 进程监控

使用宝塔面板的「进程监控」或 Supervisor 确保服务持续运行。

### 9. 备份策略

#### 9.1 自动备份

**宝塔面板 → 计划任务**

1. 每日备份网站文件
2. 每日备份数据库（如果有）
3. 保留最近7天的备份

#### 9.2 手动备份

定期备份以下重要文件：
- `zodiac_model.pkl`（模型文件）
- `lottery_history.csv`（历史数据）
- 自定义配置文件

---

## 🚀 快速启动命令

### 在宝塔面板终端中执行：

```bash
# 1. 进入项目目录
cd /www/wwwroot/新版2.0

# 2. 安装依赖（如果需要）
pip install flask numpy scikit-learn

# 3. 启动API服务（端口8000）
nohup python3 api/index.py > api.log 2>&1 &

# 4. 启动ML服务（端口5001）
nohup python3 python/ml_api_server.py > ml.log 2>&1 &

# 5. 查看运行状态
ps aux | grep python
```

---

## ⚠️ 注意事项

1. **使用根目录的 index.html**，不要使用 frontend/ 目录下的旧版本
2. 确保Python版本 >= 3.7
3. 确保防火墙配置正确
4. 定期检查日志文件大小，避免占用过多磁盘空间
5. 建议使用 Supervisor 或 systemd 管理服务进程

---

## 📞 故障排查

### 问题1：API服务无法启动
**检查：**
- Python版本是否正确
- 依赖包是否安装
- 端口是否被占用

### 问题2：ML预测功能不工作
**检查：**
- ML服务是否启动（端口5001）
- 模型文件 `zodiac_model.pkl` 是否存在
- 历史数据 `lottery_history.csv` 是否存在

### 问题3：页面无法访问
**检查：**
- Nginx配置是否正确
- 网站根目录权限是否正确
- 防火墙是否开放80/443端口

---

## ✅ 部署检查清单

- [ ] 所有核心文件已上传
- [ ] Python环境已配置
- [ ] 依赖包已安装
- [ ] API服务已启动（端口8000）
- [ ] ML服务已启动（端口5001）
- [ ] Nginx反向代理已配置
- [ ] HTTPS证书已安装
- [ ] 防火墙已配置
- [ ] 目录权限已设置
- [ ] 备份策略已配置
- [ ] 功能测试已通过
