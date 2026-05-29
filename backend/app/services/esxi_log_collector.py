"""
ESXi Host Log Collector - SSH-based direct log collection from ESXi hosts

Reads /var/log/ files from ESXi hosts via SSH and categorizes by service.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Log files to collect and their service mapping
ESXI_LOG_FILES = {
    "/var/log/hostd.log": {"category": "system", "service": "hostd", "description": "ESXi主机管理服务"},
    "/var/log/vpxa.log": {"category": "system", "service": "vpxa", "description": "vCenter代理服务"},
    "/var/log/vmkernel.log": {"category": "virtualization", "service": "vmkernel", "description": "虚拟化内核"},
    "/var/log/vmkwarning.log": {"category": "virtualization", "service": "vmkwarning", "description": "内核警告"},
    "/var/log/vmksummary.log": {"category": "virtualization", "service": "vmksummary", "description": "内核摘要"},
    "/var/log/auth.log": {"category": "ssh", "service": "sshd", "description": "SSH认证日志"},
    "/var/log/shell.log": {"category": "ssh", "service": "shell", "description": "Shell操作日志"},
    "/var/log/esxcli.log": {"category": "system", "service": "esxcli", "description": "CLI操作日志"},
    "/var/log/rhttpproxy.log": {"category": "network", "service": "rhttpproxy", "description": "HTTP代理"},
    "/var/log/storageRM.log": {"category": "storage", "service": "storageRM", "description": "存储资源管理"},
    "/var/log/fdm.log": {"category": "system", "service": "fdm", "description": "HA故障检测"},
}

# Severity detection patterns
_SEVERITY_PATTERNS = {
    "critical": [r"\bcritical\b", r"\bfatal\b", r"\bpanic\b", r"\bCRITICAL\b", r"\bFATAL\b"],
    "error": [r"\berror\b", r"\berr\b", r"\bfailed\b", r"\bERROR\b", r"\bFAIL\b"],
    "warning": [r"\bwarn\b", r"\bwarning\b", r"\bWARN\b", r"\bWARNING\b"],
    "info": [r"\binfo\b", r"\bnotice\b", r"\bINFO\b"],
}

# ESXi syslog line format: "2024-01-15T10:30:45Z hostname service[pid]: message"
_SYSLOG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)\s+"  # timestamp
    r"(\S+)\s+"  # hostname
    r"(\S+?)(?:\[\d+\])?:\s+"  # service[pid]:
    r"(.+)$"  # message
)


def _detect_severity(message: str) -> str:
    """Detect log severity from message content."""
    msg_lower = message.lower()
    for severity, patterns in _SEVERITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return severity
    return "info"


def _parse_syslog_line(line: str, default_host: str = "") -> Optional[Dict[str, Any]]:
    """Parse a single syslog line into structured data."""
    line = line.strip()
    if not line or line.startswith("---"):
        return None

    match = _SYSLOG_PATTERN.match(line)
    if match:
        ts_str, hostname, service, message = match.groups()
        try:
            # Handle both Z-suffixed and non-suffixed timestamps
            ts_str_clean = ts_str.rstrip("Z")
            event_time = datetime.fromisoformat(ts_str_clean)
        except ValueError:
            event_time = None

        return {
            "host_name": hostname or default_host,
            "service": service,
            "message": message.strip(),
            "event_time": event_time,
            "severity": _detect_severity(message),
        }

    # Fallback: treat entire line as message
    return {
        "host_name": default_host,
        "service": "unknown",
        "message": line,
        "event_time": None,
        "severity": _detect_severity(line),
    }


def collect_esxi_logs_via_ssh(
    host_ip: str,
    username: str,
    password: str,
    port: int = 22,
    hours: int = 24,
    max_lines_per_file: int = 200,
) -> List[Dict[str, Any]]:
    """
    Collect ESXi host logs via SSH.

    Args:
        host_ip: ESXi host IP address
        username: SSH username (usually 'root')
        password: SSH password
        port: SSH port (default 22)
        hours: How many hours of logs to collect
        max_lines_per_file: Max lines to read per log file

    Returns:
        List of log entries with category, service, severity, message
    """
    try:
        import paramiko
    except ImportError:
        return [{"host_name": host_ip, "category": "system", "service": "collector",
                 "severity": "error", "message": "paramiko not installed: pip install paramiko",
                 "event_time": datetime.now()}]

    logs = []
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host_ip, port=port, username=username, password=password, timeout=10)

        for log_path, meta in ESXI_LOG_FILES.items():
            try:
                # Read last N lines of each log file
                cmd = f"tail -n {max_lines_per_file} {log_path} 2>/dev/null"
                stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
                output = stdout.read().decode("utf-8", errors="replace")

                for line in output.split("\n"):
                    parsed = _parse_syslog_line(line, default_host=host_ip)
                    if not parsed:
                        continue

                    # Filter by time range
                    if parsed["event_time"] and parsed["event_time"] < datetime.now() - timedelta(hours=hours):
                        continue

                    parsed["category"] = meta["category"]
                    parsed["service"] = meta["service"]
                    if parsed["service"] == "unknown":
                        parsed["service"] = meta["service"]

                    # Override severity if the log file itself implies a level
                    if "warning" in log_path:
                        if parsed["severity"] == "info":
                            parsed["severity"] = "warning"

                    logs.append(parsed)

            except Exception:
                # Skip files that don't exist or can't be read
                continue

    except Exception as e:
        logs.append({
            "host_name": host_ip, "category": "system", "service": "ssh",
            "severity": "error", "message": f"SSH连接失败: {str(e)}",
            "event_time": datetime.now(),
        })
    finally:
        client.close()

    # Sort by time descending
    logs.sort(key=lambda x: x.get("event_time") or datetime.min, reverse=True)
    return logs
