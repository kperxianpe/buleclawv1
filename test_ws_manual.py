#!/usr/bin/env python3
"""Manual WebSocket test"""
import asyncio
import json
import websockets

async def test():
    uri = 'ws://localhost:8765'
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as ws:
            print("Connected!")
            
            # Send task start
            await ws.send(json.dumps({
                "type": "task.start",
                "payload": {"user_input": "Plan a trip to Shanghai"}
            }))
            print("Sent: task.start")
            
            # Receive response
            resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(resp)
            print(f"Received: {data['type']}")
            print(f"Payload: {json.dumps(data['payload'], indent=2)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
