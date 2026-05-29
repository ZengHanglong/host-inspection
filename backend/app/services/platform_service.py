"""
Platform Service - PostgreSQL version
Core business logic for data collection, alerts, and reporting.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import text

from app.database import (
    AlertRecord,
    AlertRule,
    EsxiHostLog,
    PlatformInstance,
    PlatformType,
    ResourceIndex,
    SessionLocal,
    SmartxCluster,
    SmartxHost,
    SmartxMetric,
    SmartxSnapshot,
    SmartxVm,
    SmartxVolume,
    VmwareCluster,
    VmwareDatastore,
    VmwareEvent,
    VmwareHost,
    VmwareMetric,
    VmwareSnapshot,
    VmwareTask,
    VmwareVm,
)
from app.services.smartx_client import SmartXClient
from app.services.vmware_client import PYVMOMI_AVAILABLE, VMwareClient

NAMING_RULES = {
    "备注格式": "备注建议包含环境/系统/负责人等关键信息；临时虚拟机备注以 \"临时-\" 开头",
    "命名格式": "临时或克隆恢复用途的虚拟机名称以 \"tmp-\" 开头",
    "命名规则": "克隆、恢复、短期用途资产需要在名称和备注中显式标识临时属性",
}

IDLE_VM_DAYS = 30
REALTIME_READY_STATUSES = {"real_data", "partial_data"}
SNAPSHOT_CACHE_TTL_SECONDS = 180

_SNAPSHOT_CACHE: Dict[str, Any] = {"expires_at": None, "key": None, "resolution": None}
_SNAPSHOT_CACHE_LOCK = Lock()

# Simple in-memory cache for rarely-changing data
_PLATFORM_LIST_CACHE: Dict[str, Any] = {"data": None, "expires_at": None}
_THRESHOLD_CACHE: Dict[str, Any] = {"data": None, "expires_at": None}
_CACHE_TTL = 300  # 5 minutes


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _uid() -> str:
    import uuid
    return str(uuid.uuid4())


def _empty_statistics() -> Dict[str, Any]:
    return {
        "clusters": 0, "hosts": 0, "vms": 0,
        "total": 0, "normal": 0, "warning": 0, "critical": 0,
        "expired_snapshots": 0, "large_vms": 0,
    }


def _format_percent(value: Any) -> str:
    return f"{round(float(value or 0), 2)}%"


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _map_runtime_state(value: Optional[str]) -> str:
    state = str(value or "").lower()
    if state in {"connected", "maintenance"}:
        return "normal"
    if state in {"disconnected", "notresponding"}:
        return "critical"
    return "warning" if state else "unknown"


def _map_power_state(value: Optional[str]) -> str:
    state = str(value or "").lower()
    if state in {"poweredon", "poweredonstate"}:
        return "normal"
    if state in {"poweredoff", "unknown"}:
        return "warning"
    return "unknown"


def _looks_temporary(vm: Dict[str, Any]) -> bool:
    vm_name = str(vm.get("vm_name") or "").lower()
    note = str(vm.get("note") or "")
    lower_note = note.lower()
    return vm_name.startswith("tmp-") or note.startswith("临时-") or "clone" in lower_note or "恢复" in note or "备份" in note


def _extract_vm_metadata(vm_name: str, note: str, guest_os: str = "") -> Dict[str, str]:
    """Smart detection of system, owner, function, environment from VM name and note."""
    name = str(vm_name or "")
    note_text = str(note or "")
    os_text = str(guest_os or "")
    combined = f"{name} {note_text}".lower()

    # Environment
    if name.lower().startswith("tmp-") or note_text.startswith("临时-") or "clone" in combined:
        environment = "临时"
    elif "测试" in combined or "test" in combined or "dev" in combined:
        environment = "测试"
    elif "灾备" in combined or "dr" in combined.split("-"):
        environment = "灾备"
    else:
        environment = "生产"

    # System detection from VM name, guest_os, or note
    system = "未标记"
    system_patterns = {
        "windows": "Windows", "win": "Windows", "win10": "Windows 10", "win11": "Windows 11",
        "win2012": "Windows Server 2012", "win2016": "Windows Server 2016", "win2019": "Windows Server 2019",
        "win2022": "Windows Server 2022", "winserver": "Windows Server",
        "centos": "CentOS", "cent": "CentOS",
        "ubuntu": "Ubuntu", "debian": "Debian", "redhat": "Red Hat", "rhel": "Red Hat",
        "oracle linux": "Oracle Linux", "ol7": "Oracle Linux", "ol8": "Oracle Linux",
        "suse": "SUSE", "sles": "SUSE",
        "rocky": "Rocky Linux", "alma": "AlmaLinux",
        "linux": "Linux",
        "nas": "NAS", "synology": "Synology", "qnap": "QNAP",
        "docker": "Docker", "k8s": "Kubernetes", "kubernetes": "Kubernetes",
        "mysql": "MySQL", "oracle": "Oracle", "postgres": "PostgreSQL", "redis": "Redis",
        "nginx": "Nginx", "apache": "Apache", "tomcat": "Tomcat",
        "nbu": "NetBackup", "netbackup": "NetBackup", "veeam": "Veeam", "commvault": "Commvault",
    }
    # Try guest_os first (most accurate)
    if os_text:
        os_lower = os_text.lower()
        for pattern, label in system_patterns.items():
            if pattern in os_lower:
                system = label
                break
    # Fallback to VM name
    if system == "未标记":
        name_lower = name.lower()
        for pattern, label in system_patterns.items():
            if pattern in name_lower:
                system = label
                break
    # Fallback to note
    if system == "未标记" and note_text:
        note_lower = note_text.lower()
        for pattern, label in system_patterns.items():
            if pattern in note_lower:
                system = label
                break

    # Owner detection — look for person-name patterns
    owner = "未标记"
    owner_patterns = [
        "peter", "hans", "david", "michael", "john", "james", "robert", "william",
        "alex", "tom", "jack", "lisa", "mary", "anna", "sarah", "emma",
        "张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
        "admin", "administrator",
    ]
    name_parts = name.lower().replace("-", " ").replace("_", " ").split()
    for part in name_parts:
        if part in owner_patterns:
            owner = part.capitalize()
            break
        # Check if a name-like pattern (2-4 chars, starts with letter, not a tech word)
        if 2 <= len(part) <= 8 and part[0].isalpha() and not any(
            tech in part for tech in ["vm", "srv", "db", "web", "app", "api", "log", "bak", "dev", "test", "prod"]
        ):
            # Could be a name, but don't auto-assign — too risky
            pass

    # Function detection
    function = "未标记"
    func_patterns = {
        "web": "Web服务", "api": "API服务", "db": "数据库", "database": "数据库",
        "file": "文件服务", "nas": "文件存储", "backup": "备份", "bak": "备份",
        "mail": "邮件服务", "email": "邮件服务",
        "monitor": "监控", "log": "日志", "日志": "日志",
        "test": "测试", "dev": "开发", "staging": "预发布",
        "dns": "DNS", "dhcp": "DHCP", "ad": "AD域控", "域控": "AD域控",
        "proxy": "代理", "vpn": "VPN", "firewall": "防火墙",
        "oracle": "Oracle数据库", "mysql": "MySQL数据库", "redis": "Redis缓存",
        "nginx": "Nginx代理", "tomcat": "Tomcat应用",
        "nbu": "NetBackup备份", "veeam": "Veeam备份",
    }
    for pattern, label in func_patterns.items():
        if pattern in combined:
            function = label
            break

    if function == "未标记" and note_text:
        function = note_text[:30]

    return {
        "owner": owner,
        "system": system,
        "function": function,
        "environment": environment,
    }


# ──────────────────────────────────────────────
# Threshold loading
# ──────────────────────────────────────────────

DEFAULT_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "cpu": {"warning": 70.0, "critical": 80.0},
    "memory": {"warning": 70.0, "critical": 80.0},
    "storage": {"warning": 60.0, "critical": 70.0},
    "snapshot_days": {"warning": 5.0, "critical": 7.0},
}


def load_thresholds_from_rules(db) -> Dict[str, Dict[str, float]]:
    """Load thresholds from alert_rule table with caching."""
    now = datetime.now()
    cached = _THRESHOLD_CACHE.get("data")
    expires = _THRESHOLD_CACHE.get("expires_at")
    if cached and expires and expires > now:
        return cached
    thresholds = {k: dict(v) for k, v in DEFAULT_THRESHOLDS.items()}
    rules = db.query(AlertRule).filter(AlertRule.category == "metric", AlertRule.is_active == True).all()
    for rule in rules:
        if rule.resource_type:
            thresholds[rule.resource_type] = {
                "warning": float(rule.warning_value or 0),
                "critical": float(rule.critical_value or 0),
            }
    _THRESHOLD_CACHE["data"] = thresholds
    _THRESHOLD_CACHE["expires_at"] = now + timedelta(seconds=_CACHE_TTL)
    return thresholds


# ──────────────────────────────────────────────
# Platform queries
# ──────────────────────────────────────────────

def list_platform_templates(db) -> List[Dict[str, Any]]:
    now = datetime.now()
    cached = _PLATFORM_LIST_CACHE.get("data")
    expires = _PLATFORM_LIST_CACHE.get("expires_at")
    if cached and expires and expires > now:
        return cached
    platforms = db.query(PlatformType).order_by(PlatformType.sort_order).all()
    result = [{"code": p.code, "name": p.name, "category": p.category} for p in platforms]
    _PLATFORM_LIST_CACHE["data"] = result
    _PLATFORM_LIST_CACHE["expires_at"] = now + timedelta(seconds=_CACHE_TTL)
    return result


def get_active_instances(db) -> List[PlatformInstance]:
    return db.query(PlatformInstance).filter(PlatformInstance.is_active == True).order_by(PlatformInstance.id).all()


def get_connected_instances(db) -> List[PlatformInstance]:
    return (
        db.query(PlatformInstance)
        .filter(PlatformInstance.is_active == True, PlatformInstance.is_configured == True, PlatformInstance.is_connected == True)
        .order_by(PlatformInstance.id)
        .all()
    )


# ──────────────────────────────────────────────
# Snapshot cache
# ──────────────────────────────────────────────

def invalidate_snapshot_cache() -> None:
    with _SNAPSHOT_CACHE_LOCK:
        _SNAPSHOT_CACHE["expires_at"] = None
        _SNAPSHOT_CACHE["key"] = None
        _SNAPSHOT_CACHE["resolution"] = None


def _build_snapshot_cache_key(instances: List[PlatformInstance]) -> str:
    parts = []
    for inst in instances:
        parts.append("|".join([
            str(inst.id) or "",
            inst.api_url or "",
            str(inst.api_port or ""),
            inst.api_username or "",
            str(bool(inst.is_connected)),
            str(inst.last_test_at.isoformat() if inst.last_test_at else ""),
            str(inst.updated_at.isoformat() if inst.updated_at else ""),
        ]))
    return "||".join(parts)


def collect_connected_snapshots(db) -> List[Dict[str, Any]]:
    resolution = _collect_connected_snapshots_resolution(db)
    return [dict(snapshot) for snapshot in resolution["usable_snapshots"]]


def is_cache_warm() -> bool:
    """Check if snapshot cache is populated."""
    with _SNAPSHOT_CACHE_LOCK:
        return _SNAPSHOT_CACHE.get("resolution") is not None and _SNAPSHOT_CACHE.get("expires_at") and _SNAPSHOT_CACHE["expires_at"] > datetime.now()


def _collect_connected_snapshots_resolution(db) -> Dict[str, Any]:
    connected = get_connected_instances(db)
    if not connected:
        invalidate_snapshot_cache()
        return {"status": "no_credentials", "message": "未配置可用的API凭证", "usable_snapshots": [], "failed_snapshots": [], "connected_instances": []}

    cache_key = _build_snapshot_cache_key(connected)
    now = datetime.now()
    with _SNAPSHOT_CACHE_LOCK:
        cached = _SNAPSHOT_CACHE.get("resolution")
        if cached and _SNAPSHOT_CACHE.get("key") == cache_key and _SNAPSHOT_CACHE.get("expires_at") and _SNAPSHOT_CACHE["expires_at"] > now:
            return cached

        thresholds = load_thresholds_from_rules(db)
        snapshots = [collect_instance_snapshot(inst, thresholds) for inst in connected]
        resolution = _resolve_snapshot_collection_status(snapshots)
        resolution["connected_instances"] = connected
        _SNAPSHOT_CACHE["key"] = cache_key
        _SNAPSHOT_CACHE["resolution"] = resolution
        _SNAPSHOT_CACHE["expires_at"] = datetime.now() + timedelta(seconds=SNAPSHOT_CACHE_TTL_SECONDS)
        return resolution


def _resolve_snapshot_collection_status(snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not snapshots:
        return {"status": "collection_failed", "message": "已连接平台暂未返回真实巡检数据", "usable_snapshots": [], "failed_snapshots": []}

    usable = [s for s in snapshots if s.get("status") in REALTIME_READY_STATUSES]
    failed = [s for s in snapshots if s.get("status") not in REALTIME_READY_STATUSES]

    if not usable:
        failed_names = "、".join(s.get("platform_name", s.get("platform", "平台")) for s in failed)
        return {"status": "collection_failed", "message": f"已连接平台采集失败: {failed_names}" if failed_names else "采集失败", "usable_snapshots": [], "failed_snapshots": failed}

    if failed:
        failed_names = "、".join(s.get("platform_name", s.get("platform", "平台")) for s in failed)
        return {"status": "partial_data", "message": f"部分平台采集成功，以下平台失败: {failed_names}", "usable_snapshots": usable, "failed_snapshots": failed}

    return {"status": "real_data", "message": "数据来源: 真实API", "usable_snapshots": usable, "failed_snapshots": []}


# ──────────────────────────────────────────────
# Instance snapshot collection
# ──────────────────────────────────────────────

def collect_instance_snapshot(instance: PlatformInstance, thresholds: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """Collect data from a single platform instance."""
    platform_code = instance.platform.code if instance.platform else ""

    if platform_code == "vmware":
        return _collect_vmware_snapshot(instance, thresholds)
    if platform_code == "smartx":
        return _collect_smartx_snapshot(instance)
    return _build_unavailable_snapshot(instance, "该平台尚未纳入首批真实巡检范围")


def _collect_vmware_snapshot(instance: PlatformInstance, thresholds: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    if not PYVMOMI_AVAILABLE:
        return _build_unavailable_snapshot(instance, "pyVmomi 未安装")

    from app.utils.encryption import decrypt_password
    password = decrypt_password(instance.api_password or "")

    client = VMwareClient(
        host=instance.api_url or "",
        port=instance.api_port or 443,
        username=instance.api_username or "",
        password=password,
        ssl_verify=instance.ssl_verify if instance.ssl_verify is not None else True,
    )

    if not client.connect():
        return _build_unavailable_snapshot(instance, f"连接失败: {client.get_last_error()}")

    try:
        check_time = datetime.now().isoformat()
        clusters = client.get_all_clusters()
        hosts = client.get_all_hosts()
        vms = client.get_all_vms()
        collection_errors = client.get_collection_errors()
        expired_snapshots = _decorate_snapshot_rows("vmware", "VMware vCenter", client.get_expired_snapshots(int(thresholds["snapshot_days"]["critical"])), check_time)
        large_vms = _decorate_large_vm_rows("vmware", "VMware vCenter", client.get_large_vms(1.0), vms, check_time)
        naming_issues = _build_naming_issue_rows("vmware", "VMware vCenter", vms, check_time)
        idle_vms = _build_idle_vm_rows("vmware", "VMware vCenter", vms, check_time)
        triggered_alarms = _build_triggered_alarm_rows("vmware", "VMware vCenter", client.get_triggered_alarms(), check_time)

        # Collect ESXi host logs via SSH (concurrent, per-host credentials)
        from app.database import EsxiHostCredential
        from app.services.esxi_log_collector import collect_all_esxi_logs

        esxi_user = instance.esxi_ssh_username or "root"
        esxi_pass_enc = instance.esxi_ssh_password or ""
        esxi_port = instance.esxi_ssh_port or 22
        if esxi_pass_enc:
            from app.utils.encryption import decrypt_password
            esxi_pass = decrypt_password(esxi_pass_enc)
        else:
            esxi_pass = password  # fallback to vCenter password

        # Load per-host credential overrides
        host_creds = {}
        overrides = db.query(EsxiHostCredential).filter(
            EsxiHostCredential.instance_id == instance.id,
            EsxiHostCredential.is_active == True,
        ).all()
        for ov in overrides:
            host_creds[ov.host_ip] = {
                "username": ov.ssh_username or esxi_user,
                "password": decrypt_password(ov.ssh_password) if ov.ssh_password else esxi_pass,
                "port": ov.ssh_port or esxi_port,
            }

        log_result = collect_all_esxi_logs(
            hosts=hosts,
            default_username=esxi_user,
            default_password=esxi_pass,
            default_port=esxi_port,
            hours=24,
            max_lines_per_file=100,
            per_host_credentials=host_creds,
            max_workers=5,
        )
        esxi_logs = log_result["logs"]

        # Store collection errors for reporting
        if log_result["errors"]:
            for host_ip, err_msg in log_result["errors"].items():
                collection_errors.append(f"esxi_log:{host_ip}: {err_msg}")

        alerts = _build_alert_rows("vmware", "VMware vCenter", hosts, expired_snapshots, large_vms, naming_issues, idle_vms, thresholds, instance.api_url, check_time)
        statistics = _build_platform_statistics(hosts, vms, clusters, expired_snapshots, large_vms)
        capabilities = {"cluster_status": True, "hosts": True, "vms": True, "snapshots": True, "annotations": True, "idle_assets": True, "large_vms": True, "history": True, "auth_verified": True}

        if not clusters and not hosts and not vms:
            return {
                "status": "collection_failed", "message": "VMware 连接成功，但未采集到任何数据",
                "platform": "vmware", "platform_name": "VMware vCenter", "display_name": instance.instance_name,
                "data_source": instance.api_url, "last_sync": check_time, "connected": False,
                "clusters": [], "hosts": [], "vms": [], "expired_snapshots": [], "large_vms": [],
                "naming_issues": [], "idle_vms": [], "triggered_alarms": [], "alerts": [],
                "statistics": statistics, "capabilities": capabilities, "collection_errors": collection_errors,
            }

        snapshot_status = "partial_data" if collection_errors else "real_data"
        snapshot_message = f"VMware 数据部分采集成功，存在 {len(collection_errors)} 个异常" if collection_errors else f"数据来源: {instance.api_url}"

        return {
            "status": snapshot_status, "message": snapshot_message,
            "platform": "vmware", "platform_name": "VMware vCenter", "display_name": instance.instance_name,
            "data_source": instance.api_url, "last_sync": check_time, "connected": True,
            "clusters": clusters, "hosts": hosts, "vms": vms,
            "expired_snapshots": expired_snapshots, "large_vms": large_vms,
            "naming_issues": naming_issues, "idle_vms": idle_vms, "triggered_alarms": triggered_alarms,
            "alerts": alerts, "statistics": statistics, "capabilities": capabilities, "collection_errors": collection_errors,
            "esxi_logs": esxi_logs,
        }
    finally:
        client.disconnect()


def _collect_smartx_snapshot(instance: PlatformInstance) -> Dict[str, Any]:
    from app.utils.encryption import decrypt_password
    password = decrypt_password(instance.api_password or "")

    client = SmartXClient(
        host=instance.api_url or "",
        port=instance.api_port or 443,
        username=instance.api_username or "",
        password=password,
        ssl_verify=instance.ssl_verify if instance.ssl_verify is not None else True,
    )
    status = client.describe_integration_status()
    return {
        "status": "collection_failed", "message": status["message"],
        "platform": "smartx", "platform_name": "SmartX CloudTower", "display_name": instance.instance_name,
        "data_source": instance.api_url, "last_sync": datetime.now().isoformat(), "connected": False,
        "clusters": [], "hosts": [], "vms": [], "expired_snapshots": [], "large_vms": [],
        "naming_issues": [], "idle_vms": [], "alerts": [], "statistics": _empty_statistics(),
        "capabilities": status["capabilities"], "collection_errors": [status["message"]],
    }


def _build_unavailable_snapshot(instance: PlatformInstance, message: str) -> Dict[str, Any]:
    platform_code = instance.platform.code if instance.platform else ""
    platform_name = instance.platform.name if instance.platform else ""
    return {
        "status": "collection_failed", "message": message,
        "platform": platform_code, "platform_name": platform_name, "display_name": instance.instance_name,
        "data_source": instance.api_url, "last_sync": datetime.now().isoformat(), "connected": False,
        "clusters": [], "hosts": [], "vms": [], "expired_snapshots": [], "large_vms": [],
        "naming_issues": [], "idle_vms": [], "alerts": [], "statistics": _empty_statistics(),
        "capabilities": {}, "collection_errors": [message],
    }


# ──────────────────────────────────────────────
# Alert helpers
# ──────────────────────────────────────────────

def flatten_alerts(snapshots: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for snapshot in snapshots:
        alerts.extend(snapshot.get("alerts", []))
    return sorted(alerts, key=lambda a: a.get("created_at", ""), reverse=True)


def _build_alert_rows(platform, platform_name, hosts, expired_snapshots, large_vms, naming_issues, idle_vms, thresholds, data_source, created_at):
    alerts = []
    for host in hosts:
        if host.get("status") == "normal":
            continue
        alerts.append({
            "platform": platform, "platform_name": platform_name,
            "resource_type": "host", "resource_name": host.get("host_name", ""),
            "alert_level": host.get("status", "warning"),
            "message": f"主机 {host.get('host_name')} 状态异常，CPU {host.get('cpu_usage_percent', 0)}%，内存 {host.get('memory_usage_percent', 0)}%",
            "threshold_value": thresholds["cpu"]["warning"],
            "current_value": max(host.get("cpu_usage_percent", 0), host.get("memory_usage_percent", 0)),
            "created_at": created_at, "status": "active", "data_source": data_source,
        })
    for row in expired_snapshots:
        alerts.append({
            "platform": platform, "platform_name": platform_name,
            "resource_type": "snapshot", "resource_name": row.get("vm_name", ""),
            "alert_level": row.get("status", "warning"),
            "message": row.get("action") or f"虚拟机 {row.get('vm_name')} 存在过期快照",
            "threshold_value": row.get("threshold_days", 7), "current_value": row.get("snapshot_days", 0),
            "created_at": created_at, "status": "active", "data_source": data_source,
        })
    for row in large_vms:
        alerts.append({
            "platform": platform, "platform_name": platform_name,
            "resource_type": "vm", "resource_name": row.get("vm_name", ""),
            "alert_level": "warning",
            "message": row.get("action") or f"虚拟机 {row.get('vm_name')} 容量超过 1TB",
            "threshold_value": 1.0, "current_value": row.get("disk_tb", 0),
            "created_at": created_at, "status": "active", "data_source": data_source,
        })
    for row in naming_issues:
        alerts.append({
            "platform": platform, "platform_name": platform_name,
            "resource_type": "vm", "resource_name": row.get("vm_name", ""),
            "alert_level": "warning",
            "message": f"虚拟机 {row.get('vm_name')} 命名/备注不符合规范",
            "created_at": created_at, "status": "active", "data_source": data_source,
        })
    for row in idle_vms:
        alerts.append({
            "platform": platform, "platform_name": platform_name,
            "resource_type": "vm", "resource_name": row.get("vm_name", ""),
            "alert_level": "warning",
            "message": row.get("action") or f"虚拟机 {row.get('vm_name')} 疑似闲置",
            "threshold_value": IDLE_VM_DAYS, "current_value": row.get("created_days", 0),
            "created_at": created_at, "status": "active", "data_source": data_source,
        })
    return alerts


def _build_platform_statistics(hosts, vms, clusters, expired_snapshots, large_vms):
    return {
        "clusters": len(clusters), "hosts": len(hosts), "vms": len(vms),
        "total": len(hosts),
        "normal": len([h for h in hosts if h.get("status") == "normal"]),
        "warning": len([h for h in hosts if h.get("status") == "warning"]),
        "critical": len([h for h in hosts if h.get("status") == "critical"]),
        "expired_snapshots": len(expired_snapshots), "large_vms": len(large_vms),
    }


def _decorate_snapshot_rows(platform, platform_name, rows, check_time):
    decorated = []
    for row in rows:
        days = int(row.get("snapshot_days", 0) or 0)
        threshold = int(row.get("threshold_days", 7) or 7)
        severity = "critical" if days > threshold + 3 else "warning"
        decorated.append({
            "platform": platform, "platform_name": platform_name,
            "vm_name": row.get("vm_name"), "snapshot_name": row.get("snapshot_name") or "root-snapshot",
            "cluster_name": row.get("cluster_name", ""), "snapshot_days": days, "threshold_days": threshold,
            "status": severity, "action": f"删除超过 {threshold} 天的快照", "check_time": row.get("check_time") or check_time,
        })
    return decorated


def _decorate_large_vm_rows(platform, platform_name, rows, all_vms, check_time):
    vm_map = {vm.get("vm_name"): vm for vm in all_vms}
    decorated = []
    for row in rows:
        vm = vm_map.get(row.get("vm_name"), {})
        metadata = _extract_vm_metadata(vm.get("vm_name", ""), vm.get("note", ""), vm.get("guest_os", ""))
        decorated.append({
            "platform": platform, "platform_name": platform_name,
            "vm_name": row.get("vm_name"),
            "cluster_name": row.get("cluster_name", vm.get("cluster_name", "")),
            "ip": vm.get("ip_address") or "--",
            "disk_tb": round(float(row.get("storage_tb", vm.get("storage_tb", 0)) or 0), 2),
            "cpu": int(row.get("cpu_count", vm.get("cpu_count", 0)) or 0),
            "memory_gb": round(float(row.get("memory_gb", vm.get("memory_gb", 0)) or 0), 2),
            "owner": metadata["owner"], "system": metadata["system"], "function": metadata["function"],
            "action": "确认是否可以清理历史数据、日志或归档磁盘", "check_time": row.get("check_time") or check_time,
        })
    return decorated


def _build_naming_issue_rows(platform, platform_name, vms, check_time):
    rows = []
    for vm in vms:
        issues = []
        vm_name = str(vm.get("vm_name") or "")
        note = str(vm.get("note") or "")
        temporary = _looks_temporary(vm)
        if not note.strip():
            issues.append("缺少备注")
        if temporary and not vm_name.lower().startswith("tmp-"):
            issues.append("临时资产名称未以 tmp- 开头")
        if temporary and not note.startswith("临时-"):
            issues.append("临时资产备注未以 临时- 开头")
        if " " in vm_name:
            issues.append("名称包含空格")
        if not issues:
            continue
        rows.append({
            "platform": platform, "platform_name": platform_name,
            "cluster_name": vm.get("cluster_name", ""), "vm_name": vm_name,
            "ip": vm.get("ip_address") or "--", "current_note": note, "issues": issues, "check_time": check_time,
        })
    return rows


def _build_idle_vm_rows(platform, platform_name, vms, check_time):
    rows = []
    for vm in vms:
        created_days = int(vm.get("created_days", 0) or 0)
        powered_off = str(vm.get("power_state") or "").lower() != "poweredon"
        temporary = _looks_temporary(vm)
        if not temporary and not (powered_off and created_days >= IDLE_VM_DAYS):
            continue
        rows.append({
            "platform": platform, "platform_name": platform_name,
            "cluster_name": vm.get("cluster_name", ""), "vm_name": vm.get("vm_name"),
            "ip": vm.get("ip_address") or "--", "note": vm.get("note", ""),
            "cpu": int(vm.get("cpu_count", 0) or 0),
            "memory_gb": round(float(vm.get("memory_gb", 0) or 0), 2),
            "disk_gb": round(float(vm.get("storage_gb", 0) or 0), 2),
            "power_state": vm.get("power_state"), "created_days": created_days,
            "action": "确认是否仍需保留；如为临时用途请按规则标识并尽快清理", "check_time": check_time,
        })
    return rows


def _build_triggered_alarm_rows(platform, platform_name, rows, check_time):
    result = []
    for row in rows:
        result.append({
            "platform": platform, "platform_name": platform_name,
            "alarm_id": row.get("alarm_id", ""), "alarm_name": row.get("alarm_name", ""),
            "description": row.get("description", ""), "entity_name": row.get("entity_name", ""),
            "entity_type": row.get("entity_type", ""), "status": row.get("status", "unknown"),
            "triggered_time": row.get("triggered_time"), "acknowledged": row.get("acknowledged", False),
            "check_time": check_time,
        })
    return result


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

def build_dashboard_payload(db) -> Dict[str, Any]:
    connected = get_connected_instances(db)
    if not connected:
        return {
            "status": "no_credentials", "message": "未配置可用的API凭证，请先完成平台连接测试",
            "configured_count": 0, "total_platforms": db.query(PlatformType).count(),
            "platforms": {}, "overall": {"total_hosts": 0, "normal": 0, "warning": 0, "critical": 0, "data_source": "none", "last_check_time": None, "data_cutoff_time": None, "data_sources": []},
            "alerts": [], "periodic_status": {}, "failed_platforms": {},
        }

    resolution = _collect_connected_snapshots_resolution(db)
    if not resolution["usable_snapshots"]:
        return {
            "status": resolution["status"], "message": resolution["message"],
            "configured_count": len(connected), "total_platforms": db.query(PlatformType).count(),
            "platforms": {}, "overall": {"total_hosts": 0, "normal": 0, "warning": 0, "critical": 0, "data_source": "none", "last_check_time": None, "data_cutoff_time": None, "data_sources": []},
            "alerts": [], "periodic_status": {}, "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
        }

    return _build_dashboard_from_snapshots(resolution["usable_snapshots"], status=resolution["status"], message=resolution["message"], failed_snapshots=resolution["failed_snapshots"])


def _build_failed_platform_entries(failed_snapshots):
    return {
        s["platform"]: {
            "name": s.get("platform_name"), "data_source": s.get("data_source"),
            "connected": False, "last_sync": s.get("last_sync"),
            "statistics": s.get("statistics", _empty_statistics()),
            "clusters": s.get("clusters", []), "capabilities": s.get("capabilities", {}),
            "status": s.get("status"), "message": s.get("message", "采集失败"),
        }
        for s in failed_snapshots
    }


def _build_dashboard_from_snapshots(snapshots, status="real_data", message="", failed_snapshots=None):
    failed_snapshots = failed_snapshots or []
    platforms = {
        s["platform"]: {
            "name": s["platform_name"], "data_source": s.get("data_source"),
            "connected": s.get("connected", False), "last_sync": s.get("last_sync"),
            "statistics": s.get("statistics", _empty_statistics()),
            "clusters": s.get("clusters", []), "capabilities": s.get("capabilities", {}),
            "status": s.get("status"), "message": s.get("message", ""),
            "collection_errors": s.get("collection_errors", []),
        }
        for s in snapshots
    }
    platforms.update(_build_failed_platform_entries(failed_snapshots))

    all_hosts = [h for s in snapshots for h in s.get("hosts", [])]
    all_alerts = flatten_alerts(snapshots)

    return {
        "status": status, "message": message, "platforms": platforms,
        "failed_platforms": _build_failed_platform_entries(failed_snapshots),
        "overall": {
            "total_hosts": len(all_hosts),
            "normal": len([h for h in all_hosts if h.get("status") == "normal"]),
            "warning": len([h for h in all_hosts if h.get("status") == "warning"]),
            "critical": len([h for h in all_hosts if h.get("status") == "critical"]),
            "data_source": "real_api",
            "last_check_time": max((s.get("last_sync") for s in snapshots), default=datetime.now().isoformat()),
            "data_cutoff_time": max((s.get("last_sync") for s in snapshots), default=datetime.now().isoformat()),
            "data_sources": [s.get("data_source") for s in snapshots if s.get("data_source")],
        },
        "alerts": all_alerts,
        "periodic_status": {
            "snapshot_check": {"name": "过期快照检查", "expired_count": len([r for s in snapshots for r in s.get("expired_snapshots", [])]), "data_source": "real_api"},
            "large_vm_check": {"name": "大容量虚拟机排查", "large_count": len([r for s in snapshots for r in s.get("large_vms", [])]), "data_source": "real_api"},
            "naming_check": {"name": "命名与备注维护", "issue_count": len([r for s in snapshots for r in s.get("naming_issues", [])]), "data_source": "real_api"},
            "idle_vm_check": {"name": "闲置资产排查", "issue_count": len([r for s in snapshots for r in s.get("idle_vms", [])]), "data_source": "real_api"},
        },
    }


# ──────────────────────────────────────────────
# Inspection list
# ──────────────────────────────────────────────

def build_inspection_list_payload(db, platform=None, status=None, category=None):
    connected = get_connected_instances(db)
    if not connected:
        return {"status": "no_credentials", "message": "未配置可用的API凭证", "total": 0, "data": [], "platforms": list_platform_templates(db), "last_check_time": None}

    resolution = _collect_connected_snapshots_resolution(db)
    if not resolution["usable_snapshots"]:
        return {"status": resolution["status"], "message": resolution["message"], "total": 0, "data": [], "platforms": list_platform_templates(db), "last_check_time": None, "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"])}

    rows = []
    for snapshot in resolution["usable_snapshots"]:
        if platform and snapshot["platform"] != platform:
            continue
        rows.extend(_build_host_inspection_rows(snapshot))

    if category:
        rows = [r for r in rows if r.get("category") == category]
    if status:
        rows = [r for r in rows if r.get("status") == status]

    return {
        "status": resolution["status"] if rows else resolution["status"],
        "message": resolution["message"] if rows else "当前没有符合条件的巡检记录",
        "total": len(rows), "data": rows, "platforms": list_platform_templates(db),
        "last_check_time": max((r["check_time"] for r in rows), default=max((s.get("last_sync") for s in resolution["usable_snapshots"]), default=None)),
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def _build_host_inspection_rows(snapshot):
    rows = []
    for host in snapshot.get("hosts", []):
        cpu_total_ghz = round(float(host.get("cpu_total_mhz", 0) or 0) / 1000, 2)
        cpu_used_ghz = round(float(host.get("cpu_usage_mhz", 0) or 0) / 1000, 2)
        cpu_avail_ghz = round(cpu_total_ghz - cpu_used_ghz, 2)
        mem_total_gb = round(float(host.get("memory_total_mb", 0) or 0) / 1024, 2)
        mem_used_gb = round(float(host.get("memory_used_mb", 0) or 0) / 1024, 2)
        mem_avail_gb = round(mem_total_gb - mem_used_gb, 2)
        storage_pct = float(host.get("storage_usage_percent", 0) or 0)

        rows.append({
            "platform": snapshot["platform"], "platform_name": snapshot["platform_name"],
            "category": "虚拟化", "cluster_name": host.get("cluster_name") or "--",
            "host_name": host.get("host_name"), "status": host.get("status", "unknown"),
            "inspection_items": {
                "CPU": f"可用: {cpu_avail_ghz} GHz | 已用: {cpu_used_ghz} GHz | 总计: {cpu_total_ghz} GHz",
                "内存": f"可用: {mem_avail_gb} GB | 已用: {mem_used_gb} GB | 总计: {mem_total_gb} GB",
                "存储": f"使用率: {_format_percent(storage_pct)}",
                "连接状态": _map_runtime_state(host.get("connection_state")),
                "电源状态": _map_power_state(host.get("power_state")),
                "虚拟机数量": str(int(host.get("vm_count", 0) or 0)),
            },
            "host_detail": {
                "cpu_cores": int(host.get("cpu_cores", 0) or 0),
                "cpu_total_ghz": cpu_total_ghz,
                "cpu_used_ghz": cpu_used_ghz,
                "cpu_avail_ghz": cpu_avail_ghz,
                "cpu_percent": float(host.get("cpu_usage_percent", 0) or 0),
                "mem_total_gb": mem_total_gb,
                "mem_used_gb": mem_used_gb,
                "mem_avail_gb": mem_avail_gb,
                "mem_percent": float(host.get("memory_usage_percent", 0) or 0),
                "storage_percent": storage_pct,
                "vm_count": int(host.get("vm_count", 0) or 0),
                "uptime_days": float(host.get("uptime_days", 0) or 0),
            },
            "check_time": snapshot.get("last_sync"), "data_source": snapshot.get("data_source"),
        })
    return rows


# ──────────────────────────────────────────────
# Platform inspection
# ──────────────────────────────────────────────

def build_platform_inspection_payload(db, platform: str):
    instance = db.query(PlatformInstance).join(PlatformType).filter(PlatformType.code == platform).first()
    if not instance:
        raise ValueError(f"平台 {platform} 不存在")

    if not instance.is_configured:
        return {"status": "not_configured", "message": f"{instance.instance_name} 未配置API凭证", "platform": platform, "hosts": [], "statistics": _empty_statistics()}

    if not instance.is_connected:
        return {"status": "not_connected", "message": f"{instance.instance_name} 连接失败", "platform": platform, "last_error": instance.last_error, "hosts": [], "statistics": _empty_statistics()}

    resolution = _collect_connected_snapshots_resolution(db)
    snapshot = next((s for s in resolution["usable_snapshots"] if s.get("platform") == platform), None)
    if not snapshot:
        failed = next((s for s in resolution["failed_snapshots"] if s.get("platform") == platform), None)
        snapshot = failed or {"status": resolution.get("status", "collection_failed"), "message": resolution.get("message", "采集失败"), "platform": platform, "hosts": [], "clusters": [], "vms": []}

    rows = _build_host_inspection_rows(snapshot)
    return {
        "status": snapshot.get("status", "no_data"), "message": snapshot.get("message", ""),
        "platform": platform, "platform_name": snapshot.get("platform_name", ""),
        "data_source": snapshot.get("data_source"), "hosts": rows,
        "clusters": snapshot.get("clusters", []), "vms": snapshot.get("vms", []),
        "statistics": {
            "total": len(rows),
            "normal": len([r for r in rows if r["status"] == "normal"]),
            "warning": len([r for r in rows if r["status"] == "warning"]),
            "critical": len([r for r in rows if r["status"] == "critical"]),
        },
        "last_check_time": snapshot.get("last_sync"), "capabilities": snapshot.get("capabilities", {}),
    }


# ──────────────────────────────────────────────
# Alerts payload
# ──────────────────────────────────────────────

def build_alerts_payload(db, status=None, level=None, platform=None, category=None, alert_type=None, limit=100):
    connected = get_connected_instances(db)
    if not connected:
        return {"status": "no_credentials", "message": "未配置可用的API凭证", "total": 0, "statistics": {"active": 0, "warning": 0, "critical": 0}, "alerts": [], "platforms": list_platform_templates(db), "categories": [], "failed_platforms": {}}

    resolution = _collect_connected_snapshots_resolution(db)
    if not resolution["usable_snapshots"]:
        return {"status": resolution["status"], "message": resolution["message"], "total": 0, "statistics": {"active": 0, "warning": 0, "critical": 0}, "alerts": [], "platforms": list_platform_templates(db), "categories": [], "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"])}

    alerts = flatten_alerts(resolution["usable_snapshots"])
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    if level:
        alerts = [a for a in alerts if a["alert_level"] == level]
    if platform:
        alerts = [a for a in alerts if a["platform"] == platform]
    alerts = alerts[:limit]

    return {
        "status": resolution["status"], "message": resolution["message"] if alerts else "当前没有告警项",
        "total": len(alerts),
        "statistics": {
            "active": len([a for a in alerts if a["status"] == "active"]),
            "warning": len([a for a in alerts if a["alert_level"] == "warning"]),
            "critical": len([a for a in alerts if a["alert_level"] == "critical"]),
        },
        "alerts": alerts, "platforms": list_platform_templates(db),
        "categories": sorted({a["category"] for a in alerts if a.get("category")}),
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def build_alert_statistics_payload(db):
    resolution = _collect_connected_snapshots_resolution(db)
    alerts = flatten_alerts(resolution["usable_snapshots"])
    by_platform: Dict[str, Dict[str, Any]] = {}
    for alert in alerts:
        p = alert["platform"]
        entry = by_platform.setdefault(p, {"name": alert["platform_name"], "warning": 0, "critical": 0})
        entry[alert["alert_level"]] += 1
    return {
        "status": resolution["status"], "message": resolution["message"] if alerts else "当前没有告警",
        "total_alerts": len(alerts), "by_platform": by_platform,
        "by_level": {"warning": len([a for a in alerts if a["alert_level"] == "warning"]), "critical": len([a for a in alerts if a["alert_level"] == "critical"])},
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def build_thresholds_payload(db):
    rules = db.query(AlertRule).filter(AlertRule.category == "metric", AlertRule.is_active == True).all()
    return {
        "thresholds": [
            {"resource_type": r.resource_type, "warning_threshold": r.warning_value, "critical_threshold": r.critical_value}
            for r in rules
        ]
    }


# ──────────────────────────────────────────────
# Ledger
# ──────────────────────────────────────────────

def build_vm_ledger_payload(db, platform=None, cluster=None, owner=None, environment=None, has_snapshot=None):
    from app.database import VmMetadataOverride

    connected = get_connected_instances(db)
    if not connected:
        return {"name": "虚拟机台账", "status": "no_credentials", "message": "未配置可用的API凭证", "total": 0, "statistics": {"total_cpu_cores": 0, "total_memory_gb": 0, "total_disk_gb": 0, "with_snapshot_count": 0}, "data": [], "failed_platforms": {}}

    resolution = _collect_connected_snapshots_resolution(db)
    rows = _build_vm_ledger_rows(resolution["usable_snapshots"])

    # Apply user overrides
    overrides = {(o.platform, o.vm_name): o for o in db.query(VmMetadataOverride).all()}
    for row in rows:
        key = (row["platform"], row["vm_name"])
        if key in overrides:
            ov = overrides[key]
            if ov.system:
                row["system"] = ov.system
            if ov.function:
                row["function"] = ov.function
            if ov.owner:
                row["owner"] = ov.owner
            if ov.note is not None:
                row["note"] = ov.note

    if platform:
        rows = [r for r in rows if r["platform"] == platform]
    if cluster:
        rows = [r for r in rows if r["cluster"] == cluster]

    return {
        "name": "虚拟机台账", "status": resolution["status"],
        "message": resolution["message"] if rows else "当前没有符合条件的虚拟机数据",
        "total": len(rows),
        "statistics": {
            "total_cpu_cores": sum(r["cpu"] for r in rows),
            "total_memory_gb": round(sum(r["memory_gb"] for r in rows), 2),
            "total_disk_gb": round(sum(r["disk_gb"] for r in rows), 2),
            "with_snapshot_count": len([r for r in rows if r["has_snapshot"]]),
        },
        "data": rows, "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def _build_vm_ledger_rows(snapshots):
    rows = []
    for snapshot in snapshots:
        for vm in snapshot.get("vms", []):
            metadata = _extract_vm_metadata(vm.get("vm_name", ""), vm.get("note", ""), vm.get("guest_os", ""))
            rows.append({
                "platform": snapshot["platform"], "platform_name": snapshot["platform_name"],
                "cluster": vm.get("cluster_name") or "--", "vm_name": vm.get("vm_name"),
                "ip": vm.get("ip_address") or "--", "cpu": vm.get("cpu_count", 0),
                "memory_gb": round(float(vm.get("memory_gb", 0)), 2),
                "disk_gb": round(float(vm.get("storage_gb", 0)), 2),
                "disk_tb": round(float(vm.get("storage_tb", 0)), 2),
                "system": metadata["system"], "function": metadata["function"],
                "owner": metadata["owner"], "environment": metadata["environment"],
                "power_state": vm.get("power_state"), "has_snapshot": bool(vm.get("has_snapshot")),
                "snapshot_days": int(vm.get("snapshot_days", 0) or 0),
                "note": vm.get("note", ""), "status": vm.get("power_state") or "unknown",
            })
    return rows


def build_physical_ledger_payload(db, platform=None, cluster=None):
    connected = get_connected_instances(db)
    if not connected:
        return {"name": "物理机台账", "status": "no_credentials", "message": "未配置可用的API凭证", "total": 0, "statistics": {"total_cpu_cores": 0, "total_memory_gb": 0, "by_platform": {}}, "data": [], "failed_platforms": {}}

    resolution = _collect_connected_snapshots_resolution(db)
    rows = _build_physical_ledger_rows(resolution["usable_snapshots"])
    if platform:
        rows = [r for r in rows if r["platform"] == platform]
    if cluster:
        rows = [r for r in rows if r["cluster"] == cluster]

    return {
        "name": "物理机台账", "status": resolution["status"],
        "message": resolution["message"] if rows else "当前没有符合条件的物理主机数据",
        "total": len(rows),
        "statistics": {
            "total_cpu_cores": sum(r["cpu"] for r in rows),
            "total_memory_gb": round(sum(r["memory_gb"] for r in rows), 2),
            "by_platform": {k: len([r for r in rows if r["platform"] == k]) for k in sorted({r["platform"] for r in rows})},
        },
        "data": rows, "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def _build_physical_ledger_rows(snapshots):
    rows = []
    for snapshot in snapshots:
        for host in snapshot.get("hosts", []):
            rows.append({
                "platform": snapshot["platform"], "platform_name": snapshot["platform_name"],
                "cluster": host.get("cluster_name") or "--", "host_name": host.get("host_name"),
                "ip": host.get("ip_address") or "--", "mgmt_ip": host.get("ip_address") or "--",
                "cpu": int(host.get("cpu_cores", 0) or 0),
                "memory_gb": round(float(host.get("memory_total_mb", 0)) / 1024, 2),
                "host_type": "Hypervisor Host", "status": host.get("status", "unknown"),
                "uptime_days": round(float(host.get("uptime_days", 0) or 0), 2),
            })
    return rows


def build_db_ledger_payload():
    return {
        "name": "数据库台账", "total": 0,
        "statistics": {"total_space_gb": 0, "used_space_gb": 0, "avg_space_usage": 0},
        "data": [], "message": "数据库台账待接入真实数据源",
    }


def build_ledger_summary_payload(db):
    vm = build_vm_ledger_payload(db)
    physical = build_physical_ledger_payload(db)
    db_payload = build_db_ledger_payload()
    return {
        "vm_ledger": {"name": vm["name"], "total": vm["total"], "with_snapshot": vm["statistics"]["with_snapshot_count"]},
        "physical_ledger": {"name": physical["name"], "total": physical["total"], "by_platform": physical["statistics"]["by_platform"]},
        "db_ledger": {"name": db_payload["name"], "total": db_payload["total"]},
    }


# ──────────────────────────────────────────────
# Periodic checks
# ──────────────────────────────────────────────

def build_snapshot_periodic_payload(db):
    connected = get_connected_instances(db)
    if not connected:
        return {"status": "no_credentials", "message": "未配置可用的API凭证", "total": 0, "warning": 0, "critical": 0, "data": [], "threshold_days": 7, "failed_platforms": {}}

    resolution = _collect_connected_snapshots_resolution(db)
    rows = [r for s in resolution["usable_snapshots"] for r in s.get("expired_snapshots", [])]
    return {
        "status": resolution["status"], "message": resolution["message"] if rows else "当前没有超过阈值的过期快照",
        "total": len(rows),
        "warning": len([r for r in rows if r["status"] == "warning"]),
        "critical": len([r for r in rows if r["status"] == "critical"]),
        "data": rows, "threshold_days": 7,
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def build_large_vm_periodic_payload(db):
    resolution = _collect_connected_snapshots_resolution(db)
    rows = [r for s in resolution["usable_snapshots"] for r in s.get("large_vms", [])]
    return {
        "status": resolution["status"], "message": resolution["message"] if rows else "当前没有超过 1TB 的虚拟机",
        "total": len(rows), "threshold_tb": 1.0, "data": rows,
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def build_naming_periodic_payload(db):
    resolution = _collect_connected_snapshots_resolution(db)
    rows = [r for s in resolution["usable_snapshots"] for r in s.get("naming_issues", [])]
    return {
        "status": resolution["status"], "message": resolution["message"] if rows else "当前没有命名或备注规范问题",
        "total": len(rows), "rules": NAMING_RULES, "data": rows,
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def build_idle_vm_periodic_payload(db):
    resolution = _collect_connected_snapshots_resolution(db)
    rows = [r for s in resolution["usable_snapshots"] for r in s.get("idle_vms", [])]
    return {
        "status": resolution["status"], "message": resolution["message"] if rows else "当前没有符合规则的闲置虚拟机",
        "total": len(rows), "data": rows,
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


def build_triggered_alarms_payload(db):
    resolution = _collect_connected_snapshots_resolution(db)
    rows = [r for s in resolution["usable_snapshots"] for r in s.get("triggered_alarms", [])]
    return {
        "status": resolution["status"], "message": resolution["message"] if rows else "当前没有已触发的告警",
        "total": len(rows), "data": rows,
        "failed_platforms": _build_failed_platform_entries(resolution["failed_snapshots"]),
    }


# ──────────────────────────────────────────────
# History
# ──────────────────────────────────────────────

def build_history_payload(db, host_name: str, days: int):
    since = datetime.now() - timedelta(days=days)
    rows = (
        db.query(VmwareMetric)
        .filter(VmwareMetric.resource_name == host_name, VmwareMetric.check_time >= since)
        .order_by(VmwareMetric.check_time.desc())
        .all()
    )
    data = [
        {"timestamp": r.check_time.isoformat(), "cpu_usage": float(r.cpu_usage or 0), "memory_usage": float(r.memory_usage or 0), "storage_usage": float(r.storage_usage or 0)}
        for r in rows
    ]
    return {"status": "real_data" if data else "no_data", "message": "历史巡检记录加载成功" if data else "当前主机暂无历史记录", "host_name": host_name, "days": days, "total": len(data), "data": data}


# ──────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────

def build_report_payload(db, include_empty=False):
    thresholds = load_thresholds_from_rules(db)
    instances = get_active_instances(db)
    connected_snapshots = {s["platform"]: s for s in collect_connected_snapshots(db)}

    report_platforms = []
    data_sources = []
    warnings = []
    errors = []

    for inst in instances:
        platform_code = inst.platform.code if inst.platform else ""
        snapshot = connected_snapshots.get(platform_code)
        if snapshot:
            report_platforms.append(_build_report_platform_from_snapshot(snapshot))
            if snapshot.get("data_source"):
                data_sources.append(snapshot["data_source"])
            warnings.extend(snapshot.get("alerts", []))
            continue

        if inst.is_configured and not inst.is_connected:
            errors.append({"platform": inst.instance_name, "error": inst.last_error or "连接失败"})

        if include_empty:
            report_platforms.append({
                "platform": platform_code, "display_name": inst.instance_name,
                "is_configured": inst.is_configured, "is_connected": inst.is_connected,
                "api_url": inst.api_url or "未配置", "data_source": None,
                "status": "连接失败" if inst.is_configured else "未配置",
                "statistics": _empty_statistics(), "clusters": [], "hosts": [], "vms": [],
                "expired_snapshots": [], "large_vms": [], "naming_issues": [], "idle_vms": [],
                "periodic_items": [], "capabilities": {},
            })

    return {
        "report_type": "每日巡检报告", "report_time": datetime.now().isoformat(), "generated_by": "主机巡检系统",
        "thresholds": thresholds, "platforms": report_platforms,
        "overall_summary": {"total_platforms": len(instances), "configured_platforms": len([i for i in instances if i.is_configured]), "connected_platforms": len([i for i in instances if i.is_connected])},
        "overall_statistics": _summarize_report_platforms(report_platforms),
        "data_sources": data_sources, "warnings": warnings, "errors": errors,
        "data_declaration": "本报告所有数据均来自真实API调用，无模拟数据。",
    }


def _build_report_platform_from_snapshot(snapshot):
    return {
        "platform": snapshot["platform"], "display_name": snapshot["platform_name"],
        "is_configured": True, "is_connected": True, "api_url": snapshot.get("data_source"),
        "data_source": snapshot.get("data_source"), "status": "正常",
        "clusters": snapshot.get("clusters", []), "hosts": snapshot.get("hosts", []),
        "vms": snapshot.get("vms", []),
        "expired_snapshots": snapshot.get("expired_snapshots", []),
        "large_vms": snapshot.get("large_vms", []),
        "naming_issues": snapshot.get("naming_issues", []),
        "idle_vms": snapshot.get("idle_vms", []),
        "statistics": {
            "total": snapshot.get("statistics", {}).get("hosts", 0),
            "normal": snapshot.get("statistics", {}).get("normal", 0),
            "warning": snapshot.get("statistics", {}).get("warning", 0),
            "critical": snapshot.get("statistics", {}).get("critical", 0),
            "clusters": snapshot.get("statistics", {}).get("clusters", 0),
            "vms": snapshot.get("statistics", {}).get("vms", 0),
            "expired_snapshots": snapshot.get("statistics", {}).get("expired_snapshots", 0),
            "large_vms": snapshot.get("statistics", {}).get("large_vms", 0),
        },
        "periodic_items": [
            {"code": "snapshot", "name": "过期快照检查", "target": "删除超过 7 天的快照", "count": len(snapshot.get("expired_snapshots", []))},
            {"code": "naming", "name": "命名与备注维护", "target": "保证资产命名与备注符合规范", "count": len(snapshot.get("naming_issues", []))},
            {"code": "idle_vm", "name": "闲置资产排查", "target": "识别长期未使用或临时用途资产", "count": len(snapshot.get("idle_vms", []))},
            {"code": "large_vm", "name": "大容量虚拟机排查", "target": "定位容量超过 1TB 的虚拟机", "count": len(snapshot.get("large_vms", []))},
        ],
        "capabilities": snapshot.get("capabilities", {}),
    }


def _summarize_report_platforms(platforms):
    return {
        "total_hosts": sum(p["statistics"]["total"] for p in platforms),
        "normal_hosts": sum(p["statistics"]["normal"] for p in platforms),
        "warning_hosts": sum(p["statistics"]["warning"] for p in platforms),
        "critical_hosts": sum(p["statistics"]["critical"] for p in platforms),
        "total_alerts": sum(p["statistics"]["warning"] + p["statistics"]["critical"] + p["statistics"].get("expired_snapshots", 0) for p in platforms),
    }


def build_snapshot_report_payload(db):
    payload = build_snapshot_periodic_payload(db)
    payload.update({"report_type": "过期快照报告", "report_time": datetime.now().isoformat(), "data_declaration": "本报告数据来自真实平台API调用"})
    return payload


# ──────────────────────────────────────────────
# Persist host records to PostgreSQL
# ──────────────────────────────────────────────

def persist_host_records(db, snapshots: Iterable[Dict[str, Any]], check_time: Optional[datetime] = None) -> int:
    persisted = 0
    for snapshot in snapshots:
        platform = snapshot.get("platform", "")
        instance_id = _get_instance_id_for_snapshot(db, snapshot)
        snapshot_check_time = _parse_datetime(snapshot.get("last_sync")) or check_time or datetime.now()

        for host in snapshot.get("hosts", []):
            if platform == "vmware":
                _persist_vmware_host(db, instance_id, host, snapshot, snapshot_check_time)
            elif platform == "smartx":
                _persist_smartx_host(db, instance_id, host, snapshot, snapshot_check_time)
            persisted += 1

        # Persist VM metrics for trend charts
        for vm in snapshot.get("vms", []):
            if platform == "vmware":
                _persist_vmware_vm_metric(db, instance_id, vm, snapshot_check_time)
            elif platform == "smartx":
                _persist_smartx_vm_metric(db, instance_id, vm, snapshot_check_time)

        # Persist ESXi logs
        for log in snapshot.get("esxi_logs", []):
            event_time = _parse_datetime(log.get("event_time")) or snapshot_check_time
            db.add(EsxiHostLog(
                instance_id=instance_id,
                host_name=log.get("host_name", ""),
                category=log.get("category", "system"),
                service=log.get("service", "unknown"),
                severity=log.get("severity", "info"),
                message=log.get("message", ""),
                log_file=log.get("log_file", ""),
                event_time=event_time,
            ))

        # Update instance last_sync_at
        if instance_id:
            db.query(PlatformInstance).filter(PlatformInstance.id == instance_id).update({"last_sync_at": snapshot_check_time})

    db.commit()
    return persisted


def _get_instance_id_for_snapshot(db, snapshot):
    platform = snapshot.get("platform", "")
    display_name = snapshot.get("display_name", "")
    inst = db.query(PlatformInstance).join(PlatformType).filter(PlatformType.code == platform, PlatformInstance.instance_name == display_name).first()
    return inst.id if inst else None


def _persist_vmware_host(db, instance_id, host, snapshot, check_time):
    # Upsert host record
    existing = db.query(VmwareHost).filter(VmwareHost.instance_id == instance_id, VmwareHost.host_name == host.get("host_name")).first()
    if existing:
        existing.cpu_usage_percent = host.get("cpu_usage_percent")
        existing.memory_usage_percent = host.get("memory_usage_percent")
        existing.storage_usage_percent = host.get("storage_usage_percent")
        existing.status = host.get("status")
        existing.connection_state = host.get("connection_state")
        existing.power_state = host.get("power_state")
        existing.vm_count = host.get("vm_count")
        existing.check_time = check_time
    else:
        db.add(VmwareHost(
            instance_id=instance_id,
            host_name=host.get("host_name", ""),
            host_id=host.get("host_id"),
            ip_address=host.get("ip_address"),
            cpu_cores=host.get("cpu_cores"),
            cpu_total_mhz=host.get("cpu_total_mhz"),
            memory_total_mb=host.get("memory_total_mb"),
            cpu_usage_mhz=host.get("cpu_usage_mhz"),
            cpu_usage_percent=host.get("cpu_usage_percent"),
            memory_used_mb=host.get("memory_used_mb"),
            memory_usage_percent=host.get("memory_usage_percent"),
            storage_usage_percent=host.get("storage_usage_percent"),
            status=host.get("status"),
            overall_status=host.get("overall_status"),
            connection_state=host.get("connection_state"),
            power_state=host.get("power_state"),
            vm_count=host.get("vm_count", 0),
            uptime_days=host.get("uptime_days"),
            check_time=check_time,
        ))

    # Write metric
    db.add(VmwareMetric(
        instance_id=instance_id, resource_type="host", resource_id=0,
        resource_name=host.get("host_name"),
        cpu_usage=host.get("cpu_usage_percent"),
        memory_usage=host.get("memory_usage_percent"),
        storage_usage=host.get("storage_usage_percent"),
        check_time=check_time,
    ))

    # Update resource index
    existing_idx = db.query(ResourceIndex).filter(ResourceIndex.platform == "vmware", ResourceIndex.instance_id == instance_id, ResourceIndex.resource_type == "host", ResourceIndex.name == host.get("host_name")).first()
    if existing_idx:
        existing_idx.ip_address = host.get("ip_address")
        existing_idx.updated_at = check_time
    else:
        db.add(ResourceIndex(
            platform="vmware", instance_id=instance_id, environment="ser",
            resource_type="host", resource_id=0,
            name=host.get("host_name"), ip_address=host.get("ip_address"),
        ))


def _persist_smartx_host(db, instance_id, host, snapshot, check_time):
    existing = db.query(SmartxHost).filter(SmartxHost.instance_id == instance_id, SmartxHost.host_name == host.get("host_name")).first()
    if existing:
        existing.cpu_usage_percent = host.get("cpu_usage_percent")
        existing.memory_usage_percent = host.get("memory_usage_percent")
        existing.status = host.get("status")
        existing.check_time = check_time
    else:
        db.add(SmartxHost(
            instance_id=instance_id,
            host_name=host.get("host_name", ""),
            ip_address=host.get("ip_address"),
            cpu_cores=host.get("cpu_cores"),
            memory_total_mb=host.get("memory_total_mb"),
            cpu_usage_percent=host.get("cpu_usage_percent"),
            memory_usage_percent=host.get("memory_usage_percent"),
            storage_usage_percent=host.get("storage_usage_percent"),
            status=host.get("status"),
            check_time=check_time,
        ))

    db.add(SmartxMetric(
        instance_id=instance_id, resource_type="host", resource_id=0,
        resource_name=host.get("host_name"),
        cpu_usage=host.get("cpu_usage_percent"),
        memory_usage=host.get("memory_usage_percent"),
        check_time=check_time,
    ))


def _persist_vmware_vm_metric(db, instance_id, vm, check_time):
    """Persist VM-level metric for trend charts."""
    # VMs don't have real-time CPU/memory usage from the current collection
    # (we only get config: cpu_count, memory_gb, storage_gb)
    # But we can store the config as a metric snapshot for trend tracking
    db.add(VmwareMetric(
        instance_id=instance_id, resource_type="vm", resource_id=0,
        resource_name=vm.get("vm_name"),
        cpu_usage=float(vm.get("cpu_count", 0) or 0),
        memory_usage=float(vm.get("memory_gb", 0) or 0),
        storage_usage=float(vm.get("storage_gb", 0) or 0),
        custom_metrics={
            "power_state": vm.get("power_state"),
            "has_snapshot": vm.get("has_snapshot"),
            "snapshot_count": vm.get("snapshot_count", 0),
        },
        check_time=check_time,
    ))


def _persist_smartx_vm_metric(db, instance_id, vm, check_time):
    """Persist SmartX VM metric for trend charts."""
    db.add(SmartxMetric(
        instance_id=instance_id, resource_type="vm", resource_id=0,
        resource_name=vm.get("vm_name"),
        cpu_usage=float(vm.get("cpu_count", 0) or 0),
        memory_usage=float(vm.get("memory_gb", 0) or 0),
        storage_usage=float(vm.get("storage_gb", 0) or 0),
        custom_metrics={"power_state": vm.get("power_state")},
        check_time=check_time,
    ))
