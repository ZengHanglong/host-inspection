# 主机巡检系统 - 打包部署指南

## 方案概述

本项目支持多种打包部署方式，推荐使用 **PyInstaller + NSIS** 方案，可实现：
- GUI安装向导
- 自定义安装路径
- 桌面快捷方式
- 开机自启动
- 完全离线部署

---

## 方案一：PyInstaller + NSIS (推荐)

### 特点
- ✅ 完整的GUI安装向导
- ✅ 支持自定义安装路径
- ✅ 创建桌面快捷方式和开始菜单
- ✅ 支持开机自启动
- ✅ 完全离线，无需Python环境
- ❌ 安装包较大 (约500MB-800MB)

### 构建步骤

#### 1. 安装构建工具

```bash
# Python依赖
pip install pyinstaller

# 下载安装 NSIS
# https://nsis.sourceforge.io/Download
```

#### 2. 构建安装包

```bash
cd host-inspection
python build_installer.py
```

#### 3. 输出产物

```
HostInspection_Setup_v3.0.0.exe  # Windows安装包
```

### 安装效果

用户双击exe后：
1. 欢迎页面
2. 许可协议
3. 选择组件（桌面快捷方式、开机自启动等）
4. 选择安装路径
5. 安装进度
6. 完成并启动

---

## 方案二：便携版（解压即用）

### 特点
- ✅ 无需安装，解压即用
- ✅ 绿色便携，可放U盘
- ✅ 构建简单
- ❌ 无GUI安装向导

### 构建步骤

```bash
# 1. 构建前端
cd frontend
npm install
npm run build

# 2. 打包后端
cd ../backend
pyinstaller --onefile --add-data "app/routers;routers" --add-data "app/services;services" app/main.py

# 3. 整理目录结构
mkdir ../portable
cp dist/main.exe ../portable/HostInspection.exe
cp -r ../frontend/dist ../portable/www
```

### 目录结构

```
HostInspection_Portable/
├── HostInspection.exe      # 主程序
├── www/                    # 前端静态文件
│   ├── index.html
│   └── assets/
├── data/                   # 数据目录（自动创建）
└── README.txt              # 使用说明
```

### 启动方式

双击 `HostInspection.exe` 或命令行：
```bash
HostInspection.exe --port 8000 --data ./data
```

---

## 方案三：Docker部署

### 特点
- ✅ 环境一致性最好
- ✅ 跨平台支持
- ✅ 易于迁移和扩展
- ❌ 需要安装Docker

### Dockerfile

```dockerfile
# 后端
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY backend/app ./app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
    restart: unless-stopped
```

### 启动命令

```bash
docker-compose up -d
```

---

## 方案四：Windows服务模式

将程序注册为Windows服务，开机自动启动。

### 使用 NSSM (Non-Sucking Service Manager)

```bash
# 1. 下载NSSM
# https://nssm.cc/download

# 2. 安装服务
nssm install HostInspection "C:\Program Files\HostInspection\HostInspection.exe"

# 3. 配置服务
nssm set HostInspection AppDirectory "C:\Program Files\HostInspection"
nssm set HostInspection DisplayName "主机巡检系统"
nssm set HostInspection Description "自动化基础设施巡检服务"
nssm set HostInspection Start SERVICE_AUTO_START

# 4. 启动服务
nssm start HostInspection
```

---

## 配置文件说明

### config.py 关键配置

```python
# 数据库路径（可自定义）
DATABASE_PATH = os.path.join(os.getcwd(), "data", "inspection.db")

# API端口
API_PORT = 8000

# 日志路径
LOG_PATH = os.path.join(os.getcwd(), "logs")

# 采集间隔（分钟）
COLLECTION_INTERVAL = 5
```

### 命令行参数

```bash
HostInspection.exe --help

选项:
  --port PORT        API服务端口 (默认: 8000)
  --data DIR         数据目录路径 (默认: ./data)
  --host HOST        监听地址 (默认: 0.0.0.0)
  --no-browser       启动时不打开浏览器
  --debug            调试模式
```

---

## 打包优化建议

### 减小安装包体积

```bash
# 1. 使用UPX压缩
pip install pyinstaller
pyinstaller --onefile --upx-dir=/path/to/upx app/main.py

# 2. 排除不需要的模块
pyinstaller --onefile \
  --exclude-module matplotlib \
  --exclude-module PIL \
  --exclude-module scipy \
  app/main.py
```

### 单文件 vs 目录模式

| 模式 | 命令参数 | 启动速度 | 更新便利性 |
|------|----------|----------|------------|
| 单文件 | `--onefile` | 较慢(需解压) | 简单 |
| 目录 | `--onedir` | 快 | 需替换文件 |

**建议**: 生产环境使用目录模式，便携版使用单文件模式

---

## 快速打包命令

```bash
# 完整构建
python build_installer.py

# 仅打包后端
cd backend && pyinstaller --onefile app/main.py

# 仅构建前端
cd frontend && npm run build

# Docker构建
docker-compose build
```

---

## 常见问题

### Q1: PyInstaller打包后运行报错？

检查隐藏导入：
```bash
pyinstaller --hidden-import=pyVmomi --hidden-import=ssl app/main.py
```

### Q2: 打包后找不到静态文件？

确保使用 `--add-data` 参数：
```bash
pyinstaller --add-data "frontend/dist;www" app/main.py
```

### Q3: 安装包太大？

考虑分离前后端：
- 后端打包为exe
- 前端单独部署或使用CDN

### Q4: 如何实现自动更新？

1. 在服务器放置版本检查接口
2. 程序启动时检查版本
3. 提示用户下载新版本

---

## 推荐部署架构

### 小型部署 (单机)
```
Windows Server
└── HostInspection.exe (直接运行)
```

### 中型部署 (容器化)
```
Docker Host
├── Backend容器 (FastAPI)
└── Frontend容器 (Nginx)
```

### 大型部署 (集群)
```
Kubernetes
├── Deployment (后端 x N副本)
├── Service (负载均衡)
├── Ingress (入口)
└── PV/PVC (持久化存储)
```

---

*文档版本: 3.0.0 | 更新时间: 2026-05-12*
