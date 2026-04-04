#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start_websocket_server.py - Start Blueclaw WebSocket Server

Usage:
    python start_websocket_server.py
    python start_websocket_server.py --host 0.0.0.0 --port 8765

Note: This is a WebSocket server, not HTTP. Use WebSocket clients to connect.
      Browser access will show errors (expected behavior).
"""

import asyncio
import argparse
import signal
import sys
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from blueclaw.api import create_server


# Global flag for shutdown
shutdown_event = threading.Event()


def signal_handler(signum, frame):
    """Handle shutdown signal"""
    print("\n[WS] Received shutdown signal...")
    shutdown_event.set()


async def main():
    parser = argparse.ArgumentParser(description='Blueclaw WebSocket Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    parser.add_argument('--port', type=int, default=8765, help='Port to bind to (default: 8765)')
    args = parser.parse_args()
    
    server = create_server(host=args.host, port=args.port)
    
    # Setup signal handler (Windows compatible)
    signal.signal(signal.SIGINT, signal_handler)
    try:
        signal.signal(signal.SIGTERM, signal_handler)
    except AttributeError:
        pass  # Windows doesn't have SIGTERM
    
    print(f"""
============================================================
                    Blueclaw WebSocket Server
============================================================
  Protocol Version: 1.0.0
  Server Address:  ws://{args.host}:{args.port}
============================================================

IMPORTANT: This is a WebSocket server, NOT a HTTP server.
  - Use WebSocket clients to connect
  - Browser access will be rejected (expected)
  - Use: python test_websocket_client.py

Ready to accept connections...
Press Ctrl+C to stop.
""")
    
    # Start server in background thread
    server_task = asyncio.create_task(server.start())
    
    # Wait for shutdown signal
    while not shutdown_event.is_set():
        await asyncio.sleep(0.1)
    
    # Shutdown
    print("[WS] Shutting down server...")
    server.stop()
    
    try:
        await asyncio.wait_for(server_task, timeout=5.0)
    except asyncio.TimeoutError:
        print("[WS] Server shutdown timed out")
    
    print("[WS] Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[WS] Interrupted by user")
        sys.exit(0)
