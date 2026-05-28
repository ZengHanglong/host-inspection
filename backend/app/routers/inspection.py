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
                "event_type": r.event_type,
                "user_name": r.user_name,
                "event_time": r.event_time.isoformat() if r.event_time else None,
            }
            for r in rows
        ]

        # Summary counts
        base_query = db.query(EsxiHostLog).filter(EsxiHostLog.event_time >= since)
        total = base_query.count()
        by_severity = {}
        for sev in ["info", "warning", "error", "critical"]:
            by_severity[sev] = base_query.filter(EsxiHostLog.severity == sev).count()
        by_category = {}
        for row in base_query.with_entities(EsxiHostLog.category, db.query(EsxiHostLog).filter(EsxiHostLog.event_time >= since).subquery().c.category).distinct():
            pass  # simplified below

        return {
            "total": total,
            "hours": hours,
            "by_severity": by_severity,
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
