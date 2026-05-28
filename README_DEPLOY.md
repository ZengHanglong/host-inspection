# 主机巡检系统部署与迁移说明

这套系统可以直接迁移到别的 Windows 服务器，不需要改业务代码。核心前提只有两个：目标机器能运行 Python 和 Node.js；如果你要保留原来的 API 凭证，就必须同时保留同一份 `INSPECTION_KEY`。

## 1. 目录说明

项目主要包含这几部分：

- `backend/`：FastAPI 后端，默认监听 `8000`
- `frontend/`：Vue + Vite 前端，开发模式默认监听 `5173`
- `scripts/`：一键安装、启动、打包脚本
- `backend/inspection.db`：本地 SQLite 数据库，里面包含阈值配置、告警记录、巡检记录、平台凭证、**采集调度配置**

## 2. 运行环境要求

建议目标机器准备下面这些环境：

- Python 3.10 及以上（**注意：Windows Server 2012 需要手动安装，见下方说明**）
- Node.js 18 及以上
- npm

建议先确认命令可用：

```bash
python --version
npm --version
```

### Windows Server 2012 特别说明

Server 2012 已停止主流支持，安装现代运行环境需要注意：

1. **Python 安装**：从 python.org 下载 3.10+ 安装包（选择 Windows installer 64-bit），安装时勾选 "Add Python to PATH"。Server 2012 可能缺少某些 VC runtime，如果安装失败，先安装 [Visual C++ Redistributable 2015-2022](https://aka.ms/vs/17/release/vc_redist.x64.exe)。

2. **Node.js 安装**：从 nodejs.org 下载 18+ LTS 版本（Windows 64-bit .msi）。Server 2012 的 IE 版本太老，建议用其他浏览器下载或用 PowerShell：
   ```powershell
   Invoke-WebRequest -Uri "https://nodejs.org/dist/v18.20.0/node-v18.20.0-x64.msi" -OutFile "node.msi"
   ```

3. **防火墙**：Server 2012 默认防火墙可能阻止 8000/5173 端口，需手动放行：
   ```powershell
   netsh advfirewall firewall add rule name="Inspection Backend" dir=in action=allow protocol=tcp localport=8000
   netsh advfirewall firewall add rule name="Inspection Frontend" dir=in action=allow protocol=tcp localport=5173
   ```

## 3. 第一次部署

### 3.1 安装依赖

在项目根目录执行：

```bash
scripts\install-deps.bat
```

这个脚本会做两件事：

1. 安装后端依赖：`backend/requirements.txt`
2. 安装前端依赖：`frontend/package.json`

### 3.2 启动后端

```bash
scripts\start-backend.bat
```

启动后可访问：

- API 根地址：`http://localhost:8000`
- Swagger 文档：`http://localhost:8000/docs`

### 3.3 启动前端

```bash
scripts\start-frontend.bat
```

启动后访问：

- 前端地址：`http://localhost:5173`

### 3.4 同时启动前后端

```bash
scripts\start-all.bat
```

这个脚本会弹出两个命令行窗口，分别运行前端和后端。

## 4. 核心功能说明

### 4.1 数据流

凭证配置完成后，系统按以下流程工作：

1. **凭证配置** → 前端”API凭证”页面填写 vCenter 地址/端口/用户名/密码
2. **连接测试** → 点击”测试连接”验证凭证有效性
3. **快照采集** → 定时调度或手动触发采集 VMware 集群/主机/虚拟机数据
4. **共享缓存** → 采集结果缓存 180 秒，各页面复用同一数据源
5. **页面展示** → Dashboard、Inspection、Ledger、Alerts 等页面从缓存读取
6. **告警持久化** → 超阈值主机、过期快照、命名问题、闲置资产写入告警表
7. **报告导出** → 支持导出 JSON/HTML/DOCX 格式巡检报告

### 4.2 采集调度控制

系统支持灵活的采集调度配置，位于前端”设置”页面：

- **采集间隔**：可配置 1-1440 分钟，默认 5 分钟
- **自动采集开关**：可关闭自动采集，仅依赖手动触发
- **立即采集**：点击按钮后台触发采集，前端轮询进度
- **采集进度显示**：实时显示当前阶段和进度百分比
- **数据截止时间**：每页显示当前数据截至何时

采集间隔配置保存在 `backend/inspection.db` 的 `system_collection_configs` 表，迁移时自动保留。

### 4.3 报告导出

前端”报告”页面支持三种格式：

- **JSON**：原始数据结构，适合程序处理
- **HTML**：网页格式报告，浏览器直接查看
- **DOCX**：Word 文档格式，包含封面、执行摘要、平台详情、告警汇总、数据来源声明

报告文件名自动包含日期，DOCX 采用 UTF-8 编码确保中文正常显示。

## 5. API 凭证配置

首次启动后，后端会自动初始化 `backend/inspection.db`，并写入一批默认平台条目。

进入前端”API凭证”页面，给对应平台补齐连接信息：

- API 地址（如 vCenter IP 或域名）
- 端口（默认 443）
- 用户名（如 administrator@vsphere.local）
- 密码
- 是否校验 SSL 证书（内网环境通常关闭）

点击”测试连接”验证凭证有效性。只要平台接口可访问、账号权限足够，测试通过后系统即可开始拉取真实数据。

## 6. 加密密钥非常重要

后端会用环境变量 `INSPECTION_KEY` 对平台密码做加密存储。

如果你没有手动设置，它会退回到代码里的默认值；但只要你未来换成了自定义密钥，就必须在新机器保持完全一致，否则旧数据库里的密码会无法解密。

建议在目标机器启动前先设置环境变量。

Windows CMD：

```bash
set INSPECTION_KEY=your-32-byte-secret
python backend/run.py
```

PowerShell：

```bash
$env:INSPECTION_KEY="your-32-byte-secret"
python backend/run.py
```

更稳妥的做法，是把这条环境变量配置进系统环境变量或你自己的启动方式里。

## 7. 迁移到别的服务器怎么做

### 方案 A：全新迁移，不带原有凭证和历史数据

这种最干净，也最适合交付给别人：

1. 复制整个项目目录
2. 不带 `backend/inspection.db`
3. 在新机器执行 `scripts\install-deps.bat`
4. 启动后端，自动生成新的空数据库
5. 重新在“API凭证”页面录入各平台信息

### 方案 B：完整迁移，保留历史数据和已配置凭证

这种适合你自己换服务器：

1. 复制整个项目目录
2. 一并复制 `backend/inspection.db`
3. 确保新机器的 `INSPECTION_KEY` 和旧机器一致
4. 执行 `scripts\install-deps.bat`
5. 启动系统验证

如果第 3 步没做到，系统虽然能启动，但已保存的平台密码可能无法正常解密，表现通常是测试连接失败或平台拉取数据失败。

## 8. 打包成可分发目录

我已经加了一个可移植打包脚本：

```bash
scripts\package-portable.bat
```

这个脚本会生成：

```bash
dist-package/
```

处理逻辑是：

- 复制 `backend/`
- 复制 `frontend/`
- 复制 `scripts/`
- 复制 `README.md`
- 复制这份 `README_DEPLOY.md`
- 自动删除打包目录里的 `backend/inspection.db`
- 自动删除 `frontend/node_modules`
- 自动删除 `frontend/dist`

也就是说，这个打包目录默认是“可交付但不带现网数据”的安全版本。

## 9. 前端打包

如果你要先构建前端静态文件：

```bash
scripts\build-frontend.bat
```

构建产物会在：

```bash
frontend/dist
```

## 10. 最少需要一起带走哪些文件

最少带这些：

- `backend/`
- `frontend/`
- `scripts/`
- `README.md`
- `README_DEPLOY.md`

如果你要保留现有数据，再额外带上：

- `backend/inspection.db`

如果你用了自定义加密密钥，再额外保证：

- 新机器配置同样的 `INSPECTION_KEY`

## 11. 常见问题

### 前端打不开

先确认后端有没有启动，再确认前端是不是跑在 `5173` 端口。

### 前端能打开但没数据

通常是后端没启动，或者 API 凭证还没配置。

### 凭证明明存在，但迁移后连接失败

优先检查：

1. `backend/inspection.db` 是否一起迁移了
2. `INSPECTION_KEY` 是否和旧机器一致
3. 新机器到各平台 API 的网络是否可达

### 想改前后端端口

当前默认配置是：

- 后端：`backend/run.py`
- 前端代理：`frontend/vite.config.js`

如果你改了后端端口，也要同步改前端里的 `/api` 代理目标。

## 12. 建议的交付方式

如果你是发给别人直接使用，建议交付 `dist-package/` 这个目录再压缩成 zip。

这样更稳：

- 不会把你本机数据库和凭证一起带出去
- 对方解压后直接安装依赖即可
- 结构更干净，适合二次部署
