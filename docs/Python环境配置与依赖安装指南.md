# Python环境配置与依赖安装指南

## 一、环境要求

### 1. Python版本
- **推荐版本**：Python 3.8 或更高
- **最低版本**：Python 3.7

### 2. 系统要求
- **CentOS**：7.0+  
- **Ubuntu**：18.04+ 
- **Debian**：9.0+ 

## 二、Python环境配置

### 方法一：使用宝塔面板 Python项目管理器

**步骤**：
1. 登录宝塔面板
2. 进入 `软件商店`
3. 搜索并安装 `Python项目管理器`
4. 打开 `Python项目管理器`
5. 点击 `添加项目`

**配置项目**：
| 配置项 | 值 | 说明 |
|--------|-----|------|
| 项目路径 | `/www/wwwroot/xboyi.cn` | 项目根目录 |
| Python版本 | 选择 3.8 或更高 | 推荐 3.8+ |
| 框架 | Flask | Web框架 |
| 启动方式 | Gunicorn | 生产服务器 |
| 端口 | 8000 | 应用监听端口 |
| 备注 | 小摇筛选项目 | 项目描述 |

**点击 `确定`** 创建项目

### 方法二：手动配置Python环境

**步骤**：
1. 登录服务器
2. 检查Python版本：
   ```bash
   python3 --version
   ```
3. 如果版本低于 3.8，安装新版本：
   ```bash
   # CentOS 系统
   yum install -y python38 python38-pip python38-devel
   
   # Ubuntu/Debian 系统
   apt install -y python3.8 python3.8-pip python3.8-dev
   ```
4. 创建虚拟环境（可选）：
   ```bash
   # 进入项目目录
   cd /www/wwwroot/xboyi.cn
   
   # 创建虚拟环境
   python3 -m venv venv
   
   # 激活虚拟环境
   source venv/bin/activate
   ```

## 三、依赖安装

### 方法一：使用宝塔面板 Python项目管理器

**步骤**：
1. 打开 `Python项目管理器`
2. 找到 `xboyi.cn` 项目
3. 点击 `设置`
4. 进入 `模块` 标签
5. 点击 `安装模块`
6. 选择 `从文件导入`
7. 选择项目根目录下的 `requirements.txt` 文件
8. 点击 `确定` 等待安装完成

### 方法二：手动安装依赖

**步骤**：
1. 登录服务器
2. 进入项目目录：
   ```bash
   cd /www/wwwroot/xboyi.cn
   ```
3. 激活虚拟环境（如果使用）：
   ```bash
   source venv/bin/activate
   ```
4. 安装依赖：
   ```bash
   # 使用默认源
   pip3 install -r requirements.txt
   
   # 或使用国内镜像源（推荐）
   pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

## 四、依赖文件说明

### requirements.txt 内容

```
# Web框架
Flask==2.0.1

# 数据处理
pandas==1.3.3
numpy==1.21.2

# 机器学习
scikit-learn==0.24.2
joblib==1.0.1

# 生产服务器
gunicorn==20.1.0
gevent==21.8.0

# 工具库
requests==2.26.0
python-dotenv==0.19.0
```

### 依赖说明

| 依赖包 | 版本 | 用途 |
|--------|------|------|
| Flask | 2.0.1 | Web框架 |
| pandas | 1.3.3 | 数据处理 |
| numpy | 1.21.2 | 数值计算 |
| scikit-learn | 0.24.2 | 机器学习 |
| joblib | 1.0.1 | 模型序列化 |
| gunicorn | 20.1.0 | 生产服务器 |
| gevent | 21.8.0 | 并发处理 |
| requests | 2.26.0 | HTTP请求 |
| python-dotenv | 0.19.0 | 环境变量管理 |

## 五、常见问题

### 1. 依赖安装失败

**原因**：
- 网络连接不稳定
- Python版本不兼容
- 缺少系统依赖

**解决**：
- 使用国内镜像源
- 检查Python版本
- 安装系统依赖：
  ```bash
  # CentOS 系统
  yum install -y gcc gcc-c++ make openssl-devel libffi-devel
  
  # Ubuntu/Debian 系统
  apt install -y build-essential libssl-dev libffi-dev
  ```

### 2. 模块导入错误

**原因**：
- 依赖未正确安装
- 虚拟环境未激活
- Python路径配置错误

**解决**：
- 重新安装依赖
- 确保虚拟环境已激活
- 检查Python路径：
  ```bash
  echo $PYTHONPATH
  ```

### 3. 版本冲突

**原因**：
- 不同依赖包版本不兼容
- 系统已安装的包与项目需要的版本冲突

**解决**：
- 使用虚拟环境隔离依赖
- 明确指定依赖版本
- 升级或降级冲突的包

### 4. 内存不足

**原因**：
- 服务器内存不足
- 安装大型依赖包时内存不够

**解决**：
- 增加服务器内存
- 关闭其他占用内存的进程
- 使用交换空间：
  ```bash
  # 创建交换文件
  dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  ```

## 六、验证安装

### 1. 检查依赖安装情况

**步骤**：
1. 登录服务器
2. 进入项目目录
3. 激活虚拟环境（如果使用）
4. 执行：
   ```bash
   pip3 list
   ```
5. 检查所有依赖是否已安装

### 2. 测试Python环境

**步骤**：
1. 执行：
   ```bash
   python3 -c "import flask; import pandas; import sklearn; print('环境配置成功')"
   ```
2. 如果输出 `环境配置成功`，说明环境配置正确

### 3. 测试模型加载

**步骤**：
1. 执行：
   ```bash
   python3 -c "import joblib; model = joblib.load('zodiac_model.pkl'); print('模型加载成功')"
   ```
2. 如果输出 `模型加载成功`，说明模型文件正确

## 七、最佳实践

1. **使用虚拟环境**：隔离项目依赖，避免版本冲突
2. **明确版本**：在 requirements.txt 中明确指定依赖版本
3. **使用镜像源**：使用国内镜像源加速依赖安装
4. **定期更新**：定期更新依赖包，修复安全漏洞
5. **备份环境**：定期备份虚拟环境，便于快速恢复

## 八、总结

正确配置Python环境和安装依赖是项目部署的关键步骤。通过宝塔面板或手动方式，确保所有必要的依赖包都已正确安装，为应用的正常运行提供基础保障。

配置完成后，应进行充分的测试，确保Python环境和依赖都已就绪，为后续的应用启动和功能测试做好准备。
