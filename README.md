# 🤖 ASUS-VivoBookS15 AI Server

> An old laptop, reborn as an AI agent orchestration hub with private VPN access, public tunnel reach, and 24/7 health monitoring.

[![Status](https://img.shields.io/badge/Status-Online-success)](https://health.droidvm.dev)
[![Health](https://img.shields.io/badge/Health-All%20Systems%20Go-brightgreen)](https://health.droidvm.dev)
[![AI](https://img.shields.io/badge/AI-OpenClaw-blue)](https://openclaw.droidvm.dev)
[![Access](https://img.shields.io/badge/Access-Tailscale%20%7C%20Cloudflare-informational)](https://health.droidvm.dev)

---

## The Setup

This is **not your average home server**. It's a WSL2-based AI orchestration platform that:

- 🔄 **Auto-starts on Windows boot** — No manual intervention needed
- 🌐 **Accessible from anywhere** — Private VPN + public tunnel
- 💚 **Self-monitoring** — Health API with connectivity checks
- 🤖 **Runs AI agents** — OpenClaw (Lexi) with web dashboard control
- 🛠️ **Claude Code powered** — AI-assisted development environment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Windows 11                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              WSL2 (Ubuntu 24.04.3 LTS)                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │   systemd (system + user)                       │  │  │
│  │  │                                                  │  │  │
│  │  │   ┌────────────┐  ┌────────────┐  ┌──────────┐ │  │  │
│  │  │   │ OpenClaw   │  │ Health API │  │   Klydo  │ │  │  │
│  │  │   │ Gateway    │  │            │  │   MCP    │ │  │  │
│  │  │   │  (18789)   │  │  (8080)    │  │  (8000)  │ │  │  │
│  │  │   └────────────┘  └────────────┘  └──────────┘ │  │  │
│  │  │                                                  │  │  │
│  │  │   ┌────────────┐  ┌────────────┐                │  │  │
│  │  │   │  SSH       │  │ Tailscale  │                │  │  │
│  │  │   │  (22)      │  │            │                │  │  │
│  │  │   └────────────┘  └────────────┘                │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │   Task Scheduler: WSL2 Auto-Start (30s delay)         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
        ┌─────▼─────┐                 ┌─────▼─────┐
        │ Tailscale │                 │ Cloudflare│
        │   VPN     │                 │  Tunnel   │
        │ (Private) │                 │ (Public)  │
        └───────────┘                 └───────────┘
```

---

## The Stack

| Component | What | How |
|-----------|------|-----|
| **Hardware** | ASUS VivoBook S15 | Intel i5-12500H (12 cores), 16GB RAM |
| **OS** | Ubuntu 24.04.3 LTS | Running on WSL2 (12GB RAM allocated) |
| **AI** | OpenClaw v2026.2.26 | "Lexi" — autonomous AI agent |
| **VPN** | Tailscale | Private mesh network (100.85.179.13) |
| **Tunnel** | cloudflared | Public access via droidvm.dev |
| **Health** | Custom Python API | Real-time monitoring at `/health` |
| **Dev** | Claude Code | AI-powered development CLI |

---

## Services at a Glance

| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| **OpenClaw Gateway** | 18789 | [openclaw.droidvm.dev](https://openclaw.droidvm.dev) | AI agent dashboard |
| **Health API** | 8080 | [health.droidvm.dev](https://health.droidvm.dev) | System monitoring |
| **SSH Server** | 22 | [ssh.droidvm.dev](ssh://ssh.droidvm.dev) | Remote shell |
| **Klydo MCP** | 8000 | [klydo-mcp.droidvm.dev](https://klydo-mcp.droidvm.dev) | Fashion search |
| **Tailscale** | 41641 | `asus-vivobooks15-1` | Private VPN |

---

## Access Your Server

### From Anywhere (Public)

```bash
# SSH via Cloudflare Tunnel
ssh lextex@ssh.droidvm.dev

# Check health status
curl https://health.droidvm.dev | jq .

# Access AI dashboard
open https://openclaw.droidvm.dev
```

### From Your Network (Private via Tailscale)

```bash
# SSH via VPN
ssh lextex@asus-vivobooks15-1
# or by IP:
ssh lextex@100.85.179.13

# Direct access to services
http://100.85.179.13:18789  # OpenClaw
http://100.85.179.13:8080   # Health API
```

---

## Health Monitor

The server runs a custom health monitoring API at [`https://health.droidvm.dev`](https://health.droidvm.dev).

**What it checks:**

- ✅ System uptime & load averages
- ✅ Memory & disk usage
- ✅ Service status (SSH, Tailscale, Cloudflare, OpenClaw)
- ✅ OpenClaw gateway connectivity & response time
- ✅ External connectivity (DNS servers)

**Sample output:**

```json
{
  "host": "ASUS-VivoBookS15",
  "status": "healthy",
  "uptime": "5d 12h 30m",
  "load": {"1m": 0.42, "5m": 0.35, "15m": 0.28},
  "memory": {
    "total_mb": 11750,
    "used_mb": 2847,
    "available_mb": 8903,
    "usage_pct": 24.2
  },
  "overall_healthy": true
}
```

---

## AI Agent: OpenClaw (Lexi)

The server runs **OpenClaw**, an autonomous AI agent that you control via a web dashboard.

**Access:** [`https://openclaw.droidvm.dev`](https://openclaw.droidvm.dev)

**Capabilities:**
- 🧠 Multi-model AI (Zai, Groq, Ollama)
- 💬 Messaging integration (WhatsApp, Telegram)
- 🔌 MCP server support
- 🎯 Custom skills and tools

**First-time setup:**
1. Open the dashboard
2. Approve the device pairing from the server:
   ```bash
   openclaw devices list
   openclaw devices approve <request-id>
   ```

---

## What Makes This Legendary

### 1. WSL2 as a Server Platform
Running a full server stack on WSL2 is unconventional, but it works beautifully:
- **Windows integration** — Auto-start via Task Scheduler
- **Linux power** — Full systemd, containers, native tooling
- **Resource flexibility** — Adjustable RAM/CPU via `.wslconfig`

### 2. Dual Access Layer
```
        ┌─────────────────────────────────────┐
        │                                     │
   ┌────▼────┐                          ┌────▼────┐
   │ Tailscale│                          │Cloudflare│
   │   VPN    │                          │  Tunnel  │
   │(Private) │                          │ (Public) │
   └────┬────┘                          └────┬────┘
        │                                    │
        └──────────────┬─────────────────────┘
                       │
                ┌──────▼──────┐
                │   The Server │
                │   (WSL2)     │
                └─────────────┘
```

- **Tailscale** — Secure, keyless SSH within your tailnet
- **Cloudflare** — Public access from anywhere in the world

### 3. Health-First Design
Every service is monitored:
- **Passive checks** — Is the process running?
- **Active checks** — Can we reach the HTTP endpoint?
- **Dependency checks** — Are required services up first?

The health API even validates **external connectivity** by checking DNS servers.

### 4. Auto-Start Chain
```
Windows Boot
    ↓ (30s delay)
Task Scheduler: wsl.exe
    ↓
WSL2 starts
    ↓
systemd (system + user)
    ↓
┌─────────────┬─────────────┐
│ System Services           │
│ ├─ ssh                    │
│ ├─ tailscaled             │
│ ├─ cloudflared (waits for user@1000) │
│ └─ health-server (waits for openclaw) │
└─────────────┴─────────────┘
    ↓
User Services (via loginctl enable-linger)
    ↓
├─ openclaw-gateway
└─ other user services
```

### 5. Claude Code Integration
Development is AI-assisted:
```bash
# Claude Code runs natively in WSL2
claude-code --help

# Your AI server helps you build on itself
```

---

## Quick Commands

```bash
# Check system health
curl https://health.droidvm.dev | jq .overall_healthy

# SSH into the server
ssh lextex@ssh.droidvm.dev

# Restart OpenClaw
ssh lextex@ssh.droidvm.dev "systemctl --user restart openclaw-gateway"

# View OpenClaw logs
ssh lextex@ssh.droidvm.dev "journalctl --user -u openclaw-gateway -f"

# Check Tailscale status
ssh lextex@ssh.droidvm.dev "tailscale status"

# Tunnel into localhost (port forwarding)
ssh -L 18789:localhost:18789 lextex@ssh.droidvm.dev
# Then open: http://localhost:18789
```

---

## Development

Want to set this up yourself? See the **[Complete Setup Guide](./system-setup-guide.md)** for:

- Windows & WSL2 configuration
- Ubuntu base setup
- Service installation (Tailscale, Cloudflare, OpenClaw)
- Auto-start configuration
- Migration guide

---

## Project Structure

```
~/lextex-docs/
├── README.md                    # This file
└── system-setup-guide.md       # Complete technical guide

/home/lextex/
├── health_server.py             # Health monitoring API
├── klydo-mcp-http.py            # Klydo MCP HTTP wrapper
├── .config/systemd/user/
│   └── openclaw-gateway.service # User-level AI agent service
└── .openclaw/                   # OpenClaw configuration
    ├── openclaw.json
    └── skills/                  # Custom AI skills
```

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| CPU | 4 cores | 8+ cores |
| Storage | 50 GB | 100+ GB SSD |
| OS | Windows 11 | Windows 11 22H2+ |

---

## License

This setup is personal infrastructure. Do what you want with it.

---

## Acknowledgments

- **OpenClaw** — The AI agent framework
- **Tailscale** — The mesh network that just works
- **Cloudflare** — The tunnel that makes public access trivial
- **WSL2** — For making Linux-on-Windows actually usable

---

**Built with ❤️ and too much caffeine**

_Last updated: March 1, 2026_
