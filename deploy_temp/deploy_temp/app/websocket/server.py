#!/usr/bin/env python3
"""
WebSocket Server
Listens on localhost:8765 and echoes back client messages
"""

import asyncio
import json
import logging
from websockets import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

clients = set()

async def handle_client(websocket: WebSocketServerProtocol):
    """Handle individual client connections"""
    client_id = id(websocket)
    client_addr = websocket.remote_address
    
    logger.info(f"🟢 New client connected: {client_addr} (ID: {client_id})")
    clients.add(websocket)
    
    try:
        async for message in websocket:
            try:
                # Try to parse as JSON first
                data = json.loads(message)
                logger.info(f"📨 Received JSON from {client_addr}: {data}")
            except json.JSONDecodeError:
                # Handle plain text messages
                logger.info(f"📨 Received text from {client_addr}: {message}")
            
            # Send echo response
            echo_message = f"Echo: {message}"
            await websocket.send(echo_message)
            logger.info(f"📤 Sent echo to {client_addr}: {echo_message}")
            
    except ConnectionClosed:
        logger.info(f"🔴 Client {client_addr} disconnected normally")
    except Exception as e:
        logger.error(f"❌ Error handling client {client_addr}: {e}")
    finally:
        clients.discard(websocket)
        logger.info(f"🔴 Client {client_addr} removed from active connections")

async def main():
    """Main entry point"""
    host = 'localhost'
    port = 8765
    logger.info(f"🚀 Starting WebSocket server on {host}:{port}")
    logger.info("📋 Server will echo back all received messages")
    logger.info("💡 Use 'ngrok tcp 8765' to expose server publicly")
    
    async with serve(handle_client, host, port):
        logger.info(f"✅ Server is running and listening on ws://{host}:{port}")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}") 