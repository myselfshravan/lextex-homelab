# Contributing to lextex-homelab

First off, thanks for taking an interest in this project! While this is primarily a personal infrastructure repository, contributions and suggestions are welcome.

## Types of Contributions

This project welcomes:

- **Bug reports** — If something in the setup guide doesn't work
- **Documentation improvements** — Typos, clarity, formatting
- **Configuration examples** — Additional service configurations
- **Architecture suggestions** — Better ways to organize the stack

## Getting Started

### Setting Up Your Own Homelab

Follow the [Complete Setup Guide](./system-setup-guide.md) to replicate this setup on your own hardware.

### Testing Changes

If you're proposing changes to configuration files:
1. Test in a non-production environment first
2. Ensure services start correctly with `systemctl`
3. Verify health checks pass at `/health`

## Submitting Changes

1. Fork the repository
2. Create a descriptive branch: `git checkout -b feature/improve-health-monitor`
3. Make your changes with clear commit messages
4. Push to your fork: `git push origin feature/improve-health-monitor`
5. Open a pull request

### Commit Message Guidelines

Use conventional commit format:
- `feat: Add monitoring for disk I/O`
- `fix: Correct cloudflared dependency order`
- `docs: Update WSL2 configuration for Windows 11 23H2`
- `refactor: Simplify health check logic`

## Reporting Issues

When reporting issues, include:

- Your OS version (`wsl.exe --version`)
- Ubuntu release (`lsb_release -a`)
- Service logs (`journalctl -u <service-name> -n 50`)
- Steps to reproduce

## Documentation Style

- Use present tense: "Run the command" not "Ran the command"
- Use imperative mood: "Add this line" not "Added this line"
- Include code examples with proper syntax highlighting
- Keep Mermaid diagrams simple and readable

## Project Structure

```
lextex-homelab/
├── README.md                    # Main overview
├── CONTRIBUTING.md              # This file
├── LICENSE                      # MIT License
├── system-setup-guide.md        # Technical implementation
├── health_server.py             # Health monitoring code
├── klydo-mcp-http.py            # MCP HTTP wrapper
├── services/                    # systemd service templates
└── examples/                    # Configuration examples
```

## Questions?

Feel free to open an issue with the `question` label.
