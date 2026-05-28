"""
Report API Router - PostgreSQL version
"""
from datetime import datetime
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from urllib.parse import quote

from app.database import SessionLocal
from app.services.platform_service import build_report_payload, build_snapshot_report_payload
from app.services.report_generator import create_inspection_report

router = APIRouter()


def _build_docx_thresholds(report: dict) -> dict:
    thresholds = report.get("thresholds", {})
    return {
        "cpu_warning": thresholds.get("cpu", {}).get("warning", 70.0),
        "cpu_critical": thresholds.get("cpu", {}).get("critical", 80.0),
        "memory_warning": thresholds.get("memory", {}).get("warning", 70.0),
        "memory_critical": thresholds.get("memory", {}).get("critical", 80.0),
        "storage_warning": thresholds.get("storage", {}).get("warning", 60.0),
        "storage_critical": thresholds.get("storage", {}).get("critical", 70.0),
    }


def _build_docx_data(report: dict) -> dict:
    platforms = {}
    data_sources = []
    for platform in report.get("platforms", []):
        code = platform.get("platform")
        if not code:
            continue
        platforms[code] = {
            "name": platform.get("display_name"),
            "data_source": platform.get("data_source"),
            "status": platform.get("status"),
            "clusters": platform.get("clusters", []),
            "hosts": platform.get("hosts", []),
            "vms": platform.get("vms", []),
            "statistics": platform.get("statistics", {}),
            "expired_snapshots": platform.get("expired_snapshots", []),
            "large_vms": platform.get("large_vms", []),
            "naming_issues": platform.get("naming_issues", []),
            "idle_vms": platform.get("idle_vms", []),
            "periodic_items": platform.get("periodic_items", []),
            "capabilities": platform.get("capabilities", {}),
        }
        if platform.get("data_source"):
            data_sources.append(platform["data_source"])
    return {
        "report_type": report.get("report_type"),
        "report_time": report.get("report_time"),
        "generated_by": report.get("generated_by"),
        "data_declaration": report.get("data_declaration"),
        "overall_summary": report.get("overall_summary", {}),
        "overall_statistics": report.get("overall_statistics", {}),
        "warnings": report.get("warnings", []),
        "errors": report.get("errors", []),
        "platforms": platforms,
        "data_sources": data_sources,
    }


@router.get("/daily")
async def generate_daily_report(
    format: str = Query("json"),
    include_empty: bool = Query(False),
):
    db = SessionLocal()
    try:
        report = build_report_payload(db, include_empty=include_empty)
        if format == "json":
            return report
        return _generate_html_report(report)
    finally:
        db.close()


def _generate_html_report(report: dict) -> str:
    platform_sections = ""
    for p in report.get("platforms", []):
        stats = p.get("statistics", {})
        host_rows = "".join([
            f"<tr class='{h.get('status','normal')}'><td>{h.get('host_name','')}</td><td>{h.get('cluster_name','')}</td>"
            f"<td>{h.get('cpu_usage_percent',0)}%</td><td>{h.get('memory_usage_percent',0)}%</td>"
            f"<td>{h.get('status','unknown')}</td></tr>"
            for h in p.get("hosts", [])
        ]) or "<tr><td colspan='5'>暂无主机数据</td></tr>"
        platform_sections += f"""
        <div style="margin-bottom:20px;">
            <h3>{p['display_name']}</h3>
            <p>统计: 集群 {stats.get('clusters',0)} | 主机 {stats.get('total',0)} | 正常 {stats.get('normal',0)} | 警告 {stats.get('warning',0)} | 严重 {stats.get('critical',0)}</p>
            <table><tr><th>主机名</th><th>集群</th><th>CPU</th><th>内存</th><th>状态</th></tr>{host_rows}</table>
        </div>"""

    overall = report.get("overall_statistics", {})
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>{report['report_type']}</title>
    <style>body{{font-family:'Microsoft YaHei',Arial,sans-serif;padding:20px}}
    table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
    th{{background:#f3f4f6}}.warning{{background:#fef3c7}}.critical{{background:#fee2e2}}</style></head>
    <body><h1>{report['report_type']}</h1><p>报告时间: {report['report_time']}</p>
    <h2>整体概况</h2>
    <p>总主机: {overall.get('total_hosts',0)} | 正常: {overall.get('normal_hosts',0)} | 警告: {overall.get('warning_hosts',0)} | 严重: {overall.get('critical_hosts',0)}</p>
    <h2>平台详情</h2>{platform_sections}</body></html>"""


@router.get("/snapshot")
async def generate_snapshot_report():
    db = SessionLocal()
    try:
        return build_snapshot_report_payload(db)
    finally:
        db.close()


@router.get("/download/html")
async def download_html_report():
    db = SessionLocal()
    try:
        report = build_report_payload(db, include_empty=False)
        if not report.get("platforms"):
            raise HTTPException(status_code=400, detail="未配置API凭证或连接失败，无法生成报告")
        html_content = _generate_html_report(report)
    finally:
        db.close()
    return StreamingResponse(
        iter([html_content.encode("utf-8")]),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=inspection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"},
    )


@router.get("/download/docx")
async def download_docx_report(company_name: str = Query("厦门国际信托")):
    import traceback
    db = SessionLocal()
    try:
        report = build_report_payload(db, include_empty=False)
        if not report.get("platforms"):
            raise HTTPException(status_code=400, detail="未配置API凭证或连接失败，无法生成报告")

        report_date = datetime.now().strftime("%Y%m%d")
        doc = create_inspection_report(
            company_name=company_name,
            report_date=report_date,
            data=_build_docx_data(report),
            thresholds=_build_docx_thresholds(report),
        )
        docx_stream = io.BytesIO()
        doc.save(docx_stream)
        docx_stream.seek(0)
    except HTTPException:
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        print("DOCX_ERROR:", tb)
        raise HTTPException(status_code=500, detail=f"报告生成失败: {exc}\n{tb}")
    finally:
        db.close()

    filename_ascii = quote(f"巡检报告_{report_date}.docx")
    return Response(
        content=docx_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename_ascii}"},
    )
