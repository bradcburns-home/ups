from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

try:
    from burns_logger import configure_logging, configure_uvicorn, get_logger
    configure_logging(source="ups-web")
    configure_uvicorn("ups-web")
    log = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger(__name__)

_start_time = time.monotonic()
_templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))

app = FastAPI(title="The Power Play", docs_url=None, redoc_url=None)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "uptime_seconds": round(time.monotonic() - _start_time, 1),
    }


@app.get("/api/status")
async def api_status() -> JSONResponse:
    from app.nut_client import query_ups
    result = await asyncio.to_thread(query_ups)
    if result.get("status") == "error":
        return JSONResponse(result, status_code=503)
    return JSONResponse(result)


@app.get("/api/history")
async def api_history(
    range: str = Query("24h", alias="range", description="Time range: 1h, 12h, 24h, 7d"),
    metric: str = Query("all", description="Metric column or 'all'"),
) -> JSONResponse:
    from app.bq_client import query_history
    result = await asyncio.to_thread(query_history, range, metric)
    if result.get("status") == "error":
        return JSONResponse(result, status_code=400 if not result.get("retryable") else 503)
    return JSONResponse(result)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.exception_handler(404)
async def not_found(request: Request, exc: Any) -> HTMLResponse:
    return HTMLResponse(
        content="""<!DOCTYPE html>
<html><head><title>404 — The Power Play</title>
<style>body{font-family:system-ui;display:flex;align-items:center;justify-content:center;
height:100vh;margin:0;background:#1a1a1a;color:#fff;text-align:center}
h1{font-size:3rem;margin-bottom:0.5rem}p{color:#999;font-size:1.2rem}
a{color:#CE1126;text-decoration:none}</style></head>
<body><div><h1>404</h1><p>This page is as reliable as DTE.</p>
<p><a href="/">Back to The Power Play</a></p></div></body></html>""",
        status_code=404,
    )
