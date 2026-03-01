#!/usr/bin/env python3
"""
HTTP wrapper for klydo-mcp server.
Runs the Klydo MCP server with streamable HTTP transport.
"""
import sys
import os

# Add site-packages to path
sys.path.insert(0, '/home/lextex/.local/lib/python3.12/site-packages')

# Load API token from secure file
with open('/home/lextex/.klydo-mcp-token', 'r') as f:
    token = f.read().strip()
os.environ['KLYDO_KLYDO_API_TOKEN'] = token

# Set other environment variables (matching OpenClaw config)
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
    # Run with HTTP transport instead of stdio
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8000)
