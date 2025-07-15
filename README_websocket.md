# WebSocket Server & Client Setup

A complete WebSocket server and client implementation using Python's `websockets` library.

## 📋 Features

- **WebSocket Server** (`ws_server.py`):
  - Listens on `localhost:8765`
  - Accepts multiple client connections
  - Echoes back all received messages
  - Handles both JSON and plain text messages
  - Comprehensive logging with emojis

- **WebSocket Client** (`ws_client.py`):
  - Connects to any WebSocket server
  - Sends JSON and text messages
  - Receives and displays server responses
  - Supports command-line URI specification

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# or
pip install websockets
```

### 2. Start the Server

```bash
python ws_server.py
```

You should see:
```
🚀 Starting WebSocket server on localhost:8765
📋 Server will echo back all received messages
💡 Use 'ngrok tcp 8765' to expose server publicly
✅ Server is running and listening on ws://localhost:8765
```

### 3. Start the Client

In a new terminal:

```bash
python ws_client.py
```

You should see:
```
🔗 Connecting to ws://localhost:8765
✅ Connected to ws://localhost:8765
📤 Sent JSON: {'test': 'hello from client', 'timestamp': '2024-01-01'}
📤 Sent text: Hello server!
👂 Listening for server responses...
📨 Received: Echo: {"test": "hello from client", "timestamp": "2024-01-01"}
📨 Received: Echo: Hello server!
```

## 🌐 Exposing Server with ngrok

### 1. Install ngrok

Download from [ngrok.com](https://ngrok.com) or install via package manager.

### 2. Start ngrok tunnel

```bash
ngrok tcp 8765
```

You'll see output like:
```
Forwarding    tcp://1.tcp.in.ngrok.io:20306 -> localhost:8765
```

### 3. Connect client to ngrok URL

```bash
python ws_client.py ws://1.tcp.in.ngrok.io:20306
```

## 📝 Usage Examples

### Basic Local Usage

```bash
# Terminal 1: Start server
python ws_server.py

# Terminal 2: Start client
python ws_client.py
```

### Using ngrok for Public Access

```bash
# Terminal 1: Start server
python ws_server.py

# Terminal 2: Start ngrok tunnel
ngrok tcp 8765

# Terminal 3: Connect client to ngrok URL
python ws_client.py ws://1.tcp.in.ngrok.io:20306
```

### Custom Server URL

```bash
# Connect to a different WebSocket server
python ws_client.py ws://example.com:8080
```

## 🔧 Configuration

### Server Configuration

Edit `ws_server.py` to change:
- Host: Modify `host='localhost'` in `WebSocketServer()`
- Port: Modify `port=8765` in `WebSocketServer()`

### Client Configuration

The client accepts the server URL as a command-line argument:
```bash
python ws_client.py ws://your-server:port
```

## 📊 Message Types

### JSON Messages
```python
{"test": "hello from client", "timestamp": "2024-01-01"}
```

### Plain Text Messages
```
Hello server!
```

## 🛠️ Error Handling

Both server and client include comprehensive error handling:

- **Connection errors**: Invalid URIs, refused connections
- **Message errors**: JSON parsing, sending failures
- **Network errors**: Timeouts, disconnections
- **Graceful shutdown**: Ctrl+C handling

## 📁 File Structure

```
├── ws_server.py      # WebSocket server implementation
├── ws_client.py      # WebSocket client implementation
├── requirements.txt   # Python dependencies
└── README_websocket.md  # This file
```

## 🔍 Troubleshooting

### Common Issues

1. **"Connection refused"**
   - Ensure server is running: `python ws_server.py`
   - Check port 8765 is not in use

2. **"Invalid URI"**
   - Use correct WebSocket URL format: `ws://host:port`
   - For ngrok: `ws://1.tcp.in.ngrok.io:20306`

3. **ngrok connection issues**
   - Verify ngrok tunnel is active
   - Check ngrok URL is correct
   - Ensure server is running locally

### Debug Mode

Add more verbose logging by modifying the logging level in both files:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🎯 Next Steps

- Add authentication
- Implement message queuing
- Add SSL/TLS support
- Create a web-based client
- Add message persistence

## 📄 License

This project is open source and available under the MIT License. 