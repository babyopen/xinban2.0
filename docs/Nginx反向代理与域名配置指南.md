# Nginx反向代理与域名配置指南

## 一、Nginx配置准备

### 1. 检查Nginx安装

**步骤**：
1. 登录宝塔面板
2. 进入 `软件商店`
3. 检查 `Nginx` 是否已安装
4. 如果未安装，点击 `安装` 按钮安装Nginx

### 2. 配置文件准备

确保 `nginx_config.conf` 文件已上传到项目根目录：
- 文件路径：`/www/wwwroot/xboyi.cn/nginx_config.conf`
- 该文件包含了完整的Nginx配置

## 二、添加站点

### 1. 进入站点管理

**步骤**：
1. 登录宝塔面板
2. 进入 `网站` 管理
3. 点击 `添加站点` 按钮

### 2. 配置站点信息

**配置项**：
| 配置项 | 值 | 说明 |
|--------|-----|------|
| 域名 | `www.xboyi.cn` | 主域名 |
| 备注 | 小摇筛选项目 | 项目描述 |
| 根目录 | `/www/wwwroot/xboyi.cn/frontend` | 前端文件目录 |
| PHP版本 | 纯静态 | 选择纯静态，因为使用Flask |
| 数据库 | 无 | 暂不需要数据库 |
| SSL | 暂不配置 | 可后续配置 |

**点击 `提交`** 创建站点

## 三、配置反向代理

### 1. 进入反向代理设置

**步骤**：
1. 进入 `网站` 管理
2. 找到 `www.xboyi.cn` 站点
3. 点击 `设置` 按钮
4. 进入 `反向代理` 标签

### 2. 添加反向代理

**步骤**：
1. 点击 `添加反向代理` 按钮
2. 配置反向代理：

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 代理名称 | `flask_app` | 代理名称 |
| 目标URL | `http://127.0.0.1:8000` | Flask应用地址 |
| 发送域名 | `$host` | 保持原域名 |
| 启用WebSocket | 关闭 | 暂不需要 |
| 代理目录 | `/` | 根目录代理 |

**点击 `提交`** 添加反向代理

### 3. 配置高级选项

**步骤**：
1. 点击 `flask_app` 代理的 `编辑` 按钮
2. 在 `高级功能` 中添加以下配置：

```nginx
# 超时设置
proxy_connect_timeout 600;
proxy_send_timeout 600;
proxy_read_timeout 600;

# 缓存设置
proxy_buffers 16 16k;
proxy_buffer_size 32k;

# 附加头信息
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

**点击 `保存`** 应用配置

## 四、修改Nginx配置文件

### 1. 进入配置文件编辑

**步骤**：
1. 进入 `网站` 管理
2. 找到 `www.xboyi.cn` 站点
3. 点击 `设置` 按钮
4. 进入 `配置文件` 标签

### 2. 替换配置内容

**步骤**：
1. 复制 `nginx_config.conf` 文件中的内容
2. 替换当前配置文件的全部内容
3. 点击 `保存` 按钮

### 3. 配置文件说明

```nginx
# 小摇筛选项目Nginx配置
# 适用于宝塔面板

server {
    listen 80;
    server_name www.xboyi.cn xboyi.cn;
    access_log /www/wwwlogs/xboyi.cn.access.log;
    error_log /www/wwwlogs/xboyi.cn.error.log;
    
    # 重定向HTTP到HTTPS（如果已配置SSL）
    # return 301 https://$server_name$request_uri;
    
    # 静态文件处理
    location / {
        try_files $uri @flask_app;
    }
    
    # 前端静态文件
    location ~* \.(html|css|js|ico|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$ {
        root /www/wwwroot/xboyi.cn/frontend;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Flask应用反向代理
    location @flask_app {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
    
    # API路径直接代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 处理404错误
    error_page 404 /404.html;
    location = /404.html {
        root /www/wwwroot/xboyi.cn/frontend;
    }
    
    # 处理500错误
    error_page 500 502 503 504 /500.html;
    location = /500.html {
        root /www/wwwroot/xboyi.cn/frontend;
    }
}
```

## 五、SSL证书配置（可选）

### 1. 申请SSL证书

**步骤**：
1. 进入 `网站` 管理
2. 找到 `www.xboyi.cn` 站点
3. 点击 `设置` 按钮
4. 进入 `SSL` 标签
5. 选择 `Let's Encrypt`
6. 勾选 `www.xboyi.cn` 和 `xboyi.cn` 域名
7. 点击 `申请` 按钮

### 2. 配置HTTPS

**步骤**：
1. 申请成功后，SSL状态会显示为 `已启用`
2. 修改Nginx配置文件，取消注释HTTPS配置部分
3. 保存配置文件
4. 重启Nginx

## 六、Nginx重启

### 1. 通过宝塔面板重启

**步骤**：
1. 进入 `软件商店`
2. 找到 `Nginx`
3. 点击 `设置` 按钮
4. 点击 `重启` 按钮

### 2. 通过命令行重启

**步骤**：
1. 登录服务器
2. 执行：
   ```bash
   # 重启Nginx
   systemctl restart nginx
   
   # 或使用宝塔命令
   bt restart nginx
   ```

## 七、验证配置

### 1. 检查Nginx配置

**步骤**：
1. 登录服务器
2. 执行：
   ```bash
   nginx -t
   ```
3. 如果显示 `nginx: configuration file /www/server/nginx/conf/nginx.conf test is successful`，说明配置正确

### 2. 测试域名访问

**步骤**：
1. 打开浏览器
2. 访问 `http://www.xboyi.cn`
3. 检查是否能正常访问
4. 访问 `http://www.xboyi.cn/api/health`
5. 检查API是否正常响应

### 3. 测试静态文件

**步骤**：
1. 访问 `http://www.xboyi.cn/style.css`
2. 检查样式文件是否能正常加载
3. 访问 `http://www.xboyi.cn/index.html`
4. 检查HTML文件是否能正常加载

## 八、常见问题

### 1. 404错误

**原因**：
- 静态文件路径错误
- Nginx配置错误
- 前端文件未上传

**解决**：
- 检查静态文件路径是否正确
- 检查Nginx配置文件
- 确保前端文件已上传

### 2. 502错误

**原因**：
- Flask应用未启动
- 端口8000未开放
- 反向代理配置错误

**解决**：
- 启动Flask应用
- 检查端口8000是否开放
- 检查反向代理配置

### 3. 504错误

**原因**：
- 应用响应超时
- 网络连接问题
- 服务器负载过高

**解决**：
- 检查应用运行状态
- 检查网络连接
- 优化服务器性能

### 4. SSL配置错误

**原因**：
- 证书过期
- 证书配置错误
- 域名不匹配

**解决**：
- 重新申请SSL证书
- 检查证书配置
- 确保域名正确

## 九、性能优化

### 1. 静态文件缓存

**配置**：
```nginx
location ~* \.(html|css|js|ico|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$ {
    root /www/wwwroot/xboyi.cn/frontend;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
}
```

### 2. Gzip压缩

**配置**：
```nginx
# 在http块中添加
gzip on;
gzip_min_length 1k;
gzip_buffers 4 16k;
gzip_comp_level 5;
gzip_types text/plain application/javascript application/x-javascript text/css application/xml text/javascript application/x-httpd-php image/jpeg image/gif image/png;
gzip_vary on;
gzip_disable "MSIE [1-6]\\.";
```

### 3. 连接池配置

**配置**：
```nginx
# 在http块中添加
keepalive_timeout 65;
keepalive_requests 10000;
```

## 十、总结

正确配置Nginx反向代理和域名是项目部署的重要环节。通过宝塔面板的可视化操作，我们可以轻松完成站点添加、反向代理配置和SSL证书申请等操作。

配置完成后，应进行充分的测试，确保域名访问、API调用和静态文件加载都能正常工作。同时，通过性能优化配置，可以提高应用的响应速度和用户体验。

Nginx作为Web服务器和反向代理，为应用提供了稳定、高效的访问支持，是项目部署中不可或缺的组件。
