from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from google.cloud import bigquery

from app.config import get_settings

log = logging.getLogger(__name__)

_RANGE_MAP: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "12h": timedelta(hours=12),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}

_ALLOWED_METRICS = {
    "battery_charge", "battery_runtime", "ups_load",
    "input_voltage", "output_voltage", "output_current",
    "ups_power", "ups_realpower", "ups_temperature", "ups_efficiency",
}


def _client() -> bigquery.Client:
    s = get_settings()
    return bigquery.Client(project=s.google_cloud_project)


def query_history(
    time_range: str = "24h",
    metric: str = "all",
) -> dict[str, Any]:
    """Query BigQuery for historical UPS readings. Blocking — use via asyncio.to_thread()."""
    s = get_settings()
    tz = ZoneInfo(s.default_timezone)

    delta = _RANGE_MAP.get(time_range)
    if not delta:
        return {"status": "error", "message": f"Invalid range '{time_range}'. Use: 1h, 12h, 24h, 7d", "retryable": False}

    cutoff = (datetime.now(tz) - delta).isoformat()

    if metric == "all":
        cols = "timestamp, " + ", ".join(sorted(_ALLOWED_METRICS))
    elif metric in _ALLOWED_METRICS:
        cols = f"timestamp, {metric}"
    else:
        return {"status": "error", "message": f"Unknown metric '{metric}'", "retryable": False}

    # Downsample for longer ranges to keep chart payload reasonable
    if time_range == "7d":
        # ~1 reading per 5 minutes for 7 days = ~2016 points
        sample_clause = "AND MOD(UNIX_SECONDS(TIMESTAMP(timestamp)), 300) < 15"
    elif time_range == "24h":
        # ~1 reading per minute for 24h = ~1440 points
        sample_clause = "AND MOD(UNIX_SECONDS(TIMESTAMP(timestamp)), 60) < 15"
    else:
        sample_clause = ""

    sql = f"""
        SELECT {cols}
        FROM `{s.google_cloud_project}.{s.ups_dataset}.readings`
        WHERE timestamp >= @cutoff
        {sample_clause}
        ORDER BY timestamp ASC
    """
    params = [bigquery.ScalarQueryParameter("cutoff", "STRING", cutoff)]
    job_config = bigquery.QueryJobConfig(
        query_parameters=params,
        labels={"service": "ups-web"},
    )

    try:
        client = _client()
        rows = client.query(sql, job_config=job_config).result()
        readings = []
        for row in rows:
            d: dict[str, Any] = {}
            for key, val in row.items():
                if isinstance(val, datetime):
                    d[key] = val.astimezone(tz).isoformat()
                else:
                    d[key] = val
            readings.append(d)
        return {"readings": readings, "count": len(readings), "range": time_range}
    except Exception:
        log.error("BigQuery query failed in query_history", exc_info=True)
        return {"status": "error", "message": "Failed to query historical data from BigQuery", "retryable": True}
