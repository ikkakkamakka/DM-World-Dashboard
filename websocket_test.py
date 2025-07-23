#!/usr/bin/env python3
"""
Simple WebSocket test for Fantasy Kingdom Backend
"""

import asyncio
import websockets
import json

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BACKEND_URL = get_backend_url()
WS_URL = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws"

print(f"Testing WebSocket at: {WS_URL}")

async def test_websocket():
    try:
        print("Attempting WebSocket connection...")
        async with websockets.connect(WS_URL, timeout=10) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send test message
            await websocket.send("Hello from test")
            print("📤 Sent test message")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📥 Received: {response}")
            
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status code: {e.status_code}")
        print(f"   Headers: {e.headers}")
        return False
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timeout")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    if result:
        print("🎉 WebSocket test passed!")
    else:
        print("💥 WebSocket test failed!")