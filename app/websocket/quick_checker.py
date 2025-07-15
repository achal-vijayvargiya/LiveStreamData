#!/usr/bin/env python3
"""
Quick WebSocket Endpoint Checker
Simple command-line tool to test endpoint accessibility
"""

import asyncio
import websockets
import sys

async def quick_check(uri):
    """Quick check if endpoint is accessible"""
    try:
        print(f"🔍 Testing: {uri}")
        async with websockets.connect(uri) as ws:
            print("✅ CONNECTED!")
            return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

async def main():
    if len(sys.argv) != 2:
        print("Usage: python quick_check.py <websocket_uri>")
        print("Example: python quick_check.py ws://localhost:8765")
        return
    
    uri = sys.argv[1]
    success = await quick_check(uri)
    
    if success:
        print("🎉 Endpoint is accessible!")
    else:
        print("💡 Try starting the server: python ws_server.py")

if __name__ == "__main__":
    asyncio.run(main()) 