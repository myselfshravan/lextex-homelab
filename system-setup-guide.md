# ASUS-VivoBookS15 System Setup Guide

_Comprehensive guide to the OpenClaw server setup - From Scratch to Production_
_Last Updated: March 1, 2026_

---

## Table of Contents

1. [Complete Setup Guide (From Scratch)](#complete-setup-guide-from-scratch)
   - [Windows & WSL2 Configuration](#windows--wsl2-configuration)
   - [Ubuntu Base Setup](#ubuntu-base-setup)
   - [System Services Configuration](#system-services-configuration)
   - [Application Setup](#application-setup)
   - [Auto-Start Configuration](#auto-start-configuration)
2. [System Overview](#system-overview)
3. [Network Configuration](#network-configuration)
4. [Tailscale VPN Setup](#tailscale-vpn-setup)
5. [Cloudflare Tunnel Setup](#cloudflare-tunnel-setup)
6. [SSH Access](#ssh-access)
7. [OpenClaw AI Agent](#openclaw-ai-agent)
8. [Klydo MCP Server](#klydo-mcp-server)
9. [Health Monitoring](#health-monitoring)
10. [Remote Access Comparison](#remote-access-comparison)
11. [Troubleshooting](#troubleshooting)
12. [Migration Guide](#migration-guide)

---

## Complete Setup Guide (From Scratch)

This section documents the complete setup process for recreating this server on a new machine or VM.

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Windows 11                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              WSL2 (Ubuntu 24.04.3 LTS)                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │   systemd (system + user)                       │  │  │
│  │  │   ┌────────────┐ ┌────────────┐ ┌────────────┐  │  │  │
│  │  │   │ tailscaled │ │openclaw   │ │cloudflared │  │  │  │
│  │  │   │            │ │gateway    │ │            │  │  │  │
│  │  │   └────────────┘ └────────────┘ └────────────┘  │  │  │
│  │  │   ┌────────────┐ ┌────────────┐                 │  │  │
│  │  │   │    ssh     │ │  health    │                 │  │  │
│  │  │   │            │ │  server    │                 │  │  │
│  │  │   └────────────┘ └────────────┘                 │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Task Scheduler: WSL2 Auto-Start                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Hardware Requirements

| Component | Minimum | Recommended | Current System |
|-----------|---------|-------------|----------------|
| RAM | 8 GB | 16 GB | 16 GB (12 GB to WSL) |
| CPU | 4 cores | 8+ cores | Intel i5-12500H (12 cores) |
| Storage | 50 GB | 100+ GB SSD | 251 GB |
| OS | Windows 11 | Windows 11 22H2+ | Windows 11 with WSL2 |

---

### Windows & WSL2 Configuration

#### 1. Install WSL2 on Windows

**Open PowerShell as Administrator** and run:

```powershell
# Enable WSL
wsl --install

# Or specify Ubuntu 24.04
wsl --install -d Ubuntu-24.04

# Restart Windows when prompted
```

After restart, complete the Ubuntu setup (create user `lextex`).

#### 2. Configure WSL2 Resource Limits

**Create `.wslconfig` on Windows** (PowerShell):

```powershell
notepad $env:USERPROFILE\.wslconfig
```

**Add the following configuration**:

```ini
[wsl2]
# Allocate 12GB to WSL (adjust based on your physical RAM)
memory=12GB

# Use more CPU cores (your CPU may have more or less)
processors=12

# Increase swap size for memory pressure
swap=4GB

# Disable memory reclaiming (prevents services from dying)
memoryReclaim=false

# Enable systemd (default in newer WSL2)
boot=systemd

# Enable nested virtualization (for running VMs in WSL)
nestedVirtualization=true
```

**Restart WSL** to apply changes:

```powershell
wsl --shutdown
# Then reopen your WSL terminal
```

**Verify the new RAM allocation** (in WSL):

```bash
free -h
```

You should see ~12GB total memory instead of default 7-8GB.

#### 3. Enable WSL2 Auto-Start on Windows Boot

**Open Task Scheduler** (Windows):

```powershell
taskschd.msc
```

**Create a new task**:

1. Right-click **Task Scheduler Library** → **Create Task**
2. **General tab**:
   - Name: `WSL2 Auto-Start`
   - Select **Run whether user is logged in or not**
   - Check **Do not store password**
   - Check **Run with highest privileges**

3. **Triggers tab**:
   - Click **New** → **At startup**
   - Set delay to **30 seconds**

4. **Actions tab**:
   - Click **New** → **Start a program**
   - Program: `C:\Windows\System32\wsl.exe`
   - Arguments: (leave empty)

5. **Conditions tab**:
   - Uncheck **Start the task only if the computer is on AC power**

6. **Settings tab**:
   - Check **Allow task to be run on demand**
   - Check **Run task as soon as possible after a scheduled start is missed**

Click **OK** and enter Windows password if prompted.

**Test the task**:

```powershell
# Right-click the task → Run
# Or in PowerShell:
schtasks /Run /TN "WSL2 Auto-Start"
```

---

### Ubuntu Base Setup

#### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### 2. Verify systemd is enabled

```bash
systemctl --user
echo $?
# Should return 0 (success)
```

If not enabled, add to `/etc/wsl.conf`:

```bash
sudo bash -c 'cat > /etc/wsl.conf << EOF
[boot]
systemd=true
EOF'
```

Then restart WSL from PowerShell: `wsl --shutdown`

#### 3. Install essential packages

```bash
# Essential tools
sudo apt install -y curl wget git vim htop net-tools unzip build-essential

# Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Node.js and npm (using NodeSource)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# SSH server
sudo apt install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
```

#### 4. Configure global npm packages

```bash
# Create directory for global packages
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'

# Add to PATH in .bashrc
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

---

### System Services Configuration

#### 1. Tailscale VPN Setup

**Install Tailscale**:

```bash
# Add Tailscale's GPG key and repository
curl -fsSL https://tailscale.com/install.sh | sh
```

**Authenticate and connect**:

```bash
sudo tailscale up
```

This will provide a URL to authenticate in your browser.

**Enable Tailscale SSH** (recommended for keyless access):

```bash
sudo tailscale up --ssh
```

**Verify Tailscale is running**:

```bash
tailscale status
```

**Service files**:
- System service: `/lib/systemd/system/tailscaled.service`
- State: `/var/lib/tailscale/tailscaled.state`

---

#### 2. Cloudflare Tunnel Setup

**Download and install cloudflared**:

```bash
# Download the latest version
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install
sudo dpkg -i cloudflared-linux-amd64.deb
```

**Create a new tunnel** (or use existing):

```bash
# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create droidvm-tunnel

# Note the tunnel ID from output
# Example: f20f29c9-edc1-4039-b2f5-0442c865c9cc
```

**Create tunnel configuration**:

```bash
sudo mkdir -p /etc/cloudflared
sudo vim /etc/cloudflared/config.yml
```

**Add the configuration**:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /etc/cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: ssh.droidvm.dev
    service: ssh://localhost:22
  - hostname: health.droidvm.dev
    service: http://localhost:8080
  - hostname: openclaw.droidvm.dev
    service: http://localhost:18789
  - hostname: klydo-mcp.droidvm.dev
    service: http://localhost:8000
  - service: http_status:404  # Catch-all
```

**Move credentials file**:

```bash
sudo mv ~/.cloudflared/YOUR_TUNNEL_ID.json /etc/cloudflared/
sudo chmod 600 /etc/cloudflared/YOUR_TUNNEL_ID.json
```

**Configure DNS routes**:

```bash
cloudflared tunnel route dns droidvm-tunnel ssh.droidvm.dev
cloudflared tunnel route dns droidvm-tunnel health.droidvm.dev
cloudflared tunnel route dns droidvm-tunnel openclaw.droidvm.dev
cloudflared tunnel route dns droidvm-tunnel klydo-mcp.droidvm.dev
```

**Install as system service**:

```bash
sudo cloudflared service install
```

**Create systemd service file** `/etc/systemd/system/cloudflared.service`:

```ini
[Unit]
Description=cloudflared
After=network-online.target
Wants=network-online.target
# Wait for user systemd session and OpenClaw gateway
Requires=user@1000.service

[Service]
TimeoutStartSec=60
Type=notify
ExecStart=/usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

---

#### 3. Health Monitoring Service

**Create the health server script** `~/health_server.py`:

```bash
cat > ~/health_server.py << 'HEALTH_EOF'
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
    with open('/proc/uptime', 'r') as f:
        uptime_sec = float(f.read().split()[0])
    days = int(uptime_sec // 86400)
    hours = int((uptime_sec % 86400) // 3600)
    minutes = int((uptime_sec % 3600) // 60)
    return f"{days}d {hours}h {minutes}m"

def get_load():
    with open('/proc/loadavg', 'r') as f:
        load = f.read().split()[:3]
    return {"1m": float(load[0]), "5m": float(load[1]), "15m": float(load[2])}

def get_memory():
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
    services = {
        "ssh": check_service_status("ssh"),
        "tailscaled": check_service_status("tailscaled"),
        "cloudflared": check_service_status("cloudflared"),
        "openclaw-gateway": check_openclaw_service(),
        "health-server": {"running": True, "enabled": True}
    }
    return services

def check_service_status(name):
    active = check_service_active(name)
    enabled = check_service_enabled(name)
    return {
        "running": active,
        "enabled": enabled,
        "status": "active" if active else "inactive"
    }

def check_service_active(name):
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', name],
            capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def check_service_enabled(name):
    try:
        result = subprocess.run(
            ['systemctl', 'is-enabled', name],
            capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip() == 'enabled'
    except:
        return False

def check_openclaw_service():
    try:
        result = subprocess.run(
            ['systemctl', '--user', 'is-active', 'openclaw-gateway'],
            capture_output=True, text=True, timeout=2,
            env={**os.environ, 'XDG_RUNTIME_DIR': f'/run/user/{os.getuid()}'}
        )
        active = result.stdout.strip() == 'active'

        proc_result = subprocess.run(['pgrep', '-f', 'openclaw-gateway'], capture_output=True)
        process_running = proc_result.returncode == 0

        return {
            "running": active and process_running,
            "enabled": True,
            "status": "active" if active else "inactive",
            "service_type": "user"
        }
    except Exception as e:
        return {"running": False, "enabled": False, "status": f"error: {str(e)}"}

def check_openclaw_detailed():
    result = {
        "port": OPENCLAW_PORT,
        "listening": False,
        "gateway_reachable": False,
        "api_healthy": False,
        "response_time_ms": None,
        "error": None
    }

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
            content = response.read(1000).decode('utf-8', errors='ignore')
            result["api_healthy"] = 'OpenClaw' in content or 'openclaw' in content.lower()
    except Exception as e:
        result["error"] = f"HTTP request failed: {str(e)}"

    return result

def get_connectivity():
    result = {"dns_working": False, "external_reachable": False, "checks": []}
    dns_ok = False

    for name, host, port in EXTERNAL_CHECKS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            reachable = sock.connect_ex((host, port)) == 0
            sock.close()

            result["checks"].append({
                "name": name, "host": host, "port": port, "reachable": reachable
            })
            if reachable and port == 53:
                dns_ok = True
        except Exception as e:
            result["checks"].append({
                "name": name, "host": host, "port": port, "error": str(e)
            })

    result["dns_working"] = dns_ok
    result["external_reachable"] = dns_ok
    return result

def check_readiness():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        gateway_ready = sock.connect_ex(('127.0.0.1', OPENCLAW_PORT)) == 0
        sock.close()
        return gateway_ready
    except:
        return False

def run_server(port=8080):
    server = HTTPServer(('127.0.0.1', port), HealthHandler)
    print(f"Enhanced health server running on http://127.0.0.1:{port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
HEALTH_EOF
```

**Make it executable**:

```bash
chmod +x ~/health_server.py
```

**Create systemd service** `/etc/systemd/system/health-server.service`:

```bash
sudo bash -c 'cat > /etc/systemd/system/health-server.service << EOF
[Unit]
Description=Enhanced Health Check API Server
After=network.target openclaw-gateway.service
Wants=openclaw-gateway.service

[Service]
Type=simple
User=lextex
ExecStart=/usr/bin/python3 /home/lextex/health_server.py
Restart=always
RestartSec=10
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
EOF'
```

**Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable health-server
sudo systemctl start health-server
```

**Test the health endpoint**:

```bash
curl http://localhost:8080/health | jq .
```

---

### Application Setup

#### 1. OpenClaw AI Agent

**Install OpenClaw globally via npm**:

```bash
npm install -g openclaw
```

**Initialize OpenClaw**:

```bash
openclaw init
```

**Configure OpenClaw**:

```bash
# Set gateway port
openclaw config set gateway.port 18789

# Set auth token
openclaw config set gateway.auth.token YOUR_TOKEN_HERE

# Enable Tailscale bypass
openclaw config set gateway.allowTailscale true
```

**Create user systemd service** `~/.config/systemd/user/openclaw-gateway.service`:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/openclaw-gateway.service << EOF
[Unit]
Description=OpenClaw Gateway (v2026.2.26)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/node /home/lextex/.npm-global/lib/node_modules/openclaw/dist/index.js gateway --port 18789
Restart=always
RestartSec=5
KillMode=process
Environment="GROQ_API_KEY=your_api_key_here"
Environment="PYTHONUNBUFFERED=1"
Environment="UV_CACHE_DIR=/home/lextex/.uv/cache"
Environment="HOME=/home/lextex"
Environment="TMPDIR=/tmp"
Environment="OPENCLAW_GATEWAY_PORT=18789"
Environment="OPENCLAW_GATEWAY_TOKEN=your_token_here"
Environment="OPENCLAW_SYSTEMD_UNIT=openclaw-gateway.service"

[Install]
WantedBy=default.target
EOF
```

**Enable and start the user service**:

```bash
systemctl --user daemon-reload
systemctl --user enable openclaw-gateway
systemctl --user start openclaw-gateway
```

**Enable user services to persist** (important for WSL):

```bash
sudo loginctl enable-linger lextex
```

This allows user systemd services to run even when the user is not logged in.

---

#### 2. Klydo MCP Server

**Install klydo-mcp**:

```bash
pip install --user klydo-mcp
```

**Create HTTP wrapper script** `~/klydo-mcp-http.py`:

```bash
cat > ~/klydo-mcp-http.py << 'MCP_EOF'
#!/usr/bin/env python3
"""HTTP wrapper for klydo-mcp server."""
import sys
import os

# Add site-packages to path
sys.path.insert(0, '/home/lextex/.local/lib/python3.12/site-packages')

# Load API token from secure file
with open('/home/lextex/.klydo-mcp-token', 'r') as f:
    token = f.read().strip()
os.environ['KLYDO_KLYDO_API_TOKEN'] = token

# Set other environment variables
os.environ.update({
    'KLYDO_DEFAULT_SCRAPER': 'klydo',
    'KLYDO_REQUEST_TIMEOUT': '30',
    'KLYDO_CACHE_TTL': '3600',
    'KLYDO_REQUESTS_PER_MINUTE': '30',
    'KLYDO_DEBUG': 'true',
})

# Import and run with HTTP transport
from klydo.server import mcp

if __name__ == '__main__':
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
MCP_EOF

chmod +x ~/klydo-mcp-http.py
```

**Create API token file**:

```bash
echo "your_klydo_api_token_here" > ~/.klydo-mcp-token
chmod 600 ~/.klydo-mcp-token
```

**Create systemd service** `/etc/systemd/system/klydo-mcp.service`:

```bash
sudo bash -c 'cat > /etc/systemd/system/klydo-mcp.service << EOF
[Unit]
Description=Klydo MCP Server (HTTP Transport)
After=network.target
Wants=network.target

[Service]
Type=simple
User=lextex
WorkingDirectory=/home/lextex
Environment="KLYDO_DEFAULT_SCRAPER=klydo"
Environment="KLYDO_REQUEST_TIMEOUT=30"
Environment="KLYDO_CACHE_TTL=3600"
Environment="KLYDO_REQUESTS_PER_MINUTE=30"
Environment="KLYDO_DEBUG=true"
ExecStart=/usr/bin/python3 /home/lextex/klydo-mcp-http.py
Restart=always
RestartSec=10
TimeoutStartSec=30
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF'
```

**Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable klydo-mcp
sudo systemctl start klydo-mcp
```

---

### Auto-Start Configuration

#### Service Dependency Chain

The services are configured with the following dependency order:

```
Windows Boot
    ↓
WSL2 Auto-Start (Task Scheduler)
    ↓
systemd (system + user)
    ↓
┌─────────────┬─────────────┐
│ System Services           │
│ ├─ ssh                    │
│ ├─ tailscaled             │
│ ├─ health-server (waits for openclaw-gateway) │
│ └─ cloudflared (waits for user@1000.service) │
└─────────────┴─────────────┘
    ↓
User Services (via `loginctl enable-linger`)
    ↓
├─ openclaw-gateway
└─ other user services
```

#### Service Startup Order

1. **Windows Task Scheduler** starts WSL2 on boot
2. **systemd** starts system services:
   - `ssh` - immediate start
   - `tailscaled` - immediate start
   - `user@1000.service` - starts user systemd session
   - `cloudflared` - waits for `user@1000.service`
3. **User systemd** starts:
   - `openclaw-gateway`
4. **health-server** waits for `openclaw-gateway` before starting

#### Verify Auto-Start Works

```bash
# Check all services are running
systemctl status ssh
systemctl status tailscaled
sudo systemctl status cloudflared
systemctl --user status openclaw-gateway
sudo systemctl status health-server

# Check health endpoint
curl http://localhost:8080/health | jq .overall_healthy
```

---

## System Overview

### Hardware
- **Device**: ASUS-VivoBookS15 (Old laptop repurposed as server)
- **OS**: Ubuntu 24.04.3 LTS on WSL2
- **Kernel**: Linux 6.6.87.2-microsoft-standard-WSL2
- **Windows User**: Shravan
- **WSL User**: `lextex` (UID: 1000)
- **Hostname**: `ASUS-VivoBookS15`

### WSL2 Resources (Configured in `.wslconfig`)
| Resource | Configured | Current Usage |
|----------|-----------|---------------|
| RAM | 12 GB | ~2-3 GB typical |
| CPUs | 12 cores | All available |
| Swap | 4 GB | Minimal usage |
| Disk | 251 GB | ~18 GB used |

### Key Services Running

| Service | Type | Port | Purpose |
|---------|------|------|---------|
| OpenClaw Gateway | User systemd | 18789 | AI agent control interface |
| SSH Server | System systemd | 22 | Remote shell access |
| Tailscale | System systemd | 41641 | VPN access |
| Cloudflared | System systemd | - | Public tunnel access |
| Health API | System systemd | 8080 (localhost) | System health monitoring |
| Klydo MCP | System systemd | 8000 (localhost) | Fashion product search |

---

## System Overview

### Hardware
- **Device**: ASUS-VivoBookS15 (Old laptop repurposed as server)
- **OS**: Linux on WSL2 (Windows Subsystem for Linux 2)
- **User**: `lextex`
- **Hostname**: `ASUS-VivoBookS15`

### Key Services Running

| Service | Status | Port | Purpose |
|---------|--------|------|---------|
| OpenClaw Gateway | ✅ Running | 18789 (all interfaces) | AI agent control interface |
| SSH Server | ✅ Active | 22 (all interfaces) | Remote shell access |
| Tailscale | ✅ Running | 41641 | VPN access |
| Cloudflared | ✅ Running | - | Public tunnel access |
| Health API | ✅ Running | 8080 (localhost) | System health monitoring |

---

## Network Configuration

### Network Interfaces

```
Interface        IP Address              Type
-----------      ----------------        ----------
lo               127.0.0.1/8            Loopback
eth0             172.24.34.250/20       WSL2 NAT (internal)
tailscale0       100.85.179.13/32       Tailscale VPN
```

### Port Bindings

| Port | Interface | Service | Access |
|------|-----------|---------|--------|
| 22 | 0.0.0.0 (all) | SSH | Local + Tailscale + Cloudflare ✅ |
| 8080 | 127.0.0.1 | Health API | Cloudflare ✅ |
| 18789 | 0.0.0.0 (all) | OpenClaw Gateway | Tailscale + Cloudflare ✅ |

---

## Tailscale VPN Setup

### Current Status
- **Status**: ✅ Active and running
- **Tailscale IP**: 100.85.179.13
- **Hostname in Tailnet**: `asus-vivobooks15-1` (droidvmtailscale@)

### Devices in Tailnet

| Device | Tailscale IP | OS | Status |
|--------|--------------|-------|--------|
| asus-vivobooks15-1 (this machine) | 100.85.179.13 | Linux | - |
| asus-vivobooks15 | 100.113.165.69 | Windows | - |
| shravans-m3-pro | 100.64.16.69 | macOS | Active (direct) |
| vivo-v2158 | 100.94.102.37 | Android | Offline (2d ago |

### SSH via Tailscale

**Current State**: Tailscale is configured but **Tailscale SSH is NOT enabled**.

To enable Tailscale SSH (allows SSH without keys):
```bash
sudo tailscale up --ssh
```

**Manual SSH via Tailscale IP** (requires SSH keys or password):
```bash
ssh lextex@100.85.179.13
```

**From another Tailscale device by hostname**:
```bash
ssh lextex@asus-vivobooks15-1
```

### Enabling Tailscale SSH (Recommended)

Tailscale SSH provides secure, keyless authentication within your tailnet:

```bash
# Enable Tailscale SSH
sudo tailscale up --ssh

# Verify it's enabled
tailscale status
```

Once enabled, any device in your tailnet can SSH without keys:
```bash
ssh lextex@asus-vivobooks15-1
# Or by IP:
ssh lextex@100.85.179.13
```

---

## Cloudflare Tunnel Setup

### Configuration Details

| Setting | Value |
|---------|-------|
| Tunnel Name | `droidvm-tunnel` |
| Tunnel ID | `f20f29c9-edc1-4039-b2f5-0442c865c9cc` |
| Domain | `droidvm.dev` |
| Config File | `/etc/cloudflared/config.yml` |
| Credentials | `/etc/cloudflared/f20f29c9-edc1-4039-b2f5-0442c865c9cc.json` |

### Current Status
✅ **Running as a system service**

The tunnel has 4 active connections to Cloudflare edge servers (Mumbai/Bangalore, India). The service starts automatically on boot.

### Public Domains

| Domain | Service | URL | Purpose |
|--------|---------|-----|---------|
| `ssh.droidvm.dev` | SSH (port 22) | `ssh lextex@ssh.droidvm.dev` | Remote shell access |
| `health.droidvm.dev` | Health API | https://health.droidvm.dev | System health monitoring |
| `openclaw.droidvm.dev` | OpenClaw Dashboard | https://openclaw.droidvm.dev | AI agent control interface |
| `klydo-mcp.droidvm.dev` | Klydo MCP Server | https://klydo-mcp.droidvm.dev/mcp | Fashion product search MCP |

### Ingress Rules

```yaml
ingress:
  - hostname: ssh.droidvm.dev
    service: ssh://localhost:22
  - hostname: health.droidvm.dev
    service: http://localhost:8080
  - hostname: openclaw.droidvm.dev
    service: http://localhost:18789
  - hostname: klydo-mcp.droidvm.dev
    service: http://localhost:8000
  - hostname: www.droidvm.dev
    service: http_status:404
  - service: http_status:404  # Catch-all
```

### Managing the Cloudflare Tunnel

The tunnel is installed as a system service and starts automatically on boot.

**Check tunnel status**:
```bash
# View tunnel info and connections
cloudflared tunnel info droidvm-tunnel

# Check service status
sudo systemctl status cloudflared
```

**Restart tunnel** (if needed):
```bash
sudo systemctl restart cloudflared
```

**Stop tunnel**:
```bash
sudo systemctl stop cloudflared
```

**Disable auto-start on boot**:
```bash
sudo systemctl disable cloudflared
```

### Access via Cloudflare Tunnel

Once the tunnel is running, you can SSH without VPN:

```bash
# Direct SSH through tunnel
ssh lextex@ssh.droidvm.dev

# Or using jump proxy
ssh -J ssh.droidvm.dev lextex@localhost
```

### Adding More Services

To expose additional services (web servers, APIs, etc.), edit `~/.cloudflared/config.yml`:

```yaml
ingress:
  - hostname: ssh.droidvm.dev
    service: ssh://localhost:22
  - hostname: openclaw.droidvm.dev
    service: http://localhost:18789  # OpenClaw web UI
  - hostname: app.droidvm.dev
    service: http://localhost:3000  # Example web app
  - service: http_status:404  # Catch-all
```

Then update DNS:
```bash
cloudflared tunnel route dns droidvm-tunnel openclaw.droidvm.dev
cloudflared tunnel route dns droidvm-tunnel app.droidvm.dev
```

Restart the tunnel after configuration changes.

---

## SSH Access

### SSH Service Status

| Setting | Value |
|---------|-------|
| Service | ✅ Active (running) |
| Port | 22 (all interfaces: 0.0.0.0) |
| Config | `/etc/ssh/sshd_config` |
| Password Auth | ✅ Enabled (iPhone Shortcuts compatible) |

### Current Authentication

✅ **Password authentication enabled** - You can log in with:
- **Password**: Your system password (works with iPhone Shortcuts)
- **SSH keys** (if set up): More secure, passwordless login
- **Tailscale SSH** (if enabled): Keyless access within tailnet

### Setting Up SSH Keys (Optional, but recommended)

### Setting Up SSH Keys (Recommended)

**On your local machine** (the one you'll connect FROM):
```bash
# Generate SSH key pair (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to the server
ssh-copy-id lextex@100.85.179.13  # Via Tailscale IP
# OR
ssh-copy-id lextex@ssh.droidvm.dev  # Via Cloudflare tunnel (when running)
```

**Manual key copy** (if ssh-copy-id doesn't work):
```bash
# On local machine, display your public key
cat ~/.ssh/id_ed25519.pub

# On the server (ASUS-VivoBookS15):
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Testing SSH Access

```bash
# Test local SSH
ssh lextex@localhost

# Test via Tailscale IP
ssh lextex@100.85.179.13

# Test via Cloudflare tunnel (when running)
ssh lextex@ssh.droidvm.dev

# Test via Tailscale hostname
ssh lextex@asus-vivobooks15-1
```

---

## OpenClaw AI Agent

### Overview
- **Name**: Lexi
- **Version**: v2026.2.1
- **Purpose**: Autonomous AI agent running locally

### Services Running

| Service | Port | Status | Access |
|---------|------|--------|--------|
| openclaw-gateway | 18789 | ✅ Running | All interfaces |
| openclaw (core) | - | ✅ Running | - |
| openclaw-logs | - | ✅ Running | - |

### Accessing OpenClaw

**Public Dashboard (HTTPS)**:
```
https://openclaw.droidvm.dev
```

**Via Tailscale**:
```
http://100.85.179.13:18789
```

**Local**:
```bash
# Access from the machine itself
xdg-open http://127.0.0.1:18789

# Or via CLI (opens browser)
openclaw dashboard
```

**Authentication**:
- Dashboard uses token-based authentication
- Token: `0c646ff6ea22ea9ba106f182e0d63495bead69a26a238385`
- With `allowTailscale: true` in config, Tailscale access should work without token
- Get token: `openclaw config get gateway.auth.token`

### Device Pairing (First Time Setup)

When you first access the OpenClaw dashboard, you'll see **"Disconnected - pairing required"**. This is a security feature that requires explicit approval for new devices.

**To pair your browser:**

1. Open the dashboard at https://openclaw.droidvm.dev
2. The dashboard will show a pairing request is pending
3. From the server terminal, approve the device:
   ```bash
   # List pending pairing requests
   openclaw devices list

   # Approve the device (use the request ID from pending list)
   openclaw devices approve <request-id>
   ```
4. Refresh the dashboard and click **Connect**

**Example**:
```bash
# Check for pending requests
openclaw devices list

# Output shows:
# Pending (1)
# ┌──────────────┬─────────┬─────────┬─────────┬────────┬────────┐
# │ Request      │ Device  │ Role    │ IP      │ Age    │ Flags  │
# ├──────────────┼─────────┼─────────┼─────────┼────────┼────────┤
# │ bd71ddbc-... │ <hash>  │ operator│         │ 3m ago │        │
# └──────────────┴─────────┴─────────┴─────────┴────────┴────────┘

# Approve it
openclaw devices approve bd71ddbc-8867-47e3-b782-9e6e892037ea

# Output: Approved <device-hash>
```

**After pairing**, the dashboard will show:
- **Status**: Connected
- **Uptime**: How long the gateway has been running
- **Last Channels Refresh**: When channels were last updated

**Messaging Platforms**:
- **WhatsApp**: Bot named Lexi, DM from +919945332995
- **Telegram**: Bot configured, user ID 1798234105

**Mention Patterns**: `lexi`, `@lexi`, `hey lexi`, `Lexi`

### AI Models Configured

| Provider | Model | Type |
|----------|-------|------|
| Zai (Primary) | glm-4.7 | Cloud API |
| Groq | llama-3.1-8b-instant | Free tier |
| Ollama | llama3.2:1b | Local (localhost:11434) |

### Configuration Files

- **Config**: `~/.openclaw/openclaw.json`
- **Workspace**: `~/.openclaw/workspace/`
- **Skills**: `~/.openclaw/skills/`
- **Logs**: Available via openclaw-logs service

### Health Monitoring

#### Enhanced Health API (✅ Running)

A comprehensive health monitoring API is available at `https://health.droidvm.dev`:

**Health Endpoint**: `/health`
```json
{
  "host": "ASUS-VivoBookS15",
  "status": "healthy",
  "timestamp": 1771498597,
  "uptime": "0d 0h 8m",
  "load": {"1m": 0.0, "5m": 0.19, "15m": 0.16},
  "memory": {
    "total_mb": 7752,
    "used_mb": 2595,
    "available_mb": 5157,
    "usage_pct": 33.5
  },
  "disk": {
    "total_gb": 250.9,
    "used_gb": 13.2,
    "available_gb": 224.9,
    "usage_pct": 6.0
  },
  "services": {
    "ssh": {"running": true, "enabled": true, "status": "active"},
    "tailscaled": {"running": true, "enabled": true, "status": "active"},
    "cloudflared": {"running": true, "enabled": true, "status": "active"},
    "openclaw-gateway": {
      "running": true,
      "enabled": true,
      "status": "active",
      "service_type": "user"
    }
  },
  "connectivity": {
    "dns_working": true,
    "external_reachable": true,
    "checks": [
      {"name": "Google DNS", "host": "8.8.8.8", "port": 53, "reachable": true},
      {"name": "Cloudflare DNS", "host": "1.1.1.1", "port": 53, "reachable": true}
    ]
  },
  "openclaw": {
    "port": 18789,
    "listening": true,
    "gateway_reachable": true,
    "api_healthy": true,
    "response_time_ms": 77.49
  },
  "overall_healthy": true
}
```

**Features**:
- ✅ System metrics: uptime, load, memory, disk
- ✅ Service status: SSH, Tailscale, Cloudflared, OpenClaw (with enabled/running state)
- ✅ OpenClaw gateway detailed health: port listening, HTTP reachable, API healthy, response time
- ✅ External connectivity checks: DNS servers (Google DNS, Cloudflare DNS)
- ✅ Overall health aggregation: `overall_healthy` field
- ✅ Readiness endpoint: `/ready` for Kubernetes-style probes

**Quick Checks**:
```bash
# Overall health
curl -s https://health.droidvm.dev | jq '.overall_healthy'

# OpenClaw gateway status
curl -s https://health.droidvm.dev | jq '.openclaw'

# External connectivity
curl -s https://health.droidvm.dev | jq '.connectivity'

# Readiness check
curl -s http://localhost:8080/ready
```

#### Health Check Script

A simple bash script is also available at `~/health.sh` for quick terminal checks.

---

## Remote Access Comparison

| Method | Requires VPN | Requires Keys | Public Access | Speed |
|--------|--------------|---------------|---------------|-------|
| **Local** | ❌ No | ⚠️ Maybe | ❌ No | Fastest |
| **Tailscale** | ✅ Yes | ⚠️ Maybe* | ❌ No | Fast |
| **Cloudflare Tunnel** | ❌ No | ⚠️ Maybe | ✅ Yes | Medium |
| **Tailscale SSH** | ✅ Yes | ❌ No | ❌ No | Fast |

\*Unless Tailscale SSH is enabled

### Recommended Setup

**For most secure access (within your trusted network)**:
1. Enable Tailscale SSH for seamless access
2. Use Tailscale IP or hostname

**For public access (from anywhere)**:
1. Start Cloudflare tunnel as a service
2. Set up SSH keys for authentication
3. Access via ssh.droidvm.dev

---

## Troubleshooting

### Cloudflare Tunnel Issues

**Tunnel not running**:
```bash
# Check tunnel status
cloudflared tunnel info droidvm-tunnel

# Start tunnel manually
cloudflared tunnel run droidvm-tunnel

# Check service status (if installed as service)
sudo systemctl status cloudflared
```

**"No active connection" error**:
- The tunnel process is not running
- Start it using one of the methods above

**DNS not resolving**:
```bash
# Check if DNS is configured
cloudflared tunnel route dns droidvm-tunnel ssh.droidvm.dev

# If not, add DNS route:
cloudflared tunnel route dns droidvm-tunnel ssh.droidvm.dev
```

### Tailscale Issues

**Tailscale not connecting**:
```bash
# Check status
tailscale status

# Restart tailscale
sudo systemctl restart tailscaled

# Reauthenticate if needed
sudo tailscale up
```

**Tailscale SSH not working**:
```bash
# Enable SSH
sudo tailscale up --ssh

# Check if enabled
tailscale status | grep -i ssh
```

### SSH Issues

**"Permission denied (publickey)"**:
- No SSH keys configured
- Set up keys as shown in [SSH Access](#ssh-access) section
- OR enable Tailscale SSH for keyless access

**"Connection refused"**:
- Check if SSH is running: `systemctl status ssh`
- Check if port 22 is open: `ss -tlnp | grep :22`

**Can't access OpenClaw web UI from remote**:
- OpenClaw gateway binds to localhost only (security feature)
- Use SSH tunnel: `ssh -L 18789:localhost:18789 lextex@server`
- Access via http://localhost:18789 on your local machine

### General Issues

**Check what services are running**:
```bash
# Check all relevant services
systemctl status ssh
systemctl status tailscaled
sudo systemctl status cloudflared
ps aux | grep openclaw
```

**Check listening ports**:
```bash
ss -tlnp | grep -E ':(22|18789|41641)'
```

**View OpenClaw logs**:
```bash
# OpenClaw logs are handled by the openclaw-logs service
# Check recent logs
journalctl -u openclaw-* -n 50 --no-pager
```

---

## Quick Start: Accessing This Machine

### From Within Your Network (Tailscale - Recommended)

**First-time setup (enable Tailscale SSH)**:
```bash
# On the server (ASUS-VivoBookS15):
sudo tailscale up --ssh
```

**Then from any Tailscale device**:
```bash
ssh lextex@asus-vivobooks15-1
# OR
ssh lextex@100.85.179.13
```

### From Anywhere (Cloudflare Tunnel)

**Start the tunnel** (if not running):
```bash
# On the server:
cloudflared tunnel run droidvm-tunnel

# Or install as service:
sudo cloudflared service install
sudo systemctl start cloudflared
```

**Then from anywhere**:
```bash
ssh lextex@ssh.droidvm.dev
```

### Access OpenClaw Web UI

**From the server itself**:
```bash
xdg-open http://127.0.0.1:18789
```

**From remote (via SSH tunnel)**:
```bash
# On your local machine:
ssh -L 18789:localhost:18789 lextex@100.85.179.13

# Then open browser to: http://localhost:18789
```

---

## Summary

This ASUS-VivoBookS15 has been configured as a robust home server running OpenClaw with comprehensive monitoring and multiple remote access options.

### Robustness Features

**Service Dependency Chain**:
- Cloudflared now waits for OpenClaw gateway before starting
- Health server waits for OpenClaw gateway
- All services configured with automatic restart on failure
- Enhanced health monitoring with OpenClaw API checks and external connectivity

**Enhanced Health Monitoring**:
- OpenClaw gateway health: port listening, HTTP reachable, API healthy, response time
- External connectivity checks: DNS servers (Google DNS, Cloudflare DNS)
- Overall health aggregation: `overall_healthy` field
- Kubernetes-style readiness endpoint at `/ready`

### Auto-Start Configuration

**Windows Boot → WSL2 Auto-Start**:
- Windows Task Scheduler: "WSL2 Auto-Start" task
- Triggers: At system startup (30 second delay)
- Runs: `wsl.exe`
- Result: All services start automatically

**Services that Auto-Start on WSL2 Boot**:
- `tailscaled.service` ✅ (user-level systemd)
- `openclaw-gateway.service` ✅ (user-level systemd)
- `cloudflared.service` ✅ (system-level, waits for user systemd)
- `health-server.service` ✅ (system-level)
- `ssh.service` ✅

### Public Services

| Service | URL | Access |
|---------|-----|--------|
| SSH | `ssh lextex@ssh.droidvm.dev` | Password auth enabled |
| Health API | `https://health.droidvm.dev` | JSON health status |
| OpenClaw Dashboard | `https://openclaw.droidvm.dev` | Token auth (Tailscale bypass) |
| Klydo MCP Server | `https://klydo-mcp.droidvm.dev/mcp` | MCP protocol (HTTP transport) |

**Recommended next steps**:
1. Enable Tailscale SSH for seamless keyless access: `sudo tailscale up --ssh`
2. Set up external monitoring to check `https://health.droidvm.dev` every 5 minutes

---

## Klydo MCP Server

The Klydo MCP (Model Context Protocol) server provides fashion product search and discovery capabilities.

### Overview

- **Package**: klydo-mcp v0.1.6
- **Transport**: HTTP (streamable)
- **Port**: 8000 (localhost only)
- **Public URL**: https://klydo-mcp.droidvm.dev/mcp
- **Service**: `klydo-mcp.service` (systemd)

### Dual Mode Operation

**Local (stdio)**: OpenClaw uses klydo-mcp via stdio transport for local access
**Remote (HTTP)**: External clients access via https://klydo-mcp.droidvm.dev/mcp

Both modes run simultaneously without conflicts.

### Service Management

```bash
# Check status
sudo systemctl status klydo-mcp

# Restart service
sudo systemctl restart klydo-mcp

# View logs
sudo journalctl -u klydo-mcp -n 50 --no-pager

# Test locally
curl -H "Accept: text/event-stream" http://localhost:8000/mcp

# Test publicly
curl -H "Accept: text/event-stream" https://klydo-mcp.droidvm.dev/mcp
```

### Configuration Files

| File | Purpose |
|------|---------|
| `~/klydo-mcp-http.py` | HTTP wrapper script |
| `~/.klydo-mcp-token` | API token (secure, 600 permissions) |
| `/etc/systemd/system/klydo-mcp.service` | systemd service file |

### MCP Tools Available

- `search_products`: Search for fashion products
- `get_product_details`: Get detailed product information
- `get_trending`: Get trending fashion items

---

_Documentation based on system state as of February 22, 2026_

---

## Migration Guide

This section covers migrating this setup to a new system or VM.

### Export Current Configuration

#### 1. Export WSL Configuration

**From PowerShell on Windows**:

```powershell
# Export .wslconfig
copy $env:USERPROFILE\.wslconfig D:\Backup\wslconfig.txt

# List WSL distributions
wsl --list --verbose
```

#### 2. Export System Configuration Files

```bash
# Create backup directory
mkdir -p ~/migration-backup
cd ~/migration-backup

# Export systemd service files
cp /etc/systemd/system/cloudflared.service ./
cp /etc/systemd/system/health-server.service ./
cp /etc/systemd/system/klydo-mcp.service ./
cp ~/.config/systemd/user/openclaw-gateway.service ./

# Export configuration files
cp /etc/cloudflared/config.yml ./
sudo cp /etc/ssh/sshd_config ./

# Export application configs
cp ~/.openclaw/openclaw.json ./
cp -r ~/.openclaw/skills ./openclaw-skills/
cp -r ~/.npm-global/lib/node_modules/openclaw ./openclaw-backup/

# Export scripts
cp ~/health_server.py ./
cp ~/klydo-mcp-http.py ./

# Export tokens (SECURE - store safely)
cp ~/.klydo-mcp-token ./

# Create package list
pip list --user > pip-packages.txt
npm list -g --depth=0 > npm-packages.txt

# Export Tailscale state (optional)
sudo cp /var/lib/tailscale/tailscaled.state ./
```

#### 3. Create Migration Archive

```bash
cd ~
tar -czf migration-backup.tar.gz migration-backup/
```

### Restore on New System

#### 1. Set Up Base System

Follow the [Complete Setup Guide](#complete-setup-guide-from-scratch) sections:
- Windows & WSL2 Configuration
- Ubuntu Base Setup
- System Services Configuration

#### 2. Restore Configuration Files

```bash
# Extract backup
tar -xzf migration-backup.tar.gz
cd migration-backup

# Restore systemd services
sudo cp cloudflared.service /etc/systemd/system/
sudo cp health-server.service /etc/systemd/system/
sudo cp klydo-mcp.service /etc/systemd/system/
mkdir -p ~/.config/systemd/user
cp openclaw-gateway.service ~/.config/systemd/user/

# Restore configurations
sudo cp config.yml /etc/cloudflared/
sudo cp sshd_config /etc/ssh/

# Restore scripts
cp health_server.py ~/
cp klydo-mcp-http.py ~/
chmod +x ~/health_server.py ~/klydo-mcp-http.py

# Restore tokens
cp .klydo-mcp-token ~/
chmod 600 ~/.klydo-mcp-token
```

#### 3. Restore Applications

```bash
# Reinstall npm packages
npm install -g openclaw

# Restore OpenClaw config
mkdir -p ~/.openclaw
cp openclaw.json ~/.openclaw/
cp -r openclaw-skills ~/.openclaw/skills

# Reinstall Python packages
pip install --user klydo-mcp
```

#### 4. Restore Tailscale (Optional)

If you have the Tailscale state file:

```bash
# Stop Tailscale
sudo systemctl stop tailscaled

# Restore state
sudo cp tailscaled.state /var/lib/tailscale/

# Start Tailscale
sudo systemctl start tailscaled
```

Otherwise, re-authenticate:

```bash
sudo tailscale up
sudo tailscale up --ssh
```

#### 5. Restore Cloudflare Tunnel

```bash
# Reinstall cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Login to Cloudflare
cloudflared tunnel login

# Use existing tunnel
cloudflared tunnel run droidvm-tunnel

# Or create new tunnel and update config
```

#### 6. Reload and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable user lingering
sudo loginctl enable-linger lextex

# Start system services
sudo systemctl enable ssh cloudflared health-server klydo-mcp
sudo systemctl start ssh cloudflared health-server klydo-mcp

# Start user services
systemctl --user daemon-reload
systemctl --user enable openclaw-gateway
systemctl --user start openclaw-gateway
```

#### 7. Verify Migration

```bash
# Check all services
systemctl status ssh tailscaled cloudflared health-server klydo-mcp
systemctl --user status openclaw-gateway

# Test health endpoint
curl http://localhost:8080/health | jq .overall_healthy

# Test OpenClaw
curl http://localhost:18789
```

### Migration Checklist

- [ ] Install WSL2 on new system
- [ ] Configure `.wslconfig` for resource limits
- [ ] Set up Windows Task Scheduler for auto-start
- [ ] Install base packages (curl, git, python3, nodejs)
- [ ] Install and configure Tailscale
- [ ] Install and configure Cloudflared
- [ ] Restore SSH configuration
- [ ] Install OpenClaw and restore config
- [ ] Install klydo-mcp and restore token
- [ ] Restore health server script
- [ ] Configure systemd services (system + user)
- [ ] Enable `loginctl enable-linger`
- [ ] Test all services
- [ ] Verify health endpoint
- [ ] Test Cloudflare tunnel access
- [ ] Test Tailscale connectivity

---

## Quick Reference

### Important Paths

| Path | Purpose |
|------|---------|
| `C:\Users\Shravan\.wslconfig` | WSL2 resource configuration |
| `/etc/wsl.conf` | WSL2 systemd enablement |
| `/etc/systemd/system/` | System systemd services |
| `~/.config/systemd/user/` | User systemd services |
| `/etc/cloudflared/` | Cloudflare tunnel config |
| `/var/lib/tailscale/` | Tailscale state |
| `~/.openclaw/` | OpenClaw configuration |

### Important Commands

```bash
# Check WSL resources
free -h
nproc

# Check services
systemctl status ssh tailscaled cloudflared health-server klydo-mcp
systemctl --user status openclaw-gateway

# Check health
curl http://localhost:8080/health | jq .

# Restart services
sudo systemctl restart cloudflared
systemctl --user restart openclaw-gateway

# View logs
sudo journalctl -u cloudflared -f
journalctl --user -u openclaw-gateway -f
```

---

_Documentation last updated: March 1, 2026_
