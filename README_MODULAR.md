# LiveStreamData - Modular Structure

A clean, modular organization of the LiveStreamData project for better maintainability and scalability.

## 📁 Project Structure

```
LiveStreamData/
├── app/
│   ├── __init__.py
│   ├── core/                    # Core functionality
│   │   ├── __init__.py
│   │   ├── main.py             # Single user main
│   │   ├── watcher.py          # Single user watcher
│   │   └── multi_user_watcher.py # Multi-user watcher
│   ├── websocket/              # WebSocket functionality
│   │   ├── __init__.py
│   │   ├── server.py           # WebSocket server
│   │   ├── client.py           # WebSocket client
│   │   ├── data_poster.py      # Data posting to WebSocket
│   │   ├── checker.py          # Endpoint checker
│   │   └── quick_checker.py    # Quick endpoint test
│   ├── ocr/                    # OCR functionality
│   │   ├── __init__.py
│   │   ├── engine.py           # OCR engine
│   │   └── vision.py           # Google Vision OCR
│   ├── config/                 # Configuration files
│   │   ├── __init__.py
│   │   ├── users.json          # User credentials
│   │   └── hardcoded_values.json # OCR mapping
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   └── image_utils.py      # Image processing utilities
│   └── scripts/                # Management scripts
│       ├── __init__.py
│       ├── manage_users.py     # User management
│       └── test_integration.py # Integration tests
├── main.py                     # Main entry point
├── run.py                      # Launcher script
├── requirements.txt
└── README_MODULAR.md
```

## 🚀 Quick Start

### 1. **Using the Launcher (Recommended)**
```bash
python run.py
```
This gives you a menu to choose what to run:
- Multi-User Watcher
- Single User Watcher
- WebSocket Server
- Test WebSocket Connection
- Manage Users

### 2. **Direct Commands**

**Run Multi-User System:**
```bash
python main.py
```

**Start WebSocket Server:**
```bash
python -m app.websocket.server
```

**Test WebSocket Connection:**
```bash
python -m app.websocket.quick_checker ws://localhost:8765
```

**Manage Users:**
```bash
python -m app.scripts.manage_users
```

## 📋 Configuration

### **User Configuration** (`app/config/users.json`)
```json
{
  "users": [
    {
      "id": "user1",
      "name": "User 1",
      "username": "your_email@example.com",
      "password": "your_password",
      "enabled": true,
      "capture_interval": 20,
      "max_captures": 2000
    }
  ]
}
```

### **WebSocket Configuration**
Update the endpoint in `app/websocket/data_poster.py`:
```python
NGROK_ENDPOINT = "ws://localhost:8765"  # Local
# or
NGROK_ENDPOINT = "ws://1.tcp.in.ngrok.io:20306"  # Ngrok
```

## 🔧 Key Features

### **Modular Design**
- **Core**: Dashboard monitoring and data processing
- **WebSocket**: Real-time communication
- **OCR**: Image text extraction
- **Config**: Centralized configuration
- **Utils**: Helper functions
- **Scripts**: Management tools

### **Multi-User Support**
- Concurrent processing of multiple user accounts
- Separate image directories per user
- User-specific configuration
- Independent error handling

### **Easy Management**
- Simple launcher script
- User management interface
- Configuration validation
- WebSocket testing tools

## 🛠️ Development

### **Adding New Features**
1. Create new modules in appropriate directories
2. Update imports to use relative paths
3. Add to launcher if needed

### **Testing**
```bash
# Test WebSocket
python -m app.websocket.quick_checker ws://localhost:8765

# Test integration
python -m app.scripts.test_integration

# Test OCR
python -c "from app.ocr.engine import ocr_image_google_vision; print(ocr_image_google_vision('test.png'))"
```

### **Debugging**
- Check logs in each module
- Use the launcher's test functions
- Verify configuration files

## 📊 Benefits of Modular Structure

1. **Maintainability**: Clear separation of concerns
2. **Scalability**: Easy to add new features
3. **Testing**: Isolated components for testing
4. **Configuration**: Centralized settings
5. **Reusability**: Components can be reused
6. **Documentation**: Self-documenting structure

## 🔄 Migration from Old Structure

The old files have been moved and updated:
- `watcher.py` → `app/core/watcher.py`
- `data_posting.py` → `app/websocket/data_poster.py`
- `ocr_engine.py` → `app/ocr/engine.py`
- `user_config.json` → `app/config/users.json`

All imports have been updated to use the new structure.

## 🎯 Next Steps

1. **Update your credentials** in `app/config/users.json`
2. **Test the WebSocket connection** using the launcher
3. **Run the multi-user system** with `python run.py`
4. **Monitor the logs** for each user session

The modular structure makes it easy to maintain, extend, and debug your multi-user dashboard monitoring system! 