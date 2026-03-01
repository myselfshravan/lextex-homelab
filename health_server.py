#!/usr/bin/env python3
"""
Enhanced health check server with comprehensive monitoring.
Checks OpenClaw gateway, external connectivity, and service dependencies.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import time
import socket
from urllib.request import urlopen, Request
from urllib.error import URLError

# Configuration
OPENCLAW_PORT = 18789
EXTERNAL_CHECKS = [
    ("Google DNS", "8.8.8.8", 53),
    ("Cloudflare DNS", "1.1.1.1", 53),
]

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            data = {
                "host": os.uname().nodename,
                "status": "healthy",
                "timestamp": int(time.time()),
                "uptime": get_uptime(),
                "load": get_load(),
                "memory": get_memory(),
                "disk": get_disk(),
                "services": get_services(),
                "connectivity": get_connectivity(),
                "openclaw": check_openclaw_detailed()
            }

            # Overall health check
            all_healthy = all([
                data["services"]["openclaw-gateway"]["running"],
                data["services"]["cloudflared"]["running"],
                data["openclaw"]["gateway_reachable"],
                data["connectivity"]["dns_working"]
            ])
            data["overall_healthy"] = all_healthy

            self.wfile.write(json.dumps(data, indent=2).encode())
        elif self.path == '/ready':
            # Kubernetes-style readiness probe
            ready = check_readiness()
            if ready:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"ready": true}')
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"ready": false}')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def log_message(self, format, *args):
        pass

def get_uptime():
    """Parse uptime from /proc/uptime"""
    with open('/proc/uptime', 'r') as f:
        uptime_sec = float(f.read().split()[0])
    days = int(uptime_sec // 86400)
    hours = int((uptime_sec % 86400) // 3600)
    minutes = int((uptime_sec % 3600) // 60)
    return f"{days}d {hours}h {minutes}m"

def get_load():
    """Get load average from /proc/loadavg"""
    with open('/proc/loadavg', 'r') as f:
        load = f.read().split()[:3]
    return {"1m": float(load[0]), "5m": float(load[1]), "15m": float(load[2])}

def get_memory():
    """Get memory info from /proc/meminfo"""
    mem = {}
    with open('/proc/meminfo', 'r') as f:
        for line in f:
            if line.startswith(('MemTotal:', 'MemAvailable:', 'MemFree:')):
                parts = line.split()
                mem[parts[0].rstrip(':')] = int(parts[1])

    total_mb = mem.get('MemTotal', 0) // 1024
    if 'MemAvailable' in mem:
        used_mb = total_mb - (mem['MemAvailable'] // 1024)
    else:
        used_mb = total_mb - (mem.get('MemFree', 0) // 1024)

    return {
        "total_mb": total_mb,
        "used_mb": used_mb,
        "available_mb": total_mb - used_mb,
        "usage_pct": round((used_mb / total_mb) * 100, 1) if total_mb > 0 else 0
    }

def get_disk():
    """Get disk info using df command"""
    try:
        result = subprocess.check_output(['df', '/'], text=True)
        lines = result.split('\n')
        parts = lines[1].split()
        total_gb = round(int(parts[1]) / 1024 / 1024, 1)
        used_gb = round(int(parts[2]) / 1024 / 1024, 1)
        available_gb = round(int(parts[3]) / 1024 / 1024, 1)
        usage_pct = float(parts[4].rstrip('%'))
        return {
            "total_gb": total_gb,
            "used_gb": used_gb,
            "available_gb": available_gb,
            "usage_pct": usage_pct
        }
    except:
        return {"error": "Could not read disk info"}

def get_services():
    """Check status of key services with detailed info"""
    services = {
        "ssh": check_service_status("ssh"),
        "tailscaled": check_service_status("tailscaled"),
        "cloudflared": check_service_status("cloudflared"),
        "openclaw-gateway": check_openclaw_service(),
        "health-server": {"running": True, "enabled": True}
    }
    return services

def check_service_status(name):
    """Check if a systemd service is active and enabled"""
    active = check_service_active(name)
    enabled = check_service_enabled(name)
    return {
        "running": active,
        "enabled": enabled,
        "status": "active" if active else "inactive"
    }

def check_service_active(name):
    """Check if a systemd service is active"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', name],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def check_service_enabled(name):
    """Check if a systemd service is enabled"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-enabled', name],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip() == 'enabled'
    except:
        return False

def check_openclaw_service():
    """Check OpenClaw gateway service status (user-level)"""
    try:
        # Check user-level service
        result = subprocess.run(
            ['systemctl', '--user', 'is-active', 'openclaw-gateway'],
            capture_output=True,
            text=True,
            timeout=2,
            env={**os.environ, 'XDG_RUNTIME_DIR': f'/run/user/{os.getuid()}'}
        )
        active = result.stdout.strip() == 'active'

        # Check if process is running
        proc_result = subprocess.run(
            ['pgrep', '-f', 'openclaw-gateway'],
            capture_output=True
        )
        process_running = proc_result.returncode == 0

        return {
            "running": active and process_running,
            "enabled": True,
            "status": "active" if active else "inactive",
            "service_type": "user"
        }
    except Exception as e:
        return {
            "running": False,
            "enabled": False,
            "status": f"error: {str(e)}"
        }

def check_openclaw_detailed():
    """Comprehensive OpenClaw gateway health check"""
    result = {
        "port": OPENCLAW_PORT,
        "listening": False,
        "gateway_reachable": False,
        "api_healthy": False,
        "response_time_ms": None,
        "error": None
    }

    # Check if port is listening
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result["listening"] = sock.connect_ex(('127.0.0.1', OPENCLAW_PORT)) == 0
        sock.close()
    except Exception as e:
        result["error"] = f"Port check failed: {str(e)}"
        return result

    if not result["listening"]:
        result["error"] = "Port not listening"
        return result

    # Check HTTP connectivity and measure response time
    try:
        start_time = time.time()
        req = Request(
            f'http://127.0.0.1:{OPENCLAW_PORT}/',
            headers={'User-Agent': 'HealthCheck/1.0'}
        )
        with urlopen(req, timeout=5) as response:
            response_time = (time.time() - start_time) * 1000
            result["gateway_reachable"] = response.status == 200
            result["response_time_ms"] = round(response_time, 2)

            # Check if it's serving the OpenClaw UI
            content = response.read(1000).decode('utf-8', errors='ignore')
            result["api_healthy"] = 'OpenClaw' in content or 'openclaw' in content.lower()
    except URLError as e:
        result["error"] = f"HTTP request failed: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result

def get_connectivity():
    """Check external connectivity"""
    result = {
        "dns_working": False,
        "external_reachable": False,
        "checks": []
    }

    dns_ok = False
    for name, host, port in EXTERNAL_CHECKS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            reachable = sock.connect_ex((host, port)) == 0
            sock.close()

            result["checks"].append({
                "name": name,
                "host": host,
                "port": port,
                "reachable": reachable
            })

            if reachable and port == 53:
                dns_ok = True
        except Exception as e:
            result["checks"].append({
                "name": name,
                "host": host,
                "port": port,
                "error": str(e)
            })

    result["dns_working"] = dns_ok
    result["external_reachable"] = dns_ok

    return result

def check_readiness():
    """Kubernetes-style readiness check"""
    try:
        # Check OpenClaw gateway
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        gateway_ready = sock.connect_ex(('127.0.0.1', OPENCLAW_PORT)) == 0
        sock.close()

        return gateway_ready
    except:
        return False

def run_server(port=8080):
    """Start the HTTP server"""
    server = HTTPServer(('127.0.0.1', port), HealthHandler)
    print(f"Enhanced health server running on http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
