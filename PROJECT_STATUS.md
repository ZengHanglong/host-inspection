# 主机巡检系统开发进度文档

## 项目概述

**项目名称**: Host Inspection Platform (主机巡检系统)
**开发目的**: 每日巡检网站，监控虚拟化平台、云桌面、数据库、存储、备份等系统状态，检测资源临界阈值并告警
**设计风格**: Sentry-inspired Dark Purple Theme (基于 DESIGN.md)

## 技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|---------|
| 后端 | Python + FastAPI | 轻量高性能，自带 Swagger |
| 前端 | Vue 3 + Vite | SPA应用 |
| UI组件 | 无第三方组件库 | 纯手写 Sentry 风格 |
| 数据库 | SQLite | 轻量级，后期可迁移 PostgreSQL |
| 定时任务 | APScheduler | Python 定时调度 |
| HTTP客户端 | Axios | 前端 API 调用 |
| 设计系统 | DESIGN.md | Sentry 深紫黑主题 |

## 项目结构

```
host-inspection/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口 ✓
│   │   ├── config.py            # 配置管理 ✓
│   │   ├── models.py            # 数据模型 ✓
│   │   ├── database.py          # 数据库连接 ✓
│   │   ├── routers/
│   │   │   ├── inspection.py    # 巡检 API ✓
│   │   │   ├── alerts.py        # 告警 API ✓
│   │   │   ├── credentials.py   # 凭证 API ✓
│   │   │   ├── ledger.py        # 台账 API ✓
│   │   │   ├── periodic.py      # 周期巡检 API ✓
│   │   │   └── reports.py       # 报告 API ✓
│   │   ├── services/
│   │   │   ├── mock_data.py     # 模拟数据 ✓
│   │   │   ├── vmware_client.py # VMware 客户端 (待对接真实API)
│   │   │   ├── smartx_client.py # SmartX 审户端 (待对接真实API)
│   │   │   └── ...
│   │   ├── scheduler.py         # 定时任务 ✓
│   │   └── utils.py             # 工具函数 ✓
│   ├── requirements.txt         # Python 依赖 ✓
│   └── run.py                   # 启动脚本 ✓
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue    # 主仪表盘 ✓ (已重设计)
│   │   │   ├── Inspection.vue   # 每日巡检 ✓ (已重设计)
│   │   │   ├── Alerts.vue       # 告警管理 ✓ (已重设计)
│   │   │   ├── Reports.vue      # 报告生成 ✓
│   │   │   ├── History.vue      # 历史趋势 ✓
│   │   │   ├── Settings.vue     # 阈值配置 ✓
│   │   │   ├── Credentials.vue  # API凭证 ✓
│   │   │   ├── periodic/
│   │   │   │   ├── Snapshot.vue # 过期快照 ✓
│   │   │   │   ├── Naming.vue   # 命名规范 ✓
│   │   │   │   ├── IdleVM.vue   # 闲置资产 ✓
│   │   │   │   └── LargeVM.vue  # 大容量VM ✓
│   │   │   └── ledger/
│   │   │   │   ├── VmLedger.vue      # 虚拟机台账 ✓
│   │   │   │   ├── PhysicalLedger.vue # 物理机台账 ✓ (已重设计)
│   │   │   │   └── DbLedger.vue      # 数据库台账 ✓ (已重设计)
│   │   ├── router/
│   │   │   └ index.js           # 路由配置 ✓
│   │   ├── App.vue              # 主布局 ✓ (已重设计)
│   │   └ main.js                # Vue 入口 ✓
│   ├── package.json             # Node 依赖 ✓
│   ├── vite.config.js           # Vite 配置 ✓
│   └── index.html               # HTML 入口 ✓
│
├── DESIGN.md                    # Sentry 设计系统 ✓
├── PROJECT_STATUS.md            # 本文档 ✓
└── README.md                    # 项目说明 ✓
```

## 设计系统 (Sentry-inspired)

### 核心色彩

| 名称 | 色值 | 用途 |
|------|------|------|
| Primary Background | `#1f1633` | 主背景色 (深紫黑) |
| Darker Background | `#150f23` | 侧边栏、更深区域 |
| Border Purple | `#362d59` | 边框、分隔线 |
| Sentry Purple | `#6a5fc1` | 链接、hover状态、交互色 |
| Muted Purple | `#79628c` | 按钮背景 |
| Deep Violet | `#422082` | 下拉框、选择器背景 |
| Lime Green | `#c2ef4e` | 高亮accent、成功状态 |
| Coral | `#ffb287` | Focus状态背景 |
| Pink | `#fa7faa` | Focus outline |
| Warning Yellow | `#fbbf24` | 警告状态 |
| Critical Red | `#f87171` | 严重告警 |

### Typography

- **Font Family**: `Rubik`, fallback: `-apple-system, system-ui, 'Segoe UI', Helvetica, Arial`
- **Buttons**: uppercase + `letter-spacing: 0.2px`
- **Labels**: uppercase + `letter-spacing: 0.25px`
- **Weight System**: 400 (body), 500 (emphasis), 600 (titles), 700 (buttons)

### Buttons

```css
/* Primary Button - Inset Shadow Style */
.btn-primary {
  background: #79628c;
  border: 1px solid #584674;
  border-radius: 13px;
  box-shadow: rgba(0, 0, 0, 0.1) 0px 1px 3px 0px inset;
  /* Hover: elevated shadow */
}

/* Glass Button */
.btn-glass {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(18px) saturate(180%);
  border-radius: 8px;
}
```

### Glass Cards

```css
.glass-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(18px) saturate(180%);
  border: 1px solid #362d59;
  border-radius: 12px;
}
```

## API 端点

### 后端 API (FastAPI)

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/dashboard` | 仪表盘汇总数据 | ✓ |
| GET | `/api/inspection/list` | 巡检记录列表 | ✓ |
| GET | `/api/inspection/{platform}` | 按平台巡检数据 | ✓ |
| POST | `/api/inspection/run` | 手动触发巡检 | ✓ |
| GET | `/api/alerts` | 告警列表 | ✓ |
| PUT | `/api/alerts/{id}/resolve` | 解决告警 | ✓ |
| PUT | `/api/alerts/{id}/ignore` | 忽略告警 | ✓ |
| GET | `/api/history/{host}` | 主机历史趋势 | ✓ |
| GET | `/api/config/thresholds` | 阈值配置 | ✓ |
| PUT | `/api/config/thresholds` | 更新阈值 | ✓ |
| GET | `/api/credentials/list` | 平台凭证列表 | ✓ |
| POST | `/api/credentials/configure` | 配置凭证 | ✓ |
| GET | `/api/ledger/vm` | 虚拟机台账 | ✓ |
| GET | `/api/ledger/physical` | 物理机台账 | ✓ |
| GET | `/api/ledger/database` | 数据库台账 | ✓ |
| GET | `/api/periodic/snapshot` | 快照检查 | ✓ |
| GET | `/api/periodic/naming` | 命名检查 | ✓ |
| GET | `/api/periodic/idle` | 闲置资产 | ✓ |
| GET | `/api/periodic/large` | 大容量VM | ✓ |
| GET | `/api/reports/generate` | 生成报告 | ✓ |

## 前端路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | Dashboard.vue | 仪表盘 |
| `/inspection` | Inspection.vue | 每日巡检 |
| `/alerts` | Alerts.vue | 告警管理 |
| `/reports` | Reports.vue | 报告生成 |
| `/credentials` | Credentials.vue | API凭证配置 |
| `/history` | History.vue | 历史趋势 |
| `/settings` | Settings.vue | 阈值配置 |
| `/periodic/snapshot` | Snapshot.vue | 过期快照检查 |
| `/periodic/naming` | Naming.vue | VM命名规范检查 |
| `/periodic/idle` | IdleVM.vue | 闲置资产检查 |
| `/periodic/large` | LargeVM.vue | 大容量VM检查 |
| `/ledger/vm` | VmLedger.vue | 虚拟机台账 |
| `/ledger/physical` | PhysicalLedger.vue | 物理机台账 |
| `/ledger/database` | DbLedger.vue | 数据库台账 |

## 已完成页面设计重构

以下页面已按 DESIGN.md Sentry风格重新设计:

1. **App.vue** - 主布局、Header、Sidebar
   - Deep purple背景 (`#1f1633`)
   - 透明Header + frosted glass效果
   - 紧凑Sidebar (`240px`)
   - Inset shadow按钮

2. **Dashboard.vue** - 仪表盘
   - Hero section with lime-green label
   - 4-column stats grid
   - Platform cards with glass effect
   - Alert list with level indicators

3. **Inspection.vue** - 每日巡检
   - Green-tinted header border
   - Glass filter card
   - Stats cards with status colors
   - Glass table with row highlighting

4. **Alerts.vue** - 告警管理
   - Red-tinted header border
   - Metric progress bars
   - Resolve/Ignore action buttons
   - Alert level indicators

5. **DbLedger.vue** - 数据库台账
   - Lime-green icon
   - Glass stats cards
   - Usage progress bars
   - Glass table

6. **PhysicalLedger.vue** - 物理机台账
   - Yellow-gold icon
   - Platform distribution grid
   - Uptime display
   - Glass table

## 待完成页面设计

以下页面仍使用旧样式，需要重构:

- `VmLedger.vue` - 虚拟机台账
- `Reports.vue` - 报告生成
- `Credentials.vue` - API凭证
- `Settings.vue` - 阈值配置
- `History.vue` - 历史趋势
- `periodic/Snapshot.vue` - 快照检查
- `periodic/Naming.vue` - 命名规范
- `periodic/IdleVM.vue` - 闲置资产
- `periodic/LargeVM.vue` - 大容量VM

## 告警阈值配置

| 资源类型 | 警告阈值 | 严重阈值 |
|---------|---------|---------|
| CPU 使用率 | 70% | 80% |
| 内存使用率 | 70% | 80% |
| 存储使用率 | 60% | 70% |
| 快照天数 | 5天 | 7天 |

## 运行方式

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python run.py
# 访问 http://localhost:8000/docs 查看 Swagger API
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173 (或其他可用端口)
```

### Vite代理配置 (vite.config.js)

```javascript
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 模拟数据策略

当前使用模拟数据 (`mock_data.py`)，支持以下平台:

| 平台 | 模拟内容 | 状态 |
|------|---------|------|
| VMware vCenter | 3集群，每集群5-10主机 | ✓ |
| SmartX 超融合 | 1集群，10主机 | ✓ |
| 华为云桌面 | FA/FC集群状态 | ✓ |
| 深信服云桌面 | VMP/VDC主备状态 | ✓ |
| TDSQL | 集群状态、空间使用率 | ✓ |
| 存储 | 华为/Xsky/ZBS容量 | ✓ |

## 下次开发待办事项

### 1. 完成剩余页面设计重构
按 DESIGN.md 样式重构:
- VmLedger.vue
- Reports.vue
- Credentials.vue
- Settings.vue
- History.vue
- periodic/*.vue (4个页面)

### 2. 真实API对接
用户获取真实API凭证后:
1. 在 Credentials.vue 配置真实凭证
2. 修改 `services/vmware_client.py` 实现真实API调用
3. 修改 `services/smartx_client.py` 实现真实API调用
4. 测试数据采集流程

### 3. 导出功能实现
- DbLedger.vue 导出Excel
- PhysicalLedger.vue 导出Excel
- VmLedger.vue 导出Excel

### 4. 历史趋势图表
- 使用 ECharts 绑定数据
- CPU/内存/存储趋势折线图

### 5. 报告生成功能
- DOCX报告模板
- 定时生成并发送

## 重要文件路径速查

```
# 设计文档
DESIGN.md                          # Sentry设计系统完整规范

# 后端核心
backend/app/main.py                 # FastAPI路由注册
backend/app/services/mock_data.py   # 模拟数据生成核心
backend/app/scheduler.py            # 定时巡检调度

# 前端核心
frontend/src/App.vue               # 主布局(已重设计)
frontend/src/views/Dashboard.vue   # 仪表盘(已重设计)
frontend/src/router/index.js       # 路由配置

# 台账页面(已重设计)
frontend/src/views/ledger/DbLedger.vue
frontend/src/views/ledger/PhysicalLedger.vue
```

## 用户代理配置

用户使用 Clash Verge，混合端口 `7897`

```bash
# 使用代理访问GitHub
curl -x http://127.0.0.1:7897 https://github.com/...
```

## 开发记录

### 2026-04-24
1. 完成 DESIGN.md 下载并保存到项目根目录
2. 重构 App.vue - Sentry深紫黑主题
3. 重构 Dashboard.vue - Hero section、Stats grid
4. 重构 Inspection.vue - Glass cards、Table
5. 重构 Alerts.vue - Alert cards、Metric bars
6. 重构 DbLedger.vue - Glass stats、Usage bars
7. 重构 PhysicalLedger.vue - Platform distribution

---
**下次开发时**: 首先阅读 DESIGN.md 了解设计规范，然后查看此文档了解已完成进度，继续未完成的页面重构和功能实现。