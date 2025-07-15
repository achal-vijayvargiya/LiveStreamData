#!/usr/bin/env python3
"""
WebSocket Client
Connects to a WebSocket server and sends JSON messages
"""

import asyncio
import json
import logging
import sys
from websockets import connect, WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, InvalidURI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketClient:
    def __init__(self, uri="ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
    
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            logger.info(f"🔗 Connecting to {self.uri}")
            self.websocket = await connect(self.uri)
            logger.info(f"✅ Connected to {self.uri}")
            return True
        except InvalidURI as e:
            logger.error(f"❌ Invalid URI: {e}")
            return False
        except ConnectionRefusedError:
            logger.error(f"❌ Connection refused. Is the server running on {self.uri}?")
            return False
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    async def send_message(self, message):
        """Send a message to the server"""
        if not self.websocket:
            logger.error("❌ Not connected to server")
            return False
        
        try:
            if isinstance(message, dict):
                # Send as JSON
                json_message = json.dumps(message)
                await self.websocket.send(json_message)
                logger.info(f"📤 Sent JSON: {message}")
            else:
                # Send as text
                await self.websocket.send(str(message))
                logger.info(f"📤 Sent text: {message}")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return False
    
    async def receive_messages(self):
        """Receive and print messages from the server"""
        if not self.websocket:
            logger.error("❌ Not connected to server")
            return
        
        try:
            async for message in self.websocket:
                logger.info(f"📨 Received: {message}")
        except ConnectionClosed:
            logger.info("🔴 Connection closed by server")
        except Exception as e:
            logger.error(f"❌ Error receiving message: {e}")
    
    async def close(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔴 Connection closed")

async def main():
    """Main entry point"""
    # Default to localhost, but allow command line argument
    uri = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
    
    client = WebSocketClient(uri)
    
    try:
        # Connect to server
        if not await client.connect():
            logger.error("❌ Failed to connect. Exiting.")
            return
        
        # Send a test JSON message
        test_message = {"test": "hello from client", "timestamp": "2024-01-01"}
        await client.send_message(test_message)
        
        # Send a plain text message
        await client.send_message("Hello server!")
        
        # Listen for responses
        logger.info("👂 Listening for server responses...")
        await client.receive_messages()
        
    except KeyboardInterrupt:
        logger.info("🛑 Client stopped by user")
    except Exception as e:
        logger.error(f"❌ Client error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main()) 