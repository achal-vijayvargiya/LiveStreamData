#!/usr/bin/env python3
"""
WebSocket Server
Listens on all interfaces using PORT environment variable
"""

import asyncio
import json
import logging
import os
from websockets import serve, WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

clients = set()
cleanup_tasks = []

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

async def health_check(request):
    """Health check endpoint for Cloud Run"""
    return web.Response(text="OK", status=200)

async def cleanup():
    """Cleanup function to close all connections"""
    logger.info("🧹 Running cleanup tasks...")
    
    # Close WebSocket server
    for task in cleanup_tasks:
        try:
            if hasattr(task, 'close'):
                await task.close()
            elif hasattr(task, 'cancel'):
                task.cancel()
                await task
        except Exception as e:
            logger.debug(f"Cleanup task completed: {e}")
    
    # Close all client connections
    close_tasks = [client.close() for client in clients]
    if close_tasks:
        await asyncio.gather(*close_tasks, return_exceptions=True)
    
    logger.info("✅ Cleanup completed")

async def start_http_server(host, port, app):
    """Start the HTTP server with retry logic"""
    retries = 3
    while retries > 0:
        try:
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()
            logger.info(f"✅ HTTP server running on http://{host}:{port}")
            cleanup_tasks.append(runner)
            return True
        except OSError as e:
            retries -= 1
            if retries == 0:
                logger.error(f"❌ Failed to start HTTP server after all retries: {e}")
                return False
            logger.warning(f"⚠️ Failed to bind HTTP port {port}, trying again... ({retries} retries left)")
            await asyncio.sleep(1)
    return False

async def start_websocket_server(host, port):
    """Start the WebSocket server with retry logic"""
    retries = 3
    while retries > 0:
        try:
            # Create the server but don't await it yet
            ws_server = serve(handle_client, host, port)
            logger.info(f"✅ WebSocket server running on ws://{host}:{port}")
            cleanup_tasks.append(ws_server)
            return ws_server  # Return the server object
        except OSError as e:
            retries -= 1
            if retries == 0:
                logger.error(f"❌ Failed to start WebSocket server after all retries: {e}")
                return None
            logger.warning(f"⚠️ Failed to bind WebSocket port {port}, trying again... ({retries} retries left)")
            await asyncio.sleep(1)
    return None

async def main():
    """Main entry point"""
    # Get ports from environment variables
    http_port = int(os.environ.get('PORT', '8080'))  # Cloud Run expects PORT=8080
    ws_port = int(os.environ.get('WS_PORT', '8765'))  # Default WebSocket port
    host = '0.0.0.0'  # Listen on all interfaces
    
    # Create aiohttp app for health checks
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)  # Root path health check
    
    # Start HTTP server
    if not await start_http_server(host, http_port, app):
        return
    
    # Start WebSocket server
    ws_server = await start_websocket_server(host, ws_port)
    if not ws_server:
        return
    
    try:
        # Run the WebSocket server forever
        await ws_server
    finally:
        await cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}") 