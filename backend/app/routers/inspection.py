"""
Inspection API Router - PostgreSQL version
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.database import EsxiHostLog, SessionLocal
from app.scheduler import get_collection_status, run_collection_in_background
from app.services.platform_service import (
    build_history_payload,
    build_idle_vm_periodic_payload,
    build_inspection_list_payload,
    build_large_vm_periodic_payload,
    build_naming_periodic_payload,
    build_platform_inspection_payload,
    build_snapshot_periodic_payload,
    build_triggered_alarms_payload,
)

router = APIRouter()


@router.get("/list")
async def get_inspection_list(
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    db = SessionLocal()
    try:
        return build_inspection_list_payload(db, platform=platform, status=status, category=category)
    finally:
        db.close()


@router.get("/status")
async def get_inspection_status():
    return get_collection_status()


@router.post("/run")
async def run_inspection():
    result = run_collection_in_background(trigger_source="manual", force_refresh=True)
    if not result["started"]:
        return {"success": False, "status": result["status"], "message": result["message"], "collection_status": result["collection_status"]}
    return {"success": True, "status": result["status"], "message": result["message"], "collection_status": result["collection_status"]}


@router.get("/history/{host_name}")
async def get_history(host_name: str, days: int = Query(7, ge=1, le=365)):
    db = SessionLocal()
    try:
        return build_history_payload(db, host_name=host_name, days=days)
    finally:
        db.close()


@router.get("/periodic/snapshot")
async def get_snapshot_check():
    db = SessionLocal()
    try:
        return build_snapshot_periodic_payload(db)
    finally:
        db.close()


@router.get("/periodic/large-vm")
async def get_large_vm_check():
    db = SessionLocal()
    try:
        return build_large_vm_periodic_payload(db)
    finally:
        db.close()


@router.get("/periodic/naming")
async def get_naming_check():
    db = SessionLocal()
    try:
        return build_naming_periodic_payload(db)
    finally:
        db.close()


@router.get("/periodic/idle-vm")
async def get_idle_vm_check():
    db = SessionLocal()
    try:
        return build_idle_vm_periodic_payload(db)
    finally:
        db.close()


@router.get("/periodic/alarms")
async def get_triggered_alarms():
    db = SessionLocal()
    try:
        return build_triggered_alarms_payload(db)
    finally:
        db.close()


@router.get("/esxi-logs")
async def get_esxi_logs(
    hours: int = Query(24, ge=1, le=168),
    host_name: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
):
    """Get ESXi host logs with filtering"""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(hours=hours)
        query = db.query(EsxiHostLog).filter(EsxiHostLog.event_time >= since)
        if host_name:
            query = query.filter(EsxiHostLog.host_name == host_name)
        if category:
            query = query.filter(EsxiHostLog.category == category)
        if severity:
            query = query.filter(EsxiHostLog.severity == severity)
        rows = query.order_by(EsxiHostLog.event_time.desc()).limit(limit).all()

        logs = [
            {
                "id": r.id,
                "host_name": r.host_name,
                "category": r.category,
                "service": r.service,
                "severity": r.severity,
                "message": r.message,
                "log_file": r.log_file or "",
                "event_time": r.event_time.isoformat() if r.event_time else None,
            }
            for r in rows
        ]

        # Summary counts using single query
        from sqlalchemy import func
        severity_counts = dict(
            db.query(EsxiHostLog.severity, func.count(EsxiHostLog.id))
            .filter(EsxiHostLog.event_time >= since)
            .group_by(EsxiHostLog.severity)
            .all()
        )

        # Unique hosts
        host_list = [
            r[0] for r in db.query(EsxiHostLog.host_name)
            .filter(EsxiHostLog.event_time >= since)
            .distinct()
            .all()
        ]

        return {
            "total": len(logs),
            "hours": hours,
            "by_severity": {
                "info": severity_counts.get("info", 0),
                "warning": severity_counts.get("warning", 0),
                "error": severity_counts.get("error", 0),
                "critical": severity_counts.get("critical", 0),
            },
            "hosts": sorted(host_list),
            "data": logs,
        }
    finally:
        db.close()


@router.get("/{platform}")
async def get_platform_inspection(platform: str):
    db = SessionLocal()
    try:
        try:
            return build_platform_inspection_payload(db, platform)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        db.close()
