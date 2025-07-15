import json
import websockets
import asyncio
import logging
from websockets.exceptions import ConnectionClosed, InvalidURI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    with open("app/config/hardcoded_values.json") as f:
        HARDCODED_NUM1 = json.load(f)
except:
    HARDCODED_NUM1 = {}

# WebSocket endpoint - can be local or ngrok
NGROK_ENDPOINT = "ws://1.tcp.in.ngrok.io:20306"
# "ws://localhost:8765"  # Default to local server
# For ngrok: "ws://1.tcp.in.ngrok.io:20306"

async def post_data(detected, image_path=None, user_info=None):
    # print(f"detect:{detected}")
    if image_path is not None:
        print(f"image_path: {image_path}")
    output = {}
    for col, keys in HARDCODED_NUM1.items():
        arr = []
        for k in keys:
            ik = int(k)
            try:
                rv = detected[ik]
            except (KeyError, IndexError):
                rv = 0
            arr.append(f"{ik:03} -> {rv}")
            output[str(col)] = arr
    print("request: \n")
    print(json.dumps(output, indent=2), flush=True)
    await _send_ws(output,user_info["request_key"])

async def _send_ws(data,request_key:str):
    try:
        logger.info(f"🔗 Connecting to WebSocket server: {NGROK_ENDPOINT}")
        async with websockets.connect(NGROK_ENDPOINT) as ws:
            logger.info("✅ Connected to WebSocket server")
            
            # Prepare the message
            message = {request_key: data}
            json_message = json.dumps(message)
            
            # Send the message
            await ws.send(json_message)
            logger.info(f"📤 Sent data: {json_message}")
            
            # Try to receive a response to confirm success
            try:
                response = await ws.recv()
                logger.info(f"📨 Received response: {response}")
                return True
            except Exception as recv_err:
                logger.warning(f"⚠️ WebSocket sent but no response received: {recv_err}")
                return False
    except ConnectionRefusedError:
        logger.error(f"❌ Connection refused. Is the server running on {NGROK_ENDPOINT}?")
        return False
    except Exception as e:
        logger.error(f"❌ Error sending data via websocket: {e}")
        return False

# Test function to demonstrate usage
async def test_websocket_connection():
    """Test the WebSocket connection with sample data"""
    sample_data = {
        "col1": ["001 -> 42", "002 -> 15", "003 -> 78"],
        "col2": ["004 -> 91", "005 -> 23", "006 -> 56"]
    }
    
    logger.info("🧪 Testing WebSocket connection...")
    success = await post_data(sample_data)
    
    if success:
        logger.info("✅ Test completed successfully!")
    else:
        logger.error("❌ Test failed!")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_websocket_connection())
