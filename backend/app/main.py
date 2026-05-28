"""
FastAPI Application Entry Point - Host Inspection System
PostgreSQL version
"""
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import PlatformInstance, SessionLocal, init_db
from app.routers import alerts, config_router, credentials, inspection, ledger, report
from app.scheduler import start_scheduler, stop_scheduler
from app.services.platform_service import build_dashboard_payload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    init_db()
    start_scheduler()
    # Pre-warm cache in background on startup
    import threading
    def _warm_cache():
        from app.services.platform_service import collect_connected_snapshots
        db = SessionLocal()
        try:
            collect_connected_snapshots(db)
        except Exception:
            pass
        finally:
            db.close()
    threading.Thread(target=_warm_cache, daemon=True).start()
    yield
    stop_scheduler()


app = FastAPI(
    title="HostInspection API",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(credentials.router, prefix="/api/credentials", tags=["Credentials"])
app.include_router(report.router, prefix="/api/report", tags=["Report"])
app.include_router(inspection.router, prefix="/api/inspection", tags=["Inspection"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(ledger.router, prefix="/api/ledger", tags=["Ledger"])
app.include_router(config_router.router, prefix="/api/config", tags=["Config"])


def get_www_path():
    """Get www directory path"""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "www")


@app.get("/api/dashboard", tags=["Dashboard"])
async def get_dashboard():
    """Get dashboard summary data"""
    from app.services.platform_service import is_cache_warm
    # If cache is warming up (first request after startup), return loading state immediately
    if not is_cache_warm():
        return {
            "status": "loading",
            "message": "数据采集中，请稍候...",
            "total_platforms": 0,
            "platforms": {},
            "overall": {"total_hosts": 0, "normal": 0, "warning": 0, "critical": 0, "data_source": "none", "last_check_time": None, "data_cutoff_time": None, "data_sources": []},
            "alerts": [],
            "periodic_status": {},
            "failed_platforms": {},
        }
    db = SessionLocal()
    try:
        return build_dashboard_payload(db)
    finally:
        db.close()


@app.get("/api/overview", tags=["Dashboard"])
async def get_overview():
    """Combined status endpoint for App header (reduces frontend requests)"""
    from app.scheduler import get_collection_status
    from app.services.platform_service import build_alerts_payload, get_connected_instances

    db = SessionLocal()
    try:
        instances = db.query(PlatformInstance).all()
        connected = [i for i in instances if i.is_connected]
        configured = [i for i in instances if i.is_configured]

        # Connection status
        if len(connected) > 0:
            conn_status = "connected" if len(connected) == len(configured) else "partial"
        elif len(configured) > 0:
            conn_status = "error"
        else:
            conn_status = "pending"

        # Active alert count (quick query)
        from app.database import AlertRecord
        active_alerts = db.query(AlertRecord).filter(AlertRecord.status == "active").count()

        return {
            "connection_status": conn_status,
            "total_count": len(instances),
            "configured_count": len(configured),
            "connected_count": len(connected),
            "unconfigured_count": len(instances) - len(configured),
            "active_alert_count": active_alerts,
            "collection_status": get_collection_status(),
        }
    finally:
        db.close()


www_path = get_www_path()
if os.path.exists(www_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(www_path, "assets")), name="assets")


@app.get("/")
async def root():
    """Serve frontend index.html"""
    index_path = os.path.join(get_www_path(), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "HostInspection API", "version": "4.0.0", "docs": "/docs"}


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    """Fallback for SPA routing"""
    if full_path.startswith("api/") or full_path.startswith("assets/"):
        return None
    index_path = os.path.join(get_www_path(), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Not found"}


if __name__ == "__main__":
    import uvicorn

    print("Starting HostInspection server...")
    print(f"WWW path: {get_www_path()}")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
