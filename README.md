# 主机巡检系统 v2.0

企业级每日巡检网站，用于监控虚拟化平台、云桌面、数据库、存储、备份等系统状态。

## 巡检内容（完整版）

### 每日巡检（11项）

| 类别 | 项目 | 巡检内容 | 状态监控 |
|------|------|---------|---------|
| 虚拟化 | VMware虚拟化 | 集群状态 | ✓ |
| 虚拟化 | SmartX超融合 | 集群状态 | ✓ |
| 云桌面 | 华为云桌面 | 集群状态(fa/fc) | ✓ |
| 云桌面 | 深信服云桌面 | 集群状态(主备机房vmp/vdc) | ✓ |
| 数据库 | Gbase/CDH | 集群状态 | ✓ |
| 数据库 | TDSQL赤兔 | 集群状态、告警、空间 | ✓ |
| 日志易 | 监控大屏/日志量 | 数据库同步状态、表空间 | ✓ |
| 存储 | 存储系统 | 华为存储、xsky、zbs、华瑞对象存储 | ✓ |
| 备份 | 备份系统 | 鼊甲、NBU、veeam、zerto任务状态 | ✓ |
| 九桥数据同步 | 九桥数据同步 | 任务状态 | ✓ |

### 周期性巡检（4项）

| 项目 | 巡检内容 | 周期 | 阈值 |
|------|---------|------|------|
| 过期快照 | 删除超过7天的快照 | 每周五 | 7天 |
| 备注/命名维护 | 格式规范化检查 | 每周五 | - |
| 闲置资产排查 | tmp-开头虚拟机清理 | 每月 | - |
| 大容量虚拟机排查 | >1TB虚拟机定位 | 每季度 | 1TB |

### 台账管理

- **虚拟机台账**: 集群/主机名/IP/CPU/内存/系统名/功能/负责人/状态
- **物理机台账**: 集群/主机名/IP/管理IP/CPU/内存/账号密码
- **数据库台账**: 集群/主机名/IP/类型/版本/空间/状态

## 告警阈值

| 资源类型 | 警告阈值 | 严重阈值 |
|---------|---------|---------|
| CPU使用率 | 70% | 80% |
| 内存使用率 | 70% | 80% |
| 存储使用率 | 60% | 70% |
| 表空间使用率 | 80% | 90% |
| 快照天数 | 5天 | 7天 |

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Python + FastAPI | 高性能REST API |
| 前端 | Vue 3 + Element Plus | 企业级浅色风格UI |
| 数据库 | SQLite | 轻量级存储，可迁移PostgreSQL |
| 定时任务 | APScheduler | 每日自动巡检 |
| 可视化 | ECharts | 资源趋势图表 |

## 快速启动

### 1. 启动后端

```bash
cd host-inspection/backend
pip install -r requirements.txt
python run.py
```

访问 http://localhost:8000/docs 查看 API 文档

### 2. 启动前端

```bash
cd host-inspection/frontend
npm install
npm run dev
```

访问 http://localhost:5173 查看巡检网站

## 项目结构

```
host-inspection/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI入口
│   │   ├── database.py          # 数据模型
│   │   ├── routers/
│   │   │   ├── inspection.py    # 每日巡检API
│   │   │   ├── alerts.py        # 告警API
│   │   │   ├── ledger.py        # 台账API
│   │   │   └── periodic.py      # 周期性巡检API
│   │   ├── services/
│   │   │   ├── mock_data.py     # 模拟数据生成器
│   │   │   ├── vmware_client.py # VMware真实API(待实现)
│   │   │   └── smartx_client.py # SmartX真实API(待实现)
│   │   └── scheduler.py         # 定时巡检任务
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue    # 仪表盘
│   │   │   ├── Inspection.vue   # 每日巡检详情
│   │   │   ├── Alerts.vue       # 告警管理
│   │   │   ├── periodic/        # 周期性巡检页面
│   │   │   └── ledger/          # 台账管理页面
│   │   └── assets/styles/main.css # 企业级浅色风格
│   └── package.json
└── README.md
```

## 页面功能

| 页面 | 功能说明 |
|------|---------|
| **仪表盘** | 按类别展示11个巡检项状态、周期性巡检提醒、活跃告警 |
| **每日巡检** | 所有平台主机列表、巡检内容详情、筛选功能 |
| **过期快照** | 超过7天的快照列表、待删除提示 |
| **命名规范** | 备注格式/命名格式不规范的VM列表 |
| **闲置资产** | tmp-开头的临时VM列表、清理建议 |
| **大容量VM** | 磁盘超过1TB的VM列表 |
| **告警管理** | 活跃告警、解决/忽略操作 |
| **虚拟机台账** | 所有VM清单、统计汇总 |
| **物理机台账** | 所有物理主机清单 |
| **数据库台账** | TDSQL/Gbase/CDH清单 |
| **历史趋势** | CPU/内存/存储趋势图表 |
| **配置管理** | 阈值设置、API凭证配置 |

## 切换真实数据

### 当前状态
系统使用模拟数据进行演示测试。

### 切换步骤
1. 获取 VMware vCenter API 凭证
   - 联系 VMware 管理员创建 API 用户
   - API地址: https://vcenter-host/sdk
   - 文档: https://developer.vmware.com/apis/vsphere-automation/latest/

2. 获取 SmartX API 凭证
   - 联系 SmartX 技术支持获取 API 权限
   - 在 SMTX OS 管理界面创建 API 用户

3. 在配置管理页面输入凭证
   - 访问"配置管理" → "平台配置"
   - 输入 API 地址、用户名、密码
   - 关闭"模拟数据"开关

4. 系统自动切换为真实 API 调用

### 实现真实 API

需要修改以下文件：

```python
# backend/app/services/vmware_client.py
from pyVmomi import vim, vmodl
import ssl

class VMwareClient:
    def __init__(self, host, user, password):
        self.si = connect_to_vcenter(host, user, password)

    def get_cluster_status(self):
        # 获取真实集群状态
        ...

    def get_host_resources(self):
        # 获取真实资源使用率
        ...

# backend/app/services/smartx_client.py
import requests

class SmartXClient:
    def __init__(self, host, user, password):
        self.api_url = f"https://{host}/api"
        self.token = self._login()

    def get_cluster_status(self):
        # 获取真实集群状态
        ...
```

## API 凭证获取指南

### VMware vCenter

1. 登录 vCenter Server
2. 创建服务账户并分配权限（建议只读权限）
3. 测试 API 连接:
   ```bash
   curl -k https://vcenter-host/sdk
   ```

### SmartX

1. 联系 SmartX 技术支持申请 API 权限
2. 在 SMTX OS 管理界面创建 API 用户
3. 获取 API 文档和端点地址

### 其他平台

| 平台 | API获取方式 |
|------|------------|
| 华为云桌面 | FA/FC管理界面 |
| 深信服云桌面 | VMP/VDC管理界面 |
| TDSQL赤兔 | 赤兔平台API |
| 存储系统 | 各存储厂商API文档 |
| 备份系统 | 备份软件API |

## 后续开发

- [ ] 实现 VMware vCenter 真实 API 客户端
- [ ] 实现 SmartX 真实 API 客户端
- [ ] 添加邮件/钉钉告警通知
- [ ] 添加导出巡检报告功能
- [ ] 添加历史数据持久化存储
- [ ] 集成更多平台API