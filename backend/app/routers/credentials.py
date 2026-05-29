"""
Credentials API Router - PostgreSQL version
"""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import PlatformInstance, PlatformType, SessionLocal
from app.services.platform_service import invalidate_snapshot_cache
from app.utils.encryption import encrypt_password

router = APIRouter()


class CredentialConfig(BaseModel):
    api_url: str
    api_port: Optional[int] = None
    api_username: Optional[str] = None
    api_password: Optional[str] = None
    api_key: Optional[str] = None
    ssl_verify: Optional[bool] = True
    esxi_ssh_username: Optional[str] = None
    esxi_ssh_password: Optional[str] = None
    esxi_ssh_port: Optional[int] = 22


class InstanceCreate(BaseModel):
    platform_code: str
    instance_name: str
    environment: str = "ser"
    api_url: Optional[str] = None
    api_port: Optional[int] = None
    api_username: Optional[str] = None
    api_password: Optional[str] = None
    ssl_verify: Optional[bool] = True
    esxi_ssh_username: Optional[str] = None
    esxi_ssh_password: Optional[str] = None
    esxi_ssh_port: Optional[int] = 22


@router.get("/list")
async def get_credentials_list():
    db = SessionLocal()
    try:
        instances = db.query(PlatformInstance).order_by(PlatformInstance.id).all()
        return {
            "total": len(instances),
            "credentials": [
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
                    "esxi_ssh_username": i.esxi_ssh_username or "",
                    "esxi_ssh_port": i.esxi_ssh_port or 22,
                }
                for i in instances
            ],
        }
    finally:
        db.close()


@router.get("/{platform}")
async def get_credential(platform: str):
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).join(PlatformType).filter(PlatformType.code == platform).first()
        if not instance:
            raise HTTPException(status_code=404, detail=f"平台 {platform} 不存在")
        return {
            "id": instance.id,
            "platform": platform,
            "display_name": instance.instance_name,
            "api_url": instance.api_url or "",
            "api_port": instance.api_port or 443,
            "api_username": instance.api_username or "",
            "has_password": bool(instance.api_password),
            "requires_ssl": instance.requires_ssl,
            "ssl_verify": instance.ssl_verify if instance.ssl_verify is not None else True,
            "is_configured": instance.is_configured,
            "is_active": instance.is_active,
            "is_connected": instance.is_connected,
            "last_error": instance.last_error or "",
            "last_test_at": instance.last_test_at.isoformat() if instance.last_test_at else None,
        }
    finally:
        db.close()


@router.put("/{platform}")
async def update_credential(platform: str, config: CredentialConfig):
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).join(PlatformType).filter(PlatformType.code == platform).first()
        if not instance:
            raise HTTPException(status_code=404, detail=f"平台 {platform} 不存在")

        instance.api_url = config.api_url
        instance.api_port = config.api_port or 443
        instance.api_username = config.api_username
        instance.ssl_verify = config.ssl_verify

        if config.api_password:
            instance.api_password = encrypt_password(config.api_password)
        if config.api_key:
            instance.api_key = config.api_key
        if getattr(config, 'esxi_ssh_username', None) is not None:
            instance.esxi_ssh_username = config.esxi_ssh_username
        if getattr(config, 'esxi_ssh_password', None):
            instance.esxi_ssh_password = encrypt_password(config.esxi_ssh_password)
        if getattr(config, 'esxi_ssh_port', None):
            instance.esxi_ssh_port = config.esxi_ssh_port

        instance.is_configured = bool(instance.api_url and instance.api_username and instance.api_password)
        instance.updated_at = datetime.now()

        db.commit()
        invalidate_snapshot_cache()
        return {"success": True, "message": f"{instance.instance_name} 凭证已保存", "platform": platform, "is_configured": True}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{platform}/test")
async def test_connection(platform: str):
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).join(PlatformType).filter(PlatformType.code == platform).first()
        if not instance:
            raise HTTPException(status_code=404, detail=f"平台 {platform} 不存在")
        if not instance.is_configured:
            return {"platform": platform, "success": False, "message": "请先配置API凭证", "test_time": datetime.now().isoformat()}

        test_result = await _test_instance_connection(instance)
        instance.is_connected = test_result["success"]
        instance.last_test_at = datetime.now()
        instance.last_error = None if test_result["success"] else test_result.get("message")
        db.commit()
        invalidate_snapshot_cache()
        return test_result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


async def _test_instance_connection(instance: PlatformInstance) -> dict:
    platform_code = instance.platform.code if instance.platform else ""
    if platform_code == "vmware":
        return await _test_vmware_connection(instance)
    if platform_code == "smartx":
        return await _test_smartx_connection(instance)
    return await _test_rest_connection(instance)


async def _test_vmware_connection(instance: PlatformInstance) -> dict:
    import ssl
    try:
        from pyVim.connect import SmartConnect
    except ImportError:
        return {"platform": "vmware", "success": False, "message": "请安装pyVmomi: pip install pyvmomi", "test_time": datetime.now().isoformat()}

    from app.utils.encryption import decrypt_password
    password = decrypt_password(instance.api_password or "")

    ssl_context = None
    if not instance.ssl_verify:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.verify_mode = ssl.CERT_NONE

    try:
        si = SmartConnect(host=instance.api_url, port=instance.api_port or 443, user=instance.api_username, pwd=password, sslContext=ssl_context)
        content = si.RetrieveContent()
        version = content.about.version
        build = content.about.build
        from pyVim.connect import Disconnect
        Disconnect(si)
        return {"platform": "vmware", "success": True, "message": f"连接成功 - vCenter {version} build {build}", "test_time": datetime.now().isoformat()}
    except Exception as e:
        return {"platform": "vmware", "success": False, "message": f"连接失败: {str(e)}", "test_time": datetime.now().isoformat()}


async def _test_smartx_connection(instance: PlatformInstance) -> dict:
    from app.services.smartx_client import SmartXClient
    from app.utils.encryption import decrypt_password
    password = decrypt_password(instance.api_password or "")
    client = SmartXClient(host=instance.api_url or "", port=instance.api_port or 443, username=instance.api_username or "", password=password, ssl_verify=instance.ssl_verify)
    return client.test_endpoint_reachability()


async def _test_rest_connection(instance: PlatformInstance) -> dict:
    import socket
    try:
        host = (instance.api_url or "").replace("https://", "").replace("http://", "").split("/")[0]
        port = instance.api_port or 443
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex((host, port))
        finally:
            sock.close()
        if result == 0:
            return {"platform": instance.platform.code if instance.platform else "", "success": True, "message": f"端口 {port} 可达，请验证API凭证是否正确", "test_time": datetime.now().isoformat()}
        return {"platform": instance.platform.code if instance.platform else "", "success": False, "message": f"无法连接到 {host}:{port}", "test_time": datetime.now().isoformat()}
    except Exception as e:
        return {"platform": instance.platform.code if instance.platform else "", "success": False, "message": f"测试失败: {str(e)}", "test_time": datetime.now().isoformat()}


@router.delete("/{platform}/clear")
async def clear_credential(platform: str):
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).join(PlatformType).filter(PlatformType.code == platform).first()
        if not instance:
            raise HTTPException(status_code=404, detail=f"平台 {platform} 不存在")
        instance.api_url = None
        instance.api_port = None
        instance.api_username = None
        instance.api_password = None
        instance.api_key = None
        instance.is_configured = False
        instance.is_connected = False
        instance.last_error = None
        db.commit()
        invalidate_snapshot_cache()
        return {"success": True, "message": f"{instance.instance_name} 凭证已清除", "platform": platform}
    finally:
        db.close()


@router.put("/{platform}/toggle")
async def toggle_platform(platform: str, is_active: bool = True):
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).join(PlatformType).filter(PlatformType.code == platform).first()
        if not instance:
            raise HTTPException(status_code=404, detail=f"平台 {platform} 不存在")
        instance.is_active = is_active
        instance.updated_at = datetime.now()
        db.commit()
        invalidate_snapshot_cache()
        return {"success": True, "message": f"{instance.instance_name} 已{'启用' if is_active else '禁用'}", "platform": platform, "is_active": is_active}
    finally:
        db.close()


# ──────────────────────────────────────────────
# Multi-instance endpoints (by instance ID)
# ──────────────────────────────────────────────

@router.post("/instances")
async def create_instance(config: InstanceCreate):
    """Create a new platform instance (for adding multiple nodes)"""
    db = SessionLocal()
    try:
        platform = db.query(PlatformType).filter(PlatformType.code == config.platform_code).first()
        if not platform:
            raise HTTPException(status_code=404, detail=f"平台类型 {config.platform_code} 不存在")

        instance = PlatformInstance(
            uid=str(uuid.uuid4()),
            platform_id=platform.id,
            environment=config.environment,
            instance_name=config.instance_name,
            api_type=platform.api_type,
            api_url=config.api_url,
            api_port=config.api_port or platform.api_type == "pyvmomi" and 443 or 443,
            api_username=config.api_username,
            requires_ssl=True,
            ssl_verify=config.ssl_verify if config.ssl_verify is not None else True,
            is_configured=False,
            is_active=True,
            is_connected=False,
        )

        if config.api_password:
            instance.api_password = encrypt_password(config.api_password)
        if config.api_url and config.api_username and instance.api_password:
            instance.is_configured = True

        db.add(instance)
        db.commit()
        db.refresh(instance)
        invalidate_snapshot_cache()

        return {
            "success": True,
            "message": f"{instance.instance_name} 创建成功",
            "instance": {
                "id": instance.id,
                "platform": platform.code,
                "display_name": instance.instance_name,
                "environment": instance.environment,
                "is_configured": instance.is_configured,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/instances/{instance_id}")
async def delete_instance(instance_id: int):
    """Delete a platform instance"""
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).filter(PlatformInstance.id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="实例不存在")

        name = instance.instance_name
        db.delete(instance)
        db.commit()
        invalidate_snapshot_cache()
        return {"success": True, "message": f"{name} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/instances/{instance_id}")
async def update_instance(instance_id: int, config: CredentialConfig):
    """Update a platform instance by ID"""
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).filter(PlatformInstance.id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="实例不存在")

        instance.api_url = config.api_url
        instance.api_port = config.api_port or 443
        instance.api_username = config.api_username
        instance.ssl_verify = config.ssl_verify

        if config.api_password:
            instance.api_password = encrypt_password(config.api_password)
        if config.api_key:
            instance.api_key = config.api_key
        if getattr(config, 'esxi_ssh_username', None) is not None:
            instance.esxi_ssh_username = config.esxi_ssh_username
        if getattr(config, 'esxi_ssh_password', None):
            instance.esxi_ssh_password = encrypt_password(config.esxi_ssh_password)
        if getattr(config, 'esxi_ssh_port', None):
            instance.esxi_ssh_port = config.esxi_ssh_port

        instance.is_configured = bool(instance.api_url and instance.api_username and instance.api_password)
        instance.updated_at = datetime.now()

        db.commit()
        invalidate_snapshot_cache()
        return {"success": True, "message": f"{instance.instance_name} 凭证已保存"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/instances/{instance_id}/test")
async def test_instance_connection(instance_id: int):
    """Test connection for a specific instance"""
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).filter(PlatformInstance.id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="实例不存在")
        if not instance.is_configured:
            return {"success": False, "message": "请先配置API凭证", "test_time": datetime.now().isoformat()}

        test_result = await _test_instance_connection(instance)
        instance.is_connected = test_result["success"]
        instance.last_test_at = datetime.now()
        instance.last_error = None if test_result["success"] else test_result.get("message")
        db.commit()
        invalidate_snapshot_cache()
        return test_result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/instances/{instance_id}/clear")
async def clear_instance(instance_id: int):
    """Clear credentials for a specific instance"""
    db = SessionLocal()
    try:
        instance = db.query(PlatformInstance).filter(PlatformInstance.id == instance_id).first()
        if not instance:
            raise HTTPException(status_code=404, detail="实例不存在")

        instance.api_url = None
        instance.api_port = None
        instance.api_username = None
        instance.api_password = None
        instance.api_key = None
        instance.is_configured = False
        instance.is_connected = False
        instance.last_error = None

        db.commit()
        invalidate_snapshot_cache()
        return {"success": True, "message": f"{instance.instance_name} 凭证已清除"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
