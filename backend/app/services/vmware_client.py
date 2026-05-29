"""
VMware vCenter Real API Client
使用 pyVmomi SDK 获取真实数据
"""
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from pyVim.connect import Disconnect, SmartConnect
    from pyVmomi import vim
    PYVMOMI_AVAILABLE = True
except ImportError:
    PYVMOMI_AVAILABLE = False
    print("pyVmomi 未安装，请运行: pip install pyvmomi")


class VMwareClient:
    """VMware vCenter API客户端"""

    def __init__(self, host: str, username: str, password: str, port: int = 443, ssl_verify: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify
        self.si = None
        self.content = None
        self._connected = False
        self._last_error = None
        self._collection_errors: List[str] = []
        self._host_inventory: Optional[List[Dict[str, Any]]] = None
        self._vm_inventory: Optional[List[Dict[str, Any]]] = None

    def connect(self) -> bool:
        if not PYVMOMI_AVAILABLE:
            self._last_error = "pyVmomi未安装"
            return False

        self._collection_errors = []
        self._host_inventory = None
        self._vm_inventory = None

        try:
            ssl_context = None
            if not self.ssl_verify:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                ssl_context.verify_mode = ssl.CERT_NONE

            self.si = SmartConnect(
                host=self.host,
                port=self.port,
                user=self.username,
                pwd=self.password,
                sslContext=ssl_context,
            )
            self.content = self.si.RetrieveContent()
            self._connected = True
            self._last_error = None
            return True
        except Exception as exc:
            self._last_error = str(exc)
            self._connected = False
            return False

    def disconnect(self):
        if self.si and self._connected:
            Disconnect(self.si)
        self.si = None
        self.content = None
        self._connected = False
        self._host_inventory = None
        self._vm_inventory = None

    def is_connected(self) -> bool:
        return self._connected

    def get_last_error(self) -> Optional[str]:
        return self._last_error

    def get_collection_errors(self) -> List[str]:
        return list(self._collection_errors)

    def get_vcenter_info(self) -> Dict[str, Any]:
        if not self._connected or not self.content:
            return {}

        about = self.content.about
        return {
            "name": getattr(about, "name", ""),
            "version": getattr(about, "version", ""),
            "build": getattr(about, "build", ""),
            "api_type": getattr(about, "apiType", ""),
            "api_version": getattr(about, "apiVersion", ""),
            "vendor": getattr(about, "vendor", ""),
            "license_product_name": getattr(about, "licenseProductName", ""),
        }

    def get_all_clusters(self) -> List[Dict[str, Any]]:
        if not self._connected or not self.content:
            return []

        clusters: List[Dict[str, Any]] = []
        for cluster in self._iter_cluster_objects():
            try:
                clusters.append(self._get_cluster_info(cluster))
            except Exception as exc:
                self._record_collection_error("cluster", self._safe_attr(cluster, "name", "unknown-cluster"), exc)
        return clusters

    def get_all_hosts(self) -> List[Dict[str, Any]]:
        if not self._connected or not self.content:
            return []
        if self._host_inventory is None:
            self._host_inventory = self._collect_all_hosts()
        return [dict(host) for host in self._host_inventory]

    def get_all_vms(self) -> List[Dict[str, Any]]:
        if not self._connected or not self.content:
            return []
        if self._vm_inventory is None:
            self._vm_inventory = self._collect_all_vms()
        return [dict(vm) for vm in self._vm_inventory]

    def get_expired_snapshots(self, threshold_days: int = 7) -> List[Dict[str, Any]]:
        expired_snapshots: List[Dict[str, Any]] = []
        for vm in self.get_all_vms():
            if vm.get("has_snapshot") and int(vm.get("snapshot_days", 0) or 0) > threshold_days:
                expired_snapshots.append(
                    {
                        "vm_name": vm.get("vm_name"),
                        "cluster_name": vm.get("cluster_name"),
                        "snapshot_name": vm.get("oldest_snapshot_name") or "root-snapshot",
                        "snapshot_days": vm.get("snapshot_days"),
                        "threshold_days": threshold_days,
                        "status": "critical" if int(vm.get("snapshot_days", 0) or 0) > threshold_days + 3 else "warning",
                        "power_state": vm.get("power_state"),
                        "storage_gb": vm.get("storage_gb"),
                        "check_time": datetime.now().isoformat(),
                    }
                )
        return expired_snapshots

    def get_triggered_alarms(self) -> List[Dict[str, Any]]:
        """获取vCenter已触发的告警"""
        if not self._connected or not self.content:
            return []
        
        alarms: List[Dict[str, Any]] = []
        try:
            # 获取所有告警管理器
            alarm_manager = self.content.alarmManager
            if not alarm_manager:
                return []
            
            # 获取所有已触发的告警
            for entity in [self.content.rootFolder]:
                try:
                    alarm_state = alarm_manager.GetAlarmState(entity)
                    if not alarm_state:
                        continue
                    
                    for state in alarm_state:
                        try:
                            alarm_info = state.alarm.info
                            alarms.append({
                                "alarm_id": self._safe_attr(state.alarm, "key"),
                                "alarm_name": self._safe_attr(alarm_info, "name"),
                                "description": self._safe_attr(alarm_info, "description"),
                                "entity_name": self._safe_attr(entity, "name"),
                                "entity_type": entity.__class__.__name__,
                                "status": self._map_status(state.overallStatus),
                                "triggered_time": state.time.isoformat() if state.time else None,
                                "acknowledged": state.acknowledged,
                            })
                        except Exception as e:
                            self._record_collection_error("alarm", "state", e)
                except Exception as e:
                    self._record_collection_error("alarm", "entity", e)
        except Exception as e:
            self._record_collection_error("alarm", "manager", e)
        
        return alarms

    def get_large_vms(self, threshold_tb: float = 1.0) -> List[Dict[str, Any]]:
        large_vms: List[Dict[str, Any]] = []
        for vm in self.get_all_vms():
            if float(vm.get("storage_tb", 0) or 0) >= threshold_tb:
                large_vms.append(
                    {
                        "vm_name": vm.get("vm_name"),
                        "cluster_name": vm.get("cluster_name"),
                        "storage_tb": vm.get("storage_tb"),
                        "cpu_count": vm.get("cpu_count"),
                        "memory_gb": vm.get("memory_gb"),
                        "guest_os": vm.get("guest_os"),
                        "power_state": vm.get("power_state"),
                        "check_time": datetime.now().isoformat(),
                    }
                )
        return large_vms

    def _get_cluster_info(self, cluster: vim.ClusterComputeResource) -> Dict[str, Any]:
        cluster_name = self._safe_attr(cluster, "name", "未命名集群")
        overall_status = self._safe_attr(self._safe_attr(cluster, "summary"), "overallStatus")
        status = self._map_status(overall_status)

        hosts: List[Dict[str, Any]] = []
        cpu_total = 0.0
        cpu_capacity_mhz = 0.0
        mem_total = 0.0
        mem_used = 0.0

        for host in list(self._safe_attr(cluster, "host", []) or []):
            try:
                host_info = self._get_host_info(host, cluster_name=cluster_name)
                hosts.append(host_info)
                cpu_total += float(host_info.get("cpu_usage_mhz", 0) or 0)
                cpu_capacity_mhz += float(host_info.get("cpu_total_mhz", 0) or 0)
                mem_total += float(host_info.get("memory_total_mb", 0) or 0)
                mem_used += float(host_info.get("memory_used_mb", 0) or 0)
            except Exception as exc:
                self._record_collection_error("host", self._safe_attr(host, "name", "unknown-host"), exc)

        cpu_usage = (cpu_total / cpu_capacity_mhz * 100) if cpu_capacity_mhz > 0 else 0
        memory_usage = (mem_used / mem_total * 100) if mem_total > 0 else 0

        return {
            "cluster_name": cluster_name,
            "status": status,
            "overall_status": overall_status,
            "host_count": len(hosts),
            "cpu_cores": sum(int(host.get("cpu_cores", 0) or 0) for host in hosts),
            "cpu_usage_mhz": round(cpu_total, 2),
            "cpu_usage_percent": round(cpu_usage, 2),
            "memory_total_mb": round(mem_total, 2),
            "memory_used_mb": round(mem_used, 2),
            "memory_usage_percent": round(memory_usage, 2),
            "hosts": hosts,
        }

    def _collect_all_hosts(self) -> List[Dict[str, Any]]:
        hosts: List[Dict[str, Any]] = []
        host_view = None
        try:
            host_view = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.HostSystem], True)
            for host in list(host_view.view or []):
                try:
                    hosts.append(self._get_host_info(host))
                except Exception as exc:
                    self._record_collection_error("host", self._safe_attr(host, "name", "unknown-host"), exc)
        finally:
            if host_view:
                host_view.Destroy()
        return hosts

    def _get_host_info(self, host: vim.HostSystem, cluster_name: Optional[str] = None) -> Dict[str, Any]:
        summary = self._safe_attr(host, "summary")
        hardware = self._safe_attr(host, "hardware")
        quick_stats = self._safe_attr(summary, "quickStats")
        runtime = self._safe_attr(summary, "runtime")

        overall_status = self._safe_attr(summary, "overallStatus")
        status = self._map_status(overall_status)

        # CPU cores - try multiple sources
        cpu_packages = list(self._safe_attr(hardware, "cpuPkg", []) or [])
        cpu_cores = sum(int(self._safe_attr(pkg, "numCpuCores", self._safe_attr(pkg, "coreCount", 0)) or 0) for pkg in cpu_packages)
        if cpu_cores == 0:
            # Fallback: try summary.hardware.numCpuCores or hardware.numCpuCores
            summary_hw = self._safe_attr(summary, "hardware")
            cpu_cores = int(self._safe_attr(summary_hw, "numCpuCores", 0) or 0)
        if cpu_cores == 0:
            cpu_cores = int(self._safe_attr(hardware, "numCpuCores", 0) or 0)

        # CPU total MHz - explicit None check instead of 'and' operator
        cpu_info = self._safe_attr(hardware, "cpuInfo")
        cpu_hz = int(self._safe_attr(cpu_info, "hz", 0) or 0) if cpu_info else 0
        if cpu_hz and cpu_cores:
            cpu_total_mhz = round((cpu_hz / 1000000) * cpu_cores, 2)
        else:
            # Fallback: try summary.hardware.cpuMhz * numCpuPkgs
            summary_hw = self._safe_attr(summary, "hardware")
            cpu_mhz_per_pkg = int(self._safe_attr(summary_hw, "cpuMhz", 0) or 0)
            num_pkgs = int(self._safe_attr(summary_hw, "numCpuPkgs", 0) or 0)
            if cpu_mhz_per_pkg and num_pkgs:
                cpu_total_mhz = round(cpu_mhz_per_pkg * num_pkgs, 2)
            else:
                cpu_total_mhz = 0

        cpu_usage_mhz = float(self._safe_attr(quick_stats, "overallCpuUsage", 0) or 0)
        cpu_usage_percent = (cpu_usage_mhz / cpu_total_mhz * 100) if cpu_total_mhz > 0 else 0

        memory_total_mb = float(self._safe_attr(hardware, "memorySize", 0) or 0) / (1024 * 1024)
        memory_used_mb = float(self._safe_attr(quick_stats, "overallMemoryUsage", 0) or 0)
        memory_usage_percent = (memory_used_mb / memory_total_mb * 100) if memory_total_mb > 0 else 0

        # 计算存储使用率：从主机挂载的数据存储汇总
        storage_capacity_bytes = 0
        storage_used_bytes = 0
        datastore_info = self._safe_attr(host, "datastore", [])
        if datastore_info:
            for ds in list(datastore_info or []):
                try:
                    ds_summary = self._safe_attr(ds, "summary")
                    ds_capacity = float(self._safe_attr(ds_summary, "capacity", 0) or 0)
                    ds_free = float(self._safe_attr(ds_summary, "freeSpace", 0) or 0)
                    storage_capacity_bytes += ds_capacity
                    storage_used_bytes += (ds_capacity - ds_free)
                except Exception:
                    pass
        storage_usage_percent = (storage_used_bytes / storage_capacity_bytes * 100) if storage_capacity_bytes > 0 else 0

        uptime_seconds = float(self._safe_attr(quick_stats, "uptime", 0) or 0)
        uptime_days = uptime_seconds / 86400 if uptime_seconds else 0

        ip_address = self._extract_host_ip(host)
        vm_count = len(list(self._safe_attr(host, "vm", []) or []))

        return {
            "cluster_name": cluster_name or self._resolve_cluster_name_from_host(host),
            "host_name": self._safe_attr(host, "name", "未命名主机"),
            "host_id": self._safe_attr(host, "_moId"),
            "ip_address": ip_address,
            "status": status,
            "overall_status": overall_status,
            "cpu_cores": cpu_cores,
            "cpu_total_mhz": round(cpu_total_mhz, 2),
            "cpu_usage_mhz": round(cpu_usage_mhz, 2),
            "cpu_usage_percent": round(cpu_usage_percent, 2),
            "memory_total_mb": round(memory_total_mb, 2),
            "memory_used_mb": round(memory_used_mb, 2),
            "memory_usage_percent": round(memory_usage_percent, 2),
            "storage_usage_percent": round(storage_usage_percent, 2),
            "uptime_days": round(uptime_days, 2),
            "connection_state": self._safe_attr(runtime, "connectionState"),
            "power_state": self._safe_attr(runtime, "powerState"),
            "vm_count": vm_count,
        }

    def _collect_all_vms(self) -> List[Dict[str, Any]]:
        vms: List[Dict[str, Any]] = []
        vm_view = None
        try:
            vm_view = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.VirtualMachine], True)
            for vm in list(vm_view.view or []):
                try:
                    vms.append(self._get_vm_info(vm))
                except Exception as exc:
                    self._record_collection_error("vm", self._safe_attr(vm, "name", "unknown-vm"), exc)
        finally:
            if vm_view:
                vm_view.Destroy()
        return vms

    def _get_vm_info(self, vm: vim.VirtualMachine) -> Dict[str, Any]:
        summary = self._safe_attr(vm, "summary")
        runtime = self._safe_attr(summary, "runtime")
        config = self._safe_attr(vm, "config")
        hardware = self._safe_attr(config, "hardware")
        guest = self._safe_attr(vm, "guest")

        power_state = self._safe_attr(runtime, "powerState")
        cpu_count = int(self._safe_attr(hardware, "numCPU", 0) or 0)
        memory_mb = float(self._safe_attr(hardware, "memoryMB", 0) or 0)

        storage_used_mb = 0.0
        for device in list(self._safe_attr(hardware, "device", []) or []):
            if isinstance(device, vim.VirtualDisk):
                storage_used_mb += float(self._safe_attr(device, "capacityInKB", 0) or 0) / 1024

        storage_gb = storage_used_mb / 1024
        storage_tb = storage_gb / 1024

        snapshot_root = list(self._safe_attr(self._safe_attr(vm, "snapshot"), "rootSnapshotList", []) or [])
        flattened_snapshots = self._flatten_snapshots(snapshot_root)
        has_snapshot = len(flattened_snapshots) > 0
        snapshot_count = len(flattened_snapshots)
        oldest_snapshot = min(flattened_snapshots, key=lambda item: item[1]) if flattened_snapshots else None
        oldest_snapshot_name = oldest_snapshot[0] if oldest_snapshot else None
        oldest_snapshot_date = oldest_snapshot[1] if oldest_snapshot else None
        snapshot_days = self._days_since(oldest_snapshot_date)

        host_ref = self._safe_attr(runtime, "host")
        host_name = self._safe_attr(host_ref, "name", "") if host_ref else ""
        cluster_name = self._resolve_cluster_name_from_host(host_ref) if host_ref else ""

        created_at = self._safe_attr(config, "createDate")
        created_days = self._days_since(created_at)

        return {
            "vm_name": self._safe_attr(vm, "name", "未命名虚拟机"),
            "vm_uuid": self._safe_attr(config, "uuid"),
            "cluster_name": cluster_name,
            "host_name": host_name,
            "ip_address": self._safe_attr(guest, "ipAddress", "") or "",
            "power_state": power_state,
            "cpu_count": cpu_count,
            "memory_mb": round(memory_mb, 2),
            "memory_gb": round(memory_mb / 1024, 2),
            "storage_mb": round(storage_used_mb, 2),
            "storage_gb": round(storage_gb, 2),
            "storage_tb": round(storage_tb, 2),
            "guest_os": self._safe_attr(guest, "guestFullName", "") or "",
            "has_snapshot": has_snapshot,
            "snapshot_count": snapshot_count,
            "snapshot_days": snapshot_days,
            "oldest_snapshot_name": oldest_snapshot_name,
            "oldest_snapshot_date": oldest_snapshot_date.isoformat() if oldest_snapshot_date else None,
            "is_large_vm": storage_tb >= 1.0,
            "note": self._safe_attr(config, "annotation", "") or "",
            "created_days": created_days,
            "is_template": bool(self._safe_attr(config, "template", False)),
        }

    def _iter_cluster_objects(self) -> List[Any]:
        clusters: List[Any] = []
        for entity in list(self._safe_attr(self.content.rootFolder, "childEntity", []) or []):
            self._walk_entities_for_clusters(entity, clusters)
        return clusters

    def _walk_entities_for_clusters(self, entity: Any, clusters: List[Any]):
        if isinstance(entity, vim.ClusterComputeResource):
            clusters.append(entity)
            return

        if isinstance(entity, vim.ComputeResource):
            return

        if isinstance(entity, vim.Datacenter):
            self._walk_entities_for_clusters(self._safe_attr(entity, "hostFolder"), clusters)
            return

        for child in list(self._safe_attr(entity, "childEntity", []) or []):
            self._walk_entities_for_clusters(child, clusters)

    def _extract_host_ip(self, host: Any) -> str:
        config = self._safe_attr(host, "config")
        network = self._safe_attr(config, "network")
        for nic in list(self._safe_attr(network, "vnic", []) or []):
            ip_spec = self._safe_attr(self._safe_attr(nic, "spec"), "ip")
            ip_address = self._safe_attr(ip_spec, "ipAddress")
            if ip_address:
                return ip_address
        management_ip = self._safe_attr(self._safe_attr(host, "summary"), "managementServerIp")
        return management_ip or ""

    def _resolve_cluster_name_from_host(self, host: Any) -> str:
        parent = self._safe_attr(host, "parent")
        while parent:
            if isinstance(parent, vim.ClusterComputeResource):
                return self._safe_attr(parent, "name", "") or ""
            parent = self._safe_attr(parent, "parent")
        return ""

    def _flatten_snapshots(self, snapshots: List[Any]) -> List[Any]:
        flattened: List[Any] = []
        for snapshot in snapshots:
            create_time = self._safe_attr(snapshot, "createTime")
            if create_time:
                flattened.append((self._safe_attr(snapshot, "name", "snapshot"), create_time))
            flattened.extend(self._flatten_snapshots(list(self._safe_attr(snapshot, "childSnapshotList", []) or [])))
        return flattened

    def _days_since(self, value: Any) -> int:
        if not value:
            return 0
        current_time = datetime.now(value.tzinfo) if getattr(value, "tzinfo", None) else datetime.now()
        try:
            return max((current_time - value).days, 0)
        except TypeError:
            normalized = self._normalize_datetime(value)
            if not normalized:
                return 0
            return max((datetime.now(timezone.utc) - normalized).days, 0)

    def _normalize_datetime(self, value: Any) -> Optional[datetime]:
        if not isinstance(value, datetime):
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _record_collection_error(self, scope: str, name: str, exc: Exception):
        message = f"{scope}:{name}: {exc}"
        if message not in self._collection_errors:
            self._collection_errors.append(message)
        self._last_error = message

    def _safe_attr(self, obj: Any, attr: str = None, default: Any = None) -> Any:
        if obj is None:
            return default
        if attr is None:
            return obj
        return getattr(obj, attr, default)

    def _map_status(self, status: Any) -> str:
        status_map = {
            "green": "normal",
            "yellow": "warning",
            "red": "critical",
        }
        value = str(status or "").lower()
        return status_map.get(value, "unknown")

    # ==================== 事件和日志采集 ====================

    def get_events(self, max_count: int = 100) -> List[Dict[str, Any]]:
        """获取vCenter事件列表"""
        if not self._connected or not self.content:
            return []

        events = []
        try:
            event_manager = self.content.eventManager
            if not event_manager:
                return []

            # 兼容新版 pyVmomi：用 CreateCollectorForEvents
            event_filter = vim.event.EventFilterSpec()
            collector = event_manager.CreateCollectorForEvents(event_filter)
            event_list = collector.latestPage

            for event in (event_list or [])[:max_count]:
                try:
                    events.append({
                        "event_id": self._safe_attr(event, "key"),
                        "event_type": event.__class__.__name__,
                        "message": self._safe_attr(event, "fullFormattedMessage", "") or self._safe_attr(event, "message", ""),
                        "created_time": self._safe_attr(event, "createdTime"),
                        "user_name": self._safe_attr(event, "userName", ""),
                        "datacenter_name": self._safe_attr(self._safe_attr(event, "datacenter", "name"), "name", ""),
                        "compute_resource_name": self._safe_attr(self._safe_attr(event, "computeResource", "name"), "name", ""),
                        "host_name": self._safe_attr(self._safe_attr(event, "host", "name"), "name", ""),
                        "vm_name": self._safe_attr(self._safe_attr(event, "vm", "name"), "name", ""),
                        "severity": self._map_event_severity(event),
                    })
                except Exception:
                    pass
        except Exception as e:
            self._record_collection_error("events", "manager", e)

        return events

    def get_host_system_events(self, host_name: str = None, max_count: int = 50) -> List[Dict[str, Any]]:
        """获取主机系统事件"""
        if not self._connected or not self.content:
            return []

        events = []
        try:
            event_manager = self.content.eventManager

            event_filter = vim.event.EventFilterSpec()
            event_filter.disableFullMessage = False

            if host_name:
                host_filter = vim.event.EventFilterSpecByEntity()
                # 查找主机
                host_view = self.content.viewManager.CreateContainerView(
                    self.content.rootFolder, [vim.HostSystem], True
                )
                for host in host_view.view:
                    if self._safe_attr(host, "name") == host_name:
                        host_filter.entity = host
                        host_filter.recursion = vim.event.EventFilterSpecRecursionOption.ALL
                        break
                host_view.Destroy()
                event_filter.entity = host_filter

            event_list = event_manager.QueryEvents(event_filter)
            for event in (event_list or [])[:max_count]:
                events.append({
                    "event_id": self._safe_attr(event, "key"),
                    "event_type": event.__class__.__name__,
                    "message": self._safe_attr(event, "fullFormattedMessage", "") or self._safe_attr(event, "message", ""),
                    "created_time": self._safe_attr(event, "createdTime"),
                    "user_name": self._safe_attr(event, "userName", ""),
                    "severity": self._map_event_severity(event),
                })
        except Exception as e:
            self._record_collection_error("host_events", host_name or "all", e)

        return events

    def get_task_history(self, max_count: int = 50) -> List[Dict[str, Any]]:
        """获取任务历史"""
        if not self._connected or not self.content:
            return []

        tasks = []
        try:
            task_manager = self.content.taskManager
            if not task_manager:
                return []

            # 获取最近的任务
            try:
                filter_spec = vim.TaskFilterSpec()
                task_list = task_manager.QueryTasks(filter_spec)
            except Exception:
                # Fallback: try collector approach
                try:
                    collector = task_manager.CreateCollectorForTasks()
                    task_list = collector.latestPage
                except Exception:
                    return []

            for task in (task_list or [])[:max_count]:
                    try:
                        tasks.append({
                            "task_id": self._safe_attr(task, "key"),
                            "task_name": self._safe_attr(task, "name"),
                            "description": self._safe_attr(task, "description"),
                            "state": self._safe_attr(task, "state"),
                            "entity_name": self._safe_attr(self._safe_attr(task, "entity", "name"), "name", ""),
                            "user_name": self._safe_attr(task, "userName", ""),
                            "start_time": self._safe_attr(task, "startTime"),
                            "complete_time": self._safe_attr(task, "completeTime"),
                            "result": str(self._safe_attr(task, "result", "")),
                            "error": str(self._safe_attr(task, "error", "")) if self._safe_attr(task, "error") else "",
                        })
                    except Exception:
                        pass
        except Exception as e:
            self._record_collection_error("tasks", "history", e)

        return tasks

    def get_host_performance_metrics(self, host_name: str = None) -> Dict[str, Any]:
        """获取主机性能指标（实时）"""
        if not self._connected or not self.content:
            return {}

        metrics = {}
        try:
            # 获取性能管理器
            perf_manager = self.content.perfManager
            if not perf_manager:
                return {}

            # 如果没有指定主机，获取所有主机
            hosts = self.get_all_hosts()
            if host_name:
                hosts = [h for h in hosts if h.get("host_name") == host_name]

            for host in hosts:
                host_moid = host.get("host_id")
                if not host_moid:
                    continue

                # 查找主机对象
                host_view = self.content.viewManager.CreateContainerView(
                    self.content.rootFolder, [vim.HostSystem], True
                )
                host_obj = None
                for h in host_view.view:
                    if h._moId == host_moid:
                        host_obj = h
                        break
                host_view.Destroy()

                if not host_obj:
                    continue

                # 获取性能计数器
                host_metrics = {}
                counter_ids = [
                    "cpu.usage.average",      # CPU使用率
                    "mem.usage.average",      # 内存使用率
                    "disk.usage.average",     # 磁盘使用率
                    "net.usage.average",      # 网络使用率
                ]

                for counter_id in counter_ids:
                    try:
                        # 查询实时性能数据
                        metric_id = vim.PerfMetricId(counterId=counter_id, instance="")
                        query = vim.PerfQuerySpec(
                            entity=host_obj,
                            metricId=[metric_id],
                            intervalId=20,  # 20秒间隔
                            startTime=None,
                            endTime=None,
                            maxSample=1
                        )

                        stats = perf_manager.QueryPerf(query)
                        if stats and stats[0].sampleInfo:
                            value = stats[0].value[0] if stats[0].value else 0
                            host_metrics[counter_id] = value
                    except Exception:
                        pass

                metrics[host.get("host_name")] = host_metrics

        except Exception as e:
            self._record_collection_error("perf", "metrics", e)

        return metrics

    def _map_event_severity(self, event: Any) -> str:
        """映射事件严重性"""
        event_type = event.__class__.__name__

        # 严重事件
        critical_types = [
            "VmBeingClonedEvent",
            "VmBeingDeployedEvent",
            "HostConnectionLostEvent",
            "HostDisconnectedEvent",
            "DatastoreRemovedOnHostEvent",
        ]

        # 警告事件
        warning_types = [
            "VmGuestRebootEvent",
            "VmPoweredOnEvent",
            "VmPoweredOffEvent",
            "VmSuspendedEvent",
            "VmResourcePoolMovedEvent",
            "VmMigratedEvent",
            "VmRelocatedEvent",
            "HostShuttingDownEvent",
        ]

        if event_type in critical_types:
            return "critical"
        elif event_type in warning_types:
            return "warning"
        else:
            return "info"

    # ==================== ESXi 主机日志采集 ====================

    # ESXi syslog services to collect
    _ESXI_LOG_SERVICES = {
        "hostd": {"category": "system", "description": "ESXi 主机管理服务"},
        "vpxa": {"category": "system", "description": "vCenter 代理服务"},
        "vmkernel": {"category": "virtualization", "description": "虚拟化内核日志"},
        "vmkwarning": {"category": "virtualization", "description": "内核警告日志"},
        "vmksummary": {"category": "virtualization", "description": "内核摘要日志"},
        "sshd": {"category": "ssh", "description": "SSH 服务日志"},
        "shell": {"category": "ssh", "description": "Shell 操作日志"},
        "storageRM": {"category": "storage", "description": "存储资源管理"},
        "fdm": {"category": "system", "description": "HA 故障检测"},
        "rhttpproxy": {"category": "network", "description": "HTTP 代理服务"},
    }

    # Event type → (category, service) mapping
    _EVENT_CLASSIFICATION = {
        # System
        "HostConnectionLostEvent": ("system", "hostd"),
        "HostDisconnectedEvent": ("system", "hostd"),
        "HostReconnectedEvent": ("system", "hostd"),
        "HostShutdownEvent": ("system", "hostd"),
        "HostAddedEvent": ("system", "vpxa"),
        "HostRemovedEvent": ("system", "vpxa"),
        "DasHostFailedEvent": ("system", "vpxa"),
        # Virtualization
        "VmPoweredOnEvent": ("virtualization", "vmx"),
        "VmPoweredOffEvent": ("virtualization", "vmx"),
        "VmSuspendedEvent": ("virtualization", "vmx"),
        "VmMigratedEvent": ("virtualization", "vmkernel"),
        "VmRelocatedEvent": ("virtualization", "vmkernel"),
        "VmClonedEvent": ("virtualization", "vmx"),
        "VmBeingClonedEvent": ("virtualization", "vmx"),
        "VmBeingDeployedEvent": ("virtualization", "vmx"),
        "VmGuestRebootEvent": ("virtualization", "vmx"),
        "VmGuestShutdownEvent": ("virtualization", "vmx"),
        "VmSnapshotCreatedEvent": ("virtualization", "vmx"),
        "VmSnapshotRemovedEvent": ("virtualization", "vmx"),
        "VmSnapshotRevertedEvent": ("virtualization", "vmx"),
        "VmResourcePoolMovedEvent": ("virtualization", "vmkernel"),
        # Storage
        "DatastoreRemovedOnHostEvent": ("storage", "storageRM"),
        "DatastoreDestroyedEvent": ("storage", "storageRM"),
        "DatastoreCapacityIncreasedEvent": ("storage", "storageRM"),
        "VmDiskFailedEvent": ("storage", "nfc"),
        # Network
        "VmNicConnectedEvent": ("network", "netd"),
        "VmNicDisconnectedEvent": ("network", "netd"),
        "HostIpChangedEvent": ("network", "netd"),
        # SSH
        "UserLoginSessionEvent": ("ssh", "shell"),
        "UserLogoutSessionEvent": ("ssh", "shell"),
        "BadUsernameSessionEvent": ("ssh", "shell"),
    }

    def get_esxi_host_logs(self, max_count: int = 200) -> List[Dict[str, Any]]:
        """Collect ESXi host logs from vCenter events, categorized by service."""
        if not self._connected or not self.content:
            return []

        logs = []
        try:
            event_manager = self.content.eventManager
            if not event_manager:
                return []

            # 兼容新版 pyVmomi：用 CreateCollectorForEvents 获取事件
            event_filter = vim.event.EventFilterSpec()
            collector = event_manager.CreateCollectorForEvents(event_filter)
            event_list = collector.latestPage

            for event in (event_list or [])[:max_count]:
                try:
                    event_type = event.__class__.__name__
                    category, service = self._EVENT_CLASSIFICATION.get(event_type, ("system", "unknown"))
                    severity = self._map_event_severity(event)
                    host_name = self._safe_attr(self._safe_attr(event, "host", "name"), "name", "") or ""
                    vm_name = self._safe_attr(self._safe_attr(event, "vm", "name"), "name", "") or ""

                    logs.append({
                        "host_name": host_name,
                        "vm_name": vm_name,
                        "category": category,
                        "service": service,
                        "severity": severity,
                        "event_type": event_type,
                        "event_id": self._safe_attr(event, "key", ""),
                        "message": self._safe_attr(event, "fullFormattedMessage", "") or self._safe_attr(event, "message", "") or "",
                        "user_name": self._safe_attr(event, "userName", "") or "",
                        "event_time": self._safe_attr(event, "createdTime"),
                        "datacenter": self._safe_attr(self._safe_attr(event, "datacenter", "name"), "name", "") or "",
                        "cluster": self._safe_attr(self._safe_attr(event, "computeResource", "name"), "name", "") or "",
                    })
                except Exception:
                    pass

        except Exception as e:
            self._record_collection_error("esxi_logs", "all", e)

        return logs

    def get_esxi_host_logs(self, max_count: int = 200) -> List[Dict[str, Any]]:
        """Collect ESXi host logs from vCenter events, categorized by service."""
        if not self._connected or not self.content:
            return []

        logs = []
        try:
            event_manager = self.content.eventManager
            if not event_manager:
                return []

            # 兼容新版 pyVmomi：用 CreateCollectorForEvents 获取事件
            # 不调用 SetPageSize（会导致 ContentLibrary 错误）
            event_filter = vim.event.EventFilterSpec()
            collector = event_manager.CreateCollectorForEvents(event_filter)
            event_list = collector.latestPage

            for event in (event_list or [])[:max_count]:
                    event_type = event.__class__.__name__
                    category, service = self._EVENT_CLASSIFICATION.get(event_type, ("system", "unknown"))
                    severity = self._map_event_severity(event)
                    host_name = self._safe_attr(self._safe_attr(event, "host", "name"), "name", "") or ""
                    vm_name = self._safe_attr(self._safe_attr(event, "vm", "name"), "name", "") or ""

                    logs.append({
                        "host_name": host_name,
                        "vm_name": vm_name,
                        "category": category,
                        "service": service,
                        "severity": severity,
                        "event_type": event_type,
                        "event_id": self._safe_attr(event, "key", ""),
                        "message": self._safe_attr(event, "fullFormattedMessage", "") or self._safe_attr(event, "message", "") or "",
                        "user_name": self._safe_attr(event, "userName", "") or "",
                        "event_time": self._safe_attr(event, "createdTime"),
                        "datacenter": self._safe_attr(self._safe_attr(event, "datacenter", "name"), "name", "") or "",
                        "cluster": self._safe_attr(self._safe_attr(event, "computeResource", "name"), "name", "") or "",
                    })

        except Exception as e:
            self._record_collection_error("esxi_logs", "all", e)

        return logs

    # ==================== 快照详细信息 ====================

    def get_all_snapshots(self) -> List[Dict[str, Any]]:
        """获取所有虚拟机的快照信息"""
        snapshots = []

        for vm in self.get_all_vms():
            if not vm.get("has_snapshot"):
                continue

            try:
                vm_obj = None
                vm_view = self.content.viewManager.CreateContainerView(
                    self.content.rootFolder, [vim.VirtualMachine], True
                )
                for v in vm_view.view:
                    if v.name == vm.get("vm_name"):
                        vm_obj = v
                        break
                vm_view.Destroy()

                if not vm_obj or not vm_obj.snapshot:
                    continue

                # 递归获取所有快照
                root_snapshots = vm_obj.snapshot.rootSnapshotList
                self._collect_snapshots_recursive(root_snapshots, vm.get("vm_name"), snapshots)

            except Exception as e:
                self._record_collection_error("snapshot", vm.get("vm_name"), e)

        return snapshots

    def _collect_snapshots_recursive(self, snapshot_list, vm_name: str, snapshots: List):
        """递归收集快照信息"""
        for snapshot in snapshot_list:
            snapshots.append({
                "vm_name": vm_name,
                "snapshot_name": self._safe_attr(snapshot, "name"),
                "snapshot_id": self._safe_attr(snapshot, "id"),
                "description": self._safe_attr(snapshot, "description"),
                "create_time": self._safe_attr(snapshot, "createTime"),
                "snapshot_size_mb": 0,  # 需要额外查询
                "is_child": False,
            })

            # 递归处理子快照
            child_snapshots = self._safe_attr(snapshot, "childSnapshotList", [])
            if child_snapshots:
                self._collect_snapshots_recursive(child_snapshots, vm_name, snapshots)


def example_usage():
    if not PYVMOMI_AVAILABLE:
        print("请先安装pyVmomi: pip install pyvmomi")
        return

    client = VMwareClient(
        host="vcenter.example.com",
        port=443,
        username="administrator@vsphere.local",
        password="your-password",
        ssl_verify=False,
    )

    if client.connect():
        print("连接成功!")
        print("vCenter信息:", client.get_vcenter_info())
        print(f"发现 {len(client.get_all_clusters())} 个集群")
        print(f"发现 {len(client.get_all_hosts())} 台主机")
        print(f"发现 {len(client.get_all_vms())} 台虚拟机")
        print(f"发现 {len(client.get_expired_snapshots(7))} 个过期快照")
        if client.get_collection_errors():
            print("采集过程中存在异常:", client.get_collection_errors())
        client.disconnect()
    else:
        print(f"连接失败: {client.get_last_error()}")


if __name__ == "__main__":
    example_usage()
