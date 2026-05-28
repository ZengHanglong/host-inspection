"""
Ledger API Router - PostgreSQL version
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database import SessionLocal, VmMetadataOverride, VmwareMetric
from app.services.platform_service import (
    build_db_ledger_payload,
    build_ledger_summary_payload,
    build_physical_ledger_payload,
    build_vm_ledger_payload,
)

router = APIRouter()


class VmMetadataUpdate(BaseModel):
    system: Optional[str] = None
    function: Optional[str] = None
    owner: Optional[str] = None
    note: Optional[str] = None


@router.get("/vm")
async def get_vm_ledger(
    platform: Optional[str] = Query(None),
    cluster: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    has_snapshot: Optional[bool] = Query(None),
):
    db = SessionLocal()
    try:
        return build_vm_ledger_payload(db, platform=platform, cluster=cluster, owner=owner, environment=environment, has_snapshot=has_snapshot)
    finally:
        db.close()


@router.get("/physical")
async def get_physical_ledger(
    platform: Optional[str] = Query(None),
    cluster: Optional[str] = Query(None),
):
    db = SessionLocal()
    try:
        return build_physical_ledger_payload(db, platform=platform, cluster=cluster)
    finally:
        db.close()


@router.get("/database")
async def get_db_ledger():
    return build_db_ledger_payload()


@router.get("/summary")
async def get_ledger_summary():
    db = SessionLocal()
    try:
        return build_ledger_summary_payload(db)
    finally:
        db.close()


@router.get("/vm/metadata/{platform}/{vm_name}")
async def get_vm_metadata(platform: str, vm_name: str):
    """Get user-edited metadata for a VM"""
    db = SessionLocal()
    try:
        override = db.query(VmMetadataOverride).filter(
            VmMetadataOverride.platform == platform,
            VmMetadataOverride.vm_name == vm_name,
        ).first()
        if override:
            return {
                "platform": platform,
                "vm_name": vm_name,
                "system": override.system or "",
                "function": override.function or "",
                "owner": override.owner or "",
                "note": override.note or "",
                "has_override": True,
            }
        return {"platform": platform, "vm_name": vm_name, "system": "", "function": "", "owner": "", "note": "", "has_override": False}
    finally:
        db.close()


@router.put("/vm/metadata/{platform}/{vm_name}")
async def update_vm_metadata(platform: str, vm_name: str, update: VmMetadataUpdate):
    """Update user-edited metadata for a VM"""
    db = SessionLocal()
    try:
        override = db.query(VmMetadataOverride).filter(
            VmMetadataOverride.platform == platform,
            VmMetadataOverride.vm_name == vm_name,
        ).first()
        if not override:
            override = VmMetadataOverride(platform=platform, vm_name=vm_name)
            db.add(override)

        if update.system is not None:
            override.system = update.system
        if update.function is not None:
            override.function = update.function
        if update.owner is not None:
            override.owner = update.owner
        if update.note is not None:
            override.note = update.note
        override.updated_at = datetime.now()

        db.commit()
        return {"success": True, "message": f"{vm_name} 元数据已更新"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/vm/metrics/{vm_name}")
async def get_vm_metrics(
    vm_name: str,
    hours: int = Query(24, ge=1, le=168, description="时间范围(小时)"),
    platform: Optional[str] = Query(None),
):
    """Get VM resource usage history for trend charts"""
    db = SessionLocal()
    try:
        since = datetime.now() - timedelta(hours=hours)
        query = db.query(VmwareMetric).filter(
            VmwareMetric.resource_type == "vm",
            VmwareMetric.resource_name == vm_name,
            VmwareMetric.check_time >= since,
        )
        rows = query.order_by(VmwareMetric.check_time.asc()).all()

        data = [
            {
                "timestamp": r.check_time.isoformat(),
                "cpu": float(r.cpu_usage or 0),
                "memory": float(r.memory_usage or 0),
                "storage": float(r.storage_usage or 0),
            }
            for r in rows
        ]

        return {
            "vm_name": vm_name,
            "hours": hours,
            "total": len(data),
            "data": data,
        }
    finally:
        db.close()
