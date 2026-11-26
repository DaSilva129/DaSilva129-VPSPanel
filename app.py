#!/usr/bin/env python3
"""VPS Panel : mini tableau de bord de monitoring (CPU, RAM, disque, réseau, températures, GPU)."""
import json
import os
import platform
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psutil

HOST = os.environ.get("PANEL_HOST", "127.0.0.1")
PORT = int(os.environ.get("PANEL_PORT", "8080"))
HTML_FILE = Path(__file__).parent / "index.html"

_net_lock = threading.Lock()
_net_state = {"t": time.time(), "c": psutil.net_io_counters()}


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def get_net_speed():
    """Débit calculé entre deux appels (donc entre deux rafraîchissements)."""
    with _net_lock:
        now = time.time()
        counters = psutil.net_io_counters()
        dt = max(now - _net_state["t"], 1e-6)
        prev = _net_state["c"]
        rx = (counters.bytes_recv - prev.bytes_recv) / dt
        tx = (counters.bytes_sent - prev.bytes_sent) / dt
        _net_state["t"], _net_state["c"] = now, counters
    return {
        "rx_bps": rx,
        "tx_bps": tx,
        "rx_total": counters.bytes_recv,
        "tx_total": counters.bytes_sent,
    }


def get_temps():
    result = {}
    try:
        sensors = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return result  # non supporté sur la plupart des VPS (virtualisés)
    for chip, entries in sensors.items():
        for entry in entries:
            label = f"{chip} {entry.label}".strip() if entry.label else chip
            result[label] = round(entry.current, 1)
    return result


def get_gpus():
    if not shutil.which("nvidia-smi"):
        return []
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=3, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []

    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 5:
            continue
        name, util, mem_used, mem_total, temp = parts
        gpus.append({
            "name": name,
            "util": to_float(util),
            "mem_used": to_float(mem_used),
            "mem_total": to_float(mem_total),
            "temp": to_float(temp),
        })
    return gpus


def get_top_processes(n=5):
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent"]):
        info = p.info
        if info.get("memory_percent"):
            procs.append(info)
    procs.sort(key=lambda i: i["memory_percent"], reverse=True)
    return [
        {"pid": i["pid"], "name": i["name"] or "?", "mem": round(i["memory_percent"], 1)}
        for i in procs[:n]
    ]


def collect():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "uptime_s": time.time() - psutil.boot_time(),
        "cpu": {
            "percent": psutil.cpu_percent(interval=None),
            "count": psutil.cpu_count(),
            "load": list(os.getloadavg()),
        },
        "ram": {"percent": mem.percent, "used": mem.used, "total": mem.total},
        "swap": {"percent": swap.percent, "used": swap.used, "total": swap.total},
        "disk": {"percent": disk.percent, "used": disk.used, "total": disk.total},
        "net": get_net_speed(),
        "temps": get_temps(),
        "gpus": get_gpus(),
        "processes": get_top_processes(),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/metrics":
            body = json.dumps(collect()).encode("utf-8")
            self._send(200, "application/json", body)
        elif path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", HTML_FILE.read_bytes())
        else:
            self._send(404, "text/plain; charset=utf-8", b"Not found")

    def _send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # on évite de polluer les logs à chaque rafraîchissement


if __name__ == "__main__":
    psutil.cpu_percent(interval=None)  # première mesure (la suivante sera exacte)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"VPS Panel lancé sur http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
