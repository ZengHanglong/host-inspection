# PostgreSQL 数据库迁移设计文档

**项目**: 主机巡检系统  
**版本**: v1.0  
**日期**: 2026-05-27  
**状态**: 设计确认完成

---

## 一、决策汇总

| 决策项 | 结论 | 理由 |
|--------|------|------|
| 主键策略 | BIGSERIAL + uid (VARCHAR(36)) | 多实例写同一个 PG，BIGSERIAL 性能最优；uid 用于 API/导出 |
| 平台结构 | 三层：plt_platform → plt_instance → 平台专用表 | 统一凭证管理，平台扩展灵活 |
| 环境层级 | dev / pre / ser，绑定在实例层 | 每个 vCenter/SmartX 实例固定属于一个环境 |
| 平台范围 | 16 个平台全部设计，分批实现 | 前后端有一致参照，新平台接入不用改结构 |
| 告警系统 | 统一 alert_rule，混合生命周期 | 指标类自动恢复，事件类手动处理 |
| 通知渠道 | 邮件 + 钉钉 + 企业微信 | 全覆盖 |
| 指标保留 | 1 个月，5 分钟粒度 | 数据量可控，定期清理 |
| 巡检 vs 指标 | 分开存储 | inspection_records 存快照结果，metric 存原始时序 |
| 资产管理 | 平台专用表取代通用资产表 | 避免字段冗余，UNION ALL 跨平台查询 |
| 跨平台查询 | VIEW (UNION ALL) + 资源索引表 | VIEW 用于仪表盘/台账，索引表用于全局搜索 |
| 巡检任务 | 全局统一 5 分钟 | 所有平台同一采集频率 |
| 数据迁移 | 全新开始 | 不迁移 SQLite 旧数据 |
| 用户权限 | 不需要 | 内部网络使用 |

---

## 二、数据库总体架构

### 2.1 层级关系

```
ast_environment (dev / pre / ser)
    └── plt_instance (具体平台实例，含凭证和连接配置)
            └── {platform}_cluster (集群/分组)
                    └── {platform}_host (主机/节点)
                            └── {platform}_vm (虚拟机/桌面)
```

### 2.2 表分类

| 分类 | 表数量 | 说明 |
|------|--------|------|
| 核心基础设施 | 5 | 平台定义、实例、环境、索引、系统配置 |
| 告警与巡检 | 6 | 规则、记录、渠道、策略、任务、执行 |
| VMware 专用 | 8 | 集群、主机、VM、数据存储、快照、指标、事件、任务 |
| SmartX 专用 | 6 | 集群、主机、VM、卷、快照、指标 |
| 华为云桌面 | 5 | 集群、宿主机、桌面、桌面池、指标 |
| 深信服云桌面 | 5 | 集群、宿主机、桌面、桌面池、指标 |
| Oracle | 4 | 实例、表空间、会话、指标 |
| MySQL | 4 | 实例、数据库、连接、指标 |
| Gbase | 4 | 实例、集群、节点、指标 |
| TDSQL | 4 | 实例、集群、节点、指标 |
| 华为存储 | 5 | 设备、存储池、卷、磁盘、指标 |
| XSKY | 5 | 集群、节点、卷、磁盘、指标 |
| 华瑞存储 | 4 | 设备、存储池、卷、指标 |
| SmartX ZBS | 4 | 集群、节点、卷、指标 |
| Veeam | 4 | 服务器、任务、恢复点、指标 |
| 鼎甲 | 4 | 服务器、任务、任务详情、指标 |
| Zerto | 4 | 服务器、VPG、VM、指标 |
| 日志易 | 4 | 实例、索引、仪表盘、指标 |
| **合计** | **~89** | |

---

## 三、核心基础设施表

### 3.1 plt_platform（平台类型字典）

```sql
CREATE TABLE plt_platform (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(30) UNIQUE NOT NULL,    -- vmware, smartx, huawei_storage
    name        VARCHAR(100) NOT NULL,          -- VMware vCenter
    category    VARCHAR(30) NOT NULL,           -- virtualization, cloud_desktop, database, storage, backup, monitoring
    api_type    VARCHAR(20),                    -- pyvmomi, rest, ssh
    icon        VARCHAR(50),
    sort_order  INT DEFAULT 0,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE plt_platform IS '平台类型字典，定义支持的平台种类';
COMMENT ON COLUMN plt_platform.code IS '平台唯一标识码，如 vmware, smartx';
COMMENT ON COLUMN plt_platform.category IS '平台类别：virtualization/cloud_desktop/database/storage/backup/monitoring';
```

**初始数据：**

| code | name | category | api_type |
|------|------|----------|----------|
| vmware | VMware vCenter | virtualization | pyvmomi |
| smartx | SmartX 超融合 | virtualization | rest |
| huawei_cd | 华为云桌面 | cloud_desktop | rest |
| sangfor_cd | 深信服云桌面 | cloud_desktop | rest |
| oracle | Oracle | database | rest |
| mysql | MySQL | database | rest |
| gbase | Gbase | database | rest |
| tdsql | TDSQL | database | rest |
| hwstorage | 华为存储 | storage | rest |
| xsky | XSKY 存储 | storage | rest |
| huarui | 华瑞存储 | storage | rest |
| smartxzbs | SmartX ZBS | storage | rest |
| veeam | Veeam 备份 | backup | rest |
| dingjia | 鼎甲备份 | backup | rest |
| zerto | Zerto 容灾 | backup | rest |
| rizhiyi | 日志易 | monitoring | rest |

### 3.2 ast_environment（环境定义）

```sql
CREATE TABLE ast_environment (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(10) UNIQUE NOT NULL,    -- dev, pre, ser
    name        VARCHAR(50) NOT NULL,           -- 测试环境, 准生产环境, 生产环境
    sort_order  INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ast_environment IS '环境定义：测试(dev)、准生产(pre)、生产(ser)';
```

**初始数据：**

| code | name | sort_order |
|------|------|------------|
| dev | 测试环境 | 1 |
| pre | 准生产环境 | 2 |
| ser | 生产环境 | 3 |

### 3.3 plt_instance（平台实例）

```sql
CREATE TABLE plt_instance (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    platform_id     BIGINT NOT NULL REFERENCES plt_platform(id),
    environment     VARCHAR(10) NOT NULL REFERENCES ast_environment(code),
    instance_name   VARCHAR(100) NOT NULL,      -- "生产vCenter-01"
    description     TEXT,

    -- API 连接信息
    api_url         VARCHAR(500),
    api_port        INT,
    api_username    VARCHAR(100),
    api_password    VARCHAR(500),               -- AES-256 加密存储
    api_key         VARCHAR(500),
    api_token       VARCHAR(500),
    api_type        VARCHAR(20),                -- pyvmomi, rest, ssh

    -- SSL 配置
    requires_ssl    BOOLEAN DEFAULT TRUE,
    ssl_verify      BOOLEAN DEFAULT TRUE,

    -- 连接状态
    is_configured   BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE,
    is_connected    BOOLEAN DEFAULT FALSE,
    last_error      TEXT,
    last_test_at    TIMESTAMPTZ,
    last_sync_at    TIMESTAMPTZ,

    -- 采集配置
    collect_interval_minutes INT DEFAULT 5,     -- 采集间隔，默认5分钟

    -- 时间戳
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_instance_platform ON plt_instance(platform_id);
CREATE INDEX idx_instance_env ON plt_instance(environment);
CREATE INDEX idx_instance_active ON plt_instance(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE plt_instance IS '所有平台实例，统一管理凭证和连接配置';
COMMENT ON COLUMN plt_instance.environment IS '所属环境：dev/pre/ser';
COMMENT ON COLUMN plt_instance.collect_interval_minutes IS '采集间隔（分钟），覆盖全局默认值';
```

### 3.4 ast_resource_index（资源搜索索引）

```sql
CREATE TABLE ast_resource_index (
    id              BIGSERIAL PRIMARY KEY,
    platform        VARCHAR(30) NOT NULL,       -- vmware, smartx...
    instance_id     BIGINT NOT NULL,
    environment     VARCHAR(10) NOT NULL,
    resource_type   VARCHAR(20) NOT NULL,       -- host, vm, cluster, storage, volume, desktop
    resource_id     BIGINT NOT NULL,            -- 指向具体平台表的 id
    name            VARCHAR(200),
    ip_address      VARCHAR(50),
    extra           JSONB,                      -- 其他可搜索字段
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_resource_platform ON ast_resource_index(platform);
CREATE INDEX idx_resource_type ON ast_resource_index(resource_type);
CREATE INDEX idx_resource_ip ON ast_resource_index(ip_address);
CREATE INDEX idx_resource_name ON ast_resource_index USING gin(to_tsvector('simple', name));
CREATE INDEX idx_resource_env ON ast_resource_index(environment);

COMMENT ON TABLE ast_resource_index IS '跨平台资源搜索索引，采集时同步写入';
```

### 3.5 cfg_system（系统配置）

```sql
CREATE TABLE cfg_system (
    id              BIGSERIAL PRIMARY KEY,
    config_key      VARCHAR(100) UNIQUE NOT NULL,
    config_value    TEXT,
    value_type      VARCHAR(20) DEFAULT 'string',   -- string, int, bool, json
    description     VARCHAR(500),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE cfg_system IS '系统配置键值对';
```

**初始配置项：**

| config_key | config_value | value_type | description |
|------------|--------------|------------|-------------|
| global_collect_interval | 5 | int | 全局采集间隔（分钟） |
| metrics_retention_days | 30 | int | 指标数据保留天数 |
| alert_auto_resolve | true | bool | 指标类告警是否自动恢复 |

---

## 四、告警与巡检表

### 4.1 alert_rule（告警规则）

```sql
CREATE TABLE alert_rule (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    rule_code       VARCHAR(50) UNIQUE NOT NULL,    -- cpu_high, snapshot_expired
    rule_name       VARCHAR(100) NOT NULL,           -- "CPU使用率过高"
    category        VARCHAR(30) NOT NULL,            -- metric, inspection, event
    target_type     VARCHAR(30) NOT NULL,            -- host, vm, snapshot, storage

    -- 条件定义
    condition_type  VARCHAR(20) NOT NULL,            -- threshold, pattern, presence
    resource_type   VARCHAR(30),                     -- cpu, memory, storage（threshold 类型用）
    warning_value   DOUBLE PRECISION,                -- 警告阈值
    critical_value  DOUBLE PRECISION,                -- 严重阈值
    config          JSONB,                           -- 其他条件参数

    -- 告警属性
    alert_level     VARCHAR(20) DEFAULT 'warning',   -- warning, critical
    is_active       BOOLEAN DEFAULT TRUE,
    description     TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rule_category ON alert_rule(category);
CREATE INDEX idx_rule_target ON alert_rule(target_type);
CREATE INDEX idx_rule_active ON alert_rule(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE alert_rule IS '统一告警规则，包含指标阈值、巡检规则、事件规则';
COMMENT ON COLUMN alert_rule.category IS '规则类别：metric(指标)/inspection(巡检)/event(事件)';
COMMENT ON COLUMN alert_rule.condition_type IS '条件类型：threshold(阈值)/pattern(模式匹配)/presence(存在性)';
```

**初始规则数据：**

| rule_code | rule_name | category | target_type | condition_type | warning | critical |
|-----------|-----------|----------|-------------|----------------|---------|----------|
| cpu_high | CPU使用率过高 | metric | host | threshold | 70 | 80 |
| memory_high | 内存使用率过高 | metric | host | threshold | 70 | 80 |
| storage_high | 存储使用率过高 | metric | host | threshold | 60 | 70 |
| table_space_high | 表空间使用率过高 | metric | database | threshold | 80 | 90 |
| snapshot_expired | 快照超过保留期 | inspection | snapshot | threshold | 5天 | 7天 |
| naming_violation | 命名/备注不规范 | inspection | vm | pattern | - | - |
| idle_vm | 闲置虚拟机 | inspection | vm | presence | - | - |
| large_vm | 大容量虚拟机(>1TB) | inspection | vm | threshold | - | 1TB |

### 4.2 alert_record（告警记录）

```sql
CREATE TABLE alert_record (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    rule_id         BIGINT NOT NULL REFERENCES alert_rule(id),

    -- 告警来源
    platform        VARCHAR(30) NOT NULL,
    instance_id     BIGINT,
    environment     VARCHAR(10),

    -- 关联资源（polymorphic reference）
    resource_type   VARCHAR(30) NOT NULL,       -- host, vm, snapshot, storage
    resource_id     BIGINT,
    resource_name   VARCHAR(200),

    -- 告警内容
    alert_level     VARCHAR(20) NOT NULL,       -- warning, critical
    message         TEXT,
    threshold_value DOUBLE PRECISION,
    current_value   DOUBLE PRECISION,

    -- 生命周期
    status          VARCHAR(20) NOT NULL DEFAULT 'active',   -- active, resolved, ignored
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ,
    resolved_by     VARCHAR(50),                -- auto, manual
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(50),
    notes           TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_status ON alert_record(status);
CREATE INDEX idx_alert_level ON alert_record(alert_level);
CREATE INDEX idx_alert_platform ON alert_record(platform);
CREATE INDEX idx_alert_triggered ON alert_record(triggered_at);
CREATE INDEX idx_alert_resource ON alert_record(resource_type, resource_id);

COMMENT ON TABLE alert_record IS '告警记录，永久保留历史';
COMMENT ON COLUMN alert_record.status IS '告警状态：active(活跃)/resolved(已恢复)/ignored(已忽略)';
COMMENT ON COLUMN alert_record.resolved_by IS '恢复方式：auto(自动)/manual(手动)';
```

### 4.3 alert_channel（通知渠道）

```sql
CREATE TABLE alert_channel (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    channel_code    VARCHAR(50) UNIQUE NOT NULL,    -- email_ops, dingtalk_ser, wechat_dev
    channel_name    VARCHAR(100) NOT NULL,           -- "运维邮件组"
    channel_type    VARCHAR(20) NOT NULL,            -- email, dingtalk, wechat

    -- 渠道配置（JSON 存储不同渠道的参数）
    config          JSONB NOT NULL,

    -- 状态
    is_active       BOOLEAN DEFAULT TRUE,
    last_sent_at    TIMESTAMPTZ,
    last_error      TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE alert_channel IS '告警通知渠道';
COMMENT ON COLUMN alert_channel.channel_type IS '渠道类型：email(邮件)/dingtalk(钉钉)/wechat(企业微信)';
COMMENT ON COLUMN alert_channel.config IS '渠道配置JSON，不同渠道参数不同';
```

**config 字段格式示例：**

```json
// email
{
    "smtp_host": "smtp.example.com",
    "smtp_port": 465,
    "smtp_user": "alert@example.com",
    "smtp_password": "encrypted_password",
    "use_ssl": true,
    "from_name": "巡检系统告警",
    "to": ["ops@example.com", "admin@example.com"]
}

// dingtalk
{
    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
    "secret": "SECxxx",
    "at_mobiles": ["13800138000"],
    "at_all": false
}

// wechat
{
    "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx",
    "mentioned_list": ["zhangsan", "lisi"],
    "mentioned_mobile_list": ["13800138000"]
}
```

### 4.4 alert_policy（告警策略）

```sql
CREATE TABLE alert_policy (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    policy_code     VARCHAR(50) UNIQUE NOT NULL,    -- critical_ser, warning_all
    policy_name     VARCHAR(100) NOT NULL,           -- "生产环境严重告警"
    description     TEXT,

    -- 策略条件
    conditions      JSONB NOT NULL,                 -- 匹配条件：环境、告警级别、平台等

    -- 关联渠道
    channel_ids     BIGINT[] NOT NULL,              -- 关联的 channel id 数组

    -- 状态
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE alert_policy IS '告警策略，定义什么条件的告警通过什么渠道通知';
COMMENT ON COLUMN alert_policy.conditions IS '匹配条件JSON，如 {"environment":["ser"],"alert_level":["critical"]}';
COMMENT ON COLUMN alert_policy.channel_ids IS '关联的通知渠道ID数组';
```

### 4.5 insp_task（巡检任务）

```sql
CREATE TABLE insp_task (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    task_code       VARCHAR(50) UNIQUE NOT NULL,    -- global_collect, weekly_snapshot
    task_name       VARCHAR(100) NOT NULL,           -- "全局定时采集"
    task_type       VARCHAR(30) NOT NULL,            -- collect, inspection, report
    description     TEXT,

    -- 调度配置
    cron_expression VARCHAR(50),                     -- "*/5 * * * *"
    interval_minutes INT,                            -- 或直接用间隔
    is_enabled      BOOLEAN DEFAULT TRUE,

    -- 目标范围
    target_platforms VARCHAR(30)[],                  -- 空=所有平台
    target_environments VARCHAR(10)[],               -- 空=所有环境

    -- 状态
    last_run_at     TIMESTAMPTZ,
    last_status     VARCHAR(20),
    last_error      TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE insp_task IS '巡检任务定义';
```

**初始任务：**

| task_code | task_name | task_type | interval_minutes |
|-----------|-----------|-----------|-----------------|
| global_collect | 全局定时采集 | collect | 5 |
| daily_report | 每日巡检报告 | report | 1440 |

### 4.6 insp_execution（巡检执行记录）

```sql
CREATE TABLE insp_execution (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    task_id         BIGINT NOT NULL REFERENCES insp_task(id),

    -- 执行信息
    trigger_source  VARCHAR(20) NOT NULL,           -- scheduled, manual
    status          VARCHAR(20) NOT NULL,           -- running, success, failed, partial

    -- 执行结果
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    duration_seconds INT,
    hosts_collected INT DEFAULT 0,
    alerts_generated INT DEFAULT 0,
    errors          JSONB,                          -- 错误详情

    -- 平台结果
    platform_results JSONB,                        -- 各平台采集结果摘要

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_execution_task ON insp_execution(task_id);
CREATE INDEX idx_execution_status ON insp_execution(status);
CREATE INDEX idx_execution_started ON insp_execution(started_at);

COMMENT ON TABLE insp_execution IS '巡检执行记录';
```

---

## 五、平台专用表（VMware 示例）

VMware 是最复杂的平台，以此为例展示完整表结构。其他平台遵循相同模式。

### 5.1 vmware_cluster

```sql
CREATE TABLE vmware_cluster (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    instance_id     BIGINT NOT NULL REFERENCES plt_instance(id),

    cluster_name    VARCHAR(200) NOT NULL,
    overall_status  VARCHAR(20),                -- green, yellow, red
    host_count      INT DEFAULT 0,
    cpu_cores       INT,
    cpu_total_mhz   DOUBLE PRECISION,
    cpu_usage_mhz   DOUBLE PRECISION,
    cpu_usage_percent DOUBLE PRECISION,
    memory_total_mb DOUBLE PRECISION,
    memory_used_mb  DOUBLE PRECISION,
    memory_usage_percent DOUBLE PRECISION,

    check_time      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vmware_cluster_instance ON vmware_cluster(instance_id);
```

### 5.2 vmware_host

```sql
CREATE TABLE vmware_host (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    instance_id     BIGINT NOT NULL REFERENCES plt_instance(id),
    cluster_id      BIGINT REFERENCES vmware_cluster(id),

    host_name       VARCHAR(200) NOT NULL,
    host_id         VARCHAR(100),               -- vCenter MOID
    ip_address      VARCHAR(50),

    -- 硬件配置
    cpu_cores       INT,
    cpu_total_mhz   DOUBLE PRECISION,
    memory_total_mb DOUBLE PRECISION,

    -- 运行指标
    cpu_usage_mhz   DOUBLE PRECISION,
    cpu_usage_percent DOUBLE PRECISION,
    memory_used_mb  DOUBLE PRECISION,
    memory_usage_percent DOUBLE PRECISION,
    storage_usage_percent DOUBLE PRECISION,

    -- 状态
    status          VARCHAR(20),                -- normal, warning, critical
    overall_status  VARCHAR(20),
    connection_state VARCHAR(30),
    power_state     VARCHAR(30),
    vm_count        INT DEFAULT 0,
    uptime_days     DOUBLE PRECISION,

    check_time      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vmware_host_instance ON vmware_host(instance_id);
CREATE INDEX idx_vmware_host_cluster ON vmware_host(cluster_id);
CREATE INDEX idx_vmware_host_status ON vmware_host(status);
CREATE INDEX idx_vmware_host_check ON vmware_host(check_time);
```

### 5.3 vmware_vm

```sql
CREATE TABLE vmware_vm (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    instance_id     BIGINT NOT NULL REFERENCES plt_instance(id),
    host_id         BIGINT REFERENCES vmware_host(id),

    vm_name         VARCHAR(200) NOT NULL,
    vm_uuid         VARCHAR(100),
    ip_address      VARCHAR(50),
    guest_os        VARCHAR(200),

    -- 配置
    cpu_count       INT,
    memory_mb       DOUBLE PRECISION,
    memory_gb       DOUBLE PRECISION,
    storage_mb      DOUBLE PRECISION,
    storage_gb      DOUBLE PRECISION,
    storage_tb      DOUBLE PRECISION,

    -- 状态
    power_state     VARCHAR(30),
    is_template     BOOLEAN DEFAULT FALSE,

    -- 快照信息
    has_snapshot    BOOLEAN DEFAULT FALSE,
    snapshot_count  INT DEFAULT 0,
    snapshot_days   INT,
    oldest_snapshot_name VARCHAR(200),
    oldest_snapshot_date TIMESTAMPTZ,

    -- 备注和元数据
    note            TEXT,
    created_days    INT,

    check_time      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vmware_vm_instance ON vmware_vm(instance_id);
CREATE INDEX idx_vmware_vm_host ON vmware_vm(host_id);
CREATE INDEX idx_vmware_vm_power ON vmware_vm(power_state);
CREATE INDEX idx_vmware_vm_snapshot ON vmware_vm(has_snapshot) WHERE has_snapshot = TRUE;
CREATE INDEX idx_vmware_vm_check ON vmware_vm(check_time);
```

### 5.4 vmware_datastore

```sql
CREATE TABLE vmware_datastore (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    instance_id     BIGINT NOT NULL REFERENCES plt_instance(id),

    datastore_name  VARCHAR(200) NOT NULL,
    datastore_id    VARCHAR(100),
    datastore_type  VARCHAR(50),                -- VMFS, NFS, vSAN

    capacity_bytes  BIGINT,
    free_bytes      BIGINT,
    used_bytes      BIGINT,
    usage_percent   DOUBLE PRECISION,

    check_time      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vmware_ds_instance ON vmware_datastore(instance_id);
```

### 5.5 vmware_snapshot

```sql
CREATE TABLE vmware_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    instance_id     BIGINT NOT NULL REFERENCES plt_instance(id),
    vm_id           BIGINT REFERENCES vmware_vm(id),

    vm_name         VARCHAR(200),
    snapshot_name   VARCHAR(200),
    snapshot_id     INT,
    description     TEXT,
    snapshot_size_mb DOUBLE PRECISION,
    create_time     TIMESTAMPTZ,
    days_old        INT,

    check_time      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vmware_snap_instance ON vmware_snapshot(instance_id);
CREATE INDEX idx_vmware_snap_vm ON vmware_snapshot(vm_id);
CREATE INDEX idx_vmware_snap_days ON vmware_snapshot(days_old);
```

### 5.6 vmware_metric（历史指标）

```sql
CREATE TABLE vmware_metric (
    id              BIGSERIAL PRIMARY KEY,
    instance_id     BIGINT NOT NULL,
    resource_type   VARCHAR(20) NOT NULL,       -- host, vm, datastore
    resource_id     BIGINT NOT NULL,
    resource_name   VARCHAR(200),

    cpu_usage       DOUBLE PRECISION,
    memory_usage    DOUBLE PRECISION,
    storage_usage   DOUBLE PRECISION,
    custom_metrics  JSONB,                      -- 平台特有指标

    check_time      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_vmware_metric_resource ON vmware_metric(resource_type, resource_id);
CREATE INDEX idx_vmware_metric_time ON vmware_metric(check_time);
CREATE INDEX idx_vmware_metric_instance ON vmware_metric(instance_id, check_time);
```

### 5.7 vmware_event

```sql
CREATE TABLE vmware_event (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    instance_id     BIGINT NOT NULL REFERENCES plt_instance(id),

    event_id        VARCHAR(100),
    event_type      VARCHAR(200),
    message         TEXT,
    severity        VARCHAR(20),                -- critical, warning, info
    user_name       VARCHAR(100),

    -- 关联对象
    datacenter_name VARCHAR(100),
    cluster_name    VARCHAR(200),
    host_name       VARCHAR(200),
    vm_name         VARCHAR(200),

    created_time    TIMESTAMPTZ,
    check_time      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_vmware_event_instance ON vmware_event(instance_id);
CREATE INDEX idx_vmware_event_severity ON vmware_event(severity);
CREATE INDEX idx_vmware_event_time ON vmware_event(created_time);
```

### 5.8 vmware_task

```sql
CREATE TABLE vmware_task (
    id              BIGSERIAL PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE NOT NULL,
    instance_id     BIGINT NOT NULL REFERENCES plt_instance(id),

    task_id         VARCHAR(100),
    task_name       VARCHAR(200),
    description     TEXT,
    state           VARCHAR(20),                -- queued, running, success, error

    entity_name     VARCHAR(200),
    user_name       VARCHAR(100),
    start_time      TIMESTAMPTZ,
    complete_time   TIMESTAMPTZ,
    result          TEXT,
    error_message   TEXT,

    check_time      TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_vmware_task_instance ON vmware_task(instance_id);
CREATE INDEX idx_vmware_task_state ON vmware_task(state);
```

---

## 六、其他平台表结构（遵循统一模式）

### 6.1 统一 metric 表模式

所有平台的 metric 表结构相同：

```sql
CREATE TABLE {platform}_metric (
    id              BIGSERIAL PRIMARY KEY,
    instance_id     BIGINT NOT NULL,
    resource_type   VARCHAR(20) NOT NULL,
    resource_id     BIGINT NOT NULL,
    resource_name   VARCHAR(200),
    cpu_usage       DOUBLE PRECISION,
    memory_usage    DOUBLE PRECISION,
    storage_usage   DOUBLE PRECISION,
    custom_metrics  JSONB,
    check_time      TIMESTAMPTZ NOT NULL
);
```

### 6.2 虚拟化平台（SmartX）

```sql
CREATE TABLE smartx_cluster (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    cluster_name VARCHAR(200), status VARCHAR(20),
    host_count INT, cpu_usage_percent DOUBLE PRECISION, memory_usage_percent DOUBLE PRECISION,
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE smartx_host (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    cluster_id BIGINT REFERENCES smartx_cluster(id),
    host_name VARCHAR(200), ip_address VARCHAR(50),
    cpu_cores INT, memory_total_mb DOUBLE PRECISION,
    cpu_usage_percent DOUBLE PRECISION, memory_usage_percent DOUBLE PRECISION, storage_usage_percent DOUBLE PRECISION,
    status VARCHAR(20), power_state VARCHAR(30),
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE smartx_vm (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    host_id BIGINT REFERENCES smartx_host(id),
    vm_name VARCHAR(200), ip_address VARCHAR(50),
    cpu_count INT, memory_gb DOUBLE PRECISION, storage_gb DOUBLE PRECISION,
    power_state VARCHAR(30), has_snapshot BOOLEAN DEFAULT FALSE,
    note TEXT, check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE smartx_volume (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    volume_name VARCHAR(200), capacity_gb DOUBLE PRECISION, used_gb DOUBLE PRECISION,
    status VARCHAR(20), check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE smartx_snapshot (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    vm_id BIGINT REFERENCES smartx_vm(id),
    vm_name VARCHAR(200), snapshot_name VARCHAR(200),
    create_time TIMESTAMPTZ, days_old INT,
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6.3 云桌面平台（华为 / 深信服）

```sql
-- 华为云桌面
CREATE TABLE huawei_cd_cluster (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    cluster_name VARCHAR(200), cluster_type VARCHAR(50),  -- FA/FC
    status VARCHAR(20), desktop_count INT,
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE huawei_cd_host (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    cluster_id BIGINT REFERENCES huawei_cd_cluster(id),
    host_name VARCHAR(200), ip_address VARCHAR(50),
    cpu_cores INT, memory_gb DOUBLE PRECISION,
    cpu_usage_percent DOUBLE PRECISION, memory_usage_percent DOUBLE PRECISION,
    status VARCHAR(20), check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE huawei_cd_desktop (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    host_id BIGINT REFERENCES huawei_cd_host(id),
    desktop_name VARCHAR(200), ip_address VARCHAR(50),
    cpu_count INT, memory_gb DOUBLE PRECISION, storage_gb DOUBLE PRECISION,
    power_state VARCHAR(30), user_name VARCHAR(100),
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE huawei_cd_pool (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    pool_name VARCHAR(200), pool_type VARCHAR(50),
    max_desktops INT, assigned_desktops INT, available_desktops INT,
    status VARCHAR(20), check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 深信服云桌面（结构类似，表名前缀改为 sangfor_cd_）
```

### 6.4 数据库平台（Oracle / MySQL / Gbase / TDSQL）

```sql
-- Oracle
CREATE TABLE oracle_instance (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    instance_name VARCHAR(200), db_name VARCHAR(200),
    version VARCHAR(50), host_name VARCHAR(200), ip_address VARCHAR(50),
    port INT, status VARCHAR(20),
    connections INT, max_connections INT,
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE oracle_tablespace (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    oracle_instance_id BIGINT REFERENCES oracle_instance(id),
    tablespace_name VARCHAR(200),
    total_gb DOUBLE PRECISION, used_gb DOUBLE PRECISION, usage_percent DOUBLE PRECISION,
    status VARCHAR(20), check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE oracle_session (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    oracle_instance_id BIGINT REFERENCES oracle_instance(id),
    session_id INT, username VARCHAR(100), status VARCHAR(30),
    machine VARCHAR(200), program VARCHAR(200),
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- MySQL（类似结构，表名前缀改为 mysql_）
-- Gbase（类似结构，表名前缀改为 gbase_，增加 cluster 和 node 层级）
-- TDSQL（类似结构，表名前缀改为 tdsql_，增加 cluster 和 node 层级）
```

### 6.5 存储平台（华为 / XSKY / 华瑞 / SmartX ZBS）

```sql
-- 华为存储
CREATE TABLE hwstorage_device (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    device_name VARCHAR(200), device_model VARCHAR(100),
    firmware_version VARCHAR(50), status VARCHAR(20),
    total_capacity_tb DOUBLE PRECISION, used_capacity_tb DOUBLE PRECISION,
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE hwstorage_pool (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    device_id BIGINT REFERENCES hwstorage_device(id),
    pool_name VARCHAR(200), pool_type VARCHAR(50),
    total_capacity_tb DOUBLE PRECISION, used_capacity_tb DOUBLE PRECISION, usage_percent DOUBLE PRECISION,
    status VARCHAR(20), check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE hwstorage_volume (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    pool_id BIGINT REFERENCES hwstorage_pool(id),
    volume_name VARCHAR(200), capacity_gb DOUBLE PRECISION,
    used_gb DOUBLE PRECISION, status VARCHAR(20),
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE hwstorage_disk (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    device_id BIGINT REFERENCES hwstorage_device(id),
    disk_name VARCHAR(200), disk_type VARCHAR(50),  -- SSD, HDD
    capacity_gb DOUBLE PRECISION, status VARCHAR(20),
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- XSKY, 华瑞, SmartX ZBS 结构类似
```

### 6.6 备份平台（Veeam / 鼎甲 / Zerto）

```sql
-- Veeam
CREATE TABLE veeam_server (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    server_name VARCHAR(200), version VARCHAR(50),
    status VARCHAR(20), check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE veeam_job (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    job_name VARCHAR(200), job_type VARCHAR(50),
    status VARCHAR(20), last_run_at TIMESTAMPTZ,
    last_status VARCHAR(20), next_run_at TIMESTAMPTZ,
    protected_vms INT, check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE veeam_restore_point (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    job_id BIGINT REFERENCES veeam_job(id),
    vm_name VARCHAR(200), restore_point_time TIMESTAMPTZ,
    size_gb DOUBLE PRECISION, check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 鼎甲、Zerto 结构类似
```

### 6.7 监控平台（日志易）

```sql
CREATE TABLE rizhiyi_instance (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    instance_name VARCHAR(200), version VARCHAR(50),
    status VARCHAR(20), check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE rizhiyi_index (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    index_name VARCHAR(200), doc_count BIGINT,
    storage_size_gb DOUBLE PRECISION, status VARCHAR(20),
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE rizhiyi_dashboard (
    id BIGSERIAL PRIMARY KEY, uid VARCHAR(36) UNIQUE NOT NULL,
    instance_id BIGINT NOT NULL REFERENCES plt_instance(id),
    dashboard_name VARCHAR(200), status VARCHAR(20),
    last_alert_at TIMESTAMPTZ,
    check_time TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 七、跨平台查询

### 7.1 v_all_hosts VIEW

```sql
CREATE VIEW v_all_hosts AS
SELECT 'vmware' AS platform, h.id, h.uid, h.instance_id, h.host_name, h.ip_address,
       h.cpu_usage_percent, h.memory_usage_percent, h.storage_usage_percent,
       h.status, h.check_time
FROM vmware_host h
UNION ALL
SELECT 'smartx' AS platform, h.id, h.uid, h.instance_id, h.host_name, h.ip_address,
       h.cpu_usage_percent, h.memory_usage_percent, h.storage_usage_percent,
       h.status, h.check_time
FROM smartx_host h
UNION ALL
SELECT 'huawei_cd' AS platform, h.id, h.uid, h.instance_id, h.host_name, h.ip_address,
       h.cpu_usage_percent, h.memory_usage_percent, NULL,
       h.status, h.check_time
FROM huawei_cd_host h
UNION ALL
SELECT 'sangfor_cd' AS platform, h.id, h.uid, h.instance_id, h.host_name, h.ip_address,
       h.cpu_usage_percent, h.memory_usage_percent, NULL,
       h.status, h.check_time
FROM sangfor_cd_host h;
```

### 7.2 v_all_vms VIEW

```sql
CREATE VIEW v_all_vms AS
SELECT 'vmware' AS platform, v.id, v.uid, v.instance_id, v.vm_name, v.ip_address,
       v.cpu_count, v.memory_gb, v.storage_gb, v.power_state, v.has_snapshot, v.check_time
FROM vmware_vm v
UNION ALL
SELECT 'smartx' AS platform, v.id, v.uid, v.instance_id, v.vm_name, v.ip_address,
       v.cpu_count, v.memory_gb, v.storage_gb, v.power_state, v.has_snapshot, v.check_time
FROM smartx_vm v;
```

---

## 八、数据生命周期

| 数据类型 | 保留策略 | 清理方式 |
|----------|----------|----------|
| 指标数据 (*_metric) | 1 个月 | 定时任务 DELETE WHERE check_time < NOW() - INTERVAL '30 days' |
| 告警记录 (alert_record) | 永久 | 不删除 |
| 巡检执行 (insp_execution) | 永久 | 不删除 |
| 事件日志 (*_event) | 1 个月 | 同指标数据 |
| 任务历史 (*_task) | 1 个月 | 同指标数据 |
| 资源索引 (ast_resource_index) | 跟随资源 | 资源删除时级联删除 |

**清理任务 SQL：**

```sql
-- 每天凌晨执行
DELETE FROM vmware_metric WHERE check_time < NOW() - INTERVAL '30 days';
DELETE FROM smartx_metric WHERE check_time < NOW() - INTERVAL '30 days';
-- ... 每个平台一行
DELETE FROM vmware_event WHERE check_time < NOW() - INTERVAL '30 days';
DELETE FROM vmware_task WHERE check_time < NOW() - INTERVAL '30 days';
```

---

## 九、索引策略总结

| 表类型 | 索引 |
|--------|------|
| plt_instance | (platform_id), (environment), partial (is_active) |
| 所有 *_host | (instance_id), (cluster_id), (status), (check_time) |
| 所有 *_vm | (instance_id), (host_id), (power_state), partial (has_snapshot), (check_time) |
| 所有 *_metric | (instance_id, check_time), (resource_type, resource_id) |
| alert_record | (status), (alert_level), (platform), (triggered_at), (resource_type, resource_id) |
| ast_resource_index | (ip_address), gin(name), (platform), (environment) |
| insp_execution | (task_id), (status), (started_at) |

---

## 十、与现有代码的映射关系

| 现有表 | 新表 | 变化 |
|--------|------|------|
| PlatformCredential | plt_instance + plt_platform | 拆分为平台类型和实例两层 |
| ConfigThreshold | alert_rule (category=metric) | 合并到统一规则表 |
| SystemCollectionConfig | cfg_system + insp_task | 配置+任务分离 |
| InspectionRecord | 各平台专用表 + *_metric | 按平台拆分 |
| Alert | alert_record | 统一告警记录，不删除 |
| VmAsset | vmware_vm / smartx_vm | 按平台拆分 |
| HostAsset | vmware_host / smartx_host | 按平台拆分 |
| DbAsset | oracle_instance / mysql_instance 等 | 按平台拆分 |
| HostMetric | vmware_metric / smartx_metric 等 | 按平台拆分 |
| VmMetric | 合并到 *_metric | 统一 metric 表 |
| VmSnapshot | vmware_snapshot / smartx_snapshot | 按平台拆分 |
| VmwareEvent | vmware_event | 保留，结构优化 |
| VmwareTask | vmware_task | 保留，结构优化 |
| （新增） | alert_channel, alert_policy | 通知渠道 |
| （新增） | insp_execution | 巡检执行记录 |
| （新增） | ast_resource_index | 跨平台搜索 |
| （删除） | mock_data.py | 不再需要模拟数据 |

---

*文档结束*
