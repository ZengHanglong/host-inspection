# 主机巡检系统 API 参考文档

> 版本: 3.0.0 | 基础路径: `/api` | 数据策略: 只使用真实API数据

---

## 目录

- [快速开始](#快速开始)
- [认证说明](#认证说明)
- [通用响应格式](#通用响应格式)
- [API接口列表](#api接口列表)
  - [仪表盘](#仪表盘)
  - [凭证管理](#凭证管理)
  - [巡检管理](#巡检管理)
  - [告警管理](#告警管理)
  - [台账管理](#台账管理)
  - [报告生成](#报告生成)
  - [配置管理](#配置管理)
- [数据状态说明](#数据状态说明)
- [错误码说明](#错误码说明)

---

## 快速开始

```bash
# 启动服务
cd backend && python run.py

# 访问API文档
open http://localhost:8000/docs
```

### 使用流程

1. 配置平台凭证 → `PUT /api/credentials/{platform}`
2. 测试连接 → `POST /api/credentials/{platform}/test`
3. 手动触发巡检 → `POST /api/inspection/run`
4. 查看数据 → `GET /api/dashboard`

---

## 认证说明

当前版本无认证机制，生产环境建议添加API Key或OAuth认证。

---

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

### 错误响应
```json
{
  "detail": "错误描述信息"
}
```

---

## API接口列表

### 仪表盘

#### GET /api/dashboard
获取仪表盘汇总数据，包含所有平台状态、主机统计、告警汇总等。

**响应示例:**
```json
{
  "status": "real_data",
  "last_update": "2026-05-11T17:00:00",
  "overall": {
    "total_hosts": 50,
    "normal_hosts": 45,
    "warning_hosts": 4,
    "critical_hosts": 1,
    "total_alerts": 5
  },
  "platforms": [
    {
      "platform": "vmware",
      "display_name": "VMware vCenter",
      "status": "connected",
      "data_source": "vcenter.example.com",
      "statistics": {
        "clusters": 3,
        "hosts": 10,
        "vms": 150
      }
    }
  ],
  "alerts": [...],
  "periodic_checks": [...]
}
```

---

### 凭证管理

#### GET /api/credentials/list
获取所有平台凭证配置列表。

**响应示例:**
```json
{
  "total": 7,
  "credentials": [
    {
      "id": 1,
      "platform": "vmware",
      "display_name": "VMware vCenter",
      "api_type": "pyVmomi SDK",
      "api_url": "vcenter.example.com",
      "api_port": 443,
      "api_username": "administrator@vsphere.local",
      "is_configured": true,
      "is_active": true,
      "is_connected": true,
      "last_test_at": "2026-05-11T16:00:00",
      "last_used": "2026-05-11T17:00:00"
    }
  ]
}
```

#### GET /api/credentials/{platform}
获取指定平台的凭证配置。

**路径参数:**
- `platform`: 平台标识 (vmware/smartx/huawei_cloud/sangfor_cloud/tdsql/storage/backup)

**响应示例:**
```json
{
  "id": 1,
  "platform": "vmware",
  "display_name": "VMware vCenter",
  "api_url": "vcenter.example.com",
  "api_port": 443,
  "api_username": "administrator@vsphere.local",
  "has_password": true,
  "is_configured": true,
  "is_connected": true
}
```

#### PUT /api/credentials/{platform}
更新平台凭证配置。

**请求体:**
```json
{
  "api_url": "vcenter.example.com",
  "api_port": 443,
  "api_username": "administrator@vsphere.local",
  "api_password": "your_password",
  "ssl_verify": true
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "VMware vCenter 凭证已保存",
  "platform": "vmware",
  "is_configured": true
}
```

#### POST /api/credentials/{platform}/test
测试平台API连接。

**响应示例 (成功):**
```json
{
  "platform": "vmware",
  "success": true,
  "message": "连接成功 - vCenter 7.0.3 build 19234567",
  "details": {
    "version": "7.0.3",
    "build": "19234567",
    "api_type": "VirtualCenter"
  },
  "test_time": "2026-05-11T17:00:00"
}
```

**响应示例 (失败):**
```json
{
  "platform": "vmware",
  "success": false,
  "message": "连接失败: Unable to connect to vCenter",
  "test_time": "2026-05-11T17:00:00"
}
```

#### DELETE /api/credentials/{platform}/clear
清除平台凭证配置。

**响应示例:**
```json
{
  "success": true,
  "message": "VMware vCenter 凭证已清除",
  "platform": "vmware"
}
```

#### PUT /api/credentials/{platform}/toggle
启用/禁用平台。

**查询参数:**
- `is_active`: 是否启用 (true/false)

**响应示例:**
```json
{
  "success": true,
  "message": "VMware vCenter 已启用",
  "platform": "vmware",
  "is_active": true
}
```

#### GET /api/credentials/help/{platform}
获取平台配置帮助文档。

**响应示例:**
```json
{
  "name": "VMware vCenter",
  "api_type": "pyVmomi SDK",
  "url_format": "vcenter.example.com",
  "port": 443,
  "username_format": "administrator@vsphere.local",
  "doc_url": "https://developer.vmware.com/apis/vsphere-automation/latest/",
  "setup_steps": [
    "1. 登录vCenter Server管理界面",
    "2. 创建API访问用户（建议只读权限）",
    "3. 输入vCenter地址、端口、用户名、密码",
    "4. 点击测试连接验证"
  ]
}
```

#### GET /api/credentials/help
获取所有平台配置帮助文档。

---

### 巡检管理

#### GET /api/inspection/list
获取巡检记录列表。

**查询参数:**
- `platform`: 平台筛选 (可选)
- `status`: 状态筛选 (可选, normal/warning/critical)
- `category`: 类别筛选 (可选)

**响应示例:**
```json
{
  "total": 150,
  "inspections": [
    {
      "id": 1,
      "platform": "vmware",
      "host_name": "esxi-01.example.com",
      "cluster_name": "Production",
      "check_time": "2026-05-11T17:00:00",
      "cpu_usage_percent": 45.5,
      "memory_usage_percent": 62.3,
      "status": "normal",
      "alerts": []
    }
  ]
}
```

#### GET /api/inspection/status
获取当前采集状态。

**响应示例:**
```json
{
  "is_collecting": false,
  "last_collection_time": "2026-05-11T17:00:00",
  "next_collection_time": "2026-05-11T17:05:00",
  "collection_count": 125,
  "trigger_source": "scheduled"
}
```

#### POST /api/inspection/run
手动触发巡检采集。

**响应示例:**
```json
{
  "success": true,
  "status": "started",
  "message": "巡检任务已启动",
  "collection_status": {
    "is_collecting": true,
    "trigger_source": "manual"
  }
}
```

#### GET /api/inspection/history/{host_name}
获取指定主机的历史巡检记录。

**路径参数:**
- `host_name`: 主机名称

**查询参数:**
- `days`: 历史天数 (1-365, 默认7)

**响应示例:**
```json
{
  "host_name": "esxi-01.example.com",
  "days": 7,
  "history": [
    {
      "check_time": "2026-05-11T17:00:00",
      "cpu_usage_percent": 45.5,
      "memory_usage_percent": 62.3,
      "status": "normal"
    }
  ],
  "trend": {
    "cpu_avg": 42.3,
    "memory_avg": 60.1
  }
}
```

#### GET /api/inspection/{platform}
获取指定平台的巡检数据。

**路径参数:**
- `platform`: 平台标识

**响应示例:**
```json
{
  "platform": "vmware",
  "display_name": "VMware vCenter",
  "status": "connected",
  "statistics": {
    "clusters": 3,
    "hosts": 10,
    "vms": 150,
    "normal": 8,
    "warning": 1,
    "critical": 1
  },
  "hosts": [...]
}
```

#### GET /api/inspection/periodic/snapshot
获取过期快照检查结果。

**响应示例:**
```json
{
  "total": 5,
  "warning_days": 5,
  "critical_days": 7,
  "data": [
    {
      "vm_name": "test-vm-01",
      "snapshot_name": "backup-20260501",
      "create_time": "2026-05-01T10:00:00",
      "age_days": 10,
      "size_gb": 50,
      "severity": "critical",
      "action": "建议立即删除或验证快照用途"
    }
  ]
}
```

#### GET /api/inspection/periodic/large-vm
获取大容量虚拟机检查结果。

**响应示例:**
```json
{
  "total": 3,
  "threshold_gb": 500,
  "data": [
    {
      "vm_name": "database-server",
      "ip": "192.168.1.100",
      "total_disk_gb": 1200,
      "provisioned_gb": 1500,
      "used_gb": 800,
      "cpu": 16,
      "memory_gb": 64,
      "action": "评估磁盘使用情况，清理不必要的数据"
    }
  ]
}
```

#### GET /api/inspection/periodic/naming
获取命名规范检查结果。

**响应示例:**
```json
{
  "total": 2,
  "rules": {
    "备注格式": "业务系统-负责人-环境",
    "命名格式": "xxx-xxx-xxx",
    "命名规则": "遵循公司命名规范"
  },
  "data": [
    {
      "vm_name": "test-vm-01",
      "ip": "192.168.1.50",
      "current_note": "测试用",
      "issues": ["备注不符合格式", "缺少负责人信息"],
      "check_time": "2026-05-11T17:00:00"
    }
  ]
}
```

#### GET /api/inspection/periodic/idle-vm
获取闲置虚拟机检查结果。

**响应示例:**
```json
{
  "total": 2,
  "rule": "涉及克隆、备份恢复的虚拟机，如果不是长期使用，虚拟机名一律tmp-开头，备注一律临时-开头",
  "data": [
    {
      "vm_name": "clone-test-01",
      "ip": "192.168.1.60",
      "note": "克隆测试",
      "cpu": 4,
      "memory_gb": 16,
      "disk_gb": 100,
      "power_state": "poweredOff",
      "created_days": 30,
      "action": "建议删除或按规范命名"
    }
  ]
}
```

---

### 告警管理

#### GET /api/alerts/
获取告警列表。

**查询参数:**
- `status`: 告警状态 (active/resolved/ignored)
- `level`: 告警级别 (warning/critical)
- `platform`: 平台筛选
- `category`: 类别筛选
- `alert_type`: 告警类型
- `limit`: 返回数量限制 (默认100)

**响应示例:**
```json
{
  "total": 5,
  "alerts": [
    {
      "id": 1,
      "platform": "vmware",
      "platform_name": "VMware vCenter",
      "host_name": "esxi-01.example.com",
      "alert_type": "cpu_usage",
      "alert_level": "warning",
      "message": "CPU使用率超过阈值: 85%",
      "status": "active",
      "triggered_at": "2026-05-11T16:30:00",
      "data_source": "vcenter.example.com"
    }
  ]
}
```

#### PUT /api/alerts/{alert_id}/resolve
解决告警。

**响应示例:**
```json
{
  "success": true,
  "message": "告警 1 已标记为已解决",
  "resolved_at": "2026-05-11T17:00:00"
}
```

#### PUT /api/alerts/{alert_id}/ignore
忽略告警。

**响应示例:**
```json
{
  "success": true,
  "message": "告警 1 已标记为已忽略",
  "ignored_at": "2026-05-11T17:00:00"
}
```

#### GET /api/alerts/statistics
获取告警统计。

**响应示例:**
```json
{
  "total_alerts": 10,
  "by_level": {
    "warning": 7,
    "critical": 3
  },
  "by_platform": {
    "vmware": 5,
    "smartx": 3,
    "huawei_cloud": 2
  },
  "by_type": {
    "cpu_usage": 4,
    "memory_usage": 3,
    "storage_usage": 3
  }
}
```

#### GET /api/alerts/thresholds
获取告警阈值配置。

**响应示例:**
```json
{
  "thresholds": {
    "cpu": {
      "warning": 70.0,
      "critical": 80.0
    },
    "memory": {
      "warning": 70.0,
      "critical": 80.0
    },
    "storage": {
      "warning": 60.0,
      "critical": 70.0
    }
  }
}
```

---

### 台账管理

#### GET /api/ledger/vm
获取虚拟机台账。

**查询参数:**
- `platform`: 平台筛选 (可选)
- `cluster`: 集群筛选 (可选)
- `owner`: 负责人筛选 (可选)
- `environment`: 环境筛选 (可选)
- `has_snapshot`: 是否有快照 (可选)

**响应示例:**
```json
{
  "total": 150,
  "status": "real_data",
  "statistics": {
    "total_vms": 150,
    "powered_on": 120,
    "powered_off": 30,
    "by_platform": {
      "vmware": 100,
      "smartx": 50
    }
  },
  "data": [
    {
      "vm_name": "app-server-01",
      "ip": "192.168.1.10",
      "platform": "vmware",
      "cluster": "Production",
      "cpu": 4,
      "memory_gb": 16,
      "disk_gb": 200,
      "power_state": "poweredOn",
      "os_type": "Linux",
      "has_snapshot": false,
      "owner": "张三",
      "environment": "production",
      "note": "业务系统-张三-生产"
    }
  ]
}
```

#### GET /api/ledger/physical
获取物理机台账。

**查询参数:**
- `platform`: 平台筛选 (可选)
- `cluster`: 集群筛选 (可选)

**响应示例:**
```json
{
  "total": 10,
  "status": "real_data",
  "statistics": {
    "total_hosts": 10,
    "total_cpu_cores": 240,
    "total_memory_gb": 2048,
    "by_platform": {
      "vmware": 6,
      "smartx": 4
    }
  },
  "data": [
    {
      "platform": "vmware",
      "platform_name": "VMware vCenter",
      "cluster": "Production",
      "host_name": "esxi-01.example.com",
      "ip": "192.168.1.101",
      "mgmt_ip": "192.168.100.101",
      "cpu": 24,
      "memory_gb": 256,
      "host_type": "ESXi",
      "uptime_days": 120,
      "status": "online"
    }
  ]
}
```

#### GET /api/ledger/database
获取数据库台账。

**响应示例:**
```json
{
  "total": 5,
  "statistics": {
    "total_hosts": 5,
    "total_space_gb": 5000,
    "used_space_gb": 3500,
    "avg_space_usage": 70
  },
  "data": [
    {
      "db_name": "TDSQL",
      "cluster": "tdsql-cluster-01",
      "host_name": "tdsql-01.example.com",
      "ip": "192.168.2.10",
      "db_type": "MySQL",
      "version": "5.7.35",
      "total_space_gb": 1000,
      "used_space_gb": 750,
      "space_usage": 75,
      "status": "online"
    }
  ]
}
```

#### GET /api/ledger/summary
获取台账汇总。

**响应示例:**
```json
{
  "vm": {
    "total": 150,
    "by_platform": {"vmware": 100, "smartx": 50}
  },
  "physical": {
    "total": 10,
    "by_platform": {"vmware": 6, "smartx": 4}
  },
  "database": {
    "total": 5,
    "by_type": {"TDSQL": 3, "Gbase": 2}
  }
}
```

---

### 报告生成

#### GET /api/report/daily
生成每日巡检报告。

**查询参数:**
- `format`: 报告格式 (json/html, 默认json)
- `include_empty`: 是否包含未配置的平台 (默认false)

**响应示例 (JSON):**
```json
{
  "report_type": "每日巡检报告",
  "report_time": "2026-05-11T17:00:00",
  "generated_by": "主机巡检系统",
  "data_declaration": "本报告数据来源: VMware vCenter (vcenter.example.com)",
  "overall_summary": {
    "total_platforms": 7,
    "configured_platforms": 1,
    "connected_platforms": 1
  },
  "overall_statistics": {
    "total_hosts": 10,
    "normal_hosts": 8,
    "warning_hosts": 1,
    "critical_hosts": 1,
    "total_alerts": 2
  },
  "data_sources": ["vcenter.example.com"],
  "platforms": [...],
  "warnings": [...],
  "errors": []
}
```

#### GET /api/report/snapshot
生成快照检查报告。

**响应示例:**
```json
{
  "report_type": "快照检查报告",
  "report_time": "2026-05-11T17:00:00",
  "total_snapshots": 50,
  "expired_count": 5,
  "by_platform": {...},
  "details": [...]
}
```

#### GET /api/report/download/html
下载HTML格式报告。

**响应:** HTML文件下载

#### GET /api/report/download/docx
下载DOCX格式报告。

**查询参数:**
- `company_name`: 公司名称 (默认"厦门国际信托")

**响应:** DOCX文件下载

---

### 配置管理

#### GET /api/config/thresholds
获取阈值配置。

**响应示例:**
```json
{
  "thresholds": [
    {
      "id": 1,
      "resource_type": "cpu",
      "warning_threshold": 70.0,
      "critical_threshold": 80.0,
      "is_active": true
    },
    {
      "id": 2,
      "resource_type": "memory",
      "warning_threshold": 70.0,
      "critical_threshold": 80.0,
      "is_active": true
    },
    {
      "id": 3,
      "resource_type": "storage",
      "warning_threshold": 60.0,
      "critical_threshold": 70.0,
      "is_active": true
    }
  ]
}
```

#### PUT /api/config/thresholds/{resource_type}
更新阈值配置。

**路径参数:**
- `resource_type`: 资源类型 (cpu/memory/storage)

**请求体:**
```json
{
  "warning_threshold": 75.0,
  "critical_threshold": 85.0,
  "is_active": true
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "cpu 阈值已更新",
  "threshold": {
    "resource_type": "cpu",
    "warning_threshold": 75.0,
    "critical_threshold": 85.0,
    "is_active": true
  }
}
```

#### GET /api/config/platforms
获取平台配置列表。

#### PUT /api/config/platforms/{platform_id}
更新平台配置。

**请求体:**
```json
{
  "api_url": "vcenter.example.com",
  "api_port": 443,
  "api_username": "administrator@vsphere.local",
  "api_password": "password",
  "ssl_verify": true,
  "is_active": true
}
```

#### POST /api/config/platforms/{platform_id}/test
测试平台连接。

#### GET /api/config/collection
获取采集配置。

**响应示例:**
```json
{
  "interval_minutes": 5,
  "auto_enabled": true,
  "updated_at": "2026-05-11T16:00:00",
  "status": {
    "is_collecting": false,
    "last_collection_time": "2026-05-11T17:00:00",
    "next_collection_time": "2026-05-11T17:05:00"
  }
}
```

#### PUT /api/config/collection
更新采集配置。

**请求体:**
```json
{
  "interval_minutes": 10,
  "auto_enabled": true
}
```

---

## 数据状态说明

| 状态值 | 说明 |
|--------|------|
| `real_data` | 真实数据，已连接平台API获取 |
| `no_credentials` | 未配置API凭证 |
| `partial_data` | 部分平台数据获取失败 |
| `collection_failed` | 数据采集失败 |
| `error` | 系统错误 |

---

## 错误码说明

| HTTP状态码 | 说明 |
|------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 支持的平台

| 平台标识 | 显示名称 | API类型 | 默认端口 |
|----------|----------|---------|----------|
| `vmware` | VMware vCenter | pyVmomi SDK | 443 |
| `smartx` | SmartX CloudTower | CloudTower API | 443 |
| `huawei_cloud` | 华为云桌面 | REST API | 443 |
| `sangfor_cloud` | 深信服云桌面 | REST API | 443 |
| `tdsql` | TDSQL赤兔 | REST API | 8080 |
| `storage` | 存储系统 | REST API | 443 |
| `backup` | 备份系统 | REST API | 443 |

---

## AI操作示例

### 1. 配置VMware并获取数据

```bash
# 步骤1: 配置凭证
curl -X PUT http://localhost:8000/api/credentials/vmware \
  -H "Content-Type: application/json" \
  -d '{
    "api_url": "vcenter.example.com",
    "api_port": 443,
    "api_username": "administrator@vsphere.local",
    "api_password": "your_password",
    "ssl_verify": false
  }'

# 步骤2: 测试连接
curl -X POST http://localhost:8000/api/credentials/vmware/test

# 步骤3: 触发巡检
curl -X POST http://localhost:8000/api/inspection/run

# 步骤4: 获取仪表盘数据
curl http://localhost:8000/api/dashboard

# 步骤5: 获取告警列表
curl "http://localhost:8000/api/alerts/?status=active&level=critical"

# 步骤6: 下载报告
curl -o report.docx "http://localhost:8000/api/report/download/docx?company_name=测试公司"
```

### 2. 更新阈值配置

```bash
# 更新CPU阈值
curl -X PUT http://localhost:8000/api/config/thresholds/cpu \
  -H "Content-Type: application/json" \
  -d '{"warning_threshold": 75, "critical_threshold": 85}'

# 查看当前阈值
curl http://localhost:8000/api/config/thresholds
```

### 3. 处理告警

```bash
# 查看活跃告警
curl "http://localhost:8000/api/alerts/?status=active"

# 解决告警
curl -X PUT http://localhost:8000/api/alerts/1/resolve

# 忽略告警
curl -X PUT http://localhost:8000/api/alerts/2/ignore
```

### 4. 获取台账数据

```bash
# 虚拟机台账
curl "http://localhost:8000/api/ledger/vm?platform=vmware"

# 物理机台账
curl "http://localhost:8000/api/ledger/physical"

# 数据库台账
curl http://localhost:8000/api/ledger/database

# 台账汇总
curl http://localhost:8000/api/ledger/summary
```

### 5. 周期性巡检

```bash
# 过期快照
curl http://localhost:8000/api/inspection/periodic/snapshot

# 大容量VM
curl http://localhost:8000/api/inspection/periodic/large-vm

# 命名规范
curl http://localhost:8000/api/inspection/periodic/naming

# 闲置资产
curl http://localhost:8000/api/inspection/periodic/idle-vm
```

---

## 注意事项

1. **数据策略**: 系统只使用真实API数据，无模拟数据
2. **凭证安全**: 密码使用AES-256-CBC加密存储
3. **缓存机制**: 数据缓存180秒，可通过手动触发刷新
4. **并发限制**: 同一时间只能执行一次数据采集
5. **SSL验证**: 建议生产环境开启SSL验证

---

*文档生成时间: 2026-05-11*
