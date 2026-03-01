# Security Policy

## Supported Versions

Currently, only the latest version of this setup is supported.

## Reporting a Vulnerability

If you discover a security vulnerability in this setup, please:

1. **Do NOT** open a public issue
2. Send an email to the maintainer privately
3. Include details about:
   - The nature of the vulnerability
   - Steps to reproduce
   - Potential impact

The maintainer will:
- Acknowledge receipt within 48 hours
- Provide a preliminary response within 7 days
- Work on a fix if applicable

## Security Best Practices

When setting up your own homelab based on this configuration:

1. **Change all default credentials** - Never use example passwords
2. **Use strong SSH keys** - Disable password authentication
3. **Keep software updated** - Regularly `apt update && apt upgrade`
4. **Review firewall rules** - Only expose necessary ports
5. **Monitor logs** - Check `journalctl` regularly for suspicious activity
6. **Backup regularly** - Keep copies of important configurations

## Sensitive Files

The following files should NEVER be committed to version control:
- API tokens and secrets
- SSH private keys
- TLS/SSL certificates
- Database credentials
- `.env` files containing secrets

This repository uses example configurations only. Always create your own secure configurations.
