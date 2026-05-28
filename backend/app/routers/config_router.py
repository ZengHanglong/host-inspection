"""
Configuration API Router - PostgreSQL version
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.database import (
    AlertRule,
    PlatformInstance,
    PlatformType,
    SessionLocal,
    SystemConfig,
)
from app.routers.credentials import _test_instance_connection
from app.scheduler import get_collection_status, reload_scheduler
from app.services.platform_service import invalidate_snapshot_cache
from app.utils.encryption import encrypt_password

router = APIRouter()


class ThresholdUpdate(BaseModel):
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    is_active: Optional[bool] = None


class PlatformUpdate(BaseModel):
    api_url: Optional[str] = None
    api_port: Optional[int] = None
    api_username: Optional[str] = None
    api_password: Optional[str] = None
    ssl_verify: Optional[bool] = True
    is_active: Optional[bool] = None


class CollectionConfigUpdate(BaseModel):
    interval_minutes: int = Field(..., ge=1, le=1440)
    auto_enabled: bool


@router.get("/thresholds")
async def get_thresholds():
    db = SessionLocal()
    try:
        rules = db.query(AlertRule).filter(AlertRule.category == "metric", AlertRule.is_active == True).all()
        return {
            "thresholds": [
                {
                    "id": r.id,
                    "resource_type": r.resource_type,
                    "warning_threshold": r.warning_value,
                    "critical_threshold": r.critical_value,
                    "is_active": r.is_active,
                }
                for r in rules
            ]
        }
    finally:
        db.close()


@router.put("/thresholds/{resource_type}")
async def update_threshold(resource_type: str, update: ThresholdUpdate):
    db = SessionLocal()
    try:
        rule = db.query(AlertRule).filter(AlertRule.resource_type == resource_type, AlertRule.category == "metric").first()
        if not rule:
            raise HTTPException(status_code=404, detail=f"资源类型 {resource_type} 不存在")

        if update.warning_threshold is not None:
            rule.warning_value = update.warning_threshold
        if update.critical_threshold is not None:
            rule.critical_value = update.critical_threshold
        if update.is_active is not None:
            rule.is_active = update.is_active

        db.commit()
        return {"success": True, "message": f"{resource_type} 阈值已更新"}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


@router.get("/platforms")
async def get_platforms():
    db = SessionLocal()
    try:
        instances = db.query(PlatformInstance).order_by(PlatformInstance.id).all()
        return {
            "platforms": [
                {
                    "id": i.id,
                    "platform": i.platform.code if i.platform else "",
                    "display_name": i.instance_name,
                    "description": i.description or "",
                    "api_type": i.api_type or "",
                    "api_url": i.api_url or "",
                    "api_port": i.api_port or 443,
                    "api_username": i.api_username or "",
                    "requires_ssl": i.requires_ssl,
                    "ssl_verify": i.ssl_verify if i.ssl_verify is not None else True,
                    "is_configured": i.is_configured,
                    "is_active": i.is_active,
                    "is_connected": i.is_connected,
                    "last_error": i.last_error or "",
                    "last_test_at": i.last_test_at.isoformat() if i.last_test_at else None,
                    "last_used": i.last_sync_at.isoformat() if i.last_sync_at else None,
                }
                for i in instances
            ]
        }
    finally:
        db.close()


@router.put("/platforms/{platform_id}")
async def update_platform(platform_id: int, update: PlatformUpdate):
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).filter(PlatformInstance.id == platform_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="平台不存在")

        if update.api_url is not None:
            instance.api_url = update.api_url
        if update.api_port is not None:
            instance.api_port = update.api_port
        if update.api_username is not None:
            instance.api_username = update.api_username
        if update.api_password:
            instance.api_password = encrypt_password(update.api_password)
        if update.ssl_verify is not None:
            instance.ssl_verify = update.ssl_verify
        if update.is_active is not None:
            instance.is_active = update.is_active

        instance.is_configured = bool(instance.api_url and instance.api_username and instance.api_password)
        instance.updated_at = datetime.now()
        if not instance.is_configured:
            instance.is_connected = False
            instance.last_error = None

        db.commit()
        invalidate_snapshot_cache()
        return {"success": True, "message": f"{instance.instance_name} 配置已更新"}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


@router.post("/platforms/{platform_id}/test")
async def test_platform_connection(platform_id: int):
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).filter(PlatformInstance.id == platform_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="平台不存在")
        if not instance.is_configured:
            return {"success": False, "message": "请先配置API凭证", "test_time": datetime.now().isoformat()}

        result = await _test_instance_connection(instance)
        instance.is_connected = result["success"]
        instance.last_test_at = datetime.now()
        instance.last_error = None if result["success"] else result.get("message")
        db.commit()
        invalidate_snapshot_cache()
        return result
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


@router.get("/collection")
async def get_collection_config():
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == "global_collect_interval").first()
        interval = int(config.config_value) if config else 5
        return {
            "interval_minutes": interval,
            "auto_enabled": True,
            "status": get_collection_status(),
        }
    finally:
        db.close()


@router.put("/collection")
async def update_collection_config(update: CollectionConfigUpdate):
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == "global_collect_interval").first()
        if config:
            config.config_value = str(update.interval_minutes)
            config.updated_at = datetime.now()
        else:
            db.add(SystemConfig(config_key="global_collect_interval", config_value=str(update.interval_minutes), value_type="int"))
        db.commit()

        scheduler_config = reload_scheduler()
        return {"success": True, "message": "采集配置已更新", "interval_minutes": scheduler_config["interval_minutes"], "auto_enabled": scheduler_config["auto_enabled"]}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()
