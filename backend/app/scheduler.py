"""
Scheduled Inspection Tasks - PostgreSQL version
"""
from __future__ import annotations

from datetime import datetime
import logging
from threading import Lock, Thread
from typing import Any, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import AlertRecord, PlatformInstance, SessionLocal, SystemConfig
from app.services.platform_service import (
    collect_connected_snapshots,
    flatten_alerts,
    invalidate_snapshot_cache,
    persist_host_records,
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
_scheduler_lock = Lock()
_run_lock = Lock()
_status_lock = Lock()

_COLLECTION_STATUS: Dict[str, Any] = {
    "is_running": False,
    "trigger_source": None,
    "started_at": None,
    "finished_at": None,
    "current_stage": "idle",
    "progress_percent": 0,
    "progress_message": "等待下一次采集",
    "last_success_at": None,
    "last_data_cutoff_at": None,
    "last_result_status": "idle",
    "last_error": None,
}


def _serialize_timestamp(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if isinstance(value, datetime) else value


def get_collection_status() -> Dict[str, Any]:
    with _status_lock:
        return {
            "is_running": bool(_COLLECTION_STATUS["is_running"]),
            "trigger_source": _COLLECTION_STATUS["trigger_source"],
            "started_at": _serialize_timestamp(_COLLECTION_STATUS["started_at"]),
            "finished_at": _serialize_timestamp(_COLLECTION_STATUS["finished_at"]),
            "current_stage": _COLLECTION_STATUS["current_stage"],
            "progress_percent": int(_COLLECTION_STATUS["progress_percent"] or 0),
            "progress_message": _COLLECTION_STATUS["progress_message"],
            "last_success_at": _serialize_timestamp(_COLLECTION_STATUS["last_success_at"]),
            "last_data_cutoff_at": _serialize_timestamp(_COLLECTION_STATUS["last_data_cutoff_at"]),
            "last_result_status": _COLLECTION_STATUS["last_result_status"],
            "last_error": _COLLECTION_STATUS["last_error"],
        }


def _update_collection_status(**changes: Any) -> None:
    with _status_lock:
        _COLLECTION_STATUS.update(changes)


def _load_collection_config() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == "global_collect_interval").first()
        interval = int(config.config_value) if config else 5
        return {"interval_minutes": max(interval, 1), "auto_enabled": True}
    finally:
        db.close()


def run_collection(trigger_source: str = "scheduled", force_refresh: bool = False) -> Dict[str, Any]:
    acquired = _run_lock.acquire(blocking=False)
    if not acquired:
        return {
            "success": False,
            "status": "running",
            "message": "采集任务正在执行中",
            "collection_status": get_collection_status(),
        }

    try:
        started_at = datetime.now()
        _update_collection_status(
            is_running=True,
            trigger_source=trigger_source,
            started_at=started_at,
            finished_at=None,
            current_stage="loading_platforms",
            progress_percent=5,
            progress_message="正在加载平台配置",
            last_result_status="running",
            last_error=None,
        )

        if force_refresh:
            invalidate_snapshot_cache()

        logger.info("开始%s采集: %s", "手动" if trigger_source == "manual" else "定时", started_at)

        db = SessionLocal()
        try:
            _update_collection_status(current_stage="collecting_snapshots", progress_percent=35, progress_message="正在采集平台数据")
            snapshots = collect_connected_snapshots(db)
            if not snapshots:
                _update_collection_status(
                    is_running=False,
                    finished_at=datetime.now(),
                    current_stage="idle",
                    progress_percent=100,
                    progress_message="当前没有可用的已连接平台",
                    last_result_status="no_credentials",
                )
                return {
                    "success": False,
                    "status": "no_credentials",
                    "message": "当前没有可用的已连接平台",
                    "total_hosts": 0,
                    "persisted_records": 0,
                    "platforms_checked": [],
                    "failed_platforms": [],
                    "check_time": datetime.now().isoformat(),
                }

            check_time = datetime.now()
            _update_collection_status(current_stage="persisting_records", progress_percent=70, progress_message="正在保存巡检结果")
            persisted_count = persist_host_records(db, snapshots, check_time=check_time)

            _update_collection_status(current_stage="refreshing_alerts", progress_percent=85, progress_message="正在刷新告警状态")
            alerts = flatten_alerts(snapshots)
            for alert in alerts:
                created_at = alert.get("created_at")
                db.add(
                    AlertRecord(
                        platform=alert.get("platform", "unknown"),
                        resource_type=alert.get("resource_type", "host"),
                        resource_name=alert.get("host_name"),
                        alert_level=alert.get("alert_level", "warning"),
                        message=alert.get("message"),
                        threshold_value=float(alert["threshold_value"]) if alert.get("threshold_value") is not None else None,
                        current_value=float(alert["current_value"]) if alert.get("current_value") is not None else None,
                        status="active",
                        triggered_at=datetime.fromisoformat(created_at) if created_at else check_time,
                    )
                )

            db.commit()

            data_cutoff = max((snapshot.get("last_sync") for snapshot in snapshots), default=check_time.isoformat())
            _update_collection_status(
                is_running=False,
                finished_at=datetime.now(),
                current_stage="idle",
                progress_percent=100,
                progress_message="采集完成",
                last_success_at=check_time,
                last_data_cutoff_at=data_cutoff,
                last_result_status="success",
            )
            logger.info("采集完成: 共 %s 台主机, %s 个告警", persisted_count, len(alerts))
            return {
                "success": True,
                "status": "success",
                "message": "巡检完成",
                "total_hosts": sum(len(snapshot.get("hosts", [])) for snapshot in snapshots),
                "persisted_records": persisted_count,
                "platforms_checked": [
                    {
                        "platform": snapshot.get("platform"),
                        "name": snapshot.get("platform_name"),
                        "hosts": len(snapshot.get("hosts", [])),
                        "data_source": snapshot.get("data_source"),
                        "status": snapshot.get("status"),
                    }
                    for snapshot in snapshots
                ],
                "failed_platforms": [],
                "check_time": check_time.isoformat(),
                "data_cutoff_time": data_cutoff,
            }
        except Exception as exc:
            db.rollback()
            raise exc
        finally:
            db.close()
    except Exception as exc:
        logger.exception("采集失败: %s", exc)
        _update_collection_status(
            is_running=False,
            finished_at=datetime.now(),
            current_stage="idle",
            progress_percent=100,
            progress_message="采集失败",
            last_result_status="failed",
            last_error=str(exc),
        )
        return {
            "success": False,
            "status": "failed",
            "message": f"采集失败: {exc}",
            "total_hosts": 0,
            "persisted_records": 0,
            "platforms_checked": [],
            "failed_platforms": [],
            "check_time": datetime.now().isoformat(),
        }
    finally:
        _run_lock.release()


def run_scheduled_inspection() -> Dict[str, Any]:
    return run_collection(trigger_source="scheduled", force_refresh=True)


def run_collection_in_background(trigger_source: str = "manual", force_refresh: bool = True) -> Dict[str, Any]:
    if _run_lock.locked():
        return {
            "started": False,
            "status": "running",
            "message": "采集任务正在执行中",
            "collection_status": get_collection_status(),
        }

    thread = Thread(target=run_collection, kwargs={"trigger_source": trigger_source, "force_refresh": force_refresh}, daemon=True)
    thread.start()
    return {
        "started": True,
        "status": "accepted",
        "message": "采集任务已启动",
        "collection_status": get_collection_status(),
    }


def reload_scheduler() -> Dict[str, Any]:
    config = _load_collection_config()
    with _scheduler_lock:
        if scheduler.get_job("inspection_job"):
            scheduler.remove_job("inspection_job")

        if config["auto_enabled"]:
            scheduler.add_job(
                run_scheduled_inspection,
                trigger=IntervalTrigger(minutes=config["interval_minutes"]),
                id="inspection_job",
                name="定时巡检",
                replace_existing=True,
            )

    logger.info("定时巡检配置已更新: interval=%s分钟", config["interval_minutes"])
    return config


def start_scheduler() -> Dict[str, Any]:
    config = reload_scheduler()
    with _scheduler_lock:
        if not scheduler.running:
            scheduler.start()
    logger.info("定时巡检调度器已启动")
    return config


def stop_scheduler() -> None:
    with _scheduler_lock:
        if scheduler.running:
            scheduler.shutdown(wait=False)
    logger.info("定时巡检调度器已停止")
