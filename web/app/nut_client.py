from __future__ import annotations

import logging
import socket
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.config import get_settings

log = logging.getLogger(__name__)

# Variables we care about for the dashboard, mapped to human-friendly keys
_VAR_MAP: dict[str, str] = {
    "ups.status": "ups_status",
    "battery.charge": "battery_charge",
    "battery.runtime": "battery_runtime",
    "ups.load": "ups_load",
    "input.voltage": "input_voltage",
    "output.voltage": "output_voltage",
    "output.current": "output_current",
    "ups.power": "ups_power",
    "ups.realpower": "ups_realpower",
    "ups.temperature": "ups_temperature",
    "ups.efficiency": "ups_efficiency",
}

_NUMERIC_KEYS = {
    "battery_charge", "battery_runtime", "ups_load",
    "input_voltage", "output_voltage", "output_current",
    "ups_power", "ups_realpower", "ups_temperature", "ups_efficiency",
}


def query_ups() -> dict[str, Any]:
    """Query NUT upsd for current UPS variables. Blocking call — use via asyncio.to_thread()."""
    s = get_settings()
    try:
        return _fetch_vars(s.nut_host, s.nut_port, s.nut_ups_name)
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        log.error("NUT daemon unreachable at %s:%d", s.nut_host, s.nut_port, exc_info=True)
        return {
            "status": "error",
            "message": f"NUT daemon unreachable: {type(e).__name__}",
            "retryable": True,
        }


def _fetch_vars(host: str, port: int, ups_name: str) -> dict[str, Any]:
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.sendall(f"LIST VAR {ups_name}\n".encode())
        data = _read_until_end(sock, ups_name)

    raw = _parse_list_var(data, ups_name)
    result: dict[str, Any] = {}
    for nut_var, key in _VAR_MAP.items():
        if nut_var in raw:
            val = raw[nut_var]
            if key in _NUMERIC_KEYS:
                try:
                    result[key] = float(val)
                except ValueError:
                    result[key] = val
            else:
                result[key] = val

    tz = ZoneInfo(get_settings().default_timezone)
    result["timestamp"] = datetime.now(tz).isoformat()
    return result


def _read_until_end(sock: socket.socket, ups_name: str) -> str:
    end_marker = f"END LIST VAR {ups_name}"
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
        if end_marker.encode() in buf:
            break
    return buf.decode("utf-8", errors="replace")


def _parse_list_var(data: str, ups_name: str) -> dict[str, str]:
    """Parse NUT LIST VAR response into {variable_name: value}."""
    result: dict[str, str] = {}
    prefix = f"VAR {ups_name} "
    for line in data.splitlines():
        line = line.strip()
        if not line.startswith(prefix):
            continue
        rest = line[len(prefix):]
        parts = rest.split(" ", 1)
        if len(parts) == 2:
            var_name = parts[0]
            value = parts[1].strip('"')
            result[var_name] = value
    return result
