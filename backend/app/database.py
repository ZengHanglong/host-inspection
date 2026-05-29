"""
Database Connection and Models for Host Inspection System
PostgreSQL version - follows the approved database design spec
"""
import os
import uuid
from datetime import datetime
from urllib.parse import quote_plus

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint, create_engine, text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ──────────────────────────────────────────────
# Database connection
# ──────────────────────────────────────────────
DB_HOST = os.environ.get("PG_HOST", "localhost")
DB_PORT = os.environ.get("PG_PORT", "5432")
DB_NAME = os.environ.get("PG_NAME", "host_inspection")
DB_USER = os.environ.get("PG_USER", "postgres")
DB_PASS = os.environ.get("PG_PASS", "admin@123")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _uid() -> str:
    return str(uuid.uuid4())


# ──────────────────────────────────────────────
# 1. Core Infrastructure
# ──────────────────────────────────────────────

class PlatformType(Base):
    """Platform type dictionary (VMware, SmartX, etc.)"""
    __tablename__ = "plt_platform"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(30), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    category = Column(String(30), nullable=False)  # virtualization, cloud_desktop, database, storage, backup, monitoring
    api_type = Column(String(20))
    icon = Column(String(50))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)

    instances = relationship("PlatformInstance", back_populates="platform")


class Environment(Base):
    """Environment definitions (dev, pre, ser)"""
    __tablename__ = "ast_environment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False)  # dev, pre, ser
    name = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))


class PlatformInstance(Base):
    """All platform instances with credentials and connection config"""
    __tablename__ = "plt_instance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    platform_id = Column(BigInteger, ForeignKey("plt_platform.id"), nullable=False)
    environment = Column(String(10), ForeignKey("ast_environment.code"), nullable=False)
    instance_name = Column(String(100), nullable=False)
    description = Column(Text)

    # API connection
    api_url = Column(String(500))
    api_port = Column(Integer)
    api_username = Column(String(100))
    api_password = Column(String(500))  # AES-256 encrypted
    api_key = Column(String(500))
    api_token = Column(String(500))
    api_type = Column(String(20))

    # ESXi SSH credentials (for direct ESXi log collection)
    esxi_ssh_username = Column(String(100))
    esxi_ssh_password = Column(String(500))  # encrypted
    esxi_ssh_port = Column(Integer, default=22)

    # SSL
    requires_ssl = Column(Boolean, default=True)
    ssl_verify = Column(Boolean, default=True)

    # Status
    is_configured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_error = Column(Text)
    last_test_at = Column(DateTime(timezone=True))
    last_sync_at = Column(DateTime(timezone=True))

    # Collection config
    collect_interval_minutes = Column(Integer, default=5)

    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)

    platform = relationship("PlatformType", back_populates="instances")

    __table_args__ = (
        Index("idx_instance_platform", "platform_id"),
        Index("idx_instance_env", "environment"),
    )


class ResourceIndex(Base):
    """Cross-platform resource search index"""
    __tablename__ = "ast_resource_index"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(30), nullable=False)
    instance_id = Column(BigInteger, nullable=False)
    environment = Column(String(10), nullable=False)
    resource_type = Column(String(20), nullable=False)  # host, vm, cluster, storage, volume, desktop
    resource_id = Column(BigInteger, nullable=False)
    name = Column(String(200))
    ip_address = Column(String(50))
    extra = Column(JSONB)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (
        Index("idx_resource_platform", "platform"),
        Index("idx_resource_type", "resource_type"),
        Index("idx_resource_ip", "ip_address"),
        Index("idx_resource_env", "environment"),
    )


class SystemConfig(Base):
    """System configuration key-value store"""
    __tablename__ = "cfg_system"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    value_type = Column(String(20), default="string")  # string, int, bool, json
    description = Column(String(500))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)


# ──────────────────────────────────────────────
# 2. Alert & Inspection
# ──────────────────────────────────────────────

class AlertRule(Base):
    """Unified alert rules (threshold, inspection, event)"""
    __tablename__ = "alert_rule"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    rule_code = Column(String(50), unique=True, nullable=False)
    rule_name = Column(String(100), nullable=False)
    category = Column(String(30), nullable=False)  # metric, inspection, event
    target_type = Column(String(30), nullable=False)  # host, vm, snapshot, storage
    condition_type = Column(String(20), nullable=False)  # threshold, pattern, presence
    resource_type = Column(String(30))
    warning_value = Column(Float)
    critical_value = Column(Float)
    config = Column(JSONB)
    alert_level = Column(String(20), default="warning")
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)

    records = relationship("AlertRecord", back_populates="rule")


class AlertRecord(Base):
    """Alert records - permanent history"""
    __tablename__ = "alert_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    rule_id = Column(BigInteger, ForeignKey("alert_rule.id"), nullable=False)

    # Source
    platform = Column(String(30), nullable=False)
    instance_id = Column(BigInteger)
    environment = Column(String(10))

    # Resource reference
    resource_type = Column(String(30), nullable=False)
    resource_id = Column(BigInteger)
    resource_name = Column(String(200))

    # Content
    alert_level = Column(String(20), nullable=False)  # warning, critical
    message = Column(Text)
    threshold_value = Column(Float)
    current_value = Column(Float)

    # Lifecycle
    status = Column(String(20), nullable=False, default="active")  # active, resolved, ignored
    triggered_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(50))  # auto, manual
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(50))
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    rule = relationship("AlertRule", back_populates="records")

    __table_args__ = (
        Index("idx_alert_status", "status"),
        Index("idx_alert_level", "alert_level"),
        Index("idx_alert_platform", "platform"),
        Index("idx_alert_triggered", "triggered_at"),
        Index("idx_alert_resource", "resource_type", "resource_id"),
    )


class AlertChannel(Base):
    """Notification channels (email, DingTalk, WeChat)"""
    __tablename__ = "alert_channel"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    channel_code = Column(String(50), unique=True, nullable=False)
    channel_name = Column(String(100), nullable=False)
    channel_type = Column(String(20), nullable=False)  # email, dingtalk, wechat
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime(timezone=True))
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)


class AlertPolicy(Base):
    """Alert policies (which conditions notify via which channels)"""
    __tablename__ = "alert_policy"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    policy_code = Column(String(50), unique=True, nullable=False)
    policy_name = Column(String(100), nullable=False)
    description = Column(Text)
    conditions = Column(JSONB, nullable=False)
    channel_ids = Column(ARRAY(BigInteger), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)


class InspectionTask(Base):
    """Inspection task definitions"""
    __tablename__ = "insp_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    task_code = Column(String(50), unique=True, nullable=False)
    task_name = Column(String(100), nullable=False)
    task_type = Column(String(30), nullable=False)  # collect, inspection, report
    description = Column(Text)
    cron_expression = Column(String(50))
    interval_minutes = Column(Integer)
    is_enabled = Column(Boolean, default=True)
    target_platforms = Column(ARRAY(String(30)))
    target_environments = Column(ARRAY(String(10)))
    last_run_at = Column(DateTime(timezone=True))
    last_status = Column(String(20))
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)


class InspectionExecution(Base):
    """Inspection execution records"""
    __tablename__ = "insp_execution"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    task_id = Column(BigInteger, ForeignKey("insp_task.id"), nullable=False)
    trigger_source = Column(String(20), nullable=False)  # scheduled, manual
    status = Column(String(20), nullable=False)  # running, success, failed, partial
    started_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    finished_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    hosts_collected = Column(Integer, default=0)
    alerts_generated = Column(Integer, default=0)
    errors = Column(JSONB)
    platform_results = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (
        Index("idx_execution_task", "task_id"),
        Index("idx_execution_status", "status"),
        Index("idx_execution_started", "started_at"),
    )


# ──────────────────────────────────────────────
# 3. VMware (most complex platform)
# ──────────────────────────────────────────────

class VmwareCluster(Base):
    __tablename__ = "vmware_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_name = Column(String(200), nullable=False)
    overall_status = Column(String(20))
    host_count = Column(Integer, default=0)
    cpu_cores = Column(Integer)
    cpu_total_mhz = Column(Float)
    cpu_usage_mhz = Column(Float)
    cpu_usage_percent = Column(Float)
    memory_total_mb = Column(Float)
    memory_used_mb = Column(Float)
    memory_usage_percent = Column(Float)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    hosts = relationship("VmwareHost", back_populates="cluster")

    __table_args__ = (Index("idx_vmware_cluster_instance", "instance_id"),)


class VmwareHost(Base):
    __tablename__ = "vmware_host"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("vmware_cluster.id"))
    host_name = Column(String(200), nullable=False)
    host_id = Column(String(100))  # vCenter MOID
    ip_address = Column(String(50))
    cpu_cores = Column(Integer)
    cpu_total_mhz = Column(Float)
    memory_total_mb = Column(Float)
    cpu_usage_mhz = Column(Float)
    cpu_usage_percent = Column(Float)
    memory_used_mb = Column(Float)
    memory_usage_percent = Column(Float)
    storage_usage_percent = Column(Float)
    status = Column(String(20))
    overall_status = Column(String(20))
    connection_state = Column(String(30))
    power_state = Column(String(30))
    vm_count = Column(Integer, default=0)
    uptime_days = Column(Float)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    cluster = relationship("VmwareCluster", back_populates="hosts")
    vms = relationship("VmwareVm", back_populates="host")

    __table_args__ = (
        Index("idx_vmware_host_instance", "instance_id"),
        Index("idx_vmware_host_cluster", "cluster_id"),
        Index("idx_vmware_host_status", "status"),
        Index("idx_vmware_host_check", "check_time"),
    )


class VmwareVm(Base):
    __tablename__ = "vmware_vm"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    host_id = Column(BigInteger, ForeignKey("vmware_host.id"))
    vm_name = Column(String(200), nullable=False)
    vm_uuid = Column(String(100))
    ip_address = Column(String(50))
    guest_os = Column(String(200))
    cpu_count = Column(Integer)
    memory_mb = Column(Float)
    memory_gb = Column(Float)
    storage_mb = Column(Float)
    storage_gb = Column(Float)
    storage_tb = Column(Float)
    power_state = Column(String(30))
    is_template = Column(Boolean, default=False)
    has_snapshot = Column(Boolean, default=False)
    snapshot_count = Column(Integer, default=0)
    snapshot_days = Column(Integer)
    oldest_snapshot_name = Column(String(200))
    oldest_snapshot_date = Column(DateTime(timezone=True))
    note = Column(Text)
    created_days = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    host = relationship("VmwareHost", back_populates="vms")
    snapshots = relationship("VmwareSnapshot", back_populates="vm")

    __table_args__ = (
        Index("idx_vmware_vm_instance", "instance_id"),
        Index("idx_vmware_vm_host", "host_id"),
        Index("idx_vmware_vm_power", "power_state"),
        Index("idx_vmware_vm_check", "check_time"),
    )


class VmwareDatastore(Base):
    __tablename__ = "vmware_datastore"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    datastore_name = Column(String(200), nullable=False)
    datastore_id = Column(String(100))
    datastore_type = Column(String(50))
    capacity_bytes = Column(BigInteger)
    free_bytes = Column(BigInteger)
    used_bytes = Column(BigInteger)
    usage_percent = Column(Float)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_vmware_ds_instance", "instance_id"),)


class VmwareSnapshot(Base):
    __tablename__ = "vmware_snapshot"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    vm_id = Column(BigInteger, ForeignKey("vmware_vm.id"))
    vm_name = Column(String(200))
    snapshot_name = Column(String(200))
    snapshot_id = Column(Integer)
    description = Column(Text)
    snapshot_size_mb = Column(Float)
    create_time = Column(DateTime(timezone=True))
    days_old = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    vm = relationship("VmwareVm", back_populates="snapshots")

    __table_args__ = (
        Index("idx_vmware_snap_instance", "instance_id"),
        Index("idx_vmware_snap_vm", "vm_id"),
        Index("idx_vmware_snap_days", "days_old"),
    )


class VmwareMetric(Base):
    __tablename__ = "vmware_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)  # host, vm, datastore
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_vmware_metric_resource", "resource_type", "resource_id"),
        Index("idx_vmware_metric_time", "check_time"),
        Index("idx_vmware_metric_instance", "instance_id", "check_time"),
    )


class VmwareEvent(Base):
    __tablename__ = "vmware_event"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    event_id = Column(String(100))
    event_type = Column(String(200))
    message = Column(Text)
    severity = Column(String(20))  # critical, warning, info
    user_name = Column(String(100))
    datacenter_name = Column(String(100))
    cluster_name = Column(String(200))
    host_name = Column(String(200))
    vm_name = Column(String(200))
    created_time = Column(DateTime(timezone=True))
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_vmware_event_instance", "instance_id"),
        Index("idx_vmware_event_severity", "severity"),
        Index("idx_vmware_event_time", "created_time"),
    )


class VmwareTask(Base):
    __tablename__ = "vmware_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    task_id = Column(String(100))
    task_name = Column(String(200))
    description = Column(Text)
    state = Column(String(20))  # queued, running, success, error
    entity_name = Column(String(200))
    user_name = Column(String(100))
    start_time = Column(DateTime(timezone=True))
    complete_time = Column(DateTime(timezone=True))
    result = Column(Text)
    error_message = Column(Text)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_vmware_task_instance", "instance_id"),
        Index("idx_vmware_task_state", "state"),
    )


# ──────────────────────────────────────────────
# 4. SmartX
# ──────────────────────────────────────────────

class SmartxCluster(Base):
    __tablename__ = "smartx_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_name = Column(String(200))
    status = Column(String(20))
    host_count = Column(Integer)
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    hosts = relationship("SmartxHost", back_populates="cluster")

    __table_args__ = (Index("idx_smartx_cluster_instance", "instance_id"),)


class SmartxHost(Base):
    __tablename__ = "smartx_host"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("smartx_cluster.id"))
    host_name = Column(String(200), nullable=False)
    ip_address = Column(String(50))
    cpu_cores = Column(Integer)
    memory_total_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    storage_usage_percent = Column(Float)
    status = Column(String(20))
    power_state = Column(String(30))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    cluster = relationship("SmartxCluster", back_populates="hosts")
    vms = relationship("SmartxVm", back_populates="host")

    __table_args__ = (
        Index("idx_smartx_host_instance", "instance_id"),
        Index("idx_smartx_host_cluster", "cluster_id"),
        Index("idx_smartx_host_status", "status"),
        Index("idx_smartx_host_check", "check_time"),
    )


class SmartxVm(Base):
    __tablename__ = "smartx_vm"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    host_id = Column(BigInteger, ForeignKey("smartx_host.id"))
    vm_name = Column(String(200), nullable=False)
    ip_address = Column(String(50))
    cpu_count = Column(Integer)
    memory_gb = Column(Float)
    storage_gb = Column(Float)
    power_state = Column(String(30))
    has_snapshot = Column(Boolean, default=False)
    note = Column(Text)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    host = relationship("SmartxHost", back_populates="vms")

    __table_args__ = (
        Index("idx_smartx_vm_instance", "instance_id"),
        Index("idx_smartx_vm_host", "host_id"),
        Index("idx_smartx_vm_check", "check_time"),
    )


class SmartxVolume(Base):
    __tablename__ = "smartx_volume"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    volume_name = Column(String(200))
    capacity_gb = Column(Float)
    used_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_smartx_vol_instance", "instance_id"),)


class SmartxSnapshot(Base):
    __tablename__ = "smartx_snapshot"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    vm_id = Column(BigInteger, ForeignKey("smartx_vm.id"))
    vm_name = Column(String(200))
    snapshot_name = Column(String(200))
    create_time = Column(DateTime(timezone=True))
    days_old = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (
        Index("idx_smartx_snap_instance", "instance_id"),
        Index("idx_smartx_snap_vm", "vm_id"),
    )


class SmartxMetric(Base):
    __tablename__ = "smartx_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_smartx_metric_resource", "resource_type", "resource_id"),
        Index("idx_smartx_metric_instance", "instance_id", "check_time"),
    )


# ──────────────────────────────────────────────
# 5. Cloud Desktop (Huawei / Sangfor)
# ──────────────────────────────────────────────

class HuaweiCdCluster(Base):
    __tablename__ = "huawei_cd_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_name = Column(String(200))
    cluster_type = Column(String(50))  # FA/FC
    status = Column(String(20))
    desktop_count = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_huawei_cd_cluster_instance", "instance_id"),)


class HuaweiCdHost(Base):
    __tablename__ = "huawei_cd_host"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("huawei_cd_cluster.id"))
    host_name = Column(String(200), nullable=False)
    ip_address = Column(String(50))
    cpu_cores = Column(Integer)
    memory_gb = Column(Float)
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_huawei_cd_host_instance", "instance_id"),)


class HuaweiCdDesktop(Base):
    __tablename__ = "huawei_cd_desktop"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    host_id = Column(BigInteger, ForeignKey("huawei_cd_host.id"))
    desktop_name = Column(String(200), nullable=False)
    ip_address = Column(String(50))
    cpu_count = Column(Integer)
    memory_gb = Column(Float)
    storage_gb = Column(Float)
    power_state = Column(String(30))
    user_name = Column(String(100))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_huawei_cd_desktop_instance", "instance_id"),)


class HuaweiCdPool(Base):
    __tablename__ = "huawei_cd_pool"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    pool_name = Column(String(200))
    pool_type = Column(String(50))
    max_desktops = Column(Integer)
    assigned_desktops = Column(Integer)
    available_desktops = Column(Integer)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_huawei_cd_pool_instance", "instance_id"),)


class HuaweiCdMetric(Base):
    __tablename__ = "huawei_cd_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_huawei_cd_metric_instance", "instance_id", "check_time"),)


class SangforCdCluster(Base):
    __tablename__ = "sangfor_cd_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_name = Column(String(200))
    status = Column(String(20))
    desktop_count = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_sangfor_cd_cluster_instance", "instance_id"),)


class SangforCdHost(Base):
    __tablename__ = "sangfor_cd_host"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("sangfor_cd_cluster.id"))
    host_name = Column(String(200), nullable=False)
    ip_address = Column(String(50))
    cpu_cores = Column(Integer)
    memory_gb = Column(Float)
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_sangfor_cd_host_instance", "instance_id"),)


class SangforCdDesktop(Base):
    __tablename__ = "sangfor_cd_desktop"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    host_id = Column(BigInteger, ForeignKey("sangfor_cd_host.id"))
    desktop_name = Column(String(200), nullable=False)
    ip_address = Column(String(50))
    cpu_count = Column(Integer)
    memory_gb = Column(Float)
    storage_gb = Column(Float)
    power_state = Column(String(30))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_sangfor_cd_desktop_instance", "instance_id"),)


class SangforCdPool(Base):
    __tablename__ = "sangfor_cd_pool"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    pool_name = Column(String(200))
    pool_type = Column(String(50))
    max_desktops = Column(Integer)
    assigned_desktops = Column(Integer)
    available_desktops = Column(Integer)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_sangfor_cd_pool_instance", "instance_id"),)


class SangforCdMetric(Base):
    __tablename__ = "sangfor_cd_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_sangfor_cd_metric_instance", "instance_id", "check_time"),)


# ──────────────────────────────────────────────
# 6. Database Platforms (Oracle, MySQL, Gbase, TDSQL)
# ──────────────────────────────────────────────

class OracleInstance(Base):
    __tablename__ = "oracle_instance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    instance_name = Column(String(200))
    db_name = Column(String(200))
    version = Column(String(50))
    host_name = Column(String(200))
    ip_address = Column(String(50))
    port = Column(Integer)
    status = Column(String(20))
    connections = Column(Integer)
    max_connections = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_oracle_inst_instance", "instance_id"),)


class OracleTablespace(Base):
    __tablename__ = "oracle_tablespace"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    oracle_instance_id = Column(BigInteger, ForeignKey("oracle_instance.id"))
    tablespace_name = Column(String(200))
    total_gb = Column(Float)
    used_gb = Column(Float)
    usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_oracle_ts_instance", "instance_id"),)


class OracleSession(Base):
    __tablename__ = "oracle_session"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    oracle_instance_id = Column(BigInteger, ForeignKey("oracle_instance.id"))
    session_id = Column(Integer)
    username = Column(String(100))
    status = Column(String(30))
    machine = Column(String(200))
    program = Column(String(200))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_oracle_sess_instance", "instance_id"),)


class OracleMetric(Base):
    __tablename__ = "oracle_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_oracle_metric_instance", "instance_id", "check_time"),)


class MysqlInstance(Base):
    __tablename__ = "mysql_instance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    instance_name = Column(String(200))
    db_name = Column(String(200))
    version = Column(String(50))
    host_name = Column(String(200))
    ip_address = Column(String(50))
    port = Column(Integer)
    status = Column(String(20))
    connections = Column(Integer)
    max_connections = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_mysql_inst_instance", "instance_id"),)


class MysqlDatabase(Base):
    __tablename__ = "mysql_database"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    mysql_instance_id = Column(BigInteger, ForeignKey("mysql_instance.id"))
    db_name = Column(String(200))
    charset = Column(String(50))
    size_mb = Column(Float)
    table_count = Column(Integer)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_mysql_db_instance", "instance_id"),)


class MysqlConnection(Base):
    __tablename__ = "mysql_connection"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    mysql_instance_id = Column(BigInteger, ForeignKey("mysql_instance.id"))
    process_id = Column(Integer)
    user = Column(String(100))
    host = Column(String(200))
    db = Column(String(200))
    command = Column(String(50))
    time_seconds = Column(Integer)
    state = Column(String(100))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_mysql_conn_instance", "instance_id"),)


class MysqlMetric(Base):
    __tablename__ = "mysql_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_mysql_metric_instance", "instance_id", "check_time"),)


class GbaseInstance(Base):
    __tablename__ = "gbase_instance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    instance_name = Column(String(200))
    version = Column(String(50))
    host_name = Column(String(200))
    ip_address = Column(String(50))
    port = Column(Integer)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_gbase_inst_instance", "instance_id"),)


class GbaseCluster(Base):
    __tablename__ = "gbase_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    gbase_instance_id = Column(BigInteger, ForeignKey("gbase_instance.id"))
    cluster_name = Column(String(200))
    node_count = Column(Integer)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_gbase_cluster_instance", "instance_id"),)


class GbaseNode(Base):
    __tablename__ = "gbase_node"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("gbase_cluster.id"))
    node_name = Column(String(200))
    ip_address = Column(String(50))
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    storage_usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_gbase_node_instance", "instance_id"),)


class GbaseMetric(Base):
    __tablename__ = "gbase_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_gbase_metric_instance", "instance_id", "check_time"),)


class TdsqlInstance(Base):
    __tablename__ = "tdsql_instance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    instance_name = Column(String(200))
    version = Column(String(50))
    host_name = Column(String(200))
    ip_address = Column(String(50))
    port = Column(Integer)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_tdsql_inst_instance", "instance_id"),)


class TdsqlCluster(Base):
    __tablename__ = "tdsql_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    tdsql_instance_id = Column(BigInteger, ForeignKey("tdsql_instance.id"))
    cluster_name = Column(String(200))
    node_count = Column(Integer)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_tdsql_cluster_instance", "instance_id"),)


class TdsqlNode(Base):
    __tablename__ = "tdsql_node"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("tdsql_cluster.id"))
    node_name = Column(String(200))
    ip_address = Column(String(50))
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    storage_usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_tdsql_node_instance", "instance_id"),)


class TdsqlMetric(Base):
    __tablename__ = "tdsql_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_tdsql_metric_instance", "instance_id", "check_time"),)


# ──────────────────────────────────────────────
# 7. Storage Platforms (Huawei, XSKY, Huarui, SmartX ZBS)
# ──────────────────────────────────────────────

class HwstorageDevice(Base):
    __tablename__ = "hwstorage_device"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    device_name = Column(String(200))
    device_model = Column(String(100))
    firmware_version = Column(String(50))
    status = Column(String(20))
    total_capacity_tb = Column(Float)
    used_capacity_tb = Column(Float)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_hwstorage_dev_instance", "instance_id"),)


class HwstoragePool(Base):
    __tablename__ = "hwstorage_pool"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    device_id = Column(BigInteger, ForeignKey("hwstorage_device.id"))
    pool_name = Column(String(200))
    pool_type = Column(String(50))
    total_capacity_tb = Column(Float)
    used_capacity_tb = Column(Float)
    usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_hwstorage_pool_instance", "instance_id"),)


class HwstorageVolume(Base):
    __tablename__ = "hwstorage_volume"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    pool_id = Column(BigInteger, ForeignKey("hwstorage_pool.id"))
    volume_name = Column(String(200))
    capacity_gb = Column(Float)
    used_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_hwstorage_vol_instance", "instance_id"),)


class HwstorageDisk(Base):
    __tablename__ = "hwstorage_disk"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    device_id = Column(BigInteger, ForeignKey("hwstorage_device.id"))
    disk_name = Column(String(200))
    disk_type = Column(String(50))  # SSD, HDD
    capacity_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_hwstorage_disk_instance", "instance_id"),)


class HwstorageMetric(Base):
    __tablename__ = "hwstorage_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_hwstorage_metric_instance", "instance_id", "check_time"),)


# XSKY
class XskyCluster(Base):
    __tablename__ = "xsky_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_name = Column(String(200))
    node_count = Column(Integer)
    total_capacity_tb = Column(Float)
    used_capacity_tb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_xsky_cluster_instance", "instance_id"),)


class XskyNode(Base):
    __tablename__ = "xsky_node"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("xsky_cluster.id"))
    node_name = Column(String(200))
    ip_address = Column(String(50))
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    storage_usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_xsky_node_instance", "instance_id"),)


class XskyVolume(Base):
    __tablename__ = "xsky_volume"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    volume_name = Column(String(200))
    capacity_gb = Column(Float)
    used_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_xsky_vol_instance", "instance_id"),)


class XskyDisk(Base):
    __tablename__ = "xsky_disk"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    disk_name = Column(String(200))
    disk_type = Column(String(50))
    capacity_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_xsky_disk_instance", "instance_id"),)


class XskyMetric(Base):
    __tablename__ = "xsky_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_xsky_metric_instance", "instance_id", "check_time"),)


# Huarui (华瑞存储)
class HuaruiDevice(Base):
    __tablename__ = "huarui_device"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    device_name = Column(String(200))
    device_model = Column(String(100))
    status = Column(String(20))
    total_capacity_tb = Column(Float)
    used_capacity_tb = Column(Float)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_huarui_dev_instance", "instance_id"),)


class HuaruiPool(Base):
    __tablename__ = "huarui_pool"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    device_id = Column(BigInteger, ForeignKey("huarui_device.id"))
    pool_name = Column(String(200))
    total_capacity_tb = Column(Float)
    used_capacity_tb = Column(Float)
    usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_huarui_pool_instance", "instance_id"),)


class HuaruiVolume(Base):
    __tablename__ = "huarui_volume"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    pool_id = Column(BigInteger, ForeignKey("huarui_pool.id"))
    volume_name = Column(String(200))
    capacity_gb = Column(Float)
    used_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_huarui_vol_instance", "instance_id"),)


class HuaruiMetric(Base):
    __tablename__ = "huarui_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_huarui_metric_instance", "instance_id", "check_time"),)


# SmartX ZBS
class SmartxzbsCluster(Base):
    __tablename__ = "smartxzbs_cluster"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_name = Column(String(200))
    node_count = Column(Integer)
    total_capacity_tb = Column(Float)
    used_capacity_tb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_smartxzbs_cluster_instance", "instance_id"),)


class SmartxzbsNode(Base):
    __tablename__ = "smartxzbs_node"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    cluster_id = Column(BigInteger, ForeignKey("smartxzbs_cluster.id"))
    node_name = Column(String(200))
    ip_address = Column(String(50))
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    storage_usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_smartxzbs_node_instance", "instance_id"),)


class SmartxzbsVolume(Base):
    __tablename__ = "smartxzbs_volume"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    volume_name = Column(String(200))
    capacity_gb = Column(Float)
    used_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_smartxzbs_vol_instance", "instance_id"),)


class SmartxzbsMetric(Base):
    __tablename__ = "smartxzbs_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_smartxzbs_metric_instance", "instance_id", "check_time"),)


# ──────────────────────────────────────────────
# 8. Backup Platforms (Veeam, Dingjia, Zerto)
# ──────────────────────────────────────────────

class VeeamServer(Base):
    __tablename__ = "veeam_server"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    server_name = Column(String(200))
    version = Column(String(50))
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_veeam_server_instance", "instance_id"),)


class VeeamJob(Base):
    __tablename__ = "veeam_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    job_name = Column(String(200))
    job_type = Column(String(50))
    status = Column(String(20))
    last_run_at = Column(DateTime(timezone=True))
    last_status = Column(String(20))
    next_run_at = Column(DateTime(timezone=True))
    protected_vms = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_veeam_job_instance", "instance_id"),)


class VeeamRestorePoint(Base):
    __tablename__ = "veeam_restore_point"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    job_id = Column(BigInteger, ForeignKey("veeam_job.id"))
    vm_name = Column(String(200))
    restore_point_time = Column(DateTime(timezone=True))
    size_gb = Column(Float)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_veeam_rp_instance", "instance_id"),)


class VeeamMetric(Base):
    __tablename__ = "veeam_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_veeam_metric_instance", "instance_id", "check_time"),)


class DingjiaServer(Base):
    __tablename__ = "dingjia_server"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    server_name = Column(String(200))
    version = Column(String(50))
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_dingjia_server_instance", "instance_id"),)


class DingjiaJob(Base):
    __tablename__ = "dingjia_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    job_name = Column(String(200))
    job_type = Column(String(50))
    status = Column(String(20))
    last_run_at = Column(DateTime(timezone=True))
    last_status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_dingjia_job_instance", "instance_id"),)


class DingjiaTask(Base):
    __tablename__ = "dingjia_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    job_id = Column(BigInteger, ForeignKey("dingjia_job.id"))
    task_name = Column(String(200))
    status = Column(String(20))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    result = Column(Text)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_dingjia_task_instance", "instance_id"),)


class DingjiaMetric(Base):
    __tablename__ = "dingjia_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_dingjia_metric_instance", "instance_id", "check_time"),)


class ZertoServer(Base):
    __tablename__ = "zerto_server"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    server_name = Column(String(200))
    version = Column(String(50))
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_zerto_server_instance", "instance_id"),)


class ZertoVpg(Base):
    __tablename__ = "zerto_vpg"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    vpg_name = Column(String(200))
    status = Column(String(20))
    vm_count = Column(Integer)
    rpo_seconds = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_zerto_vpg_instance", "instance_id"),)


class ZertoVm(Base):
    __tablename__ = "zerto_vm"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    vpg_id = Column(BigInteger, ForeignKey("zerto_vpg.id"))
    vm_name = Column(String(200))
    status = Column(String(20))
    last_sync = Column(DateTime(timezone=True))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_zerto_vm_instance", "instance_id"),)


class ZertoMetric(Base):
    __tablename__ = "zerto_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_zerto_metric_instance", "instance_id", "check_time"),)


# ──────────────────────────────────────────────
# 9. Monitoring (日志易)
# ──────────────────────────────────────────────

class RizhiyiInstance(Base):
    __tablename__ = "rizhiyi_instance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    instance_name = Column(String(200))
    version = Column(String(50))
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_rizhiyi_inst_instance", "instance_id"),)


class RizhiyiIndex(Base):
    __tablename__ = "rizhiyi_index"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    index_name = Column(String(200))
    doc_count = Column(BigInteger)
    storage_size_gb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_rizhiyi_index_instance", "instance_id"),)


class RizhiyiDashboard(Base):
    __tablename__ = "rizhiyi_dashboard"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    dashboard_name = Column(String(200))
    status = Column(String(20))
    last_alert_at = Column(DateTime(timezone=True))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_rizhiyi_dash_instance", "instance_id"),)


class RizhiyiMetric(Base):
    __tablename__ = "rizhiyi_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_rizhiyi_metric_instance", "instance_id", "check_time"),)


# ──────────────────────────────────────────────
# VM Metadata Overrides (user edits)
# ──────────────────────────────────────────────

class VmMetadataOverride(Base):
    """User-edited metadata for VMs (system, function, owner)"""
    __tablename__ = "vm_metadata_override"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(30), nullable=False)
    vm_name = Column(String(200), nullable=False)
    system = Column(String(100))
    function = Column(String(100))
    owner = Column(String(100))
    note = Column(Text)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"), onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint("platform", "vm_name", name="uq_vm_override"),
        Index("idx_vm_override_lookup", "platform", "vm_name"),
    )


# ──────────────────────────────────────────────
# ESXi Host Logs
# ──────────────────────────────────────────────

class EsxiHostLog(Base):
    """ESXi host logs collected from vCenter events"""
    __tablename__ = "esxi_host_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    host_name = Column(String(200), nullable=False)

    # Log classification
    category = Column(String(30), nullable=False)       # system, virtualization, ssh, storage, network
    service = Column(String(50), nullable=False)         # hostd, vpxa, vmkernel, sshd, etc.
    severity = Column(String(20), nullable=False)        # info, warning, error, critical

    # Content
    message = Column(Text)
    event_type = Column(String(100))
    event_id = Column(String(100))
    user_name = Column(String(100))

    # Time
    event_time = Column(DateTime(timezone=True))
    collected_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (
        Index("idx_esxi_log_host", "host_name"),
        Index("idx_esxi_log_category", "category"),
        Index("idx_esxi_log_severity", "severity"),
        Index("idx_esxi_log_time", "event_time"),
        Index("idx_esxi_log_instance", "instance_id", "event_time"),
    )


# ──────────────────────────────────────────────
# 10. SQL Server
# ──────────────────────────────────────────────

class SqlserverInstance(Base):
    __tablename__ = "sqlserver_instance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    instance_name = Column(String(200))
    db_name = Column(String(200))
    version = Column(String(50))
    host_name = Column(String(200))
    ip_address = Column(String(50))
    port = Column(Integer)
    status = Column(String(20))
    connections = Column(Integer)
    max_connections = Column(Integer)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_sqlserver_inst_instance", "instance_id"),)


class SqlserverDatabase(Base):
    __tablename__ = "sqlserver_database"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    sqlserver_instance_id = Column(BigInteger, ForeignKey("sqlserver_instance.id"))
    db_name = Column(String(200))
    recovery_model = Column(String(50))  # FULL, SIMPLE, BULK_LOGGED
    size_mb = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_sqlserver_db_instance", "instance_id"),)


class SqlserverJob(Base):
    __tablename__ = "sqlserver_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    sqlserver_instance_id = Column(BigInteger, ForeignKey("sqlserver_instance.id"))
    job_name = Column(String(200))
    job_type = Column(String(50))
    enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True))
    last_status = Column(String(20))  # succeeded, failed, retry
    next_run_at = Column(DateTime(timezone=True))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_sqlserver_job_instance", "instance_id"),)


class SqlserverMetric(Base):
    __tablename__ = "sqlserver_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_sqlserver_metric_instance", "instance_id", "check_time"),)


# ──────────────────────────────────────────────
# 11. Veritas NetBackup
# ──────────────────────────────────────────────

class NetbackupServer(Base):
    __tablename__ = "netbackup_server"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    server_name = Column(String(200))
    version = Column(String(50))
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_netbackup_server_instance", "instance_id"),)


class NetbackupJob(Base):
    __tablename__ = "netbackup_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    job_id = Column(String(100))
    job_type = Column(String(50))  # backup, restore, duplication
    policy_name = Column(String(200))
    schedule_name = Column(String(200))
    client_name = Column(String(200))
    status = Column(String(20))  # completed, failed, active, queued
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    kilobytes_transferred = Column(BigInteger)
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_netbackup_job_instance", "instance_id"),)


class NetbackupStorageUnit(Base):
    __tablename__ = "netbackup_storage_unit"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    storage_unit_name = Column(String(200))
    storage_type = Column(String(50))  # disk, tape, cloud
    total_capacity_gb = Column(Float)
    used_capacity_gb = Column(Float)
    usage_percent = Column(Float)
    status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_netbackup_su_instance", "instance_id"),)


class NetbackupClient(Base):
    __tablename__ = "netbackup_client"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uid = Column(String(36), unique=True, nullable=False, default=_uid)
    instance_id = Column(BigInteger, ForeignKey("plt_instance.id"), nullable=False)
    client_name = Column(String(200))
    os_type = Column(String(100))
    ip_address = Column(String(50))
    status = Column(String(20))
    last_backup_time = Column(DateTime(timezone=True))
    last_backup_status = Column(String(20))
    check_time = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

    __table_args__ = (Index("idx_netbackup_client_instance", "instance_id"),)


class NetbackupMetric(Base):
    __tablename__ = "netbackup_metric"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    instance_id = Column(BigInteger, nullable=False)
    resource_type = Column(String(20), nullable=False)
    resource_id = Column(BigInteger, nullable=False)
    resource_name = Column(String(200))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    storage_usage = Column(Float)
    custom_metrics = Column(JSONB)
    check_time = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("idx_netbackup_metric_instance", "instance_id", "check_time"),)


# ──────────────────────────────────────────────
# Database initialization
# ──────────────────────────────────────────────

def init_db():
    """Create all tables and seed default data"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed environments
        if db.query(Environment).count() == 0:
            db.add_all([
                Environment(code="dev", name="测试环境", sort_order=1),
                Environment(code="pre", name="准生产环境", sort_order=2),
                Environment(code="ser", name="生产环境", sort_order=3),
            ])

        # Seed platform types
        if db.query(PlatformType).count() == 0:
            db.add_all([
                PlatformType(code="vmware", name="VMware vCenter", category="virtualization", api_type="pyvmomi", icon="monitor", sort_order=1),
                PlatformType(code="smartx", name="SmartX 超融合", category="virtualization", api_type="rest", icon="cloud", sort_order=2),
                PlatformType(code="huawei_cd", name="华为云桌面", category="cloud_desktop", api_type="rest", icon="monitor", sort_order=3),
                PlatformType(code="sangfor_cd", name="深信服云桌面", category="cloud_desktop", api_type="rest", icon="monitor", sort_order=4),
                PlatformType(code="oracle", name="Oracle", category="database", api_type="rest", icon="database", sort_order=5),
                PlatformType(code="mysql", name="MySQL", category="database", api_type="rest", icon="database", sort_order=6),
                PlatformType(code="gbase", name="Gbase", category="database", api_type="rest", icon="database", sort_order=7),
                PlatformType(code="tdsql", name="TDSQL", category="database", api_type="rest", icon="database", sort_order=8),
                PlatformType(code="hwstorage", name="华为存储", category="storage", api_type="rest", icon="hard-drive", sort_order=9),
                PlatformType(code="xsky", name="XSKY 存储", category="storage", api_type="rest", icon="hard-drive", sort_order=10),
                PlatformType(code="huarui", name="华瑞存储", category="storage", api_type="rest", icon="hard-drive", sort_order=11),
                PlatformType(code="smartxzbs", name="SmartX ZBS", category="storage", api_type="rest", icon="hard-drive", sort_order=12),
                PlatformType(code="veeam", name="Veeam 备份", category="backup", api_type="rest", icon="archive", sort_order=13),
                PlatformType(code="dingjia", name="鼎甲备份", category="backup", api_type="rest", icon="archive", sort_order=14),
                PlatformType(code="zerto", name="Zerto 容灾", category="backup", api_type="rest", icon="archive", sort_order=15),
                PlatformType(code="rizhiyi", name="日志易", category="monitoring", api_type="rest", icon="bar-chart", sort_order=16),
            ])

        # Seed alert rules
        if db.query(AlertRule).count() == 0:
            db.add_all([
                AlertRule(rule_code="cpu_high", rule_name="CPU使用率过高", category="metric", target_type="host", condition_type="threshold", resource_type="cpu", warning_value=70.0, critical_value=80.0, alert_level="warning"),
                AlertRule(rule_code="memory_high", rule_name="内存使用率过高", category="metric", target_type="host", condition_type="threshold", resource_type="memory", warning_value=70.0, critical_value=80.0, alert_level="warning"),
                AlertRule(rule_code="storage_high", rule_name="存储使用率过高", category="metric", target_type="host", condition_type="threshold", resource_type="storage", warning_value=60.0, critical_value=70.0, alert_level="warning"),
                AlertRule(rule_code="table_space_high", rule_name="表空间使用率过高", category="metric", target_type="database", condition_type="threshold", resource_type="table_space", warning_value=80.0, critical_value=90.0, alert_level="warning"),
                AlertRule(rule_code="snapshot_expired", rule_name="快照超过保留期", category="inspection", target_type="snapshot", condition_type="threshold", resource_type="snapshot_days", warning_value=5.0, critical_value=7.0, alert_level="warning"),
                AlertRule(rule_code="naming_violation", rule_name="命名/备注不规范", category="inspection", target_type="vm", condition_type="pattern", alert_level="warning"),
                AlertRule(rule_code="idle_vm", rule_name="闲置虚拟机", category="inspection", target_type="vm", condition_type="presence", alert_level="warning"),
                AlertRule(rule_code="large_vm", rule_name="大容量虚拟机(>1TB)", category="inspection", target_type="vm", condition_type="threshold", resource_type="storage_tb", critical_value=1.0, alert_level="warning"),
            ])

        # Seed system config
        if db.query(SystemConfig).count() == 0:
            db.add_all([
                SystemConfig(config_key="global_collect_interval", config_value="5", value_type="int", description="全局采集间隔（分钟）"),
                SystemConfig(config_key="metrics_retention_days", config_value="30", value_type="int", description="指标数据保留天数"),
                SystemConfig(config_key="alert_auto_resolve", config_value="true", value_type="bool", description="指标类告警是否自动恢复"),
            ])

        # Seed inspection task
        if db.query(InspectionTask).count() == 0:
            db.add(InspectionTask(
                task_code="global_collect",
                task_name="全局定时采集",
                task_type="collect",
                interval_minutes=5,
                is_enabled=True,
            ))

        db.commit()
    finally:
        db.close()
