"""
Alerts API Router - PostgreSQL version
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Path, Query

from app.database import AlertRecord, SessionLocal
from app.services.platform_service import (
    build_alert_statistics_payload,
    build_alerts_payload,
    build_thresholds_payload,
)

router = APIRouter()


@router.get("/")
async def get_alerts(
    status: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    limit: int = Query(100),
):
    db = SessionLocal()
    try:
        return build_alerts_payload(db, status=status, level=level, platform=platform, category=category, alert_type=alert_type, limit=limit)
    finally:
        db.close()


@router.put("/{alert_id}/resolve")
async def resolve_alert(alert_id: int = Path(...)):
    db = SessionLocal()
    try:
        alert = db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()
        if alert:
            alert.status = "resolved"
            alert.resolved_at = datetime.now()
            alert.resolved_by = "manual"
            db.commit()
        return {"success": True, "message": f"告警 {alert_id} 已标记为已解决", "resolved_at": datetime.now().isoformat()}
    finally:
        db.close()


@router.put("/{alert_id}/ignore")
async def ignore_alert(alert_id: int = Path(...)):
    db = SessionLocal()
    try:
        alert = db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()
        if alert:
            alert.status = "ignored"
            alert.notes = "手动忽略"
            db.commit()
        return {"success": True, "message": f"告警 {alert_id} 已标记为已忽略"}
    finally:
        db.close()


@router.get("/statistics")
async def get_alert_statistics():
    db = SessionLocal()
    try:
        return build_alert_statistics_payload(db)
    finally:
        db.close()


@router.get("/thresholds")
async def get_thresholds():
    db = SessionLocal()
    try:
        return build_thresholds_payload(db)
    finally:
        db.close()
