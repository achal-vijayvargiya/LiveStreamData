#!/usr/bin/env python3
"""
Test script to verify WebSocket integration with data_posting.py
"""

import asyncio
import json
from ..websocket.data_poster import post_data

async def test_data_posting():
    """Test the data posting functionality"""
    print("🧪 Testing data_posting.py integration...")
    
    # Sample detected data (simulating OCR results)
    detected_data = {
        0: 42,   # col1, key 0
        1: 15,   # col1, key 1  
        2: 78,   # col1, key 2
        3: 91,   # col2, key 3
        4: 23,   # col2, key 4
        5: 56    # col2, key 5
    }
    
    print(f"📊 Sample detected data: {detected_data}")
    
    # Test the post_data function
    success = await post_data(detected_data)
    
    if success:
        print("✅ Integration test passed!")
    else:
        print("❌ Integration test failed!")
        print("💡 Make sure the WebSocket server is running: python ws_server.py")

if __name__ == "__main__":
    asyncio.run(test_data_posting()) 