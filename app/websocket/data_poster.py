import json
import websockets
import asyncio
import logging
from websockets.exceptions import ConnectionClosed, InvalidURI
import os
import httpx

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

# Global variable to store previous call data
_previous_call_data = {}

def validate_and_replace_zeros(current_data):
    """
    Validates current data and replaces zero values with previous call values.
    If any value in any column is zero, it gets replaced by the previous call value of that column.
    
    Args:
        current_data (dict): Current call data with format {"column": ["key -> value", ...]}
    
    Returns:
        dict: Validated data with zero values replaced by previous values
    """
    global _previous_call_data
    validated_data = {}
    
    for column, values in current_data.items():
        validated_values = []
        
        for i, value_str in enumerate(values):
            # Parse the value string (e.g., "126 -> 0")
            if " -> " in value_str:
                key, value = value_str.split(" -> ")
                current_value = int(value)
                
                # If current value is 0 and we have previous data for this column and position
                if current_value == 0 and column in _previous_call_data and i < len(_previous_call_data[column]):
                    # Get the previous value for this position
                    prev_value_str = _previous_call_data[column][i]
                    if " -> " in prev_value_str:
                        _, prev_value = prev_value_str.split(" -> ")
                        # Replace with previous value
                        validated_values.append(f"{key} -> {prev_value}")
                        logger.info(f"🔄 Replaced zero value in column {column}, position {i}: {value_str} -> {key} -> {prev_value}")
                    else:
                        validated_values.append(value_str)
                else:
                    validated_values.append(value_str)
            else:
                validated_values.append(value_str)
        
        validated_data[column] = validated_values
    
    return validated_data

def update_previous_call_data(current_data):
    """
    Updates the previous call data with current data after validation.
    
    Args:
        current_data (dict): Current validated data to store as previous
    """
    global _previous_call_data
    _previous_call_data = current_data.copy()
    logger.info("💾 Updated previous call data")

# WebSocket endpoint - can be local or ngrok
NGROK_ENDPOINT = "ws://1.tcp.in.ngrok.io:20369"
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
    # Apply validation to replace zero values with previous call values
    validated_output = validate_and_replace_zeros(output)
    
    print("request (after validation): \n")
    print(json.dumps(validated_output, indent=2), flush=True)
    
    # Send validated data
    await _send_ws(validated_output,"machine1")
    # Call the send_post function with validated_output
    await send_post(None, validated_output)
    # Update previous call data with current validated data
    update_previous_call_data(validated_output)

async def send_post(self, data):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    "https://be.khodalmaa.in/api/v1/project2_data",
                    data=json.dumps({"machine1": data}),
                    headers={"Content-Type": "application/json"}
                )
                print("Status:", response.status_code)
                print("Response:", response.text)
        except httpx.RequestError as e:
            print(f"Request failed: {e}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e.response.text}")

async def post_table_data(table_data, image_path=None, user_info=None, request_key="machine1"):
    """
    Post table data extracted from Sub Total row.
    
    Args:
        table_data: Dictionary mapping column numbers (1-10) to their Sub Total values
        image_path: Optional image path for logging
        user_info: Optional user information
        request_key: WebSocket request key (default: "machine1")
    """
    if image_path is not None:
        print(f"image_path: {image_path}")
    
    # Format: List of 10 numbers [value1, value2, ..., value10] for columns 1-10
    # Ensure proper ordering by explicitly iterating columns 1-10 in ascending order
    output = []
    for col_num in sorted(range(1, 11)):  # Columns 1-10 in order (sorted to ensure order)
        value = table_data.get(col_num, 0)
        output.append(value)
    
    print("request: \n")
    print(json.dumps(output, indent=2), flush=True)
    
    # Send data directly (no zero replacement)
    await _send_ws(output, request_key)

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
