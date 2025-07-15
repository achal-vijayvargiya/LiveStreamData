#!/usr/bin/env python3
"""
LiveStreamData - Main Entry Point
Multi-User Dashboard OCR System
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.main import main as core_main
from app.core.multi_user_watcher import MultiUserWatcher
from app.core.multi_user_watcher_fixed import MultiUserWatcherFixed
from app.core.watcher import watch_image_src

async def main():
    """Main entry point for the application"""
    print("🚀 LiveStreamData - Multi-User Dashboard OCR System")
    print("=" * 60)
    
    # You can choose which mode to run
    # For single user mode:
    # await core_main()
    # await watch_image_src()
    
    # For multi-user mode:
    watcher = MultiUserWatcher("app/config/users.json")
    await watcher.run_all_users()
    # watcher = MultiUserWatcherFixed("app/config/users.json")
    # await watcher.run_all_users()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n🛑 Shutting down gracefully.')
    except Exception as e:
        print(f'❌ Error: {e}') 