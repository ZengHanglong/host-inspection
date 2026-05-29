"""
ESXi Host Log Collector - SSH-based direct log collection

Collects logs from ESXi hosts via SSH, with:
- Per-host credential override support
- Concurrent collection with timeout
- Incremental collection via watermarks
- Robust multi-format log parsing
- Per-host error tracking
"""
from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────
# Log file definitions with service mapping
# ──────────────────────────────────────────────

ESXI_LOG_FILES = {
    "/var/log/hostd.log": {"category": "system", "service": "hostd"},
    "/var/log/vpxa.log": {"category": "system", "service": "vpxa"},
    "/var/log/fdm.log": {"category": "system", "service": "fdm"},
    "/var/log/esxcli.log": {"category": "system", "service": "esxcli"},
    "/var/log/vmkernel.log": {"category": "virtualization", "service": "vmkernel"},
    "/var/log/vmkwarning.log": {"category": "virtualization", "service": "vmkwarning"},
    "/var/log/vmksummary.log": {"category": "virtualization", "service": "vmksummary"},
    "/var/log/auth.log": {"category": "ssh", "service": "sshd"},
    "/var/log/shell.log": {"category": "ssh", "service": "shell"},
    "/var/log/rhttpproxy.log": {"category": "network", "service": "rhttpproxy"},
    "/var/log/storageRM.log": {"category": "storage", "service": "storageRM"},
}

# ──────────────────────────────────────────────
# Log parsing patterns (multiple formats)
# ──────────────────────────────────────────────

# Format 1: ISO timestamp - "2024-01-15T10:30:45Z hostname service[pid]: message"
_SYSLOG_ISO = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)\s+"
    r"(\S+)\s+"
    r"(\S+?)(?:\[\d+\])?:\s+"
    r"(.+)$"
)

# Format 2: vmkernel style - "2024-01-15T10:30:45.123Z cpu0:12345) message"
_VMKERNEL = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z?)\s+"
    r"cpu\d+:(\d+)\)\s+"
    r"(.+)$"
)

# Format 3: Simple timestamp - "Jan 15 10:30:45 hostname service: message"
_SIMPLE_TS = re.compile(
    r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(\S+)\s+"
    r"(\S+?):\s+"
    r"(.+)$"
)

# Severity detection
_SEVERITY_PATTERNS = {
    "critical": [r"\bcritical\b", r"\bfatal\b", r"\bpanic\b", r"\bCRITICAL\b", r"\bFATAL\b"],
    "error": [r"\berror\b", r"\bfailed\b", r"\bERROR\b", r"\bFAIL\b", r"\bErr\b"],
    "warning": [r"\bwarn(?:ing)?\b", r"\bWARN(?:ING)?\b"],
}


def _detect_severity(message: str) -> str:
    for severity, patterns in _SEVERITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return severity
    return "info"


def _parse_log_line(line: str, default_host: str = "", log_file: str = "") -> Optional[Dict[str, Any]]:
    """Parse a single log line using multiple format patterns."""
    line = line.strip()
    if not line or len(line) < 10:
        return None
    # Skip ESXi log rotation markers
    if line.startswith("---") or line.startswith("=== "):
        return None

    # Try ISO syslog format
    m = _SYSLOG_ISO.match(line)
    if m:
        ts_str, hostname, service, message = m.groups()
        event_time = _parse_timestamp(ts_str)
        return {
            "host_name": hostname or default_host,
            "service": service,
            "message": message.strip(),
            "event_time": event_time,
            "severity": _detect_severity(message),
            "log_file": log_file,
        }

    # Try vmkernel format
    m = _VMKERNEL.match(line)
    if m:
        ts_str, pid, message = m.groups()
        event_time = _parse_timestamp(ts_str)
        return {
            "host_name": default_host,
            "service": "vmkernel",
            "message": message.strip(),
            "event_time": event_time,
            "severity": _detect_severity(message),
            "log_file": log_file,
        }

    # Try simple timestamp format
    m = _SIMPLE_TS.match(line)
    if m:
        ts_str, hostname, service, message = m.groups()
        return {
            "host_name": hostname or default_host,
            "service": service,
            "message": message.strip(),
            "event_time": None,  # simple format needs year inference
            "severity": _detect_severity(message),
            "log_file": log_file,
        }

    # Fallback: entire line as message
    return {
        "host_name": default_host,
        "service": "unknown",
        "message": line,
        "event_time": None,
        "severity": _detect_severity(line),
        "log_file": log_file,
    }


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse various timestamp formats."""
    ts_str = ts_str.rstrip("Z")
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        pass
    # Try simple format without year (ESXi sometimes omits year)
    try:
        return datetime.strptime(ts_str, "%b %d %H:%M:%S").replace(year=datetime.now().year)
    except ValueError:
        return None


# ──────────────────────────────────────────────
# Single host collector
# ──────────────────────────────────────────────

def _collect_from_single_host(
    host_ip: str,
    username: str,
    password: str,
    port: int = 22,
    hours: int = 24,
    max_lines_per_file: int = 200,
    since: Optional[datetime] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Collect logs from a single ESXi host.
    Returns (logs, error_message). error_message is None on success.
    """
    try:
        import paramiko
    except ImportError:
        return [], "paramiko not installed"

    logs = []
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host_ip, port=port, username=username, password=password, timeout=15)
    except Exception as e:
        return [], f"SSH连接失败: {type(e).__name__}: {str(e)[:100]}"

    try:
        cutoff = since or (datetime.now() - timedelta(hours=hours))

        for log_path, meta in ESXI_LOG_FILES.items():
            try:
                cmd = f"tail -n {max_lines_per_file} {log_path} 2>/dev/null"
                stdin, stdout, stderr = client.exec_command(cmd, timeout=15)
                output = stdout.read().decode("utf-8", errors="replace")

                for line in output.split("\n"):
                    parsed = _parse_log_line(line, default_host=host_ip, log_file=log_path)
                    if not parsed:
                        continue

                    # Filter by time
                    if parsed["event_time"] and parsed["event_time"] < cutoff:
                        continue

                    # Apply service mapping from file
                    parsed["category"] = meta["category"]
                    if parsed["service"] == "unknown":
                        parsed["service"] = meta["service"]

                    # vmkwarning files imply at least warning severity
                    if "warning" in log_path and parsed["severity"] == "info":
                        parsed["severity"] = "warning"

                    logs.append(parsed)
            except Exception:
                continue  # Skip files that don't exist

    except Exception as e:
        return logs, f"日志读取异常: {str(e)[:100]}"
    finally:
        client.close()

    logs.sort(key=lambda x: x.get("event_time") or datetime.min, reverse=True)
    return logs, None


# ──────────────────────────────────────────────
# Concurrent multi-host collector
# ──────────────────────────────────────────────

def collect_all_esxi_logs(
    hosts: List[Dict[str, Any]],
    default_username: str = "root",
    default_password: str = "",
    default_port: int = 22,
    hours: int = 24,
    max_lines_per_file: int = 100,
    per_host_credentials: Optional[Dict[str, Dict[str, Any]]] = None,
    max_workers: int = 5,
) -> Dict[str, Any]:
    """
    Collect logs from multiple ESXi hosts concurrently.

    Args:
        hosts: List of host dicts with at least 'ip_address'
        default_username: Default SSH username
        default_password: Default SSH password
        default_port: Default SSH port
        hours: Hours of logs to collect
        max_lines_per_file: Max lines per log file
        per_host_credentials: Dict of {host_ip: {username, password, port}} overrides
        max_workers: Max concurrent SSH connections

    Returns:
        {
            "logs": [...],
            "errors": {host_ip: error_message},
            "hosts_attempted": N,
            "hosts_success": N,
            "hosts_failed": N,
        }
    """
    per_host_credentials = per_host_credentials or {}
    all_logs = []
    errors = {}
    success_count = 0

    def _collect_one(host_ip: str) -> Tuple[str, List[Dict[str, Any]], Optional[str]]:
        cred = per_host_credentials.get(host_ip, {})
        user = cred.get("username") or default_username
        pwd = cred.get("password") or default_password
        port = cred.get("port") or default_port
        logs, err = _collect_from_single_host(
            host_ip=host_ip,
            username=user,
            password=pwd,
            port=port,
            hours=hours,
            max_lines_per_file=max_lines_per_file,
        )
        return host_ip, logs, err

    # Filter hosts with valid IPs
    valid_hosts = [h["ip_address"] for h in hosts if h.get("ip_address")]

    with ThreadPoolExecutor(max_workers=min(max_workers, len(valid_hosts))) as executor:
        futures = {executor.submit(_collect_one, ip): ip for ip in valid_hosts}
        for future in as_completed(futures, timeout=120):
            try:
                host_ip, logs, err = future.result()
                if err:
                    errors[host_ip] = err
                else:
                    success_count += 1
                all_logs.extend(logs)
            except Exception as e:
                ip = futures[future]
                errors[ip] = f"采集异常: {str(e)[:100]}"

    all_logs.sort(key=lambda x: x.get("event_time") or datetime.min, reverse=True)

    return {
        "logs": all_logs,
        "errors": errors,
        "hosts_attempted": len(valid_hosts),
        "hosts_success": success_count,
        "hosts_failed": len(errors),
    }
