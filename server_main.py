#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueclaw WebSocket Server Entry Point

Integrates Week 15-17 core engine with WebSocket layer.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from blueclaw.server import BlueclawWebSocketServer


async def main():
    print("="*70)
    print("Blueclaw WebSocket Server")
    print("Integrating Week 15-17 Core Engine")
    print("="*70)
    print()
    print("Features:")
    print("  - Intent Analysis (Week 16)")
    print("  - Thinking Chain with Clarification (Week 16)")
    print("  - Blueprint Generation (Week 16)")
    print("  - Step Execution with Skills (Week 17)")
    print("  - Intervention & REPLAN (Week 16)")
    print("  - State Persistence (Week 16)")
    print()
    
    server = BlueclawWebSocketServer(host="localhost", port=8765)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
